import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import combined_m3u_collector as collector
import tinhlagi_app_export as exporter


class TinhlagiIsolationTests(unittest.TestCase):
    def test_disabled_app_does_not_contact_activation_service(self):
        with patch.object(collector, "TINHLAGI_APP_ENABLE", False), \
                patch.object(collector, "TINHLAGI_APP_CACHE", None), \
                patch.object(collector, "tinhlagi_app_post_json") as post:
            self.assertEqual(collector.get_tinhlagi_app_sources(), {})
            post.assert_not_called()

    def test_sports_failure_preserves_sports_and_refreshes_highlights(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sports = root / "tlgapp.m3u"
            sports.write_text("previous sports", encoding="utf-8")
            sources = [{"id": "sport", "name": "SPORT", "url": "sport"},
                       {"id": "highlight", "name": "HIGHLIGHT", "url": "highlight"}]

            def fetch(url):
                if url == "sport":
                    raise TimeoutError("source unavailable")
                return "#EXTM3U\n#EXTINF:-1,Video\nhttps://example.com/video.m3u8\n"

            with patch.object(exporter, "BASE_DIR", root), \
                    patch.object(exporter, "OUTPUT_M3U", sports), \
                    patch.object(exporter, "get_sources", return_value=sources), \
                    patch.object(exporter, "fetch_text", side_effect=fetch):
                exporter.main()
            self.assertEqual(sports.read_text(encoding="utf-8"), "previous sports")
            self.assertIn("#EXTINF", (root / "hl.m3u").read_text(encoding="utf-8"))

    def test_html_error_does_not_replace_playlists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sports = root / "tlgapp.m3u"
            sports.write_text("previous sports", encoding="utf-8")
            with patch.object(exporter, "BASE_DIR", root), \
                    patch.object(exporter, "OUTPUT_M3U", sports), \
                    patch.object(exporter, "get_sources", return_value=[{"id": "sport", "url": "sport"}]), \
                    patch.object(exporter, "fetch_text", return_value="<html>Access denied</html>"):
                with self.assertRaises(RuntimeError):
                    exporter.main()
            self.assertEqual(sports.read_text(encoding="utf-8"), "previous sports")


if __name__ == "__main__":
    unittest.main()
