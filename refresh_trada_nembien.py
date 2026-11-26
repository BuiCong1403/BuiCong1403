"""Refresh short-lived live streams, then merge into existing playlists."""
import combined_m3u_collector as collector


def main():
    rows = []
    previous = []
    for source, group, filename, collect in (
        ("TraDaTV", "Trà Đá TV", "tradatv_cache.json", collector.collect_tradatv),
        ("NemBienTV", "Ném Biên TV", "nembientv_cache.json", collector.collect_nembientv),
        ("AntLive", "AntLive", "antlive_cache.json", collector.collect_antlive),
    ):
        previous.extend(collector.load_source_cache(collector.BASE_DIR / filename, source, group, allow_flv=True))
        rows.extend(collect())
    collector.merge_slow_source_playlists(rows, previous)
    collector.log(f"[TraDaNemBien] {len(rows)} links; other sources were not collected")


if __name__ == "__main__":
    main()
