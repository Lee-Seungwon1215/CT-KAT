# Root-cause experiment for the mixed-input ML-KEM signals (Table A16; exploratory, outside the frozen V10 campaign)

Purpose: test whether the mixed-input ML-KEM timing signals of Table 10 come from the secret key, the ciphertext, or the public key embedded in the secret-key object.

Host: same Intel Core i7-10875H host as V10, run on 2026-10-16 with SMT/turbo restored (not a protocol run), pinned with `taskset -c 3`.

## Sources

- PQClean ML-KEM-768 clean: copy of `examples/pqc_mlkem768/{clean,common}`.
- mlkem-native v1.3.0: copy of `examples/mlkem_native/upstream/mlkem`.
- The only source change in the copies is one counter increment at the start of the Keccak-f[1600] permutation functions:
  - PQClean `common/fips202.c`: `KeccakF1600_StatePermute` → `ctkat_perm_x1++`
  - mlkem-native `src/fips202/keccakf1600.c`: `mlk_keccakf1600x4_permute` → `ctkat_perm_x4++`, `mlk_keccakf1600_permute` → `ctkat_perm_x1++`

## Build (same flags as the V10 timing configs)

```bash
P=pqclean
gcc -O2 -g -fno-omit-frame-pointer -fno-lto -DIMPL_PQCLEAN -I$P/clean -I$P/common driver2.c \
    $P/clean/{kem,indcpa,poly,polyvec,ntt,reduce,cbd,symmetric-shake,verify}.c $P/common/fips202.c -o i_pqclean
gcc -std=c99 -O2 -g -fno-omit-frame-pointer -fno-lto -DMLK_CONFIG_PARAMETER_SET=768 -Imlkem \
    driver2.c mlkem/mlkem_native.c -o i_mlkn_portable
gcc -std=c99 -O2 -g -fno-omit-frame-pointer -fno-lto -DMLK_CONFIG_PARAMETER_SET=768 \
    -DMLK_CONFIG_USE_NATIVE_BACKEND_ARITH -DMLK_CONFIG_USE_NATIVE_BACKEND_FIPS202 \
    '-DMLK_CONFIG_ARITH_BACKEND_FILE="native/meta.h"' '-DMLK_CONFIG_FIPS202_BACKEND_FILE="fips202/native/auto.h"' \
    -DMLK_FORCE_X86_64 -mavx2 -mbmi2 -Imlkem driver2.c mlkem/mlkem_native.c mlkem/mlkem_native_asm.S -o i_mlkn_x86_64
```

`driver.c` builds the same way (replace `driver2.c`, binaries `r23_*`).

## Run

```bash
for b in pqclean mlkn_portable mlkn_x86_64; do
  for m in fresh secret public ciphertext second_fixed; do taskset -c 3 ./i_$b $m 20000 > i_${b}_$m.csv; done
  taskset -c 3 ./r23_$b 1000 > $b.csv
done
python3 analyze.py; python3 analyze2.py; python3 table_root_cause.py > table_root_cause.tex
```

Raw CSV outputs are in `raw_csv.tgz`.

## Result summary

- Permutation count per decapsulation is constant when only the secret part (s, z) or only the ciphertext varies, and varies only when the embedded public key varies (all three implementations).
- Interleaved fixed-versus-variant timing: varying only the embedded public key reproduces the whole-tuple difference; varying only the secret part or only the ciphertext gives |t| ≤ 1.6.
- Two fixed tuples differ exactly by their permutation-count difference times the cost of one permutation; fresh public keys add a further cost only in the scalar rejection-sampling implementations.
