# Final adversarial audit evidence (PHASE3_SIX_FAMILIES_V2, anchor 6090be68…9324c)

- `attack_registry_v2_final.py.txt`: the harness. It runs against a **scratch copy** only. The large M1 files are symlinked read-only; everything else is copied.
- `attack_results.txt`: the final run. **70 attacks, 70 EXPECTED_REJECTION; 4/4 legitimate controls accepted; 0 DEFECT.**
- The real registry tree (`de0c101a…`) and witness (`05d4544b…`) were byte-identical before and after the run.

Reproduce with:
```bash
python attack_registry_v2_final.py <scratch> 6090be68184af7643f82b680d144a1b9e1622b3bbceebfb872729b97b9d9324c 6 bbd9a28ed6bc7e0b20f3fca9f9ba1fe437f4bd39dc9c1e99ed73fb7505be5b2b
```

Earlier runs, kept for the record:
- `research/reports/adversarial_v2/` holds the 2026-09-27 evidence, whose defects A6d, A10b and X1 were fixed.
- During 2026-09-29 one run found A30b (a raw exception on a missing protocol file). It was fixed and the freeze superseded.
- A25 once showed as a DEFECT because of a harness bug: the function was called before it was defined.
