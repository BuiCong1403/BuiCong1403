import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

import youtube_highlight_collector as source


class YoutubeHighlightTests(unittest.TestCase):
    def test_expiry_uses_publication_time(self):
        now = datetime.now(timezone.utc)
        items = [{"published": (now - timedelta(days=d)).isoformat(), "id": str(d)} for d in (1, 7)]
        self.assertEqual([x["id"] for x in source.recent(items)], ["1"])

    def test_html_is_not_a_playlist(self):
        with patch.object(source.requests, "get", return_value=Mock(text="<html>error</html>")):
            self.assertFalse(source.valid_hls("https://example.org/master"))

    def test_master_requires_real_media_playlist(self):
        master = Mock(text="#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1000\nmedia.m3u8\n")
        media = Mock(text="#EXTM3U\n#EXTINF:5,\nsegment.ts\n")
        with patch.object(source.requests, "get", side_effect=[master, media]) as get:
            self.assertTrue(source.valid_hls("https://example.org/master"))
        self.assertEqual(get.call_args.args[0], "https://example.org/media.m3u8")

    def test_invalid_publication_date_is_excluded(self):
        self.assertEqual(source.recent([{"published": "unknown"}]), [])

    def test_channel_fallback_uses_selected_video_tab(self):
        import json
        video = {"videoRenderer": {"videoId": "abc", "title": {"runs": [{"text": "Match"}]}, "publishedTimeText": {"simpleText": "2 hours ago"}}}
        data = {"contents": {"twoColumnBrowseResultsRenderer": {"tabs": [{"tabRenderer": {"selected": True, "content": video}}]}}}
        result = source.channel_page_items("var ytInitialData = " + json.dumps(data) + ";", "Test")
        self.assertEqual(result[0]["id"], "abc")


if __name__ == "__main__":
    unittest.main()
