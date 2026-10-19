"""Emit Table A16 (root-cause experiment for the mixed-input ML-KEM signals) from the interleaved runs."""
import csv
import math
import statistics as st

IMPL = [('pqclean', 'PQClean ML-KEM-768'), ('mlkn_portable', 'mlkem-native-768, portable'),
        ('mlkn_x86_64', 'mlkem-native-768, optimized')]
MODES = [('fresh', 'Whole tuple (as in V10)'), ('secret', 'Secret part only ($s$, $z$)'),
         ('public', 'Embedded public key only'), ('ciphertext', 'Ciphertext only'),
         ('second_fixed', 'Another fixed tuple')]

def neg(x):
    if x.startswith('-') and x.strip('-0.,') == '':
        return x[1:]
    return '$-$' + x[1:] if x.startswith('-') else x


out = [r'\begin{table}[h]', r'\centering',
       r'\caption{Follow-up root-cause experiment for the mixed-input ML-KEM signals (exploratory, outside the frozen '
       r'campaign). Class 0 is a fixed valid tuple; class 1 cycles through 64 variants in which only the listed '
       r'component differs from class 0. Each row uses 20,000 interleaved decapsulations on the same host, with the '
       r'slowest 5\% removed. $\Delta$ is the class~1 minus class~0 mean in cycles, and $\Delta_{\mathrm{perm}}$ is the '
       r'mean difference in Keccak-f[1600] permutation calls per decapsulation (four-way calls for the optimized build).}',
       r'\label{tab:mlkem-rootcause}', r'\scriptsize', r'\setlength{\tabcolsep}{3pt}',
       r'\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.27\linewidth}>{\raggedright\arraybackslash}p{0.33\linewidth}rrr@{}}',
       r'\toprule',
       r'\textbf{Implementation} & \textbf{Varied component} & \textbf{$\Delta$ (cycles)} & \textbf{$t$} & '
       r'\textbf{$\Delta_{\mathrm{perm}}$} \\']
for impl, label in IMPL:
    out.append(r'\midrule')
    for mode, mlabel in MODES:
        rows = list(csv.DictReader(open(f'i_{impl}_{mode}.csv')))
        cut = sorted(int(r['cycles']) for r in rows)[int(0.95 * len(rows))]
        c, p = {0: [], 1: []}, {0: [], 1: []}
        for r in rows:
            cl = int(r['class'])
            p[cl].append(int(r['perm_x4']) if impl == 'mlkn_x86_64' else int(r['perm_x1']))
            if int(r['cycles']) <= cut:
                c[cl].append(int(r['cycles']))
        d = st.mean(c[1]) - st.mean(c[0])
        t = d / math.sqrt(st.variance(c[0]) / len(c[0]) + st.variance(c[1]) / len(c[1]))
        pd = st.mean(p[1]) - st.mean(p[0])
        pds = f'{pd:+.2f}'.replace('+0.00', '0.00').replace('-0.00', '0.00').lstrip('+')
        cells = [neg(f'{d:,.0f}'), neg(f'{t:.1f}'), neg(pds)]
        out.append(f'{label if mode == "fresh" else ""} & {mlabel} & ' + ' & '.join(cells) + r' \\')
out += [r'\bottomrule', r'\end{tabular}', r'\end{table}']
print('\n'.join(out))
