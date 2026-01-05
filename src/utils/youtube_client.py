# src/utils/youtube_client.py
import os
import asyncio
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode
import httpx
from cachetools import TTLCache

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
MAX_RESULTS = int(os.getenv("YOUTUBE_SEARCH_MAX_RESULTS", "3"))
CACHE_TTL = int(os.getenv("VIDEO_CACHE_TTL_SECONDS", "900"))  # seconds

_video_cache = TTLCache(maxsize=1024, ttl=CACHE_TTL)

def _yt_search_url(params: Dict[str, Any]) -> str:
    base = "https://www.googleapis.com/youtube/v3/search"
    p = params.copy()
    p["key"] = YOUTUBE_API_KEY
    return f"{base}?{urlencode(p)}"

async def _fetch_json(client: httpx.AsyncClient, url: str) -> dict:
    resp = await client.get(url, timeout=10.0)
    resp.raise_for_status()
    return resp.json()

async def search_videos(query: str,
                        channel_ids: Optional[List[str]] = None,
                        max_results: int = MAX_RESULTS) -> List[Dict[str, Any]]:
    """
    Search videos by query. If channel_ids provided, aggregate results per channel
    (ensures videos come from your curated official channels).
    Returns list of dicts: videoId, title, channelTitle, thumbnail, url, publishedAt
    """
    if not YOUTUBE_API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY not set")

    channels_key = ",".join(sorted(channel_ids)) if channel_ids else "ALL"
    cache_key = f"q:{query}|ch:{channels_key}|max:{max_results}"
    if cache_key in _video_cache:
        return _video_cache[cache_key]

    results: List[Dict[str, Any]] = []
    async with httpx.AsyncClient() as client:
        if channel_ids:
            sem = asyncio.Semaphore(6)

            async def search_channel(ch_id: str):
                async with sem:
                    params = {
                        "part": "snippet",
                        "channelId": ch_id,
                        "q": query,
                        "type": "video",
                        "order": "date",
                        "maxResults": min(5, max_results)
                    }
                    url = _yt_search_url(params)
                    try:
                        data = await _fetch_json(client, url)
                    except Exception:
                        return []
                    out = []
                    for it in data.get("items", []):
                        vid = it.get("id", {}).get("videoId")
                        if not vid:
                            continue
                        snip = it.get("snippet", {})
                        thumb = (snip.get("thumbnails", {}) or {}).get("high", {}).get("url") \
                                or (snip.get("thumbnails", {}) or {}).get("default", {}).get("url")
                        out.append({
                            "videoId": vid,
                            "title": snip.get("title"),
                            "channelTitle": snip.get("channelTitle"),
                            "thumbnail": thumb,
                            "url": f"https://www.youtube.com/watch?v={vid}",
                            "publishedAt": snip.get("publishedAt")
                        })
                    return out

            tasks = [search_channel(ch) for ch in channel_ids]
            channel_results = await asyncio.gather(*tasks)
            for sub in channel_results:
                results.extend(sub)

        else:
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "order": "relevance",
                "maxResults": max_results
            }
            url = _yt_search_url(params)
            try:
                data = await _fetch_json(client, url)
                for it in data.get("items", []):
                    vid = it.get("id", {}).get("videoId")
                    if not vid:
                        continue
                    snip = it.get("snippet", {})
                    thumb = (snip.get("thumbnails", {}) or {}).get("high", {}).get("url") \
                            or (snip.get("thumbnails", {}) or {}).get("default", {}).get("url")
                    results.append({
                        "videoId": vid,
                        "title": snip.get("title"),
                        "channelTitle": snip.get("channelTitle"),
                        "thumbnail": thumb,
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "publishedAt": snip.get("publishedAt")
                    })
            except Exception:
                results = []

    # sort by publishedAt (recent first) and limit
    results_sorted = sorted(results, key=lambda i: i.get("publishedAt") or "", reverse=True)
    limited = results_sorted[:max_results]
    _video_cache[cache_key] = limited
    return limited
