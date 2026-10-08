package com.titanium.torrentpoc

import android.app.Activity
import android.content.ClipboardManager
import android.content.Context
import android.graphics.Color
import android.os.Bundle
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.media3.common.MediaItem
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import com.nuvio.engine.NuvioEngine
import com.nuvio.engine.NuvioEngineConfig
import com.nuvio.engine.NuvioStream
import com.nuvio.engine.NuvioTorrentFile
import com.nuvio.engine.NuvioTorrentProfile
import com.nuvio.engine.NuvioUploadMode
import java.io.File
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : Activity() {

    private val uiScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    private lateinit var rootLayout: LinearLayout
    private lateinit var magnetInput: EditText
    private lateinit var sourceList: LinearLayout
    private lateinit var startButton: Button
    private lateinit var stopButton: Button
    private lateinit var statusText: TextView
    private lateinit var statsText: TextView
    private lateinit var playerView: PlayerView

    private var engine: NuvioEngine? = null
    private var player: ExoPlayer? = null
    private var currentTorrentId: String? = null
    private var currentStream: NuvioStream? = null
    private var statsJob: Job? = null
    private var fullscreen = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        buildUi()
        ensureEngine()
    }

    private fun buildUi() {
        rootLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.rgb(10, 10, 12))
            setPadding(dp(20), dp(16), dp(20), dp(16))
        }

        val title = TextView(this).apply {
            text = "TITANIUM — TORRENT STREAM TEST"
            setTextColor(Color.WHITE)
            textSize = 22f
            setPadding(0, 0, 0, dp(10))
        }
        rootLayout.addView(title)

        magnetInput = EditText(this).apply {
            hint = "Paste a magnet link"
            setHintTextColor(Color.GRAY)
            setTextColor(Color.WHITE)
            setBackgroundColor(Color.rgb(35, 35, 40))
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS
            isSingleLine = true
            setPadding(dp(12), dp(8), dp(12), dp(8))
        }
        rootLayout.addView(
            magnetInput,
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                dp(52)
            )
        )

        val buttonRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }

        val loadTestButton = Button(this).apply {
            text = "LOAD SOURCES"
            isFocusable = true
            setOnClickListener {
                if (engine == null) {
                    status("Engine is still starting.")
                } else {
                    isEnabled = false
                    status("Fetching provider results...")
                    uiScope.launch {
                        try {
                            val sources = withContext(Dispatchers.IO) {
                                ProviderClient.fetchMany(PROVIDER_URL)
                            }
                            renderSourceButtons(sources)
                            status("Provider returned ${sources.size} sources. Choose one.")
                            isEnabled = true
                        } catch (error: Throwable) {
                            status("PROVIDER ERROR: ${error.message ?: error.javaClass.simpleName}")
                            isEnabled = true
                        }
                    }
                }
            }
        }

        val pasteButton = Button(this).apply {
            text = "PASTE"
            isFocusable = true
            setOnClickListener {
                val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val text = clipboard.primaryClip
                    ?.getItemAt(0)
                    ?.coerceToText(this@MainActivity)
                    ?.toString()
                    .orEmpty()
                if (text.isNotBlank()) {
                    magnetInput.setText(text)
                    status("Magnet pasted.")
                } else {
                    status("Clipboard is empty.")
                }
            }
        }

        startButton = Button(this).apply {
            text = "START"
            isFocusable = true
            setOnClickListener { startTorrent() }
        }

        stopButton = Button(this).apply {
            text = "STOP"
            isFocusable = true
            isEnabled = false
            setOnClickListener { stopCurrent() }
        }

        for (button in listOf(loadTestButton, pasteButton, startButton, stopButton)) {
            buttonRow.addView(
                button,
                LinearLayout.LayoutParams(0, dp(50), 1f).apply {
                    setMargins(dp(4), dp(8), dp(4), dp(8))
                }
            )
        }
        rootLayout.addView(buttonRow)

        sourceList = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            visibility = View.GONE
        }
        rootLayout.addView(sourceList)

        statusText = TextView(this).apply {
            text = "Starting engine..."
            setTextColor(Color.WHITE)
            textSize = 15f
            setPadding(0, dp(2), 0, dp(4))
        }
        rootLayout.addView(statusText)

        statsText = TextView(this).apply {
            text = ""
            setTextColor(Color.LTGRAY)
            textSize = 13f
            setPadding(0, 0, 0, dp(6))
        }
        rootLayout.addView(statsText)

        playerView = PlayerView(this).apply {
            setBackgroundColor(Color.BLACK)
            useController = true
            isFocusable = true
            visibility = View.GONE
        }
        rootLayout.addView(
            playerView,
            LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                0,
                1f
            )
        )

        setContentView(rootLayout)
        loadTestButton.requestFocus()
    }

    private fun ensureEngine() {
        uiScope.launch {
            try {
                val created = withContext(Dispatchers.IO) {
                    val dataDir = File(filesDir, "nuvio-data").apply { mkdirs() }
                    val torrentCache = File(cacheDir, "nuvio-torrent-cache").apply { mkdirs() }
                    NuvioEngine.create(
                        NuvioEngineConfig(
                            dataDirectory = dataDir,
                            cacheDirectory = torrentCache,
                            memoryCacheCapacityBytes = 64L * 1024L * 1024L,
                            diskCacheCapacityBytes = 768L * 1024L * 1024L,
                            torrentProfile = NuvioTorrentProfile.Balanced,
                            uploadMode = NuvioUploadMode.Disabled
                        )
                    )
                }
                engine = created
                status("Engine ready — Nuvio ${NuvioEngine.version}. Choose LOAD SOURCES.")
            } catch (error: Throwable) {
                status("ENGINE ERROR: ${error.message ?: error.javaClass.simpleName}")
            }
        }
    }

    private fun renderSourceButtons(sources: List<ProviderSource>) {
        sourceList.removeAllViews()

        sources.forEach { source ->
            val button = Button(this).apply {
                text = "${source.label ?: "Source"}  •  ${source.name}"
                isFocusable = true
                setOnClickListener {
                    magnetInput.setText(MagnetBuilder.from(source))
                    status("Selected ${source.name}. Starting torrent...")
                    startTorrent()
                }
            }
            sourceList.addView(
                button,
                LinearLayout.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    dp(54)
                ).apply {
                    setMargins(dp(4), dp(3), dp(4), dp(3))
                }
            )
        }

        sourceList.visibility = if (sources.isEmpty()) View.GONE else View.VISIBLE
        if (sourceList.childCount > 0) {
            sourceList.getChildAt(0).requestFocus()
        }
    }

    private fun startTorrent() {
        val magnet = magnetInput.text?.toString()?.trim().orEmpty()
        if (!magnet.startsWith("magnet:?")) {
            status("Enter a valid magnet link first.")
            return
        }

        val localEngine = engine
        if (localEngine == null) {
            status("Engine is still starting.")
            return
        }

        startButton.isEnabled = false
        stopButton.isEnabled = true
        status("Reading torrent metadata...")

        uiScope.launch {
            try {
                releasePlayerOnly()
                stopEngineStreamOnly()

                val result = withContext(Dispatchers.IO) {
                    val torrentId = localEngine.addMagnet(magnet)
                    val files = localEngine.files(torrentId)
                    val selected = chooseVideo(files)
                        ?: error("Torrent contains no files")
                    val stream = localEngine.prepareStream(
                        torrentId = torrentId,
                        fileIndex = selected.index,
                        filenameHint = selected.path,
                        minimumContiguousBytes = 4L * 1024L * 1024L
                    )
                    Triple(torrentId, selected, stream)
                }

                currentTorrentId = result.first
                currentStream = result.third
                status("Playing: ${result.second.path}")

                val exo = ExoPlayer.Builder(this@MainActivity).build()
                player = exo
                playerView.player = exo
                exo.setMediaItem(MediaItem.fromUri(result.third.url))
                exo.prepare()
                exo.playWhenReady = true
                startStats(result.third)
                enterFullscreen()
            } catch (error: CancellationException) {
                throw error
            } catch (error: Throwable) {
                status("START ERROR: ${error.message ?: error.javaClass.simpleName}")
                startButton.isEnabled = true
                stopButton.isEnabled = false
            }
        }
    }

    private fun chooseVideo(files: List<NuvioTorrentFile>): NuvioTorrentFile? {
        val preferred = files.filter {
            val lower = it.path.lowercase()
            lower.endsWith(".mp4") ||
                lower.endsWith(".mkv") ||
                lower.endsWith(".webm") ||
                lower.endsWith(".m4v") ||
                lower.endsWith(".mov") ||
                lower.endsWith(".avi") ||
                lower.endsWith(".ts")
        }
        return (preferred.ifEmpty { files }).maxByOrNull { it.size }
    }

    private fun startStats(stream: NuvioStream) {
        statsJob?.cancel()
        statsJob = uiScope.launch {
            while (isActive && currentStream?.id == stream.id) {
                try {
                    val streamStats = withContext(Dispatchers.IO) {
                        engine?.currentStreamStats(stream.id)
                    }
                    val engineStats = engine?.stats?.value
                    if (streamStats != null && engineStats != null) {
                        statsText.text =
                            "Peers ${engineStats.connectedPeers}  Seeds ${engineStats.connectedSeeds}  " +
                            "Down ${formatRate(engineStats.downloadRateBytesPerSecond)}  " +
                            "Ready ${formatBytes(streamStats.contiguousReadyBytes)}"
                    }
                } catch (_: Throwable) {
                    // Diagnostic only.
                }
                delay(1000)
            }
        }
    }

    private fun stopCurrent() {
        uiScope.launch {
            releasePlayerOnly()
            stopEngineStreamOnly()
            status("Stopped. Ready for another test.")
            statsText.text = ""
            startButton.isEnabled = true
            stopButton.isEnabled = false
            exitFullscreen()
            rootLayout.getChildAt(2).requestFocus()
        }
    }

    private suspend fun stopEngineStreamOnly() {
        statsJob?.cancel()
        statsJob = null

        val localEngine = engine
        val stream = currentStream
        val torrentId = currentTorrentId
        currentStream = null
        currentTorrentId = null

        withContext(Dispatchers.IO) {
            if (localEngine != null && stream != null) {
                runCatching { localEngine.stopStream(stream.id) }
            }
            if (localEngine != null && torrentId != null) {
                runCatching { localEngine.removeTorrent(torrentId) }
            }
        }
    }

    private fun enterFullscreen() {
        fullscreen = true
        for (i in 0 until rootLayout.childCount) {
            rootLayout.getChildAt(i).visibility = View.GONE
        }
        playerView.visibility = View.VISIBLE
        playerView.layoutParams = LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            0,
            1f
        )
        window.decorView.systemUiVisibility =
            View.SYSTEM_UI_FLAG_FULLSCREEN or
            View.SYSTEM_UI_FLAG_HIDE_NAVIGATION or
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
        playerView.requestFocus()
    }

    private fun exitFullscreen() {
        fullscreen = false
        window.decorView.systemUiVisibility = View.SYSTEM_UI_FLAG_VISIBLE
        for (i in 0 until rootLayout.childCount) {
            rootLayout.getChildAt(i).visibility = View.VISIBLE
        }
        playerView.visibility = View.GONE
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (fullscreen) {
            stopCurrent()
        } else {
            super.onBackPressed()
        }
    }

    private fun releasePlayerOnly() {
        playerView.player = null
        player?.release()
        player = null
    }

    private fun status(message: String) {
        statusText.text = message
    }

    override fun onDestroy() {
        statsJob?.cancel()
        releasePlayerOnly()
        engine?.close()
        engine = null
        uiScope.cancel()
        super.onDestroy()
    }

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).toInt()

    private fun formatRate(bytesPerSecond: Long): String =
        if (bytesPerSecond >= 1024L * 1024L) {
            String.format("%.1f MB/s", bytesPerSecond / (1024.0 * 1024.0))
        } else {
            String.format("%.0f KB/s", bytesPerSecond / 1024.0)
        }

    private fun formatBytes(bytes: Long): String =
        if (bytes >= 1024L * 1024L) {
            String.format("%.1f MB", bytes / (1024.0 * 1024.0))
        } else {
            String.format("%.0f KB", bytes / 1024.0)
        }

    companion object {
        private const val PROVIDER_URL =
            "https://raw.githubusercontent.com/fwhwindows-cmd/titanium-releases/torrent-poc/torrent-test-app/provider/legal-sources.json"
    }
}
