import unittest
from unittest.mock import patch

from ui.main_window import YtDlpInstallWorker


class YtDlpInstallWorkerTests(unittest.TestCase):
    def test_emits_completed_path(self):
        completed = []
        failed = []
        worker = YtDlpInstallWorker()
        worker.completed.connect(completed.append)
        worker.failed.connect(failed.append)

        with patch(
            'ui.main_window.install_or_update_yt_dlp',
            return_value='/tmp/yt-dlp',
        ):
            worker.run()

        self.assertEqual(completed, ['/tmp/yt-dlp'])
        self.assertEqual(failed, [])

    def test_emits_failure_without_raising_on_worker_thread(self):
        completed = []
        failed = []
        worker = YtDlpInstallWorker()
        worker.completed.connect(completed.append)
        worker.failed.connect(failed.append)

        with patch(
            'ui.main_window.install_or_update_yt_dlp',
            side_effect=RuntimeError('network failure'),
        ):
            worker.run()

        self.assertEqual(completed, [])
        self.assertEqual(failed, ['network failure'])


if __name__ == '__main__':
    unittest.main()
