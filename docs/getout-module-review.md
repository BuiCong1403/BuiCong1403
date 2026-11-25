# GetOut module review (2026-11-25)

Reference: https://github.com/leeshin5757/getout/tree/main/module

Static analysis only; downloaded DEX modules were not executed. Android DEX
bytecode was decompiled locally with Androguard. Reconstructed Java is not
the original source and can contain decompiler artifacts.

## Applied

NemBien.loadLink reads the actual `hlsStreamUrl` assignment from the match
page. The collector now uses this as a bounded fallback when `?kd_source=1`
fails or returns no usable URL. Empty assignments and waiting streams are
not exported. No synthetic `/live/{id}/index.m3u8` URLs are generated.
The existing half-hour workflow and all/OTT merge remain unchanged.

## Findings not enabled

- TraDa uses `/matches/by-slug/` (already used here) and paginated
  `/matches/spotlight?sport=...&liveOnly=false&page=...&pageSize=12` for
  football, volleyball, badminton, basketball, billiards, esports and tennis.
  A live volleyball spotlight request timed out; expansion is not enabled.
- VSC uses `/api/proxy/data/lives/matches` and separate esports match routes.
  These require further comparison with the existing VSC collector before
  changing production behavior.
- XoiLac has a rotating-domain reference at the upstream `txt/xoilactv` file.
  The address found in bytecode is not proof that it is currently usable.
- AntLive contains API discovery and WebSocket/session logic. Static URLs
  alone are not enough to establish a working playlist export.

Local decompiled review files are in `getout_module_review` in the user's
New project workspace, outside this repository. Removed providers are not
re-enabled and upstream executable code is not installed into workflows.
