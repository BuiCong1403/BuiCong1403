import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import combined_m3u_collector as collector


class VscRefreshTests(unittest.TestCase):
    def test_empty_response_preserves_outputs(self):
        with patch.object(collector, "RUN_MODE", "vsc9"), patch.object(
            collector, "collect_vsc9", return_value=[]
        ), patch.object(collector, "save_source_cache") as save:
            with self.assertRaises(RuntimeError):
                collector.main()
            save.assert_not_called()

    def test_refresh_merges_without_losing_other_groups(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            main = root / "all.m3u"
            ott = root / "ott.m3u"
            text = '#EXTM3U\n\n#EXTINF:-1 group-title="VTV",VTV1\nhttps://example.org/vtv.m3u8\n'
            main.write_text(text, encoding="utf-8")
            ott.write_text(text, encoding="utf-8")
            channel = {"source": "VSC9", "group": "Vua Sân Cỏ TV", "name": "Team A vs Team B", "stream_url": "https://example.org/match.m3u8"}
            with patch.multiple(collector, RUN_MODE="vsc9", BASE_DIR=root, ALL_M3U=main, OTT_M3U=ott, VSC9_CACHE=root / "cache.json"), patch.object(collector, "collect_vsc9", return_value=[channel]):
                collector.main()
            for path in (main, ott):
                result = path.read_text(encoding="utf-8")
                self.assertIn("vtv.m3u8", result)
                self.assertIn("match.m3u8", result)
                self.assertEqual(result.count("match.m3u8"), 1)


if __name__ == "__main__":
    unittest.main()
