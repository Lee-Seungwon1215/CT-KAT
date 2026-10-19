"""Refresh the committed corpus with the timing results of the final single-host (V10) campaign.

The committed corpus (docs/corpus/corpus_summary.csv) still holds the timing rows of an earlier
experimental backend. Under the project rules, V10 results are not promoted into the committed
corpus automatically; promotion waits for the automated audit and artifact-integrity gates. This
script produces the V10 refresh that the paper reports, without changing the committed corpus.

For every pair that has a timing axis in the committed-corpus component of the V10 named analysis,
it replaces the timing fields, rewrites the timing part of the notes, and re-folds the overall
status with the unchanged decision procedure (ctkat.evidence.fold_overall). All other pairs and
fields are copied unchanged. timing_leak_target keeps the committed axis key, because the frozen
V10 manifest (docs/measurement/native_timing_v5_campaign.yaml) identifies the ML-KEM decapsulation
row by its committed key `sk` and replaces it with the mixed `valid_tuple` axis; the measured axis
is recorded in the notes.

Usage: python3 refresh_corpus_status.py REPO CORPUS_CSV AXIS_RESULTS_CSV OUT_CSV
  REPO              repository root (for the ctkat package)
  CORPUS_CSV        docs/corpus/corpus_summary.csv
  AXIS_RESULTS_CSV  docs/paper/revision-artifacts/v10_named_analysis/paper_native_axis_results.csv
  OUT_CSV           e.g. docs/paper/revision-artifacts/status/corpus_summary_v10.csv
"""
import csv
import re
import sys
from collections import Counter

repo, corpus_csv, axis_csv, out_csv = sys.argv[1:5]
sys.path.insert(0, repo)
from ctkat.evidence import fold_overall  # noqa: E402

FIELDS = ['correctness', 'structural', 'asm', 'asm_attribution', 'timing_validity',
          'timing_signal', 'review', 'legacy_verdict_class']

# Frozen parameters of the V10 committed-corpus component (docs/measurement/native_timing_v5_campaign.yaml).
V10_MEASUREMENTS = '30000'
V10_THRESHOLD = '|t|>10;n0>=10001'

# Note clauses that described the pre-V10 experimental timing run.
LEGACY_TIMING_CLAUSES = [
    re.compile(r'^timing validity=[a-z-]+$'),
    re.compile(r'^raw (PASS|FAIL) is non-decisional$'),
    re.compile(r'^native sk-axis \|t\|='),
    re.compile(r'^per-iteration keygen confound'),
    re.compile(r'^rely on ct/fo axes$'),
]


def v10_note(axis, validity, signal, abs_t):
    note = f'V10 single-host official dudect {axis} axis: timing validity={validity}, {signal}, |t|={abs_t:.1f}'
    if axis == 'valid_tuple':
        note += ('; the frozen manifest replaces the committed sk key with this mixed axis; '
                 'key and ciphertext change together, so secret attribution is not permitted; '
                 'a follow-up experiment traces the difference to the public key embedded in the secret key')
    return note


v10 = {(r['target'], r['harness']): r for r in csv.DictReader(open(axis_csv, encoding='utf-8'))
       if r['component'] == 'committed-corpus-refresh'}
with open(corpus_csv, newline='', encoding='utf-8') as fh:
    rows = list(csv.DictReader(fh))
fieldnames = list(rows[0].keys())

refreshed = 0
for i, r in enumerate(rows, 1):
    v = v10.get((r['target'], r['harness']))
    if v is None:
        continue
    refreshed += 1
    old = r['overall']
    abs_t = float(v['abs_t_score'])
    r.update(timing_validity=v['timing_validity'], timing_signal=v['timing_signal'],
             timing_backend='official-dudect', timing_raw_status=v['raw_status'],
             timing_abs_t=f'{abs_t:.3f}', timing_measurements=V10_MEASUREMENTS,
             timing_threshold=V10_THRESHOLD)
    kept = [c for c in r['notes'].split('; ') if not any(p.search(c) for p in LEGACY_TIMING_CLAUSES)]
    r['notes'] = '; '.join(kept + [v10_note(v['axis'], v['timing_validity'], v['timing_signal'], abs_t)])
    r['overall'] = fold_overall(**{k: r[k] for k in FIELDS}).value
    print(f'#{i:<2} {r["target"]}/{r["harness"]}: {old} -> {r["overall"]}')

print('refreshed axes:', refreshed)
print('distribution:', dict(Counter(r['overall'] for r in rows)))
with open(out_csv, 'w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
