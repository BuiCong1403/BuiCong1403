"""Refresh only VTV blocks without fetching unrelated live sports sources."""
from pathlib import Path
from tempfile import TemporaryDirectory
import combined_m3u_collector as c


def main():
    channels = c.collect_vtv_channels()
    if not channels:
        raise RuntimeError('No VTV channels; preserving playlists')
    channels += c.collect_vtvgo_fast()
    with TemporaryDirectory() as folder:
        for target, writer in ((c.ALL_M3U, c.write_m3u), (c.OTT_M3U, c.write_ott_m3u)):
            generated = Path(folder) / target.name
            writer(generated, channels)
            _, new_blocks = c.split_m3u_text_blocks(generated.read_text(encoding='utf-8'))
            header, blocks = c.split_m3u_text_blocks(target.read_text(encoding='utf-8-sig'))
            kept = []
            for block in blocks:
                info = next((c.parse_extinf(line) for line in block if line.startswith('#EXTINF')), {})
                group = next((line.split(':', 1)[1].strip() for line in block if line.startswith('#EXTGRP:')), info.get('group', ''))
                if c.group_key(group) != 'vtv':
                    kept.append(block)
            c.write_m3u_text_blocks(target, header, new_blocks + kept)
    print(f'VTV refreshed: {len(channels)} entries including existing FAST channels')


if __name__ == '__main__':
    main()
