# NEXA Order-Flow & Market-Intelligence Knowledge Base (persistent, self-updating)

**Purpose:** one place where everything learned about order flow, volume/market profile, options/GEX and intraday breakout trading is stored as **reusable, citable, testable knowledge**. Every future session reads this first, adds to it, and updates claim statuses as evidence arrives.

**Rule zero:** nothing in this KB is a trading rule. Practitioner content is a *source of hypotheses*. A claim moves to SUPPORTED only through NEXA's pre-registered validation (RESEARCH_GATE G0→G7). Profitability is never assumed.

## Files

| File | What it holds | Update when |
|---|---|---|
| `SOURCES.md` | Registry of every source (ID, provenance, depth studied, conflicts of interest, reliability grade) | Any new video, doc, paper, note |
| `CONCEPTS.md` | Concept cards: consensus definition, disagreements between sources, NEXA measurability, linked hypotheses | A source adds or contradicts a definition |
| `CLAIMS.md` | Atomic claims (one row each) with source + timestamp, claim type, evidence offered, **status**, linked test | Every source; every test result |
| `HYPOTHESIS_QUEUE.md` | Testable hypotheses derived from claims (OF-xx), priority, pre-registration sketch | New claims; after each test |
| `GAPS.md` | Knowledge gaps, data gaps, unstudied-source queue, open questions | Continuously |
| `CHANGELOG.md` | Dated log of what changed and why | Every edit |
| `TOOLING_EVALUATIONS.md` | External tools/MCP servers/data vendors: what they do, safety findings, verdict for NEXA | Any tool/integration source |

Parent research documents (narrative): `../NEXA_ORDERFLOW_FRAMEWORK_REPORT.md`, `../ADDENDUM_A_VISHAAL_FX_VIDEO.md`, `../DEEPCHARTS_DOCUMENTATION_STUDY.md`. Registries upstream: `../../14_HYPOTHESIS_REGISTRY.md`, `../../11_NEW_MATHEMATICAL_CONSTRUCTS.md`, `../../validation/RESEARCH_GATE.md`.

## Update protocol (follow exactly)

1. **Register the source** in `SOURCES.md` before extracting anything: ID (`SRC-YT-nnn`, `SRC-DOC-nnn`, `SRC-NOTE-nnn`, `SRC-LIT-nnn`), title, author/channel, date, length, how it was accessed (transcript / docs / frames), **depth studied** (FULL / PARTIAL / METADATA), commercial interest (affiliate links, product sales, recruitment), reliability grade (A peer-reviewed/official docs … E anonymous marketing).
2. **Extract atomic claims** into `CLAIMS.md`: one testable statement per row, **paraphrased** (no long verbatim transcript copying), with `source:timestamp`. Classify type: DEF (definition), MECH (mechanism), STAT (quantitative/statistical), ANEC (anecdote/example), RULE (trading rule), OPIN (opinion).
3. **Merge into concepts** (`CONCEPTS.md`): add the source to "who says what"; record contradictions explicitly; never overwrite an earlier source's view — append.
4. **Derive or update hypotheses** (`HYPOTHESIS_QUEUE.md`): map each RULE/STAT claim to an existing OF-/HYP- ID or create a new OF-ID; state data feasibility for NEXA (CALC / PROXY / NO).
5. **Record gaps** (`GAPS.md`): what could not be verified, what data is missing, which sources remain unstudied.
6. **Log** the change in `CHANGELOG.md` and, if the change is material, update the memory note `nexa-orderflow-kb`.
7. **After any NEXA test:** update the claim status (UNTESTED → SUPPORTED / CONTRADICTED / INCONCLUSIVE / BLOCKED) with the evidence artefact path. Negative results are kept.

## Status vocabulary (claims)

`UNTESTED` · `TESTABLE` (NEXA data suffices) · `PROXY-ONLY` (testable only with a proxy) · `BLOCKED-DATA` (needs data NEXA lacks) · `UNTESTABLE` (no operational definition / proprietary) · `CONTRADICTED-BY-SOURCE` (another source disagrees; both kept) · `SUPPORTED` / `CONTRADICTED` / `INCONCLUSIVE` (only from a NEXA pre-registered test, with artefact link).

## Evidence classes (added 2026-10-11; carried in the CLAIMS "Type" column)

- `VERIFIED-DOC`: an official documentation statement about what a tool *is* or *does by default* (definition, parameter, default, data requirement). This is a verifiable fact about the tool, **not** evidence that the tool predicts anything.
- `VENDOR-CLAIM`: a performance, accuracy or "what it reveals" statement by the seller of the tool. It is unverified unless data is shown.
- `PRESENTER-CLAIM`: a statement by an educator or streamer. The source's commercial interest is in `SOURCES.md`.
- `CODE-REVIEW`: NEXA's own reading of published source code (a verifiable fact about that code).
- `HYPOTHESIS`: NEXA's own derived, testable statement, held in `HYPOTHESIS_QUEUE.md` and never in CLAIMS.
- `TOPIC-ONLY`: known only from a chapter title or metadata. It is not a claim until the transcript has been read.

## Transcript access rule (option A, user-approved 2026-10-11)

- **Transcripts:** fetch them **only** through `../tools/yt_transcript_guard.py`, run with the YouTube MCP's uv-env Python (`~/.cache/uv/archive-v0/onvQ7qVfolMBxbcz/bin/python -I`). Run `status` first. While the cooldown is active, make no YouTube transcript requests by any route.
- **Metadata:** use `mcp__youtube__*` for metadata only (`get_video_info`, `get_channel_info`, `get_channel_videos`, `search_videos`). Never call the MCP's `get_transcript`, `search_transcript` or `search_channel_transcripts` directly.
- **Excluded:** no proxies, no cookies, no browser-based caption scraping.
- Diagnosis: `../tools/YT_RATE_LIMIT_DIAGNOSIS.md`.

## Hard constraints (inherited)

Research only. No production code changes, no market-data collection without approval, no MT5 interaction, no trading. 2027 data needs approval (V2 OOS). Risk Engine remains the final authority in any future design.
