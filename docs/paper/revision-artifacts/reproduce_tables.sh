#!/usr/bin/env bash
# Regenerate the tables and numbers of the revised manuscript from the recorded results in this
# directory and compare them with the committed outputs.
#
# Usage (from the repository root):
#   uv sync --frozen
#   uv run bash docs/paper/revision-artifacts/reproduce_tables.sh
#
# Set PYTHON to override the interpreter (default: python3). No timing hardware is needed.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
PY="${PYTHON:-python3}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

failed=0
check() {  # check LABEL EXPECTED ACTUAL
    if cmp -s "$2" "$3"; then
        printf 'PASS  %s\n' "$1"
    else
        printf 'FAIL  %s\n' "$1"
        diff "$2" "$3" | head -20 || true
        failed=1
    fi
}

# Table 7 and Tables A13-A14: statuses re-folded with the final (V10) timing results.
"$PY" "$HERE/status/refresh_corpus_status.py" "$REPO" \
    "$HERE/v10_named_analysis/paper_native_axis_results.csv" "$WORK/corpus_summary_v10.csv" > /dev/null
check "Table 7, Tables A13-A14: corpus statuses" "$HERE/status/corpus_summary_v10.csv" "$WORK/corpus_summary_v10.csv"
"$PY" "$HERE/status/build_appendix.py" "$WORK/corpus_summary_v10.csv" "$WORK/tables_status.tex"
check "Tables A13-A14: per-pair status tables" "$HERE/status/tables_status.tex" "$WORK/tables_status.tex"

# Section 5.3: naive pass/fail comparison (15 and 17 of 25 pairs).
"$PY" "$HERE/status/naive_vs_ctkat.py" "$WORK/corpus_summary_v10.csv" > "$WORK/naive_vs_ctkat.txt"
check "Section 5.3: naive pass/fail comparison" "$HERE/status/naive_vs_ctkat.txt" "$WORK/naive_vs_ctkat.txt"

# Alternative orders of the decision rules.
"$PY" "$HERE/status/order_sensitivity.py" "$REPO" "$WORK/corpus_summary_v10.csv" > "$WORK/order_sensitivity.txt"
check "Alternative decision orders" "$HERE/status/order_sensitivity.txt" "$WORK/order_sensitivity.txt"

# Table A15: sensitivity of every timing condition.
tar -xzf "$HERE/v10_reports.tgz" -C "$WORK"
"$PY" "$HERE/timing_sensitivity/build_sensitivity_table.py" \
    "$WORK/host-a/committed-corpus-v5" "$WORK/host-a/kyberslash-v5" \
    "$WORK/host-a/falcon-v4" "$WORK/host-a/diverse-v4" > "$WORK/table_sensitivity.tex" 2> /dev/null
check "Table A15: timing sensitivity" "$HERE/timing_sensitivity/table_sensitivity.tex" "$WORK/table_sensitivity.tex"

# Table A16: root cause of the mixed-input ML-KEM signals.
mkdir -p "$WORK/root_cause"
tar -xzf "$HERE/mlkem_root_cause/raw_csv.tgz" -C "$WORK/root_cause"
(cd "$WORK/root_cause" && "$PY" "$HERE/mlkem_root_cause/table_root_cause.py" > table_root_cause.tex)
check "Table A16: ML-KEM root cause" "$HERE/mlkem_root_cause/table_root_cause.tex" "$WORK/root_cause/table_root_cause.tex"

# Table 6: structural-test coverage (from the recorded coverage.csv; coverage.py re-measures it).
"$PY" "$HERE/structural_coverage/table_coverage.py" "$HERE/structural_coverage/coverage.csv" > "$WORK/table_coverage.tex"
check "Table 6: structural-test coverage" "$HERE/structural_coverage/table_coverage.tex" "$WORK/table_coverage.tex"

if [ "$failed" -ne 0 ]; then
    echo "Some outputs differ from the committed results." >&2
    exit 1
fi
echo "All tables match the committed results."
