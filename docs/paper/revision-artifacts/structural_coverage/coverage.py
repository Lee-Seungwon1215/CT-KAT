"""Line and branch coverage of the target code executed during the structural-test operation call.

For every corpus harness, the structural-test harness is rendered exactly as `ctkat ct` renders it, the
operation call (the first call after the secret-marking block) is bracketed with __gcov_reset()/__gcov_dump(),
and the harness is built with -O0 --coverage and run natively.  Valgrind client requests are no-ops natively,
so the executed source paths are those of the structural test's operation call.

Usage: python3 coverage.py REPO OUTDIR
"""
import csv
import gzip
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

repo, out = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo))
from ctkat.cli import _resolve, _template_context  # noqa: E402
from ctkat.config import load_config  # noqa: E402
from ctkat.ct_matrix import preprocessor_cflags  # noqa: E402
from ctkat.harness_generator import render_harness  # noqa: E402

TARGET_DIR = {
    'pqclean_mlkem512': 'pqc_mlkem512', 'pqclean_mlkem768': 'pqc_mlkem768', 'pqclean_mlkem1024': 'pqc_mlkem1024',
    'toy_lookup': 'toy_lookup', 'ct_matrix_flip': 'ct_matrix_flip',
    'pqclean_mlkem768_kyberslash1': 'pqc_mlkem768_kyberslash1', 'pqclean_mlkem768_kyberslash2': 'pqc_mlkem768_kyberslash2',
    'pqclean_mlkem768_kyberslash': 'pqc_mlkem768_kyberslash', 'pqcrystals_kyber768_ref_a621b8d': 'pqc_kyber768_historical',
    'pqclean_falcon512_reference': 'pqc_falcon512', 'pqclean_falcon1024_reference': 'pqc_falcon1024',
    'c_fndsa512_prospective': 'c_fndsa512_prospective', 'c_fndsa1024_prospective': 'c_fndsa1024_prospective',
    'pqclean_mldsa44': 'pqc_mldsa44', 'pqclean_mldsa65': 'pqc_mldsa65', 'pqclean_mldsa87': 'pqc_mldsa87',
    'pqclean_sphincs_sha2_128f_simple': 'pqc_sphincs_sha2_128f_simple',
}
EXCLUDE_SOURCE = re.compile(r'randombytes')  # test scaffolding, not target code


def bracket(code: str) -> str:
    lines = code.split('\n')
    marks = [i for i, l in enumerate(lines) if 'VALGRIND_MAKE_MEM_UNDEFINED' in l]
    if not marks:
        raise RuntimeError('no secret-marking line')
    for j in range(marks[-1] + 1, len(lines)):
        s = lines[j].strip()
        if s and not s.startswith(('//', '/*', '*', '#', '}', '{')) and '(' in s and s.endswith(';'):
            indent = lines[j][:len(lines[j]) - len(lines[j].lstrip())]
            lines[j] = f'{indent}__gcov_reset();\n{lines[j]}\n{indent}__gcov_dump(); _exit(0);'
            break
    else:
        raise RuntimeError('operation call not found')
    return '#include <unistd.h>\nextern void __gcov_reset(void);\nextern void __gcov_dump(void);\n' + '\n'.join(lines)


rows_out = []
corpus = list(csv.DictReader(open(repo / 'docs/corpus/corpus_summary.csv', encoding='utf-8')))
for row in corpus:
    if row['structural'] == 'not-run':
        rows_out.append({'target': row['target'], 'harness': row['harness'], 'status': 'structural-not-run'})
        continue
    cfg_dir = repo / 'examples' / TARGET_DIR[row['target']]
    cfg = load_config(cfg_dir / 'ctkat.yaml')
    h = next(x for x in cfg.ct.harnesses if x.name == row['harness'])
    work = _resolve(cfg_dir, cfg.ct.workdir)
    bdir = out / row['target'] / row['harness']
    shutil.rmtree(bdir, ignore_errors=True)
    (bdir / 'obj').mkdir(parents=True)
    harness_c = bdir / f'harness_{h.name}.c'
    harness_c.write_text(bracket(render_harness(h.template, _template_context(h, cfg.ct.seed))))
    base_cflags = h.cflags if h.cflags is not None else cfg.ct.cflags
    flags = ['-O0', '-g', '--coverage', '-fno-inline'] + preprocessor_cflags(base_cflags)
    incs = [f'-I{_resolve(cfg_dir, d)}' for d in h.include_dirs]
    sources = [_resolve(cfg_dir, s) for s in h.sources]
    objs = []
    for k, src in enumerate([harness_c] + sources):
        obj = bdir / 'obj' / f'{k:02d}_{src.stem}.o'
        subprocess.run(['gcc', *flags, *incs, '-c', str(src), '-o', str(obj)], cwd=work, check=True,
                       capture_output=True)
        objs.append((src, obj))
    binary = bdir / 'harness'
    subprocess.run(['gcc', '--coverage', *[str(o) for _, o in objs], '-o', str(binary), '-lm'], cwd=work,
                   check=True, capture_output=True)
    proc = subprocess.run([str(binary)], cwd=work, capture_output=True, timeout=600)
    fn_total = fn_exec = l_total = l_exec = b_total = b_taken = 0
    for src, obj in objs[1:]:
        if EXCLUDE_SOURCE.search(src.name):
            continue
        res = subprocess.run(['gcov', '-b', '--json-format', '--stdout', '-o', str(obj.parent), str(obj)],
                             cwd=bdir, capture_output=True, text=True)
        for line in res.stdout.splitlines():
            if not line.startswith('{'):
                continue
            for f in json.loads(line)['files']:
                if Path(f['file']).name != src.name:
                    continue
                executed = {fn['name'] for fn in f['functions'] if fn['execution_count'] > 0}
                fn_total += len(f['functions'])
                fn_exec += len(executed)
                for ln in f['lines']:
                    if ln.get('function_name') not in executed:
                        continue
                    l_total += 1
                    l_exec += ln['count'] > 0
                    b_total += len(ln['branches'])
                    b_taken += sum(1 for b in ln['branches'] if b['count'] > 0)
    rows_out.append({
        'target': row['target'], 'harness': row['harness'], 'status': f'rc={proc.returncode}',
        'functions_total': fn_total, 'functions_executed': fn_exec,
        'lines_in_executed_functions': l_total, 'lines_executed': l_exec,
        'branches_in_executed_functions': b_total, 'branches_taken': b_taken,
    })
    r = rows_out[-1]
    print(f"{row['target']:34} {row['harness']:15} {r['status']:6} fn {fn_exec}/{fn_total} "
          f"lines {l_exec}/{l_total} ({100 * l_exec / max(l_total, 1):.1f}%) "
          f"branches {b_taken}/{b_total} ({100 * b_taken / max(b_total, 1):.1f}%)", flush=True)

keys = ['target', 'harness', 'status', 'functions_total', 'functions_executed', 'lines_in_executed_functions',
        'lines_executed', 'branches_in_executed_functions', 'branches_taken']
with open(out / 'coverage.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=keys)
    w.writeheader()
    for r in rows_out:
        w.writerow({k: r.get(k, '') for k in keys})
