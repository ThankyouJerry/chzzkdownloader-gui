import json
import subprocess
import unittest
from unittest.mock import patch

from core.youtube_api import YouTubeAPI


class YouTubeApiTests(unittest.TestCase):
    def test_metadata_command_is_single_video_bounded_and_config_independent(self):
        info = {
            "id": "dQw4w9WgXcQ",
            "title": "테스트 영상",
            "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "formats": [],
        }
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(info),
            stderr="",
        )

        with patch(
            "core.youtube_api.resolve_yt_dlp_binary",
            return_value="/tmp/yt-dlp",
        ), patch("core.youtube_api.subprocess.run", return_value=completed) as run:
            metadata = YouTubeAPI().fetch_metadata(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL123"
            )

        command = run.call_args.args[0]
        self.assertIn("--ignore-config", command)
        self.assertIn("--dump-single-json", command)
        self.assertIn("--no-playlist", command)
        self.assertEqual(
            run.call_args.kwargs["timeout"],
            YouTubeAPI.METADATA_TIMEOUT_SECONDS,
        )
        self.assertEqual(metadata["id"], "dQw4w9WgXcQ")

    def test_metadata_timeout_has_user_facing_error(self):
        with patch(
            "core.youtube_api.resolve_yt_dlp_binary",
            return_value="/tmp/yt-dlp",
        ), patch(
            "core.youtube_api.subprocess.run",
            side_effect=subprocess.TimeoutExpired("yt-dlp", 90),
        ):
            with self.assertRaisesRegex(RuntimeError, "시간이 초과"):
                YouTubeAPI().fetch_metadata(
                    "https://youtu.be/dQw4w9WgXcQ"
                )


if __name__ == "__main__":
    unittest.main()
