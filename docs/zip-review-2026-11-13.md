# Review of files.zip

The archive was reviewed as reference material, not as commands to execute.

## Applied

- The shared publisher refuses to replace an existing nonempty M3U with an
  empty or invalid result. Failed generated output remains available for the
  existing failure-artifact step; remote data is not overwritten.
- Timestamp-only playlist changes retain their previous content-change time.
  Workflow run status remains the record of when collection was attempted.
- Ignore local environment/configuration files and temporary scraper probes.
- Remove eleven untracked HTML/JS/current-playlist probes with no code references.

## Not copied

- `m3u_manager.py`: the generic merger does not implement this repository's
  match scheduling, separate OTT format, source snapshots or highlight halves.
  Its health check also ignores channel-specific headers and can mistake an
  HTML error page for a valid non-HLS stream. URL-only deduplication may discard
  the same stream intentionally listed under different matches.
- `playlists.yml`: another scheduler is unnecessary. Its `playlists-main` lock
  differs from the existing `playlist-main` lock and would not serialize writes.
- `commit_push.sh`: `rebase -X theirs` can silently choose generated data over
  newer remote changes. Keep the existing fail-closed publisher and artifacts.
- Sample config and playlist: contain example.com placeholders, not new sources.
- `requirements.txt`: requests is already installed by the relevant workflows.
- `SECURITY_CLEANUP.md`: no history rewriting, force push, secret revocation or
  repository visibility changes were authorized or performed.

## Retained deliberately

Keep manual VTV/highlight repair scripts, local DasFootball launchers, active
snapshots/caches and tests. Tinhlagi and CaoDanh collectors remain available for
manual recovery; their automatic schedules were disabled on 2026-11-12.
The original ZIP and its contents outside this repository were not deleted.
