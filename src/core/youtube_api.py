"""
YouTube API - validated external yt-dlp metadata extraction with package fallback.
"""
import json
import subprocess
from typing import Dict, List, Optional

import yt_dlp

from core.dependency_check import resolve_yt_dlp_binary
from core.url_utils import parse_media_url


class YouTubeAPI:
    """YouTube metadata extractor using the best available yt-dlp runtime."""

    METADATA_TIMEOUT_SECONDS = 90

    # ── URL 파싱 ────────────────────────────────────────────────

    @staticmethod
    def parse_url(url: str) -> Optional[Dict[str, str]]:
        """
        YouTube URL에서 video ID를 추출합니다.
        지원: youtube.com/watch?v=, youtu.be/, youtube.com/shorts/
        """
        parsed = parse_media_url(url)
        if parsed and parsed.get('type') == 'youtube':
            return parsed
        return None

    # ── 메타데이터 추출 ─────────────────────────────────────────

    def fetch_metadata(self, url: str) -> Dict:
        """
        외부 yt-dlp 바이너리로 단일 영상 메타데이터를 가져오고,
        사용할 수 없으면 번들된 Python 패키지로 전환합니다.
        """
        parsed = self.parse_url(url)
        if not parsed:
            raise ValueError("올바른 YouTube HTTPS URL을 입력해주세요.")

        ytdlp_bin = resolve_yt_dlp_binary()
        if ytdlp_bin:
            try:
                result = subprocess.run(
                    [
                        ytdlp_bin,
                        "--ignore-config",
                        "--dump-single-json",
                        "--no-warnings",
                        "--no-playlist",
                        "--socket-timeout",
                        "20",
                        "--extractor-retries",
                        "3",
                        url,
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=self.METADATA_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(
                    "YouTube 정보 요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
                ) from exc
            if result.returncode != 0:
                err = result.stderr.strip()[-1000:]
                raise RuntimeError(f"YouTube 정보 가져오기 실패:\n{err}")
            try:
                info = json.loads(result.stdout)
            except json.JSONDecodeError as exc:
                raise RuntimeError("YouTube 정보 응답 형식이 올바르지 않습니다.") from exc
        else:
            try:
                with yt_dlp.YoutubeDL({
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                    "socket_timeout": 20,
                    "extractor_retries": 3,
                }) as ydl:
                    info = ydl.extract_info(url, download=False)
            except Exception as exc:
                raise RuntimeError(f"YouTube 정보 가져오기 실패:\n{exc}") from exc

        if not isinstance(info, dict):
            raise RuntimeError("YouTube 정보 응답 형식이 올바르지 않습니다.")

        resolutions = self._extract_resolutions(info)

        raw_date = info.get('upload_date', '')
        publish_date = (
            f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}"
            if len(raw_date) == 8 else raw_date
        )

        return {
            'id':              info.get('id', ''),
            'type':            'youtube',
            'title':           info.get('title', 'Untitled'),
            'thumbnail':       info.get('thumbnail', ''),
            'duration':        info.get('duration', 0) or 0,
            'channel_name':    info.get('channel') or info.get('uploader', 'Unknown'),
            'publish_date':    publish_date,
            'resolutions':     resolutions,
            'vod_status':      'ABR_HLS',   # yt-dlp 다운로드 모드 사용
            'is_downloadable': True,
            'url':             url,
        }

    # ── 내부 헬퍼 ───────────────────────────────────────────────

    @staticmethod
    def _extract_resolutions(info: dict) -> List[Dict]:
        """
        포맷 목록에서 사용 가능한 화질을 추출합니다.
        비디오 스트림(video-only or combined)을 높이 기준으로 정렬합니다.
        """
        formats = info.get('formats', [])

        # 비디오가 있는 포맷만 (vcodec != none, storyboard 제외)
        video_formats = [
            f for f in formats
            if f.get('vcodec') and f.get('vcodec') != 'none'
            and f.get('ext') not in ('mhtml',)
            and f.get('height')
        ]

        # 표준 해상도 목록에서 실제로 있는 것만 추출
        available_heights = sorted(
            {f['height'] for f in video_formats},
            reverse=True
        )
        standard = [4320, 2160, 1440, 1080, 720, 480, 360, 240, 144]
        available = [h for h in standard if h in available_heights]

        if not available:
            return [{
                'quality': 'best',
                'label':   'Best',
                'url':     info.get('webpage_url', ''),
                'height':  0,
                'bitrate': 0,
            }]

        resolutions = []
        for h in available:
            # 해당 높이 포맷들 중 최고 bitrate
            matching = [f for f in video_formats if f['height'] == h]
            bitrate = max((f.get('tbr') or 0 for f in matching), default=0)
            label = f"{h}p" if h < 2160 else ("4K" if h == 2160 else f"{h}p")
            resolutions.append({
                'quality':  f'{h}p',
                'label':    label,
                'url':      info.get('webpage_url', ''),
                'height':   h,
                'bitrate':  int(bitrate * 1000) if bitrate else 0,
            })

        return resolutions
