package com.titanium.torrentpoc

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/**
 * POC 004: provider-neutral discovery. This does not modify playback or Basic.
 * Pass a fully configured Stremio-compatible addon base URL (Torrentio/AIOStreams),
 * or a JSON endpoint using the POC 003 {"sources":[...]} format.
 */
data class TitaniumSource(
    val provider: String,
    val title: String,
    val url: String? = null,
    val infoHash: String? = null,
    val fileIndex: Int? = null,
    val filenameHint: String? = null,
    val quality: String? = null
) {
    val playable: Boolean get() = !url.isNullOrBlank() || !infoHash.isNullOrBlank()
}

object TitaniumProviderRegistry {
    private fun getJson(url: String): JSONObject {
        require(url.startsWith("https://")) { "HTTPS provider URL required" }
        val connection = URL(url).openConnection() as HttpURLConnection
        try {
            connection.connectTimeout = 12000
            connection.readTimeout = 12000
            connection.instanceFollowRedirects = false
            connection.setRequestProperty("Accept", "application/json")
            require(connection.responseCode in 200..299) {
                "Provider HTTP ${connection.responseCode}"
            }
            val text = connection.inputStream.bufferedReader().use { it.readText() }
            require(text.length <= 2_000_000) { "Provider response too large" }
            return JSONObject(text)
        } finally {
            connection.disconnect()
        }
    }

    /** For example: https://addon.example/config/stream/movie/tt1234567.json */
    fun stremio(addonBaseUrl: String, type: String, id: String, provider: String): List<TitaniumSource> {
        require(type == "movie" || type == "series") { "Invalid content type" }
        require(Regex("[A-Za-z0-9:_-]{1,150}").matches(id)) { "Invalid content ID" }
        val endpoint = addonBaseUrl.trimEnd('/') + "/stream/" + type + "/" + id + ".json"
        val array = getJson(endpoint).optJSONArray("streams") ?: return emptyList()
        return (0 until array.length()).mapNotNull { i ->
            val item = array.optJSONObject(i) ?: return@mapNotNull null
            val hash = item.optString("infoHash").takeIf {
                Regex("(?i)[a-f0-9]{40}|[a-f0-9]{64}").matches(it)
            }
            val direct = item.optString("url").takeIf {
                it.startsWith("https://") || it.startsWith("http://")
            }
            if (hash == null && direct == null) return@mapNotNull null
            TitaniumSource(
                provider = provider,
                title = item.optString("title").ifBlank { item.optString("name", provider) },
                url = direct,
                infoHash = hash,
                fileIndex = item.optInt("fileIdx", -1).takeIf { it >= 0 },
                filenameHint = item.optString("filename").takeIf { it.isNotBlank() },
                quality = item.optString("name").takeIf { it.isNotBlank() }
            )
        }
    }

    /** Retains compatibility with the existing legal-sources.json POC. */
    fun pocJson(endpoint: String, provider: String): List<TitaniumSource> {
        val array = getJson(endpoint).optJSONArray("sources") ?: return emptyList()
        return (0 until array.length()).mapNotNull { i ->
            val item = array.optJSONObject(i) ?: return@mapNotNull null
            val hash = item.optString("infoHash").takeIf {
                Regex("(?i)[a-f0-9]{40}|[a-f0-9]{64}").matches(it)
            }
            val direct = item.optString("url").takeIf {
                it.startsWith("https://") || it.startsWith("http://")
            }
            if (hash == null && direct == null) return@mapNotNull null
            TitaniumSource(
                provider = provider,
                title = item.optString("name", provider),
                url = direct,
                infoHash = hash,
                fileIndex = item.optInt("fileIndex", -1).takeIf { it >= 0 },
                filenameHint = item.optString("filenameHint").takeIf { it.isNotBlank() },
                quality = item.optString("label").takeIf { it.isNotBlank() }
            )
        }
    }

    fun deduplicate(sources: List<TitaniumSource>): List<TitaniumSource> =
        sources.filter { it.playable }.distinctBy {
            it.infoHash?.lowercase()?.let { hash -> "hash:$hash:${it.fileIndex ?: -1}" }
                ?: "url:${it.url}"
        }
}
