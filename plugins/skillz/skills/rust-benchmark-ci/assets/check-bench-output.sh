#!/usr/bin/env bash
# Fails when bencher-format output parsed fewer benchmarks than expected, or lacks a named one.
#
# github-action-benchmark (tool: cargo) skips every line its regex does not match. Criterion's
# default output, `--quick`, or a harness failure before criterion runs all leave it storing zero
# benchmarks and passing green. This check runs after the bench step and before the action.
#
# Usage: check-bench-output.sh <output.txt> [min-count] [required-name ...]
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo 'usage: check-bench-output.sh <output.txt> [min-count] [required-name ...]' >&2
  exit 2
fi

file="$1"
min="${2:-1}"
shift
[ "$#" -gt 0 ] && shift

if [ ! -f "$file" ]; then
  echo "bench output: $file does not exist" >&2
  exit 1
fi

# Same shape the action and check-bench-floors.ts parse: test <name> ... bench: <N> <unit>/iter (+/- <M>)
pattern='^test .+ \.\.\. bench: +[0-9,]+ [^ ]+/iter \(\+/- [0-9,]+\)[[:space:]]*$'
count="$(grep -cE "$pattern" "$file" || true)"

if [ "$count" -lt "$min" ]; then
  echo "bench output: $count benchmark line(s) in bencher format, expected at least $min." >&2
  echo 'Check --output-format bencher is passed, --quick is not, and the bench run did not fail early.' >&2
  exit 1
fi

missing=0
for name in "$@"; do
  # Fixed-string match on the whole name between "test " and " ... bench:"; >/dev/null not -q,
  # so no upstream SIGPIPE under pipefail.
  if ! grep -F "test $name ... bench:" "$file" >/dev/null; then
    echo "bench output: required benchmark \"$name\" is absent" >&2
    missing=1
  fi
done
[ "$missing" -eq 0 ] || exit 1

echo "bench output: $count benchmark(s) parsed"
