"""Compare two naive pass/fail aggregations with the CT-KAT statuses (Section 5.3).

Usage: python3 naive_vs_ctkat.py corpus_summary_v10.csv
"""
import csv
import sys
from collections import Counter

rows = list(csv.DictReader(open(sys.argv[1], encoding='utf-8')))

NAIVE = {
    # any tool reports a problem -> "vulnerable", otherwise "safe"
    'any-tool': lambda r: r['structural'] == 'finding' or r['asm'] == 'candidate' or r['timing_raw_status'] == 'FAIL',
    # dynamic tools only (Valgrind + timing), as in a typical two-tool pipeline
    'valgrind+timing': lambda r: r['structural'] == 'finding' or r['timing_raw_status'] == 'FAIL',
}

for name, vulnerable in NAIVE.items():
    table = Counter()
    for r in rows:
        table[('vulnerable' if vulnerable(r) else 'safe', r['overall'])] += 1
    safe_but_open = sum(v for (n, o), v in table.items() if n == 'safe' and o != 'no-finding-observed')
    vuln_but_not_risk = sum(v for (n, o), v in table.items() if n == 'vulnerable' and o != 'risk-detected')
    print(f'\n== naive rule: {name}')
    for (n, o), v in sorted(table.items()):
        print(f'  naive={n:10} ctkat={o:20} {v}')
    print(f'  naive "safe" but CT-KAT still open (inconclusive/needs-review/...): {safe_but_open}')
    print(f'  naive "vulnerable" but CT-KAT not Risk Identified: {vuln_but_not_risk}')
    for r in rows:
        if not vulnerable(r) and r['overall'] != 'no-finding-observed':
            print(f'    safe-but-open: {r["target"]}/{r["harness"]} -> {r["overall"]} '
                  f'(correctness={r["correctness"]}, timing={r["timing_validity"]}, review={r["review"]})')
