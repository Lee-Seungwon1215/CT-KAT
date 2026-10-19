"""Build Table A15 (per-condition timing sensitivity) from native timing campaign output roots.

Usage: python3 -I build_sensitivity_table.py ROOT [ROOT ...] > table_sensitivity.tex
Each ROOT is a component output directory containing <target>/reports/dudect_backend_report.json.
"""
import json
import math
import sys
from pathlib import Path

COMPONENT_LABEL = {
    'committed-corpus': 'Core',
    'kyberslash': 'KyberSlash',
    'falcon': 'Falcon/FN-DSA',
    'diverse': 'mlkem/mldsa-native',
}
TARGET_LABEL = {
    'pqclean_falcon512_reference': 'PQClean Falcon-512',
    'pqclean_falcon1024_reference': 'PQClean Falcon-1024',
    'pqclean_mldsa44': 'PQClean ML-DSA-44',
    'pqclean_mldsa65': 'PQClean ML-DSA-65',
    'pqclean_mldsa87': 'PQClean ML-DSA-87',
    'pqclean_mlkem768': 'PQClean ML-KEM-768',
    'pqclean_sphincs_sha2_128f_simple': 'PQClean SLH-DSA-SHA2-128f',
    'kyberslash_operand_ks1_patched': 'KS1 site, patched',
    'kyberslash_operand_ks1_vulnerable': 'KS1 site, vulnerable',
    'kyberslash_operand_ks2_poly_patched': 'KS2 poly site, patched',
    'kyberslash_operand_ks2_poly_vulnerable': 'KS2 poly site, vulnerable',
    'kyberslash_operand_ks2_polyvec_patched': 'KS2 polyvec site, patched',
    'kyberslash_operand_ks2_polyvec_vulnerable': 'KS2 polyvec site, vulnerable',
    'pqclean_mlkem768_kyberslash': 'ML-KEM-768 with KS1 and KS2',
    'pqclean_mlkem768_kyberslash1': 'ML-KEM-768 with KS1',
    'pqclean_mlkem768_kyberslash2': 'ML-KEM-768 with KS2',
    'c_fndsa512_native_fp': 'c-fn-dsa-512, native arithmetic',
    'c_fndsa512_fpr_emu': 'c-fn-dsa-512, integer-emulated',
    'c_fndsa1024_native_fp': 'c-fn-dsa-1024, native arithmetic',
    'c_fndsa1024_fpr_emu': 'c-fn-dsa-1024, integer-emulated',
    'mldsa_native_65_portable': 'mldsa-native-65, portable',
    'mldsa_native_65_x86_64': 'mldsa-native-65, optimized',
    'mlkem_native_768_portable': 'mlkem-native-768, portable',
    'mlkem_native_768_x86_64': 'mlkem-native-768, optimized',
}
AXIS_LABEL = {
    'sk': 'secret key', 'valid_tuple': 'key and ciphertext (mixed)', 'ct': 'ciphertext only',
    'fo': 'internal', 'chosen_ct': 'chosen ciphertext', 'operand_bin': 'operand bin',
}


def component_of(root: Path) -> str:
    for key, label in COMPONENT_LABEL.items():
        if key in root.name:
            return label
    return root.name


def tex(s: str) -> str:
    return s.replace('_', r'\_')


def fmt(x, digits=1):
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return '--'
    if abs(x) >= 1e5:
        e = int(math.floor(math.log10(abs(x))))
        return f'${x / 10 ** e:.2f}\\times10^{{{e}}}$'
    return f'{x:,.{digits}f}'


rows = []
for root in map(Path, sys.argv[1:]):
    for report in sorted(root.glob('*/reports/dudect_backend_report.json')):
        target = report.parent.parent.name
        data = json.loads(report.read_text())
        for h in data.get('harnesses', []):
            hp = h.get('harness_protocol', {})
            ladder = sorted({c['effect_ticks'] for c in hp.get('positive_controls', []) if c.get('role') == 'positive'})
            mdd = [x for x in hp.get('positive_detection_effects_at_target_power', []) if x is not None]
            rows.append({
                'component': component_of(root),
                'target': target,
                'axis': hp.get('axis', h.get('harness')),
                'ladder': ladder,
                'abs_t': h.get('abs_t_score'),
                'aa': max((abs(c['abs_t_score']) for c in hp.get('aa_controls', [])), default=None),
                'placebo': max((abs(c['abs_t_score']) for c in hp.get('setup_placebo_controls', [])), default=None),
                'detect': h.get('detection_estimate'),
                'mdd': max(mdd) if mdd else None,
                'validity': h.get('timing_validity'),
                'n': hp.get('target_measurements'),
            })

print(r'\begin{table}[h]')
print(r'\centering')
print(r'\caption{Sensitivity of every timing condition. Delays are the injected positive-control ladder; '
      r'MDD, in cycles, is the largest over the three processes of $(10+z_{0.80})\cdot\mathrm{SE}$, the smallest class-mean '
      r'difference the $|t|>10$ rule detects with probability 0.80; $(5/\tau)^2$ is the dudect estimate of the '
      r'measurements needed to reach $|t|=5$ at the observed effect. The null-control columns give the largest $|t|$ '
      r'over the three processes for two comparisons that contain no true difference, one between two classes of '
      r'equivalent inputs (Inputs) and one that times only the preparation code (Setup). Both use the same maximum-of-102 procedure as the target.}')
print(r'\label{tab:sensitivity}')
print(r'\scriptsize')
print(r'\setlength{\tabcolsep}{2pt}')
print(r'\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.13\linewidth}'
      r'>{\raggedright\arraybackslash}p{0.25\linewidth}rrrrrr@{}}')
print(r'\toprule')
print(r' & & & & \multicolumn{2}{c}{\textbf{Null controls}} & & \\')
print(r'\cmidrule(lr){5-6}')
print(r'\textbf{Group} & \textbf{Target (input axis)} & \textbf{Delays (ticks)} & \textbf{$|t|$} & '
      r'\textbf{Inputs} & \textbf{Setup} & \textbf{$(5/\tau)^2$} & \textbf{MDD} \\')
previous = None
for r in rows:
    if r['component'] != previous:
        print(r'\midrule')
        previous = r['component']
    ladder = '/'.join(f'{x:,}' for x in r['ladder']) or '--'
    name = TARGET_LABEL.get(r['target'], tex(r['target']))
    axis = AXIS_LABEL.get(str(r['axis']), tex(str(r['axis'])))
    print(f"{r['component']} & {name} ({axis}) & {ladder} & "
          f"{fmt(r['abs_t'], 2)} & {fmt(r['aa'], 2)} & {fmt(r['placebo'], 2)} & "
          f"{fmt(r['detect'], 0)} & {fmt(r['mdd'], 0)} \\\\")
print(r'\bottomrule')
print(r'\end{tabular}')
print(r'\end{table}')
print(f'% max A/A={max(r["aa"] for r in rows):.2f} max placebo={max(r["placebo"] for r in rows):.2f}', file=sys.stderr)
print(f'% rows={len(rows)} target_measurements={sorted({r["n"] for r in rows})} '
      f'validity={sorted({str(r["validity"]) for r in rows})}', file=sys.stderr)
