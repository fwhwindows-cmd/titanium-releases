package com.titanium.torrentpoc

import java.net.URLEncoder

object MagnetBuilder {

    fun from(source: ProviderSource): String {
        val parts = mutableListOf("xt=urn:btih:${source.infoHash}")
        parts += "dn=${encode(source.name)}"
        source.trackers.forEach { parts += "tr=${encode(it)}" }
        source.webSeeds.forEach { parts += "ws=${encode(it)}" }
        return "magnet:?${parts.joinToString("&")}"
    }

    private fun encode(value: String): String =
        URLEncoder.encode(value, "UTF-8")
}
