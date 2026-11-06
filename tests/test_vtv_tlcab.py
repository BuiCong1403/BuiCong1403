import unittest
from unittest.mock import patch
import combined_m3u_collector as c


class TLCabVTVTests(unittest.TestCase):
    def test_import_whole_group_without_cab_or_mpd(self):
        primary = dict(name="VTV1", group="VTV", stream_url="https://example.com/one.m3u8")
        backup = [dict(primary),
                  dict(name="VTVGo Event 1", group="VTV", stream_url="https://example.com/event.m3u8"),
                  dict(name="VTVGo Ca Nhac", group="VTV", stream_url="https://example.com/music.m3u8"),
                  dict(name="VTVPrime", group="VTV", stream_url="https://example.com/a.mpd"),
                  dict(name="VTVcab", group="VTVCab", stream_url="https://example.com/cab.m3u8")]
        with patch.object(c, 'collect_m3u_playlist', side_effect=[[primary], backup]) as fetch, \
             patch.object(c, 'save_vmttv_vtv_cache'), \
             patch.object(c, 'VMTTV_VTV_MIN_GOOD_COUNT', 1):
            rows = c.collect_vtv_channels()
        self.assertEqual([r['name'] for r in rows], ['VTV1', 'VTV1-1', 'VTVGo Event 1-1', 'VTVGo Ca Nhac-1'])
        self.assertEqual(fetch.call_args_list[1].args[1], c.TLCAB_VTV_M3U_URL)


if __name__ == '__main__':
    unittest.main()
