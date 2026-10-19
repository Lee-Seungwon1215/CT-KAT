# CT-KAT

CT-KAT is a constant-time screening framework for C cryptographic implementations, with a focus
on post-quantum cryptography (PQC). It runs several complementary tests on the same target under
the same build conditions, keeps every result together with the conditions that produced it, and
assigns a final status only as far as the collected evidence allows.

The full user and developer guide is currently written in Korean and is available in
[README.ko.md](README.ko.md).

## Reproducing the paper

This repository accompanies the manuscript *CT-KAT: Beyond Pass/Fail in Constant-Time Screening
of PQC Implementations*. The tag `paper-revision-2026-10` marks the version used for the revised
manuscript. The results can be checked at three levels.

1. **Regenerate the tables from the recorded results** (any machine with Python 3.11+, a few
   minutes, no timing hardware).

   ```bash
   git checkout paper-revision-2026-10
   uv sync --frozen          # or: python -m pip install .
   uv run bash docs/paper/revision-artifacts/reproduce_tables.sh
   ```

   The script rebuilds Table 6, Table 7, Tables A13–A16, and the numbers of the naive pass/fail
   comparison in Section 5.3 from the recorded results, and checks that they match the committed
   outputs. [`docs/paper/revision-artifacts/README.md`](docs/paper/revision-artifacts/README.md)
   maps every table to its data and script.

2. **Re-run the structural and instruction analyses** (Linux x86-64 with GCC, Clang, and
   Valgrind). The structural test, binary inspection, and build matrix run through the `ctkat`
   commands in [Quick start](#quick-start), using the configurations in `examples/`.
   [`structural_coverage/coverage.py`](docs/paper/revision-artifacts/structural_coverage/coverage.py)
   re-measures the coverage of Table 6, and
   [`mlkem_root_cause/README.md`](docs/paper/revision-artifacts/mlkem_root_cause/README.md)
   describes how to rebuild and rerun the root-cause experiment of Table A16.

3. **Repeat the timing campaign** (a dedicated physical x86-64 Linux host). The frozen plan is
   [`docs/measurement/paper_native_campaign_v10.yaml`](docs/measurement/paper_native_campaign_v10.yaml),
   and [`docs/artifact/README.md`](docs/artifact/README.md) gives the single-host procedure,
   including the control rehearsals that qualify a host before the final run. Timing depends on
   the host, so a repeated campaign should be compared with the paper in terms of which
   conditions show a signal and how large a difference each comparison could detect, not cycle
   by cycle.

The dudect reports, named analysis, and binary contracts of the paper campaign are included in
`docs/paper/revision-artifacts/`. The raw timing traces (about 3.3 GB) are not stored in this
repository.

## What CT-KAT does

For each configured harness, CT-KAT

1. builds the target and runs its known-answer tests (functional validation),
2. runs Valgrind/Memcheck on values marked as secret to find secret-dependent branches and memory
   addresses (structural test),
3. rebuilds the harness across compilers and optimization levels (`ct-matrix`) to find findings
   that change with the build,
4. scans the emitted assembly for variable-latency instructions such as division (`asm-scan`),
5. measures timing with two input classes and analyses the raw traces with the pinned official
   dudect backend (`dudect`), together with A/A, preparation-only, and injected-delay controls,
   and
6. combines the evidence into one of five statuses.

| Status | Meaning | Value in result files |
|---|---|---|
| Risk Identified | A valid test exceeds its risk threshold, or reviewed risk evidence exists | `risk-detected` |
| Further Review Required | A suspicious result remains, but its interpretation awaits human review | `needs-review` |
| Inconclusive | Functional behavior, environment, sample size, or controls are insufficient | `inconclusive` |
| Tool Error | A testing tool did not finish normally | `tool-error` |
| No Issue Observed under Tested Conditions | Every required test is valid and no risk signal was observed | `no-finding-observed` |

No Issue Observed under Tested Conditions is not a proof of constant-time behavior. It holds only
for the tested binary, inputs, host, and analysis scope.

## Quick start

```bash
python -m pip install .
ctkat --version
ctkat infer --header tests/fixtures/headers/kem.h
```

The structural test requires Linux with Valgrind. On Linux:

```bash
ctkat run --config examples/toy_password/ctkat.yaml
ctkat screen --config examples/pqc_mlkem768/ctkat.yaml
```

On macOS or Windows, use the provided Docker image:

```bash
docker compose run --rm ctkat-dev bash -c \
    "ctkat run --config examples/toy_password/ctkat.yaml"
```

The full list of commands and configuration options is in [README.ko.md](README.ko.md).

## Repository layout

| Path | Contents |
|---|---|
| `ctkat/` | Framework package (CLI, configuration schema, harness generation, evidence model) |
| `examples/` | Configurations and pinned sources for every evaluated target |
| `scripts/` | Campaign runners, consistency checks, and analysis scripts |
| `docs/measurement/` | Frozen timing campaigns, including the paper campaign (V10) |
| `docs/corpus/` | Committed corpus evidence |
| `docs/paper/revision-artifacts/` | Data and scripts behind the tables of the revised manuscript |
| `tests/` | Test suite |

## Citation

If you use CT-KAT, please cite the article listed in [CITATION.cff](CITATION.cff) and pin the
exact commit or tag.

## License

CT-KAT is released under the MIT License (see [LICENSE](LICENSE)). Third-party code under
`examples/` keeps its own license, as listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
