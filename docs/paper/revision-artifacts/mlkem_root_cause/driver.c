/* R2-3 root-cause experiment: Keccak permutations and cycles per ML-KEM-768 decapsulation
 * when the secret part, the embedded public key, or the ciphertext varies independently.
 * Exploratory only: not part of the frozen V10 protocol. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <x86intrin.h>

#if defined(IMPL_PQCLEAN)
#include "api.h"
#define PK_BYTES PQCLEAN_MLKEM768_CLEAN_CRYPTO_PUBLICKEYBYTES
#define SK_BYTES PQCLEAN_MLKEM768_CLEAN_CRYPTO_SECRETKEYBYTES
#define CT_BYTES PQCLEAN_MLKEM768_CLEAN_CRYPTO_CIPHERTEXTBYTES
#define SS_BYTES PQCLEAN_MLKEM768_CLEAN_CRYPTO_BYTES
int PQCLEAN_MLKEM768_CLEAN_crypto_kem_keypair_derand(uint8_t *pk, uint8_t *sk, const uint8_t *coins);
int PQCLEAN_MLKEM768_CLEAN_crypto_kem_enc_derand(uint8_t *ct, uint8_t *ss, const uint8_t *pk, const uint8_t *coins);
#define KEYPAIR PQCLEAN_MLKEM768_CLEAN_crypto_kem_keypair_derand
#define ENC PQCLEAN_MLKEM768_CLEAN_crypto_kem_enc_derand
#define DEC PQCLEAN_MLKEM768_CLEAN_crypto_kem_dec
#define RANDOMBYTES PQCLEAN_randombytes
#else
#include "mlkem_native.h"
#define PK_BYTES CRYPTO_PUBLICKEYBYTES
#define SK_BYTES CRYPTO_SECRETKEYBYTES
#define CT_BYTES CRYPTO_CIPHERTEXTBYTES
#define SS_BYTES CRYPTO_BYTES
#define KEYPAIR crypto_kem_keypair_derand
#define ENC crypto_kem_enc_derand
#define DEC crypto_kem_dec
#define RANDOMBYTES randombytes
#endif

#define S_BYTES 1152 /* k * 384 for ML-KEM-768 */
#define H_OFF (S_BYTES + PK_BYTES)
#define Z_OFF (H_OFF + 32)

unsigned long long ctkat_perm_x1, ctkat_perm_x4;

static uint64_t rng_state = 0x5EED2026ULL;
static uint64_t next64(void)
{
  uint64_t z = (rng_state += 0x9E3779B97F4A7C15ULL);
  z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
  z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
  return z ^ (z >> 31);
}
static void fill(uint8_t *b, size_t n)
{
  for (size_t i = 0; i < n; i++) b[i] = (uint8_t)(next64() >> 56);
}
int RANDOMBYTES(uint8_t *out, size_t n) { fill(out, n); return 0; }

typedef struct { uint8_t pk[PK_BYTES], sk[SK_BYTES], ct[CT_BYTES]; } tuple_t;

static void make_tuple(tuple_t *t)
{
  uint8_t kc[64], ec[32], ss[SS_BYTES];
  fill(kc, sizeof kc);
  fill(ec, sizeof ec);
  if (KEYPAIR(t->pk, t->sk, kc) != 0 || ENC(t->ct, ss, t->pk, ec) != 0) { fprintf(stderr, "setup failed\n"); exit(1); }
}

static int reps = 15;
static void measure(const char *exp, int i, const uint8_t *ct, const uint8_t *sk)
{
  uint8_t ss[SS_BYTES];
  uint64_t best = ~0ULL;
  unsigned long long p1 = 0, p4 = 0;
  int rc = 0;
  for (int r = 0; r < reps; r++) {
    unsigned aux;
    ctkat_perm_x1 = ctkat_perm_x4 = 0;
    _mm_lfence();
    uint64_t t0 = __rdtsc();
    rc = DEC(ss, ct, sk);
    uint64_t t1 = __rdtscp(&aux);
    _mm_lfence();
    if (t1 - t0 < best) best = t1 - t0;
    p1 = ctkat_perm_x1;
    p4 = ctkat_perm_x4;
  }
  printf("%s,%d,%llu,%llu,%llu,%d\n", exp, i, p1, p4, (unsigned long long)best, rc);
}

int main(int argc, char **argv)
{
  int m = argc > 1 ? atoi(argv[1]) : 300;
  static tuple_t base, pool[2000], ctpool[2000];
  uint8_t sk[SK_BYTES];
  if (m > 2000) m = 2000;
  make_tuple(&base);
  for (int i = 0; i < m; i++) make_tuple(&pool[i]);
  for (int i = 0; i < m; i++) { /* fresh ciphertexts to the base public key */
    uint8_t ec[32], ss[SS_BYTES];
    fill(ec, sizeof ec);
    ENC(ctpool[i].ct, ss, base.pk, ec);
  }
  printf("exp,i,perm_x1,perm_x4,cycles,rc\n");
  for (int i = 0; i < m; i++) measure("E0_fixed_tuple", i, base.ct, base.sk);
  for (int i = 0; i < m; i++) measure("E1_fresh_tuples", i, pool[i].ct, pool[i].sk);
  for (int i = 0; i < m; i++) { /* secret-only: s and z vary, pk and H(pk) fixed */
    memcpy(sk, base.sk, SK_BYTES);
    memcpy(sk, pool[i].sk, S_BYTES);
    memcpy(sk + Z_OFF, pool[i].sk + Z_OFF, 32);
    measure("E2_secret_only", i, base.ct, sk);
  }
  for (int i = 0; i < m; i++) { /* embedded-public-only: pk and H(pk) vary, s and z fixed */
    memcpy(sk, base.sk, SK_BYTES);
    memcpy(sk + S_BYTES, pool[i].sk + S_BYTES, PK_BYTES + 32);
    measure("E3_public_key_only", i, base.ct, sk);
  }
  for (int i = 0; i < m; i++) measure("E4_ciphertext_only", i, ctpool[i].ct, base.sk);
  return 0;
}
