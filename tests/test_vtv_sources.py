import unittest
from unittest.mock import patch, MagicMock

import combined_m3u_collector as c


class VtvSourcesTest(unittest.TestCase):
    def test_extensionless_dash_is_rejected(self):
        response = MagicMock()
        response.url = "https://example.com/stream/channel/1"
        response.iter_content.return_value = iter([b'<?xml version="1.0"?><MPD>'])
        response.__enter__.return_value = response
        with patch.object(c.requests, "get", return_value=response):
            self.assertFalse(c.tv_playlist_is_hls({"stream_url": response.url}))

    def test_primary_and_backup_names(self):
        def playlist(source, url, *args, **kwargs):
            return [{"name": "VTV1", "stream_url": url + "/live.m3u8"},
                    {"name": "VTV2", "stream_url": url + "/live.mpd?token=1"}]
        with patch.object(c, "collect_m3u_playlist", side_effect=playlist), \
             patch.object(c, "VMTTV_VTV_MIN_GOOD_COUNT", 1), \
             patch.object(c, "save_vmttv_vtv_cache"):
            rows = c.collect_vtv_channels()
        self.assertEqual([r["name"] for r in rows], ["VTV1", "VTV1-1"])
        self.assertTrue(rows[0]["stream_url"].startswith(c.VIETNG_VTV_M3U_URL))

    def test_tv360_excludes_dash_query(self):
        with patch.object(c, "collect_m3u_playlist", return_value=[
            {"name": "TV360+1", "stream_url": "https://example.com/a.mpd?token=x"},
            {"name": "TV360+2", "stream_url": "https://example.com/b.m3u8"},
        ]), patch.object(c, "tv_playlist_is_hls", side_effect=lambda r: ".mpd" not in r["stream_url"]):
            rows = c.collect_tv360_events()
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["skip_event_filter"])


if __name__ == "__main__":
    unittest.main()
