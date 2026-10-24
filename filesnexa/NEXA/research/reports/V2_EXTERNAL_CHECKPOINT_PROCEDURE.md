# PHASE3_SIX_FAMILIES_V2: external checkpoint procedure (R1 control)

## The limitation
Someone with write access to this Mac can rewrite `research/registry_v2/ledger.jsonl` and the witness `~/.nexa_registry_witness/<anchor>.jsonl` *consistently*. For example, they could roll back a validation query, or append a forged `EVALUATION_OPENED` or `OOS_SELECTED` event. Hashes stored on the same machine cannot detect this. This is the R1 trust-boundary limitation, and no local mechanism removes it.

## The control
The authoritative history is the sequence of ledger heads **published off this machine**. The local copy counts only as far as it matches that sequence.

1. **Campaign anchor.** The value `sha256(campaign.json)` is published off-machine once, at freeze time.
2. **Ledger head after every event.** Every mutating registry call returns its ledger entry:
   - `register_builder`
   - `register_event_builder`
   - `open_evaluation`
   - `select_for_oos`
   - `record`
   - `reject`

   Before the next call, publish the entry's `(seq, entry_sha256)` off-machine as a `NEXA-CHECKPOINT` line (`RegistryV2.checkpoint_line`).
3. **Compare-and-swap.** Every mutating call **requires** `checkpoint={"seq", "entry_sha256"}` equal to the current local head. The registry refuses the call in any of these cases:
   - the checkpoint is missing or malformed;
   - the checkpoint is not in the local ledger (rollback or rewrite);
   - the local ledger has entries beyond the checkpoint (unpublished or forged events).
4. **Verification against the checkpoint.** `RegistryV2.verify(anchor, checkpoint=<last published>)` pins the local ledger to the published head. Local-only `verify(anchor)` cannot detect R1. Any audit that matters must pass the published checkpoint.

## Acceptable off-machine records
Any record the local actor cannot silently rewrite qualifies:
- a signed tag or commit pushed to a remote Git host;
- an email or message to yourself;
- this conversation's transcript;
- a printed or notarised note.

Blockchain is not required. The repository is currently **not** a Git repository, so no remote Git record exists yet. Creating one and pushing is a human action. Nothing is pushed automatically.

## Minimum operating rule
Never run a mutating registry call unless the checkpoint you pass is copied **from the off-machine record**, not read from the local ledger. Reading it from the local ledger reduces compare-and-swap to a local-only check.
