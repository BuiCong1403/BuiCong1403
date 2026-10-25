import unittest
from datetime import datetime

import combined_m3u_collector as c


class MatchScheduleTests(unittest.TestCase):
    def test_suffix_schedule_with_and_without_accents(self):
        for title in ("Home vs Away lúc 18:30 ngày 25/10/2026 | Link 2 [FLV]",
                      "Home vs Away luc 18:30 ngay 25/10/2026 | Link 2 [FLV]"):
            ch = c.normalize_match_schedule({"name": title, "group": "XL-FLV"})
            self.assertEqual(ch["name"], "18:30 25/10 Home vs Away | Link 2 [FLV]")
            self.assertEqual(ch["event_datetime"].day, 25)
            self.assertEqual(c.normalize_match_schedule(ch)["name"], ch["name"])

    def test_date_first_and_explicit_metadata(self):
        title = "Home vs Away 26/10/2026 01:30"
        self.assertEqual(c.normalize_match_schedule({"name": title})["name"], "01:30 26/10 Home vs Away")
        ch = {"name": "Home vs Away", "event_datetime": datetime(2026, 10, 26, 2, tzinfo=c.TZ_VN)}
        self.assertEqual(c.normalize_match_schedule(ch)["name"], "02:00 26/10 Home vs Away")

    def test_tv_and_highlights_unchanged(self):
        for ch in ({"name": "VTV1", "group": "VTV"},
                   {"name": "Home vs Away 18:30 25/10", "group": "Highlight"}):
            self.assertEqual(c.normalize_match_schedule(ch), ch)

    def test_blocks_sorted_by_date_then_time_preserving_urls_and_options(self):
        blocks = [
            ['#EXTINF:0,A vs B luc 01:00 ngay 26/10/2026', '#EXTGRP:FLV', 'https://example/a.flv'],
            ['#EXTINF:0,Z vs Y luc 23:00 ngay 25/10/2026', '#EXTGRP:XL-FLV', '#EXTVLCOPT:http-referrer=https://example/', 'https://example/z.flv'],
        ]
        result = c.normalize_scheduled_playlist_blocks(blocks, ott=True)
        self.assertEqual(result[0][0], '#EXTINF:0,23:00 25/10 Z vs Y')
        self.assertEqual(result[1][0], '#EXTINF:0,01:00 26/10 A vs B')
        self.assertEqual(result[0][2:], blocks[1][2:])


if __name__ == "__main__":
    unittest.main()
