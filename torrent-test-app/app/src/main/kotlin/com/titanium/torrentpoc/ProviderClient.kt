package com.titanium.torrentpoc

import java.net.HttpURLConnection
import java.net.URL
import org.json.JSONObject

data class ProviderSource(
    val name: String,
    val label: String?,
    val infoHash: String,
    val fileIndex: Int?,
    val filenameHint: String?,
    val trackers: List<String>,
    val webSeeds: List<String>,
)

object ProviderClient {

    fun fetchMany(url: String): List<ProviderSource> {
        val connection = URL(url).openConnection() as HttpURLConnection
        try {
            connection.connectTimeout = 12_000
            connection.readTimeout = 12_000
            connection.setRequestProperty("Accept", "application/json")

            val code = connection.responseCode
            require(code in 200..299) { "Provider HTTP $code" }

            val body = connection.inputStream.bufferedReader().use { it.readText() }
            val root = JSONObject(body)
            val array = root.getJSONArray("sources")

            return List(array.length()) { index ->
                parseSource(array.getJSONObject(index))
            }
        } finally {
            connection.disconnect()
        }
    }

    fun fetch(url: String): ProviderSource =
        fetchMany(url).first()

    private fun parseSource(json: JSONObject): ProviderSource {
        val trackers = json.optJSONArray("trackers")?.let { array ->
            List(array.length()) { index -> array.getString(index) }
        } ?: emptyList()

        val webSeeds = json.optJSONArray("webSeeds")?.let { array ->
            List(array.length()) { index -> array.getString(index) }
        } ?: emptyList()

        val infoHash = json.getString("infoHash").trim()
        require(infoHash.length == 40 || infoHash.length == 64) {
            "Provider returned invalid infoHash"
        }

        return ProviderSource(
            name = json.optString("name", "Provider source"),
            label = json.optString("label", "").takeIf { it.isNotBlank() },
            infoHash = infoHash,
            fileIndex = if (json.isNull("fileIndex")) null else json.getInt("fileIndex"),
            filenameHint = json.optString("filenameHint", "").takeIf { it.isNotBlank() },
            trackers = trackers,
            webSeeds = webSeeds,
        )
    }
}
