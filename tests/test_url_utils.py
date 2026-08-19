import unittest

from core.url_utils import is_youtube_url, parse_media_url


class StrictUrlParsingTests(unittest.TestCase):
    def test_accepts_supported_chzzk_and_youtube_urls(self):
        self.assertEqual(
            parse_media_url("https://chzzk.naver.com/video/14046440"),
            {"type": "vod", "id": "14046440"},
        )
        self.assertEqual(
            parse_media_url("https://chzzk.naver.com/clips/p7RRZ4xsws"),
            {"type": "clip", "id": "p7RRZ4xsws"},
        )
        self.assertEqual(
            parse_media_url("https://youtu.be/dQw4w9WgXcQ"),
            {
                "type": "youtube",
                "id": "dQw4w9WgXcQ",
                "url": "https://youtu.be/dQw4w9WgXcQ",
            },
        )

    def test_rejects_substring_spoofing_and_non_https_urls(self):
        rejected = [
            "https://evil.test/chzzk.naver.com/video/123",
            "https://notyoutube.com/watch?v=dQw4w9WgXcQ",
            "https://evil.test/youtube.com/watch?v=dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "javascript:alert(1)",
            "file:///tmp/video.mp4",
            "https://user:pass@www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com:444/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com:invalid/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ/extra",
            "https://www.youtube.com/watch/extra?v=dQw4w9WgXcQ",
        ]
        for url in rejected:
            with self.subTest(url=url):
                self.assertIsNone(parse_media_url(url))
                self.assertFalse(is_youtube_url(url))


if __name__ == "__main__":
    unittest.main()
