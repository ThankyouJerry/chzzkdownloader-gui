import unittest
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import subprocess

from core.segment_downloader import SegmentDownloader


class SegmentRangeTests(unittest.TestCase):
    def setUp(self):
        self.segments = [
            {'url': 'segment-1.m4s', 'duration': 4.0},
            {'url': 'segment-2.m4s', 'duration': 4.0},
            {'url': 'segment-3.m4s', 'duration': 4.0},
        ]

    def test_playlist_duration_uses_segment_durations(self):
        self.assertEqual(
            SegmentDownloader._playlist_duration(self.segments),
            12.0,
        )

    def test_selects_segments_overlapping_requested_range(self):
        selected = SegmentDownloader._select_media_segments(
            self.segments,
            start_time=3.0,
            end_time=8.0,
        )

        self.assertEqual(selected, ['segment-1.m4s', 'segment-2.m4s'])

    def test_range_includes_exact_trim_offset_and_duration(self):
        selected, trim_start, trim_duration = SegmentDownloader._select_media_range(
            self.segments,
            start_time=3.0,
            end_time=8.0,
        )

        self.assertEqual(selected, ['segment-1.m4s', 'segment-2.m4s'])
        self.assertEqual(trim_start, 3.0)
        self.assertEqual(trim_duration, 5.0)

    def test_range_combine_reencodes_h264_aac_with_exact_times(self):
        with TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            init_path = directory / 'init.m4s'
            segment_path = directory / 'segment.m4s'
            output_path = directory / 'output.mp4'
            init_path.write_bytes(b'init')
            segment_path.write_bytes(b'segment')

            completed = subprocess.CompletedProcess([], 0, '', '')
            with patch('core.ffmpeg_utils.get_ffmpeg_binary', return_value='ffmpeg'), \
                    patch.object(
                        SegmentDownloader,
                        '_run_process',
                        return_value=completed,
                    ) as run:
                SegmentDownloader()._combine_segments(
                    init_path,
                    [segment_path],
                    str(output_path),
                    trim_start=3.0,
                    trim_duration=5.0,
                )

            trim_command = run.call_args_list[1].args[0]
            self.assertIn('libx264', trim_command)
            self.assertIn('aac', trim_command)
            self.assertEqual(trim_command[trim_command.index('-ss') + 1], '3.000000')
            self.assertEqual(trim_command[trim_command.index('-t') + 1], '5.000000')

    def test_ffmpeg_process_can_be_cancelled_without_waiting_for_completion(self):
        started = time.monotonic()
        with self.assertRaisesRegex(RuntimeError, '취소'):
            SegmentDownloader._run_process(
                [sys.executable, '-c', 'import time; time.sleep(30)'],
                cancel_callback=lambda: True,
            )

        self.assertLess(time.monotonic() - started, 4.0)

    def test_rejects_start_beyond_hls_duration(self):
        with self.assertRaisesRegex(ValueError, '시작 시간'):
            SegmentDownloader._select_media_segments(
                self.segments,
                start_time=12.0,
                end_time=None,
            )

    def test_rejects_end_beyond_hls_duration(self):
        with self.assertRaisesRegex(ValueError, '종료 시간'):
            SegmentDownloader._select_media_segments(
                self.segments,
                start_time=0.0,
                end_time=13.0,
            )

    def test_scopes_login_cookies_to_naver_domains(self):
        downloader = SegmentDownloader()
        downloader.cookies = {"NID_AUT": "secret", "NID_SES": "secret"}

        self.assertEqual(
            downloader._cookies_for_url("https://apis.naver.com/path"),
            downloader.cookies,
        )
        self.assertEqual(
            downloader._cookies_for_url("https://vod.pstatic.net/path"),
            {},
        )
        self.assertEqual(
            downloader._cookies_for_url("https://evil.example/path"),
            {},
        )

    def test_rejects_non_https_segment_urls(self):
        with self.assertRaisesRegex(RuntimeError, "안전하지 않은"):
            SegmentDownloader._validate_https_url("http://example.com/segment.m4s")


if __name__ == '__main__':
    unittest.main()
