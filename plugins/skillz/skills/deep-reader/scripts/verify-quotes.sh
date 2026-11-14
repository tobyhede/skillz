#!/bin/bash
# verify-quotes.sh <workspace-dir>
#
# Mechanical anti-hallucination check for study mode: every quoted, page-cited
# sentence in the workspace's .md notes gets checked against source.txt.
set -euo pipefail

usage() {
  echo "Usage: verify-quotes.sh <workspace-dir>" >&2
  exit 1
}

[ $# -eq 1 ] || usage
workspace="$1"
[ -d "$workspace" ] || { echo "Workspace directory not found: $workspace" >&2; exit 1; }
workspace="$(cd "$workspace" && pwd)"

[ -f "$workspace/source.txt" ] || {
  echo "source.txt not found in $workspace; cannot verify quotes without it." >&2
  exit 1
}

tmp_awk="$(mktemp)"
cleanup() { rm -f "$tmp_awk" 2>/dev/null; return 0; }
trap cleanup EXIT

cd "$workspace"

md_files=()
while IFS= read -r f; do
  md_files+=("$f")
done < <(find . -type f -name '*.md' | sed 's#^\./##' | sort)

if [ "${#md_files[@]}" -eq 0 ]; then
  echo "No markdown files found under $workspace to verify." >&2
  printf '{"checked": 0, "ok": 0, "near": 0, "fail": 0, "skipped": 0}\n'
  exit 0
fi

cat > "$tmp_awk" <<'AWK_EOF'
function normalize(s,    r) {
  r = s
  gsub(/“/, "\"", r)
  gsub(/”/, "\"", r)
  gsub(/‘/, "'", r)
  gsub(/’/, "'", r)
  gsub(/–/, "-", r)
  gsub(/—/, "-", r)
  r = tolower(r)
  # Dashes/hyphens fold to a space (not preserved as "-"): a printed
  # "lowest-end" and a quoted "lowest end" must compare equal.
  gsub(/-+/, " ", r)
  # Drop punctuation and control characters but keep every letter, including
  # non-ASCII ones: deleting accents would let "Tối" match "Tôi", and deleting
  # all non-ASCII would make Cyrillic or CJK quotes vanish unchecked.
  gsub(/[[:punct:][:cntrl:]]/, "", r)
  gsub(/[[:blank:]]+/, " ", r)
  gsub(/^ +/, "", r)
  gsub(/ +$/, "", r)
  return r
}

function wordcount(s,    tmp, warr) {
  tmp = s
  gsub(/^[[:blank:]]+/, "", tmp)
  gsub(/[[:blank:]]+$/, "", tmp)
  if (tmp == "") return 0
  return split(tmp, warr, /[[:blank:]]+/)
}

function first_n_words(s, n,    c, arr, out, i, lim) {
  c = split(s, arr, /[[:blank:]]+/)
  lim = (c < n) ? c : n
  out = ""
  for (i = 1; i <= lim; i++) out = (i == 1) ? arr[i] : out " " arr[i]
  return out
}

# True for a span with no blanks that contains non-ASCII text at least 12
# bytes long: a quote in a script written without spaces, such as Chinese or
# Japanese, which the five-word rule would otherwise never select.
function unspaced_quote(s) {
  return s !~ /[[:blank:]]/ && s ~ /[^\001-\177]/ && length(s) >= 12
}

# Extracts double-quoted spans (>=5 words, or an unspaced_quote) from a line. Curly double quotes
# are folded to straight quotes first so both styles are handled by a single
# scan; the returned text is used only for the human-readable preview.
function extract_quotes(line,    conv, i, start, end, span, n) {
  conv = line
  gsub(/“/, "\"", conv)
  gsub(/”/, "\"", conv)
  n = 0
  i = 1
  while (1) {
    start = index(substr(conv, i), "\"")
    if (start == 0) break
    start = i + start - 1
    end = index(substr(conv, start + 1), "\"")
    if (end == 0) break
    end = start + end
    span = substr(conv, start + 1, end - start - 1)
    if (wordcount(span) >= 5 || unspaced_quote(span)) {
      n++
      found[n] = span
      found_end[n] = end
    }
    i = end + 1
  }
  return n
}

BEGIN {
  checked = 0; ok = 0; near = 0; fail = 0; skipped = 0
  max_page = 0
  finalized_pages = 0
  curpage = ""
}

# --- Stage A: source.txt (first file) - build one normalized text blob per page ---
FNR == NR {
  if ($0 ~ /^\[\[page [0-9]+\]\]$/) {
    if (curpage != "") pageblob[curpage] = blob
    p = $0
    gsub(/[^0-9]/, "", p)
    curpage = p + 0
    blob = ""
  } else {
    blob = blob " " normalize($0)
  }
  next
}

# --- Transition: finalize page blobs once, on the first record of the first .md file ---
!finalized_pages {
  if (curpage != "") pageblob[curpage] = blob
  max_page = curpage + 0
  finalized_pages = 1
}

# --- Stage B: scan .md files for quote + page-citation pairs ---
# Fenced code blocks (``` or ~~~, e.g. Mermaid diagrams) are not prose and
# must never be treated as quotable/citable text. Fence state resets at the
# start of each file so an unclosed fence in one note can't swallow another.
FNR == 1 { in_fence = 0 }
$0 ~ /^[[:blank:]]*(```+|~~~+)/ { in_fence = !in_fence; next }
in_fence { next }

# Parses one citation such as "(p. 12)", "(pp. 3-4)" or "(tr. 7)" into the
# globals lo_exact, hi_exact, lo_win, hi_win and citation_display.
function parse_citation(cit,    inner, prefix, rest, rg) {
  inner = substr(cit, 2, length(cit) - 2)
  if (substr(inner, 1, 2) == "pp") {
    prefix = "pp."
    rest = inner
    sub(/^pp\.[[:blank:]]*/, "", rest)
  } else if (substr(inner, 1, 2) == "tr") {
    prefix = "tr."
    rest = inner
    sub(/^tr\.[[:blank:]]*/, "", rest)
  } else {
    prefix = "p."
    rest = inner
    sub(/^p\.[[:blank:]]*/, "", rest)
  }

  if (rest ~ /-/) {
    split(rest, rg, "-")
    lo_exact = rg[1] + 0; hi_exact = rg[2] + 0
  } else {
    lo_exact = rest + 0; hi_exact = rest + 0
  }
  lo_win = lo_exact - 1; hi_win = hi_exact + 1
  if (lo_win < 1) lo_win = 1
  if (hi_win > max_page) hi_win = max_page
  if (lo_exact < 1) lo_exact = 1
  if (hi_exact > max_page) hi_exact = max_page

  citation_display = prefix rest
}

# Joins the page blobs lo..hi with single spaces, so a quote that runs across
# a page boundary still matches.
function pages_blob(lo, hi,    pg, b) {
  b = ""
  for (pg = lo; pg <= hi; pg++) b = b " " pageblob[pg]
  gsub(/ +/, " ", b)
  return b
}

{
  # Positions are taken on the curly-quote-folded line, the same string
  # extract_quotes scans, so quote and citation offsets are comparable.
  conv = $0
  gsub(/“/, "\"", conv)
  gsub(/”/, "\"", conv)

  ncit = 0
  rest_line = conv
  offset = 0
  while (match(rest_line, /\((pp?|tr)\.[[:blank:]]*[0-9]+(-[0-9]+)?\)/)) {
    ncit++
    cit_text[ncit] = substr(rest_line, RSTART, RLENGTH)
    cit_pos[ncit] = offset + RSTART
    offset += RSTART + RLENGTH - 1
    rest_line = substr(rest_line, RSTART + RLENGTH)
  }
  if (ncit == 0) next

  nq = extract_quotes(conv)
  for (qi = 1; qi <= nq; qi++) {
    quote = found[qi]

    # Each quote takes the first citation after it; a quote with none after
    # it takes the last citation on the line.
    ci = ncit
    for (k = 1; k <= ncit; k++) if (cit_pos[k] > found_end[qi]) { ci = k; break }
    parse_citation(cit_text[ci])

    norm_q = normalize(quote)
    if (norm_q == "") {
      skipped++
      printf "SKIP\t%s:%d\t%s\t%s...\n", FILENAME, FNR, citation_display, first_n_words(quote, 8)
      continue
    }

    exact_blob = pages_blob(lo_exact, hi_exact)
    win_blob = pages_blob(lo_win, hi_win)

    checked++
    status = "FAIL"
    if (index(exact_blob, norm_q) > 0) status = "OK"
    else if (index(win_blob, norm_q) > 0) status = "NEAR"

    if (status == "OK") ok++
    else if (status == "NEAR") near++
    else fail++

    printf "%s\t%s:%d\t%s\t%s...\n", status, FILENAME, FNR, citation_display, first_n_words(quote, 8)
  }
}

END {
  printf "{\"checked\": %d, \"ok\": %d, \"near\": %d, \"fail\": %d, \"skipped\": %d}\n", checked, ok, near, fail, skipped
  # A quote that cannot be checked is not evidence that it is correct.
  if (fail > 0 || skipped > 0) exit 1
  exit 0
}
AWK_EOF

# Byte-wise (C locale) so every awk treats non-ASCII text the same way.
LC_ALL=C awk -f "$tmp_awk" source.txt "${md_files[@]}"
