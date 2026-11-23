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
             patch.object(c, 'save_source_cache'):
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


if __name__ == '__main__':
    unittest.main()
