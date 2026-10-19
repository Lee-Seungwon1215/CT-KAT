/* R2-3 follow-up: interleaved fixed-versus-variant decapsulation timing, as in the V10 valid_tuple axis.
 * Class 0 is always the base tuple; class 1 cycles through a pool of variants built according to MODE.
 * The selected inputs are copied into shared work buffers before each timed call. Exploratory only. */
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

#define S_BYTES 1152
#define Z_OFF (S_BYTES + PK_BYTES + 32)
#define POOL 64

unsigned long long ctkat_perm_x1, ctkat_perm_x4;
static uint64_t rng_state = 0x5EED2026ULL;
static uint64_t next64(void)
{
  uint64_t z = (rng_state += 0x9E3779B97F4A7C15ULL);
  z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
  z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
  return z ^ (z >> 31);
}
static void fill(uint8_t *b, size_t n) { for (size_t i = 0; i < n; i++) b[i] = (uint8_t)(next64() >> 56); }
int RANDOMBYTES(uint8_t *out, size_t n) { fill(out, n); return 0; }

typedef struct { uint8_t pk[PK_BYTES], sk[SK_BYTES], ct[CT_BYTES]; } tuple_t;
static void make_tuple(tuple_t *t)
{
  uint8_t kc[64], ec[32], ss[SS_BYTES];
  fill(kc, sizeof kc); fill(ec, sizeof ec);
  if (KEYPAIR(t->pk, t->sk, kc) != 0 || ENC(t->ct, ss, t->pk, ec) != 0) exit(1);
}

int main(int argc, char **argv)
{
  const char *mode = argc > 1 ? argv[1] : "fresh";
  int n = argc > 2 ? atoi(argv[2]) : 20000;
  static tuple_t base, other[POOL];
  static uint8_t var_sk[POOL][SK_BYTES], var_ct[POOL][CT_BYTES];
  static uint8_t work_sk[SK_BYTES], work_ct[CT_BYTES];
  uint8_t ss[SS_BYTES];
  make_tuple(&base);
  for (int i = 0; i < POOL; i++) make_tuple(&other[i]);
  for (int i = 0; i < POOL; i++) {
    memcpy(var_sk[i], base.sk, SK_BYTES);
    memcpy(var_ct[i], base.ct, CT_BYTES);
    if (!strcmp(mode, "fresh")) {                 /* whole tuple varies: V10 valid_tuple analogue */
      memcpy(var_sk[i], other[i].sk, SK_BYTES); memcpy(var_ct[i], other[i].ct, CT_BYTES);
    } else if (!strcmp(mode, "secret")) {         /* s and z vary; pk, H(pk), ct fixed */
      memcpy(var_sk[i], other[i].sk, S_BYTES); memcpy(var_sk[i] + Z_OFF, other[i].sk + Z_OFF, 32);
    } else if (!strcmp(mode, "public")) {         /* embedded pk and H(pk) vary; s, z, ct fixed */
      memcpy(var_sk[i] + S_BYTES, other[i].sk + S_BYTES, PK_BYTES + 32);
    } else if (!strcmp(mode, "ciphertext")) {     /* ciphertext varies; key fixed */
      uint8_t ec[32]; fill(ec, sizeof ec); ENC(var_ct[i], ss, base.pk, ec);
    } else if (!strcmp(mode, "second_fixed")) {   /* class 1 is one other fixed tuple */
      memcpy(var_sk[i], other[0].sk, SK_BYTES); memcpy(var_ct[i], other[0].ct, CT_BYTES);
    } else { fprintf(stderr, "unknown mode\n"); return 2; }
  }
  printf("mode,iter,class,perm_x1,perm_x4,cycles\n");
  int k = 0;
  for (int it = 0; it < 2000; it++) DEC(ss, base.ct, base.sk); /* warm-up */
  for (int it = 0; it < n; it++) {
    int cls = (int)(next64() & 1);
    const uint8_t *src_sk = cls ? var_sk[k] : base.sk, *src_ct = cls ? var_ct[k] : base.ct;
    if (cls) k = (k + 1) % POOL;
    memcpy(work_sk, src_sk, SK_BYTES);
    memcpy(work_ct, src_ct, CT_BYTES);
    unsigned aux;
    ctkat_perm_x1 = ctkat_perm_x4 = 0;
    _mm_lfence();
    uint64_t t0 = __rdtsc();
    DEC(ss, work_ct, work_sk);
    uint64_t t1 = __rdtscp(&aux);
    _mm_lfence();
    printf("%s,%d,%d,%llu,%llu,%llu\n", mode, it, cls, ctkat_perm_x1, ctkat_perm_x4, (unsigned long long)(t1 - t0));
  }
  return 0;
}
