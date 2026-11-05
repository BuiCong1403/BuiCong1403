import unittest
from datetime import datetime
from unittest.mock import patch
import combined_m3u_collector as c


class ArticleRepairTests(unittest.TestCase):
    def test_prague_praha_same_fixture(self):
        self.assertEqual(c.highlight_fixture_key({'name': 'Slavia Prague - Arsenal: Highlights'}),
                         c.highlight_fixture_key({'name': 'Slavia Praha vs Arsenal'}))

    def test_opinion_title_does_not_hide_second_half(self):
        day = datetime.now(c.TZ_VN).date()
        base = f'https://cdn.24h.com.vn/upload/{day}/'
        first = base + '1793833809-lens_como1.m3u8'
        second = base + '1793833810-lens_como2_720p.m3u8'
        original = {'source': '24hHighlight', 'name': 'Como surprises Europe',
                    'group': 'Highlight', 'stream_url': first, 'event_date': day}
        with patch.object(c, 'fetch_text', return_value='page'), \
             patch.object(c, 'extract_h24_article_urls', return_value=['https://www.24h.com.vn/match']), \
             patch.object(c, 'title_from_html_page', return_value='Lens - Como: Highlights'), \
             patch.object(c, 'extract_h24_media_urls', return_value=[first, second]), \
             patch.object(c, 'is_working_m3u8', return_value=True), \
             patch.object(c, 'merge_and_save_h24_highlight_cache'):
            rows = c.repair_h24_missing_halves([original])
        self.assertIn(second, [r['stream_url'] for r in rows])
        self.assertTrue(all(r['name'].startswith('Lens - Como') for r in rows))
