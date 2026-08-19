import subprocess
import sys
import time
import unittest
from unittest.mock import patch

from core.downloader import DownloadWorker


class DownloadCancellationTests(unittest.TestCase):
    def test_stop_returns_immediately_and_terminates_process(self):
        worker = DownloadWorker("https://example.com", "/tmp/clipcatcher-test")
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        worker.process = process

        started = time.monotonic()
        worker.stop()
        elapsed = time.monotonic() - started

        self.assertLess(elapsed, 0.25)
        process.wait(timeout=4)
        self.assertIsNotNone(process.returncode)

    def test_external_binary_is_preferred_for_chzzk_clip(self):
        worker = DownloadWorker(
            "https://chzzk.naver.com/clips/p7RRZ4xsws",
            "/tmp/clipcatcher-test",
        )
        with patch(
            "core.downloader.resolve_yt_dlp_binary",
            return_value="/tmp/yt-dlp",
        ), patch.object(
            worker,
            "_refresh_clip_stream_url",
        ) as refresh_stream_url, patch.object(
            worker,
            "_run_ytdlp_binary_download",
        ) as binary_download, patch.object(
            worker,
            "_run_ytdlp_package_download",
        ) as package_download:
            worker._run_ytdlp_download()

        refresh_stream_url.assert_called_once_with()
        binary_download.assert_called_once_with()
        package_download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
