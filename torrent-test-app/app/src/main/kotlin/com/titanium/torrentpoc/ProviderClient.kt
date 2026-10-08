package com.titanium.torrentpoc

import java.net.HttpURLConnection
import java.net.URL
import org.json.JSONObject

data class ProviderSource(
    val name: String,
    val infoHash: String,
    val fileIndex: Int?,
    val filenameHint: String?,
    val trackers: List<String>,
    val webSeeds: List<String>,
)

object ProviderClient {

    fun fetch(url: String): ProviderSource {
        val connection = URL(url).openConnection() as HttpURLConnection
        try {
            connection.connectTimeout = 12_000
            connection.readTimeout = 12_000
            connection.setRequestProperty("Accept", "application/json")

            val code = connection.responseCode
            require(code in 200..299) { "Provider HTTP $code" }

            val body = connection.inputStream.bufferedReader().use { it.readText() }
            val json = JSONObject(body)

            val trackers = json.optJSONArray("trackers")?.let { array ->
                List(array.length()) { index -> array.getString(index) }
            } ?: emptyList()

            val webSeeds = json.optJSONArray("webSeeds")?.let { array ->
                List(array.length()) { index -> array.getString(index) }
            } ?: emptyList()

            return ProviderSource(
                name = json.optString("name", "Provider source"),
                infoHash = json.getString("infoHash").trim(),
                fileIndex = if (json.isNull("fileIndex")) null else json.getInt("fileIndex"),
                filenameHint = json.optString("filenameHint", "").takeIf { it.isNotBlank() },
                trackers = trackers,
                webSeeds = webSeeds,
            )
        } finally {
            connection.disconnect()
        }
    }
}
