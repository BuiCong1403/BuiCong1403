import unittest
from unittest.mock import patch
import combined_m3u_collector as c


class PlayerTests(unittest.TestCase):
    def test_collects_distinct_alternatives_without_ads(self):
        page = """var urlStream = 'https://cdn.example/live.flv';
            var adsTvc = [{"file":"https://cdn.example/ad.m3u8"}];
            let alternatives = ["https://cdn.example/live.flv","https://cdn.example/hd.m3u8?t=1"];"""
        with patch.object(c, "fetch_text", return_value=page):
            self.assertEqual(c.extract_xoilacz_url_streams("https://player.example/", {}),
                             ["https://cdn.example/live.flv", "https://cdn.example/hd.m3u8?t=1"])

    def test_ad_alone_is_not_a_match(self):
        with patch.object(c, "fetch_text", return_value='var adsTvc = [{"file":"https://cdn.example/ad.m3u8"}];'):
            self.assertEqual(c.extract_xoilacz_url_streams("https://player.example/", {}), [])
