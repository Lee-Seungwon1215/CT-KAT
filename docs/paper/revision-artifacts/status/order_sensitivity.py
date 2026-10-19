"""Re-fold the corpus statuses under alternative orders of the decision rules.

Usage: python3 order_sensitivity.py REPO CORPUS_CSV   (CORPUS_CSV, e.g. corpus_summary_v10.csv)
"""
import csv
import sys

repo, corpus_csv = sys.argv[1], sys.argv[2]
sys.path.insert(0, repo)
from ctkat.evidence import (  # noqa: E402
    _REVIEWED_LEGACY_ACCEPTANCE, AsmAttribution as A, AsmEvidence as M, Correctness as C,
    ReviewStatus as R, Structural as S, TimingSignal as TS, TimingValidity as TV, fold_overall,
)

FIELDS = ['correctness', 'structural', 'asm', 'asm_attribution', 'timing_validity',
          'timing_signal', 'review', 'legacy_verdict_class']


def rules(e):
    """The fold_overall gates as an ordered rule list: (name, fires?, result)."""
    c, s, m, a = C(e['correctness']), S(e['structural']), M(e['asm']), A(e['asm_attribution'])
    tv, ts, rv, lg = TV(e['timing_validity']), TS(e['timing_signal']), R(e['review']), e['legacy_verdict_class']
    risk = ((tv == TV.VALID and ts == TS.SIGNAL) or lg == 'build-sensitive-ct'
            or (rv == R.REVIEWED and (lg in {'ct-leak', 'varlat-secret-risk'} or a in {A.SECRET_RISK, A.MIXED})))
    error = C.ERROR in (c,) or s == S.ERROR or m == M.ERROR or tv == TV.ERROR
    partial = (s == S.INCOMPLETE or m == M.INCOMPLETE
               or tv in {TV.CONFOUNDED, TV.INSUFFICIENT_POWER, TV.ENVIRONMENT_REJECTED}
               or (tv == TV.VALID and ts == TS.NOT_INTERPRETABLE))
    manual = a in {A.PUBLIC, A.SECRET_RISK, A.MIXED, A.UNRESOLVED}
    accept = s == S.FINDING and lg in _REVIEWED_LEGACY_ACCEPTANCE
    review = (rv in {R.PENDING, R.DISPUTED, R.EXPIRED} or a == A.UNRESOLVED
              or (manual and rv != R.REVIEWED) or (accept and rv != R.REVIEWED)
              or (lg in {'accepted-variable-time', 'ct-leak', 'varlat-secret-risk'} and rv != R.REVIEWED)
              or lg in {'needs-analysis', 'ct-clean-untriaged'} or (s == S.FINDING and not accept))
    none_ran = s == S.NOT_RUN and m == M.NOT_RUN and tv == TV.NOT_RUN
    return {
        'func_fail': (c == C.FAIL, 'inconclusive'),
        'risk': (risk, 'risk-detected'),
        'tool_error': (error, 'tool-error'),
        'corr_not_run': (c == C.NOT_RUN, 'inconclusive'),
        'partial': (partial, 'inconclusive'),
        'warning': (tv == TV.VALID and ts == TS.WARNING, 'needs-review'),
        'review': (review, 'needs-review'),
        'none_ran': (none_ran, 'inconclusive'),
    }


def fold(e, order):
    r = rules(e)
    for name in order:
        fires, result = r[name]
        if fires:
            return result
    return 'no-finding-observed'


CURRENT = ['func_fail', 'risk', 'tool_error', 'corr_not_run', 'partial', 'warning', 'review', 'none_ran']
ALTERNATIVES = {
    'A. Tool Error before Risk': ['func_fail', 'tool_error', 'risk', 'corr_not_run', 'partial', 'warning', 'review', 'none_ran'],
    'B. Inconclusive (correctness not-run, partial/invalid) before Risk': ['func_fail', 'tool_error', 'corr_not_run', 'partial', 'risk', 'warning', 'review', 'none_ran'],
    'C. Review gates before Risk': ['func_fail', 'tool_error', 'corr_not_run', 'partial', 'warning', 'review', 'risk', 'none_ran'],
    'D. Risk before functional failure': ['risk', 'func_fail', 'tool_error', 'corr_not_run', 'partial', 'warning', 'review', 'none_ran'],
}

rows = list(csv.DictReader(open(corpus_csv, encoding='utf-8')))
for i, e in enumerate(rows, 1):
    ref = fold_overall(**{k: e[k] for k in FIELDS}).value
    assert ref == e['overall'] == fold(e, CURRENT), (i, ref, e['overall'], fold(e, CURRENT))
print(f'current order reproduces stored overall for all {len(rows)} pairs')

for label, order in ALTERNATIVES.items():
    changed = [(i, e['target'], e['harness'], e['overall'], fold(e, order))
               for i, e in enumerate(rows, 1) if fold(e, order) != e['overall']]
    print(f'\n{label}: {len(changed)} changed')
    for i, t, h, old, new in changed:
        print(f'  #{i:<2} {t}/{h}: {old} -> {new}')
