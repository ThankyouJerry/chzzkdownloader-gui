
import unittest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from core.segment_downloader import SegmentDownloader

class TestSegmentDownloaderSplit(unittest.TestCase):
    def setUp(self):
        self.downloader = SegmentDownloader()
        self.downloader.session = AsyncMock()

    def test_parse_m3u8_with_duration(self):
        content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:4
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:4.000000,
segment0.ts
#EXTINF:4.000000,
segment1.ts
#EXTINF:2.500000,
segment2.ts
"""
        result = self.downloader._parse_m3u8(content)
        segments = result['media_segments']
        self.assertEqual(len(segments), 3)
        self.assertEqual(segments[0]['duration'], 4.0)
        self.assertEqual(segments[2]['duration'], 2.5)

    @patch('core.segment_downloader.SegmentDownloader._download_file')
    @patch('core.segment_downloader.SegmentDownloader._combine_segments')
    @patch('core.segment_downloader.SegmentDownloader._fetch_text')
    def test_download_video_with_range(self, mock_fetch, mock_combine, mock_download):
        # Mock m3u8 content
        mock_fetch.return_value = """#EXTM3U
#EXTINF:10.0,
seg1.ts
#EXTINF:10.0,
seg2.ts
#EXTINF:10.0,
seg3.ts
#EXTINF:10.0,
seg4.ts
"""
        
        # Test range 10s - 30s (should include seg2 and seg3)
        # seg1: 0-10 (excluded)
        # seg2: 10-20 (included)
        # seg3: 20-30 (included)
        # seg4: 30-40 (excluded)
        
        async def run_test():
             await self.downloader.download_video(
                "http://test.com/playlist.m3u8",
                "output",
                start_time=10.0,
                end_time=30.0
            )
        
        asyncio.run(run_test())
        
        # Check that _download_file was called 2 times (for seg2 and seg3)
        # Plus init segment if present (not in this mock)
        self.assertEqual(mock_download.call_count, 2)
        
        # Verify call args
        calls = mock_download.call_args_list
        self.assertIn("seg2.ts", calls[0][0][0])
        self.assertIn("seg3.ts", calls[1][0][0])

if __name__ == '__main__':
    unittest.main()
