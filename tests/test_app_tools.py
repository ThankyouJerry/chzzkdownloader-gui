import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import app_tools


class YtDlpUpdaterTests(unittest.TestCase):
    def test_selects_native_standalone_assets_per_platform(self):
        with patch.object(app_tools.sys, "platform", "win32"):
            self.assertEqual(app_tools.get_yt_dlp_asset_name(), "yt-dlp.exe")
            self.assertEqual(app_tools.executable_name("yt-dlp"), "yt-dlp.exe")
        with patch.object(app_tools.sys, "platform", "darwin"):
            self.assertEqual(app_tools.get_yt_dlp_asset_name(), "yt-dlp_macos")
        with patch.object(app_tools.sys, "platform", "linux"), patch.object(
            app_tools.platform,
            "machine",
            return_value="x86_64",
        ):
            self.assertEqual(app_tools.get_yt_dlp_asset_name(), "yt-dlp_linux")
        with patch.object(app_tools.sys, "platform", "linux"), patch.object(
            app_tools.platform,
            "machine",
            return_value="aarch64",
        ):
            self.assertEqual(
                app_tools.get_yt_dlp_asset_name(),
                "yt-dlp_linux_aarch64",
            )

    def test_installs_only_after_checksum_and_version_validation(self):
        binary = b"verified yt-dlp binary"
        digest = hashlib.sha256(binary).hexdigest()
        checksum_file = f"{digest}  {app_tools.get_yt_dlp_asset_name()}\n".encode()
        completed = subprocess.CompletedProcess([], 0, "2026.08.20\n", "")

        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            app_tools,
            "get_app_bin_dir",
            return_value=Path(temp_dir),
        ), patch.object(
            app_tools,
            "_download_bytes",
            side_effect=[checksum_file, binary],
        ), patch.object(
            app_tools.subprocess,
            "run",
            return_value=completed,
        ) as run:
            installed = Path(app_tools.install_or_update_yt_dlp())

            self.assertEqual(installed.read_bytes(), binary)
            self.assertEqual(run.call_args.args[0][1], "--version")

    def test_checksum_failure_preserves_existing_binary(self):
        old_binary = b"working old binary"
        new_binary = b"tampered new binary"
        wrong_checksum = (
            f"{'0' * 64}  {app_tools.get_yt_dlp_asset_name()}\n".encode()
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / app_tools.executable_name("yt-dlp")
            target.write_bytes(old_binary)
            target.chmod(0o755)
            with patch.object(
                app_tools,
                "get_app_bin_dir",
                return_value=Path(temp_dir),
            ), patch.object(
                app_tools,
                "_download_bytes",
                side_effect=[wrong_checksum, new_binary],
            ):
                with self.assertRaisesRegex(RuntimeError, "체크섬"):
                    app_tools.install_or_update_yt_dlp()

            self.assertEqual(target.read_bytes(), old_binary)


if __name__ == "__main__":
    unittest.main()
