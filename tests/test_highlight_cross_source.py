import unittest
from datetime import date
import combined_m3u_collector as c


class CrossSourceTests(unittest.TestCase):
    def test_same_match_day_prefers_das_but_keeps_other_dates(self):
        def row(source, day, url):
            return dict(source=source, group='Highlight', name='Liverpool vs Arsenal',
                        event_date=day, stream_url=url, skip_event_filter=True)
        das = row('DasFootballHighlight', date(2026, 11, 26), 'https://example.com/a.mp4')
        vsc = row('VSCHighlight', date(2026, 11, 26), 'https://example.com/b.m3u8')
        other = row('VSCHighlight', date(2026, 11, 20), 'https://example.com/c.m3u8')
        result = c.dedupe_and_sort_channels([vsc, das, other])
        self.assertEqual({r['stream_url'] for r in result}, {das['stream_url'], other['stream_url']})
