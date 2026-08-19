import unittest

from core.downloader import (
    build_final_cut_format_selector,
    is_youtube_url,
    select_download_format,
)


class FinalCutFormatSelectorTests(unittest.TestCase):
    def test_preserves_requested_height_limit(self):
        selector = build_final_cut_format_selector(
            'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        )

        self.assertIn('vcodec^=avc1', selector)
        self.assertIn('acodec^=mp4a', selector)
        self.assertTrue(all(
            'height<=1080' in candidate
            for candidate in selector.split('/')
        ))

    def test_works_without_a_height_limit(self):
        selector = build_final_cut_format_selector()

        self.assertNotIn('height<=', selector)
        self.assertIn('bestaudio[ext=m4a]', selector)

    def test_detects_supported_youtube_hosts(self):
        self.assertTrue(is_youtube_url('https://www.youtube.com/watch?v=dQw4w9WgXcQ'))
        self.assertTrue(is_youtube_url('https://youtu.be/dQw4w9WgXcQ'))
        self.assertTrue(is_youtube_url('https://WWW.YOUTUBE.COM/watch?v=dQw4w9WgXcQ'))
        self.assertFalse(is_youtube_url('https://chzzk.naver.com/video/1'))
        self.assertFalse(is_youtube_url('https://notyoutube.com/watch?v=dQw4w9WgXcQ'))

    def test_does_not_change_chzzk_format_selection(self):
        original = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'

        self.assertEqual(
            select_download_format('https://chzzk.naver.com/video/1', original),
            original,
        )


if __name__ == '__main__':
    unittest.main()
