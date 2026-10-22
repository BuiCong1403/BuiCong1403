import unittest
from datetime import datetime
from unittest.mock import Mock, patch

import combined_m3u_collector as collector
import youtube_highlight_collector as youtube


class SnapshotMergeTests(unittest.TestCase):
    def test_previous_playlist_keeps_independent_snapshots(self):
        day = datetime.now(collector.TZ_VN).date()
        def channel(source, suffix):
            return {"source": source, "group": "Highlight", "name": suffix,
                    "stream_url": f"https://example.org/{suffix}.m3u8", "event_date": day,
                    "skip_event_filter": True}
        yt = channel("YouTubeHighlight", "youtube")
        h24 = channel("24hHighlight", "24h")
        das = channel("DasFootballHighlight", "das")
        with patch.object(collector, "PREVIOUS_HIGHLIGHT_M3U_URL", "https://example.org/list.m3u"), patch.object(collector, "collect_m3u_playlist", return_value=[]), patch.object(youtube, "load_channels", return_value=[yt]), patch.object(collector, "load_h24_highlight_cache", return_value=[h24]), patch.object(collector, "DASFOOTBALL_M3U", Mock()), patch.object(collector, "channels_from_dasfootball_m3u_text", return_value=[das]):
            result = collector.collect_previous_highlight_playlist()
        self.assertEqual({item["source"] for item in result}, {"YouTubeHighlight", "24hHighlight", "DasFootballHighlight"})

    def test_second_half_can_have_a_different_timestamp(self):
        today = datetime.now(collector.TZ_VN).date()
        root = f"https://cdn.24h.com.vn/upload/4-2026/videoclip/{today.isoformat()}/"
        h1 = root + "cp_special_c1-1792616165-real_h1.m3u8"
        h2 = root + "cp_special_c1-1792616166-real_h2_720p.m3u8"
        title = "Real Madrid - Leipzig: Match"
        article = "https://www.24h.com.vn/bong-da/video-bong-da-real-madrid-leipzig-c48a1804646.html"
        listing = f'<a href="{article}">Match</a>'
        page = f'<title>Video bóng đá {title}</title><script>var sources=["{h1}","{h2}"];</script>'
        initial = [{"source": "24hHighlight", "group": "Highlight", "name": title,
                    "stream_url": h1, "event_date": today, "skip_event_filter": True}]
        with patch.object(collector, "fetch_text", side_effect=[listing, page]), patch.object(collector, "is_working_m3u8", return_value=True), patch.object(collector, "merge_and_save_h24_highlight_cache"):
            result = collector.repair_h24_missing_halves(initial)
        self.assertEqual({collector.h24_stream_part_number(item["stream_url"]) for item in result}, {"1", "2"})


if __name__ == "__main__":
    unittest.main()
