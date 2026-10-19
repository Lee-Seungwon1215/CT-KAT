"""Generate the per-pair status tables (Tables A13-A14) from the refreshed corpus summary.

Usage: python3 build_appendix.py corpus_summary_v10.csv OUT.tex
"""
import csv
import sys

corpus_csv, out_path = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(corpus_csv, encoding='utf-8')))
assert len(rows) == 25

LABELS = [
    ('PQClean ML-KEM-512, decapsulation', 'PQClean ML-KEM-512, 역캡슐화'),
    ('PQClean ML-KEM-512, internal comparison', 'PQClean ML-KEM-512, 내부 비교'),
    ('PQClean ML-KEM-768, key-and-ciphertext comparison', 'PQClean ML-KEM-768, 키·암호문 비교'),
    ('PQClean ML-KEM-768, ciphertext-only comparison', 'PQClean ML-KEM-768, 암호문 단독 비교'),
    ('PQClean ML-KEM-768, internal comparison', 'PQClean ML-KEM-768, 내부 비교'),
    ('PQClean ML-KEM-1024, decapsulation', 'PQClean ML-KEM-1024, 역캡슐화'),
    ('PQClean ML-KEM-1024, internal comparison', 'PQClean ML-KEM-1024, 내부 비교'),
    ('Input-dependent-work control', '입력 의존 작업량 대조군'),
    ('Input-independent-work control', '입력 독립 작업량 대조군'),
    ('Build-sensitive control', '빌드 민감 대조군'),
    ('Build-independent control', '빌드 독립 대조군'),
    ('PQClean ML-KEM-768, KyberSlash KS1', 'PQClean ML-KEM-768, KyberSlash KS1'),
    ('PQClean ML-KEM-768, KyberSlash KS2', 'PQClean ML-KEM-768, KyberSlash KS2'),
    ('PQClean ML-KEM-768, KyberSlash KS1/KS2', 'PQClean ML-KEM-768, KyberSlash KS1/KS2'),
    ('Kyber reference, decapsulation', 'Kyber 참조 구현, 역캡슐화'),
    ('PQClean Falcon-512, signing', 'PQClean Falcon-512, 서명'),
    ('PQClean Falcon-1024, signing', 'PQClean Falcon-1024, 서명'),
    ('c-fn-dsa-512, native-arithmetic signing', 'c-fn-dsa-512, 네이티브 산술 서명'),
    ('c-fn-dsa-512, integer-emulated signing', 'c-fn-dsa-512, 정수 에뮬레이션 서명'),
    ('c-fn-dsa-1024, native-arithmetic signing', 'c-fn-dsa-1024, 네이티브 산술 서명'),
    ('c-fn-dsa-1024, integer-emulated signing', 'c-fn-dsa-1024, 정수 에뮬레이션 서명'),
    ('PQClean ML-DSA-44, signing', 'PQClean ML-DSA-44, 서명'),
    ('PQClean ML-DSA-65, signing', 'PQClean ML-DSA-65, 서명'),
    ('PQClean ML-DSA-87, signing', 'PQClean ML-DSA-87, 서명'),
    ('PQClean SLH-DSA-SHA2-128f, signing', 'PQClean SLH-DSA-SHA2-128f, 서명'),
]
EXPECTED_TARGETS = ['pqclean_mlkem512'] * 2 + ['pqclean_mlkem768'] * 3 + ['pqclean_mlkem1024'] * 2
for i, t in enumerate(EXPECTED_TARGETS):
    assert rows[i]['target'] == t, (i, rows[i]['target'])

STATUS = {
    'risk-detected': ('Risk Identified', '위험 확인'),
    'needs-review': ('Further Review Required', '추가 검토 필요'),
    'inconclusive': ('Inconclusive', '판단 불가'),
    'no-finding-observed': ('No Issue Observed under Tested Conditions', '테스트 조건에서 문제 미관찰'),
    'tool-error': ('Tool Error', '도구 오류'),
}
MIXED_INPUT = {('pqclean_mlkem768', 'kem_dec')}  # V10 valid_tuple axis: key, ciphertext, and embedded public data change together


def f_code(r):
    return {'pass': 'P', 'fail': 'Fail', 'error': 'E'}.get(r['correctness'], '--')


def s_code(r):
    return {'finding': 'F', 'no-finding': 'N', 'incomplete': 'I', 'error': 'E'}.get(r['structural'], '--')


def i_code(r):
    if r['asm'] == 'candidate':
        return {'public': 'Pub', 'secret-risk': 'Sec', 'mixed': 'Mix', 'unresolved': 'Unr'}.get(r['asm_attribution'], 'Cand')
    return {'no-candidate': 'N', 'incomplete': 'I', 'error': 'E'}.get(r['asm'], '--')


def t_code(r, tex=True):
    v, s = r['timing_validity'], r['timing_signal']
    if v == 'not-run':
        return '--'
    if v != 'valid':
        return {'insufficient-power': 'Ins', 'confounded': 'Conf', 'environment-rejected': 'Env', 'error': 'E'}[v]
    code = {'signal': 'S', 'no-signal-observed': 'N', 'warning': 'W'}[s]
    if (r['target'], r['harness']) in MIXED_INPUT:
        code += r'\textsuperscript{m}' if tex else '(m)'
    return code


