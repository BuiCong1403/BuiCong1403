# Sports sources awaiting a live-event check

Recorded: 2026-11-18, Vietnam time (UTC+7).

The user reports that both sites have events starting at 18:00 on this date.
This is a one-date observation, not a confirmed daily schedule.

## Nem Bien TV

- Home: https://nembientv.com/
- Observed schedule endpoint: /cms-schedule.json (response array).
- Match page: /truc-tiep/{matchId}.
- Observed player source endpoint: /truc-tiep/{matchId}?kd_source=1.
- Earlier check: 18 matches; all source responses had an empty streamUrl.
- Do not export the waiting or reconnect videos as match streams.

## Tra Da TV

- Home: https://tradatv.live/
- User-supplied candidate; player and data endpoints not yet inspected.
- Sample supplied and checked on 2026-11-18:
  https://tradatv-s2.b-cdn.net/live/loachim_s21a562bb4.m3u8
- HTTP 200 HLS media playlist; a listed segment returned video/MP2T with TS
  sync bytes. Media sequence advanced from 136696 to 136697 during the check.
  Requests succeeded without a custom Referer. Match identity and visual
  content have not been verified; do not label this as a specific match yet.
- User subsequently identified the sample as SOOP Soopers W vs Hyundai E&C
  Hillstate W, dated 2026-11-18, commentator slug `lo-a-chim`:
  https://tradatv.live/truc-tiep/?slug=soop-soopers-w-vs-hyundai-e-c-hillstate-w-18-11-2026&blv=lo-a-chim
  This association is user-provided; kickoff time and the site's dynamic
  source mapping still need extraction. The page returns a Next.js shell.
- Verified against the homepage's public data API: base
  https://htdk.httdtvnb.xyz; endpoint
  /matches/by-slug/soop-soopers-w-vs-hyundai-e-c-hillstate-w-18-11-2026.
  Match ID yaA7CIf3nKQr, sport volleyball, startTime
  2026-11-18T10:00:00Z = 17:00 Vietnam time. The streams array directly
  associates the sample HLS URL above with commentator LO A CHIM.
  This supersedes the earlier unverified match/time mapping note.

## Next check

Update 2026-11-19: TraDaTV is integrated into the regular live collector using
the public /matches API, all sports, all unique HLS/FLV streams, Vietnam kickoff
times and today/tomorrow filtering. Expired cache entries are never reused;
cache is used only when the API request fails. HLS goes into all.m3u and
ott.m3u; FLV follows the existing OTT-only rule. Three focused tests pass.
Nem Bien TV is still pending; the user reports today's first match at 15:30 ICT.

Check both sites while a match is actually live, starting from the user-reported
18:00 window. Verify real HLS/FLV media, headers, match names and Vietnam kickoff
times before integrating with all.m3u and ott.m3u. Keep waiting videos out of
the playlists. No automatic task or collector has been enabled by this note.
