"""Re-fold the corpus statuses with the timing results of the final single-host (V10) campaign.

The committed corpus summary (docs/corpus/corpus_summary.csv) still carries timing rows from an
earlier experimental backend. This script replaces the timing fields of every pair that has a
timing axis in the committed-corpus component of the V10 named analysis and re-folds the overall
status with the unchanged decision procedure (ctkat.evidence.fold_overall).

Usage: python3 refresh_corpus_status.py REPO AXIS_RESULTS_CSV OUT_CSV
  REPO              repository root (for ctkat and docs/corpus/corpus_summary.csv)
  AXIS_RESULTS_CSV  v10_named_analysis/paper_native_axis_results.csv
  OUT_CSV           output path, e.g. corpus_summary_v10.csv
"""
import csv
import sys
from collections import Counter

repo, axis_csv, out_csv = sys.argv[1:4]
sys.path.insert(0, repo)
from ctkat.evidence import fold_overall  # noqa: E402

FIELDS = ['correctness', 'structural', 'asm', 'asm_attribution', 'timing_validity',
          'timing_signal', 'review', 'legacy_verdict_class']

v10 = {(r['target'], r['harness']): r for r in csv.DictReader(open(axis_csv, encoding='utf-8'))
       if r['component'] == 'committed-corpus-refresh'}
rows = list(csv.DictReader(open(f'{repo}/docs/corpus/corpus_summary.csv', encoding='utf-8')))
fieldnames = list(rows[0].keys())

mapped = 0
for i, r in enumerate(rows, 1):
    key = (r['target'], r['harness'])
    if key not in v10:
        continue
    v = v10[key]
    mapped += 1
    old = r['overall']
    r.update(timing_validity=v['timing_validity'], timing_signal=v['timing_signal'],
             timing_backend='official-dudect', timing_raw_status=v['raw_status'],
             timing_abs_t=f"{float(v['abs_t_score']):.3f}")
    r['overall'] = fold_overall(**{k: r[k] for k in FIELDS}).value
    print(f'#{i:<2} {r["target"]}/{r["harness"]}: {old} -> {r["overall"]}')

print('mapped axes:', mapped)
print('distribution:', dict(Counter(r['overall'] for r in rows)))
with open(out_csv, 'w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
