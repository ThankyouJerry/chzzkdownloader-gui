import asyncio
import json
import unittest
from unittest.mock import AsyncMock, patch

from core.chzzk_api import ChzzkAPI


class ChzzkApiTests(unittest.TestCase):
    def test_api_reader_reassembles_chunked_json_response(self):
        class FakeContent:
            async def iter_chunked(self, _size):
                yield b'{"con'
                yield b'tent":{"ok":true}}'

        class FakeResponse:
            status = 200
            charset = "utf-8"
            content = FakeContent()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

        class FakeSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return False

            def get(self, *_args, **_kwargs):
                return FakeResponse()

        api = ChzzkAPI()
        with patch("core.chzzk_api.aiohttp.ClientSession", return_value=FakeSession()):
            data = asyncio.run(api._request_json("https://example.com", {}))

        self.assertEqual(data, {"content": {"ok": True}})

    def test_returns_signed_master_playlist_without_synthesizing_variant(self):
        signed_url = (
            "https://example.com/live/vod_playlist.m3u8"
            "?hdnts=st%3D1~exp%3D2~hmac%3Dabc"
        )
        metadata = {
            "liveRewindPlaybackJson": json.dumps({
                "media": [{"path": signed_url}],
            })
        }

        self.assertEqual(
            ChzzkAPI.get_master_playlist_url(metadata),
            signed_url,
        )

    def test_vod_uses_safe_best_quality_fallback_when_playback_api_fails(self):
        api = ChzzkAPI()
        api._request_json = AsyncMock(return_value={
            "content": {
                "videoNo": 14046440,
                "videoId": "playback-id",
                "inKey": "signed-key",
                "vodStatus": "ABR_HLS",
                "videoTitle": "테스트 VOD",
                "channel": {"channelName": "테스트 채널"},
            }
        })
        api._fetch_abr_resolutions = AsyncMock(return_value=[])

        metadata = asyncio.run(api.fetch_vod_metadata("14046440"))

        self.assertEqual(metadata["resolutions"][0]["quality"], "best")
        self.assertEqual(
            metadata["resolutions"][0]["url"],
            "https://chzzk.naver.com/video/14046440",
        )
        self.assertTrue(metadata["is_downloadable"])

    def test_clip_merges_current_detail_and_play_info_endpoints(self):
        api = ChzzkAPI()
        api._request_json = AsyncMock(side_effect=[
            {
                "content": {
                    "clipUID": "p7RRZ4xsws",
                    "videoId": "clip-video",
                    "clipTitle": "테스트 클립",
                    "thumbnailImageUrl": "https://example.com/thumb.jpg",
                    "duration": 30,
                    "createdDate": "2026-08-20",
                    "optionalProperty": {
                        "ownerChannel": {"channelName": "클립 채널"},
                    },
                }
            },
            {
                "content": {
                    "videoId": "clip-video",
                    "inKey": "clip-key",
                    "vodStatus": "ABR_HLS",
                }
            },
        ])
        api._fetch_abr_resolutions = AsyncMock(return_value=[{
            "quality": "1080p",
            "label": "1080p",
            "url": "https://chzzk.naver.com/clips/p7RRZ4xsws",
            "height": 1080,
            "width": 1920,
            "bitrate": 6_000_000,
        }])

        metadata = asyncio.run(api.fetch_clip_metadata("p7RRZ4xsws"))

        request_urls = [call.args[0] for call in api._request_json.await_args_list]
        self.assertIn("/clips/p7RRZ4xsws/detail", request_urls[0])
        self.assertIn("/play-info/clip/p7RRZ4xsws", request_urls[1])
        self.assertEqual(metadata["title"], "테스트 클립")
        self.assertEqual(metadata["channel_name"], "클립 채널")
        self.assertEqual(metadata["resolutions"][0]["height"], 1080)
        self.assertEqual(
            metadata["url"],
            "https://chzzk.naver.com/clips/p7RRZ4xsws",
        )

    def test_clip_quality_uses_trusted_progressive_stream_url(self):
        direct_url = "https://vod.pstatic.net/path/clip.mp4?signature=valid"
        api = ChzzkAPI()
        api._request_json = AsyncMock(return_value={
            "period": [{
                "adaptationSet": [{
                    "mimeType": "video/mp4",
                    "representation": [{
                        "height": 720,
                        "width": 1280,
                        "bandwidth": 980000,
                        "baseURL": [{"value": direct_url}],
                        "any": [{"kind": "qualityId", "value": "720P"}],
                    }],
                }],
            }],
        })

        resolutions = asyncio.run(api._fetch_abr_resolutions(
            "video-id",
            "signed-key",
            "https://chzzk.naver.com/clips/p7RRZ4xsws",
            {},
            prefer_direct=True,
        ))

        self.assertEqual(resolutions[0]["url"], direct_url)

    def test_rejects_untrusted_progressive_stream_host(self):
        representation = {
            "baseURL": [{"value": "https://evil.example/clip.mp4"}],
        }

        self.assertIsNone(ChzzkAPI._progressive_stream_url(representation))


if __name__ == "__main__":
    unittest.main()
