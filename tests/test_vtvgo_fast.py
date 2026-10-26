import tempfile
import unittest
from pathlib import Path

import combined_m3u_collector as c


class VtvgoTests(unittest.TestCase):
    def test_fixed_channels_survive_event_filter_and_support_ott(self):
        channels = c.collect_vtvgo_fast()
        self.assertEqual(len(channels), 7)
        self.assertEqual(len({ch["stream_url"] for ch in channels}), 7)
        self.assertTrue(all(ch["group"] == "VTV" for ch in channels))
        self.assertEqual(len(c.filter_current_and_future_events(channels)), 7)
        self.assertEqual(len(c.select_ott_compatible_channels(channels)), 7)

    def test_writers_keep_vtv_group_and_ascii_ott_names(self):
        with tempfile.TemporaryDirectory() as folder:
            all_file = Path(folder) / "all.m3u"
            ott = Path(folder) / "ott.m3u"
            channels = c.collect_vtvgo_fast()
            c.write_m3u(all_file, channels)
            c.write_ott_m3u(ott, channels)
            text = all_file.read_text(encoding="utf-8")
            self.assertEqual(text.count('group-title="VTV"'), 7)
            self.assertIn('tvg-id="vtvgo-fast-thieu-nhi"', text)
            ott_text = ott.read_text(encoding="utf-8")
            self.assertEqual(ott_text.count('#EXTGRP:VTV'), 7)
            self.assertIn('VTVgo - Thieu nhi', ott_text)


if __name__ == "__main__":
    unittest.main()
