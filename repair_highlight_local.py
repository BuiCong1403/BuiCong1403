"""Repair missing 24h halves, then merge existing standalone snapshots."""
import combined_m3u_collector as c
import sys


def main():
    _, blocks = c.split_m3u_text_blocks(c.HIGHLIGHT_M3U.read_text(encoding="utf-8-sig"))
    rows = []
    for block in blocks:
        url = c.m3u_block_stream_url(block)
        info = next((c.parse_extinf(x) for x in block if x.startswith("#EXTINF")), None)
        if not info or not url:
            continue
        rows.append(dict(source="24hHighlight" if "cdn.24h.com.vn" in url else "PreviousHighlight",
                         group="Highlight", name=info["title"], stream_url=url, logo=info["logo"],
                         referer=c.extvlcopt_value(block, "http-referrer"), user_agent=c.UA,
                         event_date=c.m3u_block_highlight_date(block), skip_event_filter=True))
    for article in sys.argv[1:]:
        page = c.fetch_text(article, headers=c.h24_headers(article), timeout=25)
        title = c.clean_highlight_title(c.title_from_html_page(page, ""))
        for url, day in c.best_h24_stream_variants([(u, c.h24_date_from_media_url(u)) for u in c.extract_h24_media_urls(page)]):
            if day not in c.h24_allowed_highlight_dates() or not c.is_working_m3u8(url, referer=c.H24_BASE_URL):
                continue
            part = c.h24_stream_part_label(url)
            rows.append(dict(source="24hHighlight", group="Highlight", name=title + (f" [{part}]" if part else ""),
                             stream_url=url, logo="", referer=c.H24_BASE_URL, user_agent=c.UA,
                             event_date=day, skip_event_filter=True))
    rows = c.repair_h24_missing_halves(rows)
    c.write_m3u(c.HIGHLIGHT_M3U, rows)
    c.merge_local_dasfootball_playlists()


if __name__ == "__main__":
    main()