def r_code(r):
    return {'reviewed': 'Rev', 'pending': 'Pend', 'expired': 'Exp', 'disputed': 'Disp'}.get(r['review'], '--')


LEGEND = (r'F: functional validation (P, pass); S: structural test (F, finding; N, no finding); '
          r'I: suspicious-instruction scan and operand attribution (N, no candidate; Pub, public; Sec, secret; '
          r'Mix, mixed; Unr, unresolved); T: V10 timing (S, signal; N, no signal; '
          r'\textsuperscript{m}, mixed-input contrast); R: review (Rev, reviewed; Pend, pending; Exp, expired); '
          r'--, not run or not needed.')
LEGEND_KO = ('F: 기능 검증(P 통과), S: 구조 테스트(F 발견, N 없음), I: 의심 명령어 스캔과 피연산자 출처(N 후보 없음, '
             'Pub 공개, Sec 비밀, Mix 혼합, Unr 미상), T: V10 타이밍(S 신호, N 신호 없음, (m) 혼합 입력 비교), '
             'R: 검토(Rev 완료, Pend 대기, Exp 만료), --: 미실행 또는 불필요')

GROUPS_A = [range(0, 7), range(7, 11), range(11, 15)]
GROUPS_B = [range(15, 21), range(21, 25)]


def table(part, groups, label):
    out = []
    first, last = groups[0][0] + 1, groups[-1][-1] + 1
    out.append(f'% [번역] 표 A1{1 if part == 1 else 2}: 25개 대상–연산 쌍의 최종 상태와 층별 결과 ({part})')
    out.append(f'% [번역]   {LEGEND_KO}')
    out.append('% [번역]   번호 | 대상 및 테스트 | F | S | I | T | R | 최종 상태')
    for g in groups:
        for i in g:
            r = rows[i]
            out.append(f'% [번역]   {i + 1:>2} | {LABELS[i][1]} | {f_code(r)} | {s_code(r)} | {i_code(r)} | '
                       f'{t_code(r, tex=False)} | {r_code(r)} | {STATUS[r["overall"]][1]}')
    out += [
        r'\begin{table}[h]',
        r'\centering',
        rf'\caption{{Final statuses of the 25 target--operation pairs ({part}), with the outcome of each evidence layer. '
        + (LEGEND if part == 1 else r'Layer abbreviations as in Table~\ref{tab:target-results-a}.') + '}',
        rf'\label{{{label}}}',
        r'\scriptsize',
        r'\renewcommand{\arraystretch}{1.3}',
        r'\setlength{\tabcolsep}{2.5pt}',
        r'\begin{tabular}{@{}',
        r'    >{\raggedright\arraybackslash}p{0.04\linewidth}',
        r'    >{\raggedright\arraybackslash}p{0.36\linewidth}',
        r'    ccccc',
        r'    >{\raggedleft\arraybackslash}p{0.25\linewidth}',
        r'@{}}',
        r'\toprule',
        r'\textbf{No.} & \textbf{Target and Test} & \textbf{F} & \textbf{S} & \textbf{I} & \textbf{T} & \textbf{R} & \textbf{Final Status} \\',
    ]
    for g in groups:
        out.append(r'\midrule')
        for i in g:
            r = rows[i]
            out.append(f'{i + 1:<2} & {LABELS[i][0]} & {f_code(r)} & {s_code(r)} & {i_code(r)} & {t_code(r)} & '
                       f'{r_code(r)} & {STATUS[r["overall"]][0]} \\\\')
    out += [r'\bottomrule', r'\end{tabular}', r'\end{table}']
    return out


lines = [
    r'\section{Final Status of Each Evaluation Target}',
    r'%\section{각 평가 대상의 최종 상태}',
    r'\label{app:target-results}',
    '',
    '% [번역] 표 A11과 A12는 본문에서 상태별로 요약한 25개 대상–연산 쌍을 나열하며, 각 최종 상태 옆에 그 상태를 만든 '
    '층별 결과를 함께 보인다. 동일한 구현이라도 테스트한 연산이나 두 입력 클래스의 구성 방식이 다르면 별개의 쌍으로 구분된다. '
    '타이밍 열은 V10 단일 호스트 측정의 committed-corpus 구성 요소에서 가져왔으며, 이 구성 요소에 타이밍 축이 없는 쌍은 미실행으로 표시한다.',
    r'Tables~\ref{tab:target-results-a} and~\ref{tab:target-results-b} list the 25 target--operation pairs that are '
    r'summarized by status in the main text, together with the outcome of each evidence layer that produced the final status. '
    r'Pairs remain distinct when either the tested operation or the construction of the two input classes differs, even for '
    r'the same implementation. The timing column is taken from the committed-corpus component of the single-host V10 '
    r'campaign; pairs without a timing axis in that component are marked as not run.',
    '',
]
lines += table(1, GROUPS_A, 'tab:target-results-a')
lines.append('')
lines += table(2, GROUPS_B, 'tab:target-results-b')
open(out_path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('written', out_path)
