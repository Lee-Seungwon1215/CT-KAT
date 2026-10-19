# Artifacts for the revised CT-KAT manuscript

This directory holds the data and scripts behind the tables that were added or regenerated in the
revised manuscript "CT-KAT: Beyond Pass/Fail in Constant-Time Screening of PQC Implementations".
All timing results come from the final single-host measurement campaign (called V10 in this
repository), run on an Intel Core i7-10875H host with SMT and Turbo Boost disabled and the official
dudect implementation.

To regenerate every table below from the recorded results and compare it with the committed
output, run from the repository root:

```bash
uv run bash docs/paper/revision-artifacts/reproduce_tables.sh
```

| Manuscript item | Files | How it is produced |
|---|---|---|
| Table 6, structural-test coverage (Section 5.2) | `structural_coverage/` | `coverage.py REPO OUTDIR` measures line and branch coverage of the operation call, `table_coverage.py coverage.csv` emits the table |
| Table 7 and Tables A13–A14, final statuses (Section 5.3) | `status/corpus_summary_v10.csv`, `status/tables_status.tex` | `refresh_corpus_status.py REPO docs/corpus/corpus_summary.csv v10_named_analysis/paper_native_axis_results.csv OUT.csv` refreshes the committed corpus with the V10 timing results and re-folds every status, `build_appendix.py` emits Tables A13–A14 |
| Naive pass/fail comparison (Section 5.3) | `status/naive_vs_ctkat.py`, `status/naive_vs_ctkat.txt` | `naive_vs_ctkat.py status/corpus_summary_v10.csv` |
| Alternative decision orders | `status/order_sensitivity.py`, `status/order_sensitivity.txt` | `order_sensitivity.py REPO status/corpus_summary_v10.csv` |
| Timed KyberSlash binaries and their divisions (Section 5.4) | `binary_contracts/` | Disassembly and instruction-contract report of every timed binary, bound to the binary SHA-256 recorded in the timing reports |
| Table A15, sensitivity of every timing condition | `timing_sensitivity/`, `v10_reports.tgz` | Extract `v10_reports.tgz`, then `build_sensitivity_table.py ROOT ...` over the four component roots |
| Table A16, root cause of the mixed-input ML-KEM signals (Section 5.5) | `mlkem_root_cause/` | See `mlkem_root_cause/README.md` (exploratory experiment on the same host, outside the frozen V10 campaign) |

The committed corpus in `docs/corpus/` is not changed by this refresh. Measured results are
promoted into it only after the automated audit and artifact-integrity gates, so until then it keeps
the timing rows of an earlier experimental backend.

Other files:

- `v10_named_analysis/` is the named analysis of the V10 campaign (axis results, pairwise
  contrasts, signature lengths). `paper_native_axis_results.csv` is the input of
  `refresh_corpus_status.py`.
- `v10_reports.tgz` contains the dudect backend reports of the final campaign and of the control
  rehearsals that qualified it.

The full V10 measurement tree with the raw timing traces (about 3.3 GB) is not stored in this
repository.
