# V2 OOS date clarification (NON-PINNED audit note)

An earlier conversational progress message mentioned 2026-10-05→2027-10-04 as a prospective OOS candidate. This date range was never written to any V2 artifact, protocol, registry, manifest, witness, or frozen campaign. The authoritative and cryptographically pinned V2 OOS is 2027-01-04T00:00:00Z through 2028-01-03T00:00:00Z. No campaign state was changed.

## Verification (2026-09-29, read-only)
- **Scan.** Searched for `2026-10-05` / `2027-10-04` in:
  - `research/registry_v2/`
  - all four `registry_v2_superseded_*` archives and their notes
  - `~/.nexa_registry_witness/`
  - `protocols_phase3_v2.py`
  - `OOS_DETERMINATION_V2.md`
  - `PHASE3_V2_MANIFEST.md`
  - `V2_EXTERNAL_CHECKPOINT_PROCEDURE.md`

  **No match.** The only occurrences are in `reports/adversarial_v2_final/`. There, attack A06b deliberately tries to rewrite a protocol to that window, and the registry rejects it.
- **Protocols.** All six frozen protocols in `registry_v2/protocols/` match their campaign pins. F1, F2, F3 and F5 carry:
  - `OOS = [2027-01-04T00:00:00Z, 2028-01-03T00:00:00Z)`
  - `EXCLUDED = [2025-01-01T00:00:00Z, 2027-01-04T00:00:00Z)`

  F4 and F6 are BLOCKED. They carry only a placeholder tick schedule inside 2027, which requires post-freeze data.
- **Pinning.** `sha256(campaign.json)` equals the anchor `6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c`. `campaign.json` pins every protocol hash, so the anchor transitively pins these dates.
- **Pinned files untouched.** This note is deliberately **not** a pinned design artifact. The pinned OOS design file and the campaign were not edited to record this history.
