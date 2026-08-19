"""Strict parsing helpers for URLs accepted by ClipCatcher."""
from __future__ import annotations

import re
from typing import Dict, Optional
from urllib.parse import parse_qs, urlsplit


_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_CHZZK_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
    "youtu.be",
    "www.youtu.be",
}


def _normalized_parts(url: str):
    candidate = (url or "").strip()
    try:
        parts = urlsplit(candidate)
        port = parts.port
    except ValueError:
        return None
    if parts.scheme.lower() != "https":
        return None
    if parts.username or parts.password or port not in {None, 443}:
        return None
    if not parts.hostname:
        return None
    return candidate, parts


def is_youtube_url(url: str) -> bool:
    """Return whether *url* is a fully supported YouTube video URL."""
    parsed = parse_media_url(url)
    return bool(parsed and parsed.get("type") == "youtube")


def parse_media_url(url: str) -> Optional[Dict[str, str]]:
    """Parse a supported CHZZK or YouTube page URL without substring matching."""
    normalized = _normalized_parts(url)
    if not normalized:
        return None
    candidate, parts = normalized
    host = (parts.hostname or "").lower()
    path_parts = [part for part in parts.path.split("/") if part]

    if host == "chzzk.naver.com":
        if len(path_parts) == 2 and path_parts[0] == "video" and path_parts[1].isdigit():
            return {"type": "vod", "id": path_parts[1]}
        if (
            len(path_parts) == 2
            and path_parts[0] == "clips"
            and _CHZZK_ID_RE.fullmatch(path_parts[1])
        ):
            return {"type": "clip", "id": path_parts[1]}
        return None

    if host not in _YOUTUBE_HOSTS:
        return None

    video_id = ""
    if host in {"youtu.be", "www.youtu.be"}:
        if len(path_parts) == 1:
            video_id = path_parts[0]
    elif path_parts == ["watch"]:
        video_id = (parse_qs(parts.query).get("v") or [""])[0]
    elif len(path_parts) == 2 and path_parts[0] in {"shorts", "live", "embed"}:
        video_id = path_parts[1]

    if not _VIDEO_ID_RE.fullmatch(video_id):
        return None
    return {"type": "youtube", "id": video_id, "url": candidate}
