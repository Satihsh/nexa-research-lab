# YouTube HTTP 429: diagnosis and guard (2026-10-11)

## 1. Components (inspected in the uv cache; nothing modified)

| Layer | Package / version | Endpoint(s) | Used by |
|---|---|---|---|
| MCP server | `yt-mcp-server` 0.1.2 (`youtube_mcp_server`), launched by `uvx --from yt-mcp-server youtube-mcp-server` (user scope, `~/.claude.json`) | — | all `mcp__youtube__*` tools |
| Metadata | `yt-dlp` 2026.8.19 | watch page / player API via yt-dlp's own client rotation | `get_video_info`, `get_channel_info`, `get_channel_videos`, `search_videos`, `get_comments` |
| Transcripts | `youtube-transcript-api` 1.2.4 | (1) `GET https://www.youtube.com/watch?v={id}`; (2) `POST https://www.youtube.com/youtubei/v1/player?key={INNERTUBE_API_KEY}` with client `ANDROID 20.10.38`; (3) `GET` caption `baseUrl` (`/api/timedtext`) | `get_transcript`, `search_transcript`, `search_channel_transcripts` |

**Error path:**
- `_raise_http_errors()` maps **HTTP 429 → `IpBlocked`**.
- A reCAPTCHA page (`class="g-recaptcha"`) is also mapped to `IpBlocked`.
- The MCP converts any exception whose text contains "IP" into the fixed message "YouTube is temporarily blocking transcript requests from your IP…". The real exception is hidden; even unrelated errors containing "IP" are mislabelled.
- In the in-app browser, the caption URL returned **HTTP 429 with Google's "Sorry…" interstitial**, and the in-page `get_transcript` endpoint returned 400 "Precondition check failed". The block is per-IP on the caption path.

## 2. Scope of the failure
- **Metadata: working.** `get_video_info`, `get_channel_info` and `get_channel_videos` succeeded throughout the block (13+ calls, 2026-10-11).
- **Transcripts: blocked.** Every transcript route from this IP failed (MCP, direct caption URL, browser). The urllib watcher got 429 at 06:52, 07:22 and 07:52.

## 3. Root cause
1. **YouTube per-IP rate limiting of the caption/innertube path** after a burst of transcript requests. Earlier sessions pulled about 14 long transcripts plus channel transcript searches.
2. **Amplifiers in `yt-mcp-server`** (the server, not YouTube):
   - `get_transcript` catches *any* exception from `fetch()` and immediately runs a second full request chain (`list()` → `find_generated_transcript().fetch()`). Every blocked call costs about 2× the requests.
   - `search_channel_transcripts` fans out **5 parallel workers over up to 50 videos** with no pacing. This is the likely trigger of the initial block.
   - There is no backoff, cooldown or budget; each tool call re-hits the blocked endpoint.
   - Error mapping by substring hides the real exception class.
3. **Our own retries:** about 10 additional blocked attempts (MCP, browser, watcher) before the guard existed, which plausibly extended the block.

## 4. Authorised alternatives
- **The server itself:** no configuration hooks. It constructs `YouTubeTranscriptApi()` with no proxy, cookie or API-key options and reads no env vars for them.
- **The library:** supports proxies (`GenericProxyConfig`, `WebshareProxyConfig`; paid residential proxies recommended in its own messages, with an affiliate link) and cookie auth, which the library itself labels **NOT RECOMMENDED** (risk of a permanent account ban). **Both are excluded by the user's constraints.**
- **The official YouTube Data API v3 `captions.download`:** requires OAuth (`youtube.force-ssl` or `youtubepartner`) **and permission to edit the video** (403 `forbidden` otherwise); 200 quota units per call. **Not usable for third-party videos.** `captions.list` only lists tracks.
- **Free, authorised routes:**
  - wait out the block, using the guard below;
  - you export or paste transcripts from your own browser session (a different IP, and YouTube's own "Show transcript" UI);
  - creator-published transcripts or show notes where they exist.

## 5. Guard implemented (`yt_transcript_guard.py`, no installs, MCP untouched)
- **Interpreter:** the MCP's cached uv-env Python (already present).
- **Persistent state:** `yt_guard_state.json`.
- **Cooldown:** min(48 h, 2 h·2^(n−1)) + ≤ 10 min jitter after the n-th consecutive block. No request is made while it is active.
- **Stop-on-block:** the first block ends the run immediately.
- **Budget:** 25 videos per day, 10 per run, ≥ 30–45 s spacing.
- **One request chain per video** (no `list()` fallback). Permanent failures (disabled, unavailable) are never retried.
- **Lock file:** only one run at a time.
- **Self-test:** 7/7 (no network).

**Run state (2026-10-11):**
- Seeded with 2 observed blocks, so the cooldown runs until **11:52**.
- The old fixed-interval watcher was stopped.
- The guarded `watch` runs 17 queued videos in priority order, max 3 attempts, 36 h. If blocked, the cooldown escalates 8 h → 16 h, so the worst case is about 9 HTTP requests in ~24 h.

## 6. Proposed MCP-level changes (**not done; need approval**)

| Option | What | Cost | Risk |
|---|---|---|---|
| A. Use the guard for all transcript work; call `mcp__youtube__*` only for metadata | Operating rule (memory note) | 0 | None |
| B. A local wrapper MCP (or patched copy) that applies the same cooldown/budget and removes the double fetch and 5-worker fan-out | Changes the `~/.claude.json` MCP entry, plus a small local server file | 0 | A config change; needs a restart |
| C. Upstream issue/PR to `yt-mcp-server` (backoff, no double fetch, exact error classes) | GitHub contribution | 0 | None locally |
| D. Residential proxies (library-supported) | **Excluded by user**; about $3–15/GB-type pricing at proxy vendors (not checked) | Paid | ToS grey area |
| E. Cookie authentication | **Excluded by user**; the library warns of permanent account bans | 0 | Account ban |
| F. Official Data API | Only for videos you can edit | 0 quota-wise | Not applicable |
