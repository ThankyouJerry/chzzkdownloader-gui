"""CHZZK API client used by ClipCatcher."""
from __future__ import annotations

import asyncio
import json
from typing import Dict, List, Optional
from urllib.parse import urlsplit

import aiohttp

from core.url_utils import parse_media_url


class ChzzkAPI:
    """Fetch public CHZZK VOD and clip metadata."""

    BASE_URL = "https://api.chzzk.naver.com"
    API_RESPONSE_LIMIT = 5 * 1024 * 1024
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(self, request_timeout: Optional[aiohttp.ClientTimeout] = None):
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36"
            ),
            "Accept": "application/json",
        }
        self.request_timeout = request_timeout or aiohttp.ClientTimeout(
            total=20,
            connect=5,
            sock_read=15,
        )

    @staticmethod
    def parse_url(url: str) -> Optional[Dict[str, str]]:
        """Return the supported media type and identifier for the main UI."""
        return parse_media_url(url)

    async def _request_json(self, url: str, headers: Dict[str, str]) -> Dict:
        """Fetch a bounded JSON response with retries for transient failures."""
        last_was_timeout = False
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession(timeout=self.request_timeout) as session:
                    async with session.get(
                        url,
                        headers=headers,
                        allow_redirects=False,
                    ) as response:
                        if response.status == 200:
                            payload = bytearray()
                            async for chunk in response.content.iter_chunked(64 * 1024):
                                payload.extend(chunk)
                                if len(payload) > self.API_RESPONSE_LIMIT:
                                    raise RuntimeError(
                                        "CHZZK API 응답이 허용 크기를 초과했습니다."
                                    )
                            try:
                                data = json.loads(
                                    bytes(payload).decode(response.charset or "utf-8")
                                )
                            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                                raise RuntimeError(
                                    "CHZZK API 응답 형식이 올바르지 않습니다."
                                ) from exc
                            if not isinstance(data, dict):
                                raise RuntimeError(
                                    "CHZZK API 응답 형식이 올바르지 않습니다."
                                )
                            return data

                        if response.status in {401, 403}:
                            raise RuntimeError(
                                "CHZZK 콘텐츠에 접근할 수 없습니다. "
                                "로그인 쿠키 또는 시청 권한을 확인해주세요."
                            )
                        if response.status == 404:
                            raise RuntimeError("CHZZK 콘텐츠를 찾을 수 없습니다.")
                        if response.status not in self.RETRYABLE_STATUS_CODES:
                            raise RuntimeError(
                                f"CHZZK API 요청 실패 (HTTP {response.status})"
                            )
                        last_was_timeout = False
            except asyncio.TimeoutError:
                last_was_timeout = True
            except aiohttp.ClientError:
                last_was_timeout = False

            if attempt < 2:
                await asyncio.sleep(0.4 * (2**attempt))

        if last_was_timeout:
            raise RuntimeError("CHZZK API 응답 시간이 초과되었습니다.")
        raise RuntimeError("CHZZK API 요청에 실패했습니다. 잠시 후 다시 시도해주세요.")

    def _request_headers(self, cookies: str) -> Dict[str, str]:
        headers = self.headers.copy()
        if cookies:
            headers["Cookie"] = cookies
        return headers

    @staticmethod
    def _fallback_resolution(page_url: str) -> Dict:
        return {
            "quality": "best",
            "label": "최고 화질",
            "url": page_url,
            "height": 0,
            "width": 0,
            "bitrate": 0,
        }

    async def fetch_vod_metadata(self, video_id: str, cookies: str = "") -> Dict:
        """Fetch metadata for a CHZZK VOD."""
        headers = self._request_headers(cookies)
        url = f"{self.BASE_URL}/service/v3/videos/{video_id}"
        page_url = f"https://chzzk.naver.com/video/{video_id}"
        data = await self._request_json(url, headers)

        video = data.get("content")
        if not isinstance(video, dict):
            raise RuntimeError("CHZZK 영상을 찾을 수 없습니다.")

        vod_status = video.get("vodStatus", "UNKNOWN")
        in_key = video.get("inKey", "")
        playback_video_id = video.get("videoId", "")
        resolutions = self._parse_resolutions(video)

        if (
            not resolutions
            and vod_status == "ABR_HLS"
            and in_key
            and playback_video_id
        ):
            resolutions = await self._fetch_abr_resolutions(
                playback_video_id,
                in_key,
                page_url,
                headers,
            )
        if not resolutions and vod_status == "ABR_HLS":
            resolutions = [self._fallback_resolution(page_url)]

        channel = video.get("channel") or {}
        return {
            "id": video.get("videoNo"),
            "type": "vod",
            "title": video.get("videoTitle", "Untitled"),
            "thumbnail": video.get("thumbnailImageUrl", ""),
            "duration": video.get("duration", 0),
            # Fast-replay metadata can still change while HLS is finalized.
            "duration_is_reliable": vod_status == "ABR_HLS",
            "channel_name": channel.get("channelName", "Unknown"),
            "publish_date": video.get("publishDate", ""),
            "resolutions": resolutions,
            "vod_status": vod_status,
            "is_downloadable": vod_status == "ABR_HLS",
            "liveRewindPlaybackJson": video.get("liveRewindPlaybackJson"),
            "url": page_url,
        }

    async def fetch_clip_metadata(self, clip_id: str, cookies: str = "") -> Dict:
        """Fetch and merge the current CHZZK clip detail and play-info APIs."""
        headers = self._request_headers(cookies)
        page_url = f"https://chzzk.naver.com/clips/{clip_id}"
        detail_url = (
            f"{self.BASE_URL}/service/v1/clips/{clip_id}/detail"
            "?optionalProperties=OWNER_CHANNEL"
        )
        play_url = f"{self.BASE_URL}/service/v1/play-info/clip/{clip_id}"
        detail_data, play_data = await asyncio.gather(
            self._request_json(detail_url, headers),
            self._request_json(play_url, headers),
        )

        clip = detail_data.get("content")
        play_info = play_data.get("content")
        if not isinstance(clip, dict) or not isinstance(play_info, dict):
            raise RuntimeError("CHZZK 클립을 찾을 수 없습니다.")

        playback_video_id = play_info.get("videoId") or clip.get("videoId") or ""
        in_key = play_info.get("inKey", "")
        resolutions: List[Dict] = []
        if playback_video_id and in_key:
            resolutions = await self._fetch_abr_resolutions(
                playback_video_id,
                in_key,
                page_url,
                headers,
                prefer_direct=True,
            )
        if not resolutions:
            resolutions = [self._fallback_resolution(page_url)]

        optional = clip.get("optionalProperty") or {}
        owner = optional.get("ownerChannel") or play_info.get("ownerChannel") or {}
        return {
            "id": clip.get("clipUID") or clip_id,
            "type": "clip",
            "title": clip.get("clipTitle") or play_info.get("contentTitle") or "Untitled",
            "thumbnail": clip.get("thumbnailImageUrl", ""),
            "duration": clip.get("duration", 0),
            "duration_is_reliable": True,
            "channel_name": owner.get("channelName", "Unknown"),
            "publish_date": clip.get("createdDate", ""),
            "resolutions": resolutions,
            "vod_status": play_info.get("vodStatus", "UNKNOWN"),
            "is_downloadable": bool(resolutions),
            "url": page_url,
        }

    async def _fetch_abr_resolutions(
        self,
        video_id: str,
        in_key: str,
        page_url: str,
        headers: Dict[str, str],
        prefer_direct: bool = False,
    ) -> List[Dict]:
        """Fetch ABR_HLS quality information from NAVER's playback API."""
        media_url = (
            f"https://apis.naver.com/neonplayer/vodplay/v2/playback/{video_id}"
            f"?key={in_key}&cc=KR&tz=Asia%2FSeoul&lc=ko_KR&cpl=ko_KR"
            "&service=chzzk&mediaProtocol=hls&application=PC_WEB"
        )
        playback_headers = headers.copy()
        playback_headers.update(
            {
                "Referer": page_url,
                "Origin": "https://chzzk.naver.com",
            }
        )

        try:
            playback = await self._request_json(media_url, playback_headers)
        except RuntimeError as exc:
            print(f"[ABR] 화질 목록 가져오기 실패: {exc}")
            return []

        resolutions: List[Dict] = []
        seen_heights = set()
        for period in playback.get("period", []):
            if not isinstance(period, dict):
                continue
            for adaptation in period.get("adaptationSet", []):
                if not isinstance(adaptation, dict):
                    continue
                if not adaptation.get("mimeType", "").startswith("video"):
                    continue
                if prefer_direct and adaptation.get("mimeType") != "video/mp4":
                    continue
                for representation in adaptation.get("representation", []):
                    if not isinstance(representation, dict):
                        continue
                    height = representation.get("height")
                    if not height or height in seen_heights:
                        continue
                    seen_heights.add(height)
                    quality_id = ""
                    for item in representation.get("any", []):
                        if isinstance(item, dict) and item.get("kind") == "qualityId":
                            quality_id = item.get("value", "")
                            break
                    stream_url = page_url
                    if prefer_direct and adaptation.get("mimeType") == "video/mp4":
                        stream_url = self._progressive_stream_url(representation) or page_url
                    resolutions.append(
                        {
                            "quality": quality_id or f"{height}p",
                            "label": f"{height}p",
                            "url": stream_url,
                            "height": height,
                            "width": representation.get("width", 0),
                            "bitrate": representation.get("bandwidth", 0),
                        }
                    )

        resolutions.sort(key=lambda item: item["height"], reverse=True)
        return resolutions

    @staticmethod
    def _progressive_stream_url(representation: Dict) -> Optional[str]:
        """Return a trusted signed progressive URL from playback metadata."""
        for item in representation.get("baseURL", []):
            candidate = item.get("value") if isinstance(item, dict) else item
            if not isinstance(candidate, str):
                continue
            try:
                parts = urlsplit(candidate)
                port = parts.port
            except ValueError:
                continue
            host = (parts.hostname or "").lower()
            trusted_host = (
                host == "pstatic.net"
                or host.endswith(".pstatic.net")
                or host == "naver.com"
                or host.endswith(".naver.com")
            )
            if (
                parts.scheme == "https"
                and trusted_host
                and not parts.username
                and not parts.password
                and port in {None, 443}
            ):
                return candidate
        return None

    def _parse_resolutions(self, video: Dict) -> List[Dict]:
        """Parse fast-replay tracks from liveRewindPlaybackJson."""
        playback_json = video.get("liveRewindPlaybackJson")
        if not playback_json:
            return []

        try:
            playback_data = json.loads(playback_json)
        except (TypeError, json.JSONDecodeError):
            return []
        if not isinstance(playback_data, dict):
            return []

        media_list = playback_data.get("media") or []
        if not media_list or not isinstance(media_list[0], dict):
            return []
        media = media_list[0]
        master_url = media.get("path", "")
        if not master_url:
            return []

        resolutions = []
        for track in media.get("encodingTrack", []):
            if not isinstance(track, dict):
                continue
            resolutions.append(
                {
                    "quality": track.get("encodingTrackId", ""),
                    "label": f"{track.get('videoHeight', 0)}p",
                    "url": master_url,
                    "width": track.get("videoWidth", 0),
                    "height": track.get("videoHeight", 0),
                    "bitrate": track.get("videoBitRate", 0),
                }
            )
        resolutions.sort(key=lambda item: item["height"], reverse=True)
        return resolutions

    @staticmethod
    def get_master_playlist_url(video_data: Dict) -> Optional[str]:
        """Return the signed master playlist URL from fast-replay metadata."""
        playback_json = video_data.get("liveRewindPlaybackJson")
        if not playback_json:
            return None
        try:
            playback_data = json.loads(playback_json)
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(playback_data, dict):
            return None

        for media in playback_data.get("media", []):
            if isinstance(media, dict) and media.get("path"):
                return media["path"]
        return None
