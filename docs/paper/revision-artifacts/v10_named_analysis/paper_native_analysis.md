# Single-host native timing analysis

- Bundle: `ctkat-v10-1aeadb97e040-b2e608e053f6`
- CT-KAT commit: `1aeadb97e0409227aa203ba825a6bfc1d90445bc`
- Input aggregate SHA-256: `0e18d2f103ed550151fa394641d533482a8ecb8f13bcbea2d9b45482ca18e7f3`
- Axes: 28
- Combined risk: 3
- Needs review: 0
- Inconclusive: 0
- No finding observed: 25
- Heterogeneity warnings: 0

Each valid result is scoped to this physical host; it is not evidence of cross-host reproducibility.
Secondary contrasts and output-length analyses never declassify a primary finding.

## Primary axes

| Component | Target | Harness/axis | Combined | Host results | I² |
|---|---|---|---|---|---:|
| committed-corpus-refresh | pqclean_falcon512_reference | sign/sk | no-finding-observed | host-a=PASS (|t|=0.993) | unavailable |
| committed-corpus-refresh | pqclean_mldsa44 | sign/sk | no-finding-observed | host-a=PASS (|t|=2.011) | unavailable |
| committed-corpus-refresh | pqclean_mldsa65 | sign/sk | no-finding-observed | host-a=PASS (|t|=1.816) | unavailable |
| committed-corpus-refresh | pqclean_mldsa87 | sign/sk | no-finding-observed | host-a=PASS (|t|=2.346) | unavailable |
| committed-corpus-refresh | pqclean_mlkem768 | kem_dec/valid_tuple | risk-detected | host-a=FAIL (|t|=256.9) | unavailable |
| committed-corpus-refresh | pqclean_mlkem768 | kem_dec_ct/ct | no-finding-observed | host-a=PASS (|t|=1.643) | unavailable |
| committed-corpus-refresh | pqclean_mlkem768 | kem_dec_fo/fo | no-finding-observed | host-a=PASS (|t|=2.222) | unavailable |
| committed-corpus-refresh | pqclean_sphincs_sha2_128f_simple | sign/sk | no-finding-observed | host-a=PASS (|t|=1.764) | unavailable |
| diverse-lineages | mldsa_native_65_portable | sign/sk | no-finding-observed | host-a=PASS (|t|=1.991) | unavailable |
| diverse-lineages | mldsa_native_65_x86_64 | sign/sk | no-finding-observed | host-a=PASS (|t|=2.203) | unavailable |
| diverse-lineages | mlkem_native_768_portable | kem_dec_valid_tuple/valid_tuple | risk-detected | host-a=FAIL (|t|=351.5) | unavailable |
| diverse-lineages | mlkem_native_768_x86_64 | kem_dec_valid_tuple/valid_tuple | risk-detected | host-a=FAIL (|t|=101) | unavailable |
| falcon-contrast | c_fndsa1024_fpr_emu | sign/sk | no-finding-observed | host-a=PASS (|t|=1.681) | unavailable |
| falcon-contrast | c_fndsa1024_native_fp | sign/sk | no-finding-observed | host-a=PASS (|t|=1.481) | unavailable |
| falcon-contrast | c_fndsa512_fpr_emu | sign/sk | no-finding-observed | host-a=PASS (|t|=2.865) | unavailable |
| falcon-contrast | c_fndsa512_native_fp | sign/sk | no-finding-observed | host-a=PASS (|t|=1.642) | unavailable |
| falcon-contrast | pqclean_falcon1024_reference | sign/sk | no-finding-observed | host-a=PASS (|t|=1.812) | unavailable |
| falcon-contrast | pqclean_falcon512_reference | sign/sk | no-finding-observed | host-a=PASS (|t|=2.153) | unavailable |
| kyberslash-contrast | kyberslash_operand_ks1_patched | operand_bin/operand_bin | no-finding-observed | host-a=PASS (|t|=1.686) | unavailable |
| kyberslash-contrast | kyberslash_operand_ks1_vulnerable | operand_bin/operand_bin | no-finding-observed | host-a=PASS (|t|=2.133) | unavailable |
| kyberslash-contrast | kyberslash_operand_ks2_poly_patched | operand_bin/operand_bin | no-finding-observed | host-a=PASS (|t|=1.145) | unavailable |
| kyberslash-contrast | kyberslash_operand_ks2_poly_vulnerable | operand_bin/operand_bin | no-finding-observed | host-a=PASS (|t|=2.707) | unavailable |
| kyberslash-contrast | kyberslash_operand_ks2_polyvec_patched | operand_bin/operand_bin | no-finding-observed | host-a=PASS (|t|=1.421) | unavailable |
| kyberslash-contrast | kyberslash_operand_ks2_polyvec_vulnerable | operand_bin/operand_bin | no-finding-observed | host-a=PASS (|t|=1.932) | unavailable |
| kyberslash-contrast | pqclean_mlkem768 | kem_dec_chosen_ct/chosen_ct | no-finding-observed | host-a=PASS (|t|=2.449) | unavailable |
| kyberslash-contrast | pqclean_mlkem768_kyberslash | kem_dec_chosen_ct/chosen_ct | no-finding-observed | host-a=PASS (|t|=2.3) | unavailable |
| kyberslash-contrast | pqclean_mlkem768_kyberslash1 | kem_dec_chosen_ct/chosen_ct | no-finding-observed | host-a=PASS (|t|=1.891) | unavailable |
| kyberslash-contrast | pqclean_mlkem768_kyberslash2 | kem_dec_chosen_ct/chosen_ct | no-finding-observed | host-a=PASS (|t|=1.694) | unavailable |

## Secondary analyses

- Pairwise contrasts: 17 (Holm-adjusted within preregistered family).
- Signature host/axes: 13.
- Machine-readable values are in the adjacent JSON and CSV files.
