import unittest
import combined_m3u_collector as c


class AntLiveTests(unittest.TestCase):
    def test_actual_streams_and_deduplicate(self):
        room = dict(houseName='A vs B', nickName='BLV', houseId='123',
                    playStreamAddress='https://example.com/a.flv',
                    playStreamAddress2='https://example.com/a.m3u8',
                    playStreamAddress3='https://example.com/a.flv')
        rows = c.parse_antlive_streams({'data': {'ongoingLivestreams': [room, room]}})
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['name'], 'A vs B (BLV) [FLV]')
        self.assertEqual(len(c.select_ott_compatible_channels(rows)), 2)
        self.assertEqual(len(c.split_ott_channels(rows)[0]), 1)

    def test_no_synthetic_stream(self):
        self.assertEqual(c.parse_antlive_streams({'data': {'ongoingLivestreams': [{'houseId': '123'}]}}), [])
