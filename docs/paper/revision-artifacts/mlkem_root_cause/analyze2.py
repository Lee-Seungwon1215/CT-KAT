"""Summarize interleaved fixed-versus-variant timing (class 1 minus class 0)."""
import csv
import math
import statistics as st

V10 = {'pqclean': 8725, 'mlkn_portable': 11361, 'mlkn_x86_64': 378}
MODES = ['fresh', 'secret', 'public', 'ciphertext', 'second_fixed']

print(f"{'impl':14} {'mode':13} {'mean d':>8} {'median d':>9} {'t':>7} {'perm d':>7}   (V10 fresh delta)")
for impl in ['pqclean', 'mlkn_portable', 'mlkn_x86_64']:
    for mode in MODES:
        rows = list(csv.DictReader(open(f'i_{impl}_{mode}.csv')))
        cyc = [int(r['cycles']) for r in rows]
        cut = sorted(cyc)[int(0.95 * len(cyc))]  # crop the slowest 5% as dudect-style outlier control
        c = {0: [], 1: []}
        p = {0: [], 1: []}
        for r in rows:
            cl = int(r['class'])
            unit = int(r['perm_x4']) if impl == 'mlkn_x86_64' else int(r['perm_x1'])
            p[cl].append(unit)
            if int(r['cycles']) <= cut:
                c[cl].append(int(r['cycles']))
        d = st.mean(c[1]) - st.mean(c[0])
        se = math.sqrt(st.variance(c[0]) / len(c[0]) + st.variance(c[1]) / len(c[1]))
        md = st.median(c[1]) - st.median(c[0])
        pd = st.mean(p[1]) - st.mean(p[0])
        tag = f'   ({V10[impl]})' if mode == 'fresh' else ''
        print(f'{impl:14} {mode:13} {d:8.0f} {md:9.0f} {d / se:7.1f} {pd:7.2f}{tag}')
