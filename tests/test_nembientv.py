import unittest
from datetime import datetime, timedelta
from unittest.mock import patch
import combined_m3u_collector as c


class NemBienTests(unittest.TestCase):
    def collect(self, url):
        match = dict(matchId='sample', timestamp=int((datetime.now(c.TZ_VN) + timedelta(minutes=5)).timestamp()),
                     home='Home', away='Away', sport='volleyball', hasLiveSource=False,
                     commentators=[{'name': 'BLV Test'}, {'name': 'BLV Test'}, None])
        with patch.object(c, 'fetch_json_no_cache', side_effect=[{'response': [match]}, {'streamUrl': url}]), \
             patch.object(c, 'save_source_cache'), patch.object(c, 'fetch_text', return_value=''):
            return c.collect_nembientv()

    def test_false_flag_does_not_hide_real_stream(self):
        rows = self.collect('https://example.com/live/index.m3u8')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['sport'], 'volleyball')
        self.assertTrue(rows[0]['name'].endswith('[BLV Test]'))
        self.assertEqual(len(c.select_ott_compatible_channels(rows)), 1)

    def test_waiting_and_empty_not_exported(self):
        self.assertEqual(self.collect(''), [])
        self.assertEqual(self.collect('https://live.nembientv.com/nembien_tv_wait_hls/index.m3u8'), [])

    def test_rolling_24_hour_boundary(self):
        now = datetime(2026, 11, 19, 16, 30, tzinfo=c.TZ_VN)
        self.assertTrue(c.in_next_24_hours(now, now))
        self.assertTrue(c.in_next_24_hours(now + timedelta(hours=24), now))
        self.assertFalse(c.in_next_24_hours(now + timedelta(hours=24, seconds=1), now))
        self.assertTrue(c.in_next_24_hours(now - timedelta(hours=2), now))
        self.assertTrue(c.in_next_24_hours(now - timedelta(hours=3), now))
        self.assertFalse(c.in_next_24_hours(now - timedelta(hours=3, seconds=1), now))

    def test_page_player_assignment(self):
        with patch.object(c, 'fetch_text', return_value='const hlsStreamUrl = "https://example.com/live.m3u8?a=1&b=2";'):
            self.assertEqual(c.nembien_page_stream('https://example.com/match'), 'https://example.com/live.m3u8?a=1&b=2')
        with patch.object(c, 'fetch_text', return_value='const hlsStreamUrl = "";'):
            self.assertEqual(c.nembien_page_stream('https://example.com/match'), '')

    def test_api_failure_uses_page(self):
        match = dict(matchId='test', timestamp=int((datetime.now(c.TZ_VN) + timedelta(minutes=5)).timestamp()), home='A', away='B')
        with patch.object(c, 'fetch_json_no_cache', side_effect=[{'response': [match]}, TimeoutError()]), \
             patch.object(c, 'fetch_text', return_value='const hlsStreamUrl = "https://example.com/real.m3u8";'), \
             patch.object(c, 'save_source_cache'):
            self.assertEqual(c.collect_nembientv()[0]['stream_url'], 'https://example.com/real.m3u8')


if __name__ == '__main__':
    unittest.main()
