"""Emit Table 6 (structural-test coverage of the operation call) from coverage.csv."""
import csv
import sys

LABEL = {
    ('pqclean_mlkem512', 'kem_dec'): 'PQClean ML-KEM-512, decapsulation',
    ('pqclean_mlkem512', 'kem_dec_fo'): 'PQClean ML-KEM-512, internal comparison',
    ('pqclean_mlkem768', 'kem_dec'): 'PQClean ML-KEM-768, key-and-ciphertext comparison',
    ('pqclean_mlkem768', 'kem_dec_ct'): 'PQClean ML-KEM-768, ciphertext-only comparison',
    ('pqclean_mlkem768', 'kem_dec_fo'): 'PQClean ML-KEM-768, internal comparison',
    ('pqclean_mlkem1024', 'kem_dec'): 'PQClean ML-KEM-1024, decapsulation',
    ('pqclean_mlkem1024', 'kem_dec_fo'): 'PQClean ML-KEM-1024, internal comparison',
    ('toy_lookup', 'leaky'): 'Input-dependent-work control',
    ('toy_lookup', 'safe'): 'Input-independent-work control',
    ('ct_matrix_flip', 'leaky'): 'Build-sensitive control',
    ('ct_matrix_flip', 'safe'): 'Build-independent control',
    ('pqclean_mlkem768_kyberslash1', 'kem_dec'): 'PQClean ML-KEM-768, KyberSlash KS1',
    ('pqclean_mlkem768_kyberslash2', 'kem_dec'): 'PQClean ML-KEM-768, KyberSlash KS2',
    ('pqclean_mlkem768_kyberslash', 'kem_dec'): 'PQClean ML-KEM-768, KyberSlash KS1/KS2',
    ('pqcrystals_kyber768_ref_a621b8d', 'kem_dec'): 'Kyber reference, decapsulation',
    ('pqclean_falcon512_reference', 'sign'): 'PQClean Falcon-512, signing',
    ('pqclean_falcon1024_reference', 'sign'): 'PQClean Falcon-1024, signing',
    ('c_fndsa512_prospective', 'sign_native_fp'): 'c-fn-dsa-512, native-arithmetic signing',
    ('c_fndsa512_prospective', 'sign_fpr_emu'): 'c-fn-dsa-512, integer-emulated signing',
    ('c_fndsa1024_prospective', 'sign_native_fp'): 'c-fn-dsa-1024, native-arithmetic signing',
    ('c_fndsa1024_prospective', 'sign_fpr_emu'): 'c-fn-dsa-1024, integer-emulated signing',
    ('pqclean_mldsa44', 'sign'): 'PQClean ML-DSA-44, signing',
    ('pqclean_mldsa65', 'sign'): 'PQClean ML-DSA-65, signing',
    ('pqclean_mldsa87', 'sign'): 'PQClean ML-DSA-87, signing',
    ('pqclean_sphincs_sha2_128f_simple', 'sign'): 'PQClean SLH-DSA-SHA2-128f, signing',
}
rows = list(csv.DictReader(open(sys.argv[1])))
out = [r'\begin{table}[h]', r'\centering',
       r'\caption{Coverage of the structural-test operation call. Each structural harness was rebuilt with GCC '
       r'coverage instrumentation (\texttt{-O0}); counters were reset immediately before the call to the target '
       r'operation and recorded immediately after it, so input preparation is excluded. Lines and branches are counted '
       r'within the functions of the target sources that the operation executes.}',
       r'\label{tab:structural-coverage}', r'\scriptsize', r'\setlength{\tabcolsep}{3pt}',
       r'\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.04\linewidth}>{\raggedright\arraybackslash}p{0.46\linewidth}rrr@{}}',
       r'\toprule',
       r'\textbf{No.} & \textbf{Target and Test} & \textbf{Functions} & \textbf{Lines (\%)} & \textbf{Branches (\%)} \\',
       r'\midrule']
for i, r in enumerate(rows, 1):
    label = LABEL[(r['target'], r['harness'])]
    if r['status'] == 'structural-not-run':
        out.append(f'{i} & {label} & \\multicolumn{{3}}{{c}}{{structural test not run}} \\\\')
        continue
    lt, le = int(r['lines_in_executed_functions']), int(r['lines_executed'])
    bt, bk = int(r['branches_in_executed_functions']), int(r['branches_taken'])
    out.append(f"{i} & {label} & {r['functions_executed']} & {100 * le / lt:.1f} & {100 * bk / bt:.1f} \\\\")
out += [r'\bottomrule', r'\end{tabular}', r'\end{table}']
print('\n'.join(out))
