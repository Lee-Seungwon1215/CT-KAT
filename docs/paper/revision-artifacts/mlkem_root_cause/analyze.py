"""Summarize the root-cause experiment for the mixed-input ML-KEM signals."""
import csv
import statistics as st
import sys

V10_DELTA = {'pqclean': 8725.47, 'mlkn_portable': 11360.87, 'mlkn_x86_64': 377.65}


def perm_units(impl, r):
    # one "unit" = one permutation call issued by the implementation's batching level
    return int(r['perm_x4']) if impl == 'mlkn_x86_64' else int(r['perm_x1'])


for impl in ['pqclean', 'mlkn_portable', 'mlkn_x86_64']:
    rows = list(csv.DictReader(open(f'{impl}.csv')))
    print(f'\n=== {impl}')
    by = {}
    for r in rows:
        by.setdefault(r['exp'], []).append(r)
    for exp, rs in by.items():
        p = [perm_units(impl, r) for r in rs]
        c = [int(r['cycles']) for r in rs]
        print(f'  {exp:20} perms: min={min(p)} max={max(p)} distinct={len(set(p)):2} '
              f'| cycles: median={st.median(c):9.0f} mean={st.mean(c):9.0f} sd={st.pstdev(c):7.0f}')
    # regression of cycles on permutation count over fresh tuples and public-key-only variation
    for exp in ['E1_fresh_tuples', 'E3_public_key_only']:
        rs = by[exp]
        x = [perm_units(impl, r) for r in rs]
        y = [int(r['cycles']) for r in rs]
        mx, my = st.mean(x), st.mean(y)
        sxx = sum((a - mx) ** 2 for a in x)
        slope = sum((a - mx) * (b - my) for a, b in zip(x, y)) / sxx if sxx else float('nan')
        r = st.correlation(x, y) if sxx else float('nan')
        resid = [b - (my + slope * (a - mx)) for a, b in zip(x, y)]
        print(f'  {exp}: cycles per permutation unit = {slope:7.1f}, r = {r:.3f}, '
              f'residual sd = {st.pstdev(resid):6.0f} (raw sd {st.pstdev(y):6.0f})')
    e1 = [perm_units(impl, r) for r in by['E1_fresh_tuples']]
    rs = by['E1_fresh_tuples']
    x = e1; y = [int(r['cycles']) for r in rs]
    mx = st.mean(x); slope = sum((a - mx) * (b - st.mean(y)) for a, b in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    implied = V10_DELTA[impl] / slope
    sd = st.pstdev(e1)
    share = sum(1 for v in e1 if abs(v - mx) >= abs(implied)) / len(e1)
    print(f'  V10 mean delta {V10_DELTA[impl]:.0f} cycles ~ {implied:.1f} permutation units; '
          f'fresh-tuple sd = {sd:.2f} units; share of keys at least that far from the mean = {share:.1%}')
