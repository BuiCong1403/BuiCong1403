import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import combined_m3u_collector as c


class DasFootballMergeOnlyTests(unittest.TestCase):
    def test_merge_uses_only_local_playlists_and_preserves_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            das, hl, all_file, ott = [root / name for name in
                                       ("dasfootball.m3u", "highlight.m3u", "all.m3u", "ott.m3u")]
            day = datetime.now(c.TZ_VN).date()
            das_text = (f'#EXTM3U\n#EXTINF:-1 group-title="Highlight",Home vs Away\n'
                        f'#EXTVLCOPT:http-referrer=https://dasfootball.com/home-vs-away-highlights-{day}/\n'
                        'https://cdn.streamain.com/guests/test.mp4\n')
            das.write_text(das_text, encoding="utf-8")
            h24_url = f'https://cdn.24h.com.vn/upload/4-2026/videoclip/{day}/match_h2.m3u8'
            hl.write_text(f'#EXTM3U\n#EXTINF:-1 group-title="Highlight",Other vs Team\n{h24_url}\n', encoding="utf-8")
            live = '#EXTM3U\n#EXTINF:-1 group-title="VTV",VTV1\nhttps://example/vtv1.m3u8\n'
            all_file.write_text(live, encoding="utf-8")
            ott.write_text(live, encoding="utf-8")
            with patch.object(c, "DASFOOTBALL_M3U", das), patch.object(c, "HIGHLIGHT_M3U", hl), \
                 patch.object(c, "ALL_M3U", all_file), patch.object(c, "OTT_M3U", ott), \
                 patch.object(c, "fetch_text", side_effect=AssertionError("Network prohibited")), \
                 patch.object(c, "request_get", side_effect=AssertionError("Network prohibited")), \
                 patch.object(c, "repair_h24_missing_halves", side_effect=AssertionError("Scraping prohibited")):
                c.merge_local_dasfootball_playlists()
            self.assertEqual(das.read_text(encoding="utf-8"), das_text)
            for output in (hl, all_file, ott):
                text = output.read_text(encoding="utf-8")
                self.assertIn('https://cdn.streamain.com/guests/test.mp4', text)
                self.assertIn(h24_url, text)
            self.assertIn('https://example/vtv1.m3u8', all_file.read_text(encoding="utf-8"))

    def test_empty_snapshot_does_not_replace_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            das = Path(folder) / "dasfootball.m3u"
            das.write_text("#EXTM3U\n", encoding="utf-8")
            with patch.object(c, "DASFOOTBALL_M3U", das):
                with self.assertRaises(RuntimeError):
                    c.merge_local_dasfootball_playlists()

    def test_snapshot_returns_without_order_scrape_or_combined_merge(self):
        day = datetime.now(c.TZ_VN).date()
        channel = {"source": "DasFootballHighlight", "group": "Highlight", "name": "Home vs Away",
                   "stream_url": "https://cdn.streamain.com/guests/test.mp4", "event_date": day}
        with tempfile.TemporaryDirectory() as folder:
            das = Path(folder) / "dasfootball.m3u"
            with patch.object(c, "RUN_MODE", "dasfootball_snapshot"), \
                 patch.object(c, "DASFOOTBALL_M3U", das), \
                 patch.object(c, "collect_source_channels", return_value=[channel]), \
                 patch.object(c, "collect_previous_dasfootball_playlist", return_value=[]) as previous, \
                 patch.object(c, "refresh_dasfootball_order", side_effect=AssertionError("Extra scrape prohibited")), \
                 patch.object(c, "collect_previous_highlight_playlist", side_effect=AssertionError("Merge prohibited")):
                c.main()
                previous.assert_called_once_with(local_only=True)
            self.assertIn(channel["stream_url"], das.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
