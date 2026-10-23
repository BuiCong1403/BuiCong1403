import json
import unittest
from unittest.mock import patch

import combined_m3u_collector as c


class OttSourcesTests(unittest.TestCase):
    def test_flv_group_uses_source_not_shared_cdn(self):
        stream = "https://shared.example/live/channel.flv?token=x"
        self.assertEqual(c.ott_output_group({"source": "XoiLacZ", "stream_url": stream}), "XL-FLV")
        self.assertEqual(c.ott_output_group({"group": "Xôi Lạc Z TV", "stream_url": stream}), "XL-FLV")
        self.assertEqual(c.ott_output_group({"source": "KhoGa", "stream_url": stream}), "FLV")
        self.assertEqual(c.ott_output_group({"group": "Khô Gà", "stream_url": "https://example/a.m3u8"}), "Khô Gà")

    def test_khoga_keeps_hls_backup_and_commentator_flv(self):
        table = [
            {"start_time": 1, "home_team_name": 2, "away_team_name": 3,
             "primary_stream_url": 4, "backup_stream_url": 5, "commentator_streams": 6},
            "2026-10-23T15:30:00+07:00", "Home", "Away",
            "https://example/one.m3u8", "https://example/two.m3u8", [7],
            {"commentator": 8, "flv_stream_url": 9}, {"name": 10},
            "https://example/live.flv", "BLV",
        ]
        page = '<script id="__NUXT_DATA__">' + json.dumps(table) + '</script>'
        with patch.object(c, "fetch_text", return_value=page):
            result = c.collect_khoga()
        self.assertEqual(len(result), 3)
        self.assertEqual(sum(c.is_flv_url(x["stream_url"]) for x in result), 1)
        self.assertTrue(all(x["event_datetime"].hour == 15 for x in result))

    def test_missing_khoga_schedule_fails_without_empty_snapshot(self):
        with patch.object(c, "fetch_text", return_value="<html>Unavailable</html>"):
            with self.assertRaises(ValueError):
                c.collect_khoga()

    def test_khoga_shared_stream_keeps_separate_fixtures(self):
        channels = [{"source": "KhoGa", "group": "Kho Ga", "name": name,
                     "stream_url": "https://example/live.flv"}
                    for name in ("15:30 23/10 Home vs Away", "20:00 24/10 Other vs Team")]
        self.assertEqual(len(c.dedupe_and_sort_channels(channels)), 2)


if __name__ == "__main__":
    unittest.main()
