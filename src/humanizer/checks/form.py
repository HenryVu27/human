"""Form checks: deterministic tests for what the claim check missed in B36's long rewrites.

B36's audit (results/research/longform-judge-b36-copying.md) found a rewrite with three paragraphs of garbled
French, one with about 40 lines of invented code, and later sections that open as if a new post began ("This is the
second of three articles"). The model claim check passed all of them. These checks compare an output with the input
it was written from and flag:

- non-English runs: sentences dominated by French, Spanish, German, Italian or Portuguese function words;
- new code: code-like lines (statements, braces, includes, assignments, fences) that the input does not contain;
- new framing: series or continuation openers, sign-offs and headers that the input does not contain.

`check_form(output, source)` returns the findings and `ok`, which every long-form output must pass from gate 2a on.
"""

from __future__ import annotations

import re

SENT = re.compile(r"(?<=[.!?])\s+|\n+")
WORD = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)?", re.UNICODE)
EN = set("the a an and or but of to in on at for with is are was were be been it this that these those i you he she "
         "we they my your his her our their not as by from have has had do does did will would can could so if "
         "what which who when there here than then just also very more most".split())
FOREIGN = set(
    "le la les des une est et que qui pour dans pas sur avec sont mais nous vous ils elle cette ces du au aux "  # fr
    "el los las del por para una con es como pero sus está son muy también "  # es
    "der die das und ist nicht mit ein eine zu den dem sich auch auf für von "  # de
    "il di che non per sono una della nel gli "  # it
    "não uma com para os das dos mais seu sua".split())  # pt
CODE_LINE = re.compile(
    r"^\s*(#include\b|import\s+\w|from\s+\w+\s+import\b|def\s+\w+\s*\(|class\s+\w+[\s(:]|function\s+\w*\s*\(|"
    r"(public|private|static|void|int|float|double|char|bool|const|let|var)\s+\w+|return\b[^.]*;|"
    r"(if|for|while|switch)\s*\(.*\)\s*\{?\s*$|[{}]\s*;?\s*$|\w+\s*\(.*\)\s*;\s*$|\w+(\[\w*\])?\s*[+\-*/]?=\s*[^=].*;\s*$|"
    r"//|/\*|\*/|```|<\?php|\$\s*\w+\s*=|\w+\.\w+\(.*\)\s*;?\s*$)")
FRAMING = re.compile(
    r"\b(this is (?:the |my |a )?(?:second|third|fourth|fifth|final|last|next|first|latest|another) "
    r"(?:of|in|part|post|article|installment|entry|chapter)\b|this is part \w+|part (?:one|two|three|four|five|\d+) of|"
    r"in my (?:last|previous|earlier|next|first) (?:post|article|entry|piece|blog)|"
    r"last time,? (?:i|we) (?:wrote|talked|posted|discussed|looked)|continu(?:ation|ed|ing) (?:of|from) (?:my|the|a|last|this)|"
    r"to be continued|stay tuned|in (?:the|my) next (?:post|article|installment|part|entry)|"
    r"(?:this|my) (?:new |blog )?series\b|"
    r"thanks? (?:you )?for reading|until next time|see you (?:next|soon|then)|that'?s (?:all|it) for (?:now|today)|"
    r"let me know (?:in the comments|what you think)|leave a comment|subscribe|follow me on)\b", re.I)
RESTART = re.compile(
    r"\b(in (?:today'?s|this|my last|the last|a previous|an earlier) (?:post|article|entry|piece)|"
    r"(?:this|today'?s) (?:post|article|entry) (?:is|will)|today,? i(?:'m| am| want| will|'ll) (?:going to |gonna )?"
    r"(?:talk|write|share|tell|review|look)|a question i (?:get|often get|am often) asked|i (?:have|want|need) to tell you|"
    r"let me tell you about|i want to (?:share|talk about|tell you)|i started this (?:post|article)|"
    r"welcome(?: back)?(?: to)?|(?:hi|hello|hey|greetings),? (?:everyone|all|friends|readers|folks|there)|"
    r"highest of highs|last time,? (?:i|we)\b|previously,? (?:i|we) (?:wrote|talked|posted))", re.I)
PLACEHOLDER = re.compile(
    r"\$\s*[A-Z][a-z]+[A-Za-z]*\s*[{(][^$\n]{0,40}[})]\s*\$|\{\{[^}\n]{0,40}\}\}|\{[a-z_]{1,12}\}|\[(?:INSERT|TODO|TBD|PLACEHOLDER|CITATION)[^\]\n]*\]|"
    r"<(?:placeholder|insert|todo)[^>\n]*>|\bTODO\b|\bXXX\b|\bLorem ipsum\b", re.I)
HEADER = re.compile(r"^\s{0,3}(#{1,6}\s+\S.*|[A-Z][\w'&,:\- ]{2,60})$")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in SENT.split(text) if s.strip()]


def non_english_runs(text: str, min_words: int = 6) -> list[str]:
    """Sentences of at least min_words words with 2 or more foreign function words outnumbering English ones."""
    out = []
    for s in _sentences(text):
        words = [w.lower() for w in WORD.findall(s)]
        if len(words) < min_words:
            continue
        f = sum(w in FOREIGN for w in words)
        e = sum(w in EN for w in words)
        if f >= 2 and f > e:
            out.append(s)
    return out


def _norm(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip().lower())


def new_code_lines(text: str, source: str) -> list[str]:
    """Code-like lines in text whose normalized form is not a line or a substring of the source."""
    src = _norm(source)
    src_lines = {_norm(x) for x in source.splitlines()}
    out = []
    for line in text.splitlines():
        if not line.strip() or not CODE_LINE.search(line):
            continue
        n = _norm(line)
        if n in src_lines or (len(n) >= 12 and n in src):
            continue
        out.append(line.strip())
    return out


def new_framing(text: str, source: str) -> list[str]:
    """Framing phrases (series, continuation, sign-off) present in text but not in source."""
    have = {m.group(0).lower() for m in FRAMING.finditer(source)}
    return sorted({m.group(0) for m in FRAMING.finditer(text) if m.group(0).lower() not in have})


def _header_like(text: str) -> list[str]:
    return [s.strip() for s in text.splitlines() if _is_header(s.strip())]


def _is_header(s: str) -> bool:
    if not s or not HEADER.match(s) or s.endswith((".", "?", "!", ":", ",")):
        return False
    if s.startswith("#"):
        return True
    words = s.split()
    return len(words) <= 8 and sum(w[:1].isupper() for w in words) >= max(2, len(words) // 2)


def new_headers(text: str, source: str) -> list[str]:
    """Header lines beyond the source's own count: a rewrite may reword the source's headings but not add more.

    Returns the output's header lines that do not match a source line, when the output has more headers than the
    source; otherwise an empty list."""
    if len(_header_like(text)) <= len(_header_like(source)):
        return []
    src_lines = {_norm(re.sub(r"^#+\s*", "", x)) for x in source.splitlines()}
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s or not HEADER.match(s) or s.endswith((".", "?", "!", ":", ",")):
            continue
        if len(s.split()) > 10 and not s.startswith("#"):
            continue
        if _norm(re.sub(r"^#+\s*", "", s)) in src_lines:
            continue
        if s.startswith("#") or (len(s.split()) <= 8 and sum(w[:1].isupper() for w in s.split()) >= max(2, len(s.split()) // 2)):
            out.append(s)
    return out


def restart_opening(text: str, source: str, n_sentences: int = 2) -> list[str]:
    """Post-opening phrases in the first sentences of a later section that its source section does not have.

    Apply only to sections after the first: a section written on its own often opens as if a new post began."""
    have = {m.group(0).lower() for m in RESTART.finditer(source)} | {m.group(0).lower() for m in FRAMING.finditer(source)}
    head = " ".join(_sentences(text)[:n_sentences])
    found = [m.group(0) for m in RESTART.finditer(head)] + [m.group(0) for m in FRAMING.finditer(head)]
    return sorted({f for f in found if f.lower() not in have})


def placeholders(text: str, source: str) -> list[str]:
    """Template leaks and placeholder math the source does not contain ("$Rewrite{n}$", "$Gaussian(0, 1)$", "{n}",
    "[INSERT ...]"): B38's backlog, from the bandits rewrite that read Human but was not publishable."""
    have = {m.group(0) for m in PLACEHOLDER.finditer(source)}
    return sorted({m.group(0) for m in PLACEHOLDER.finditer(text) if m.group(0) not in have})


def check_form(text: str, source: str, *, later_section: bool = False, max_new_code: int = 2, max_foreign: int = 1,
               max_headers: int = 0) -> dict:
    """All form findings for an output written from source; ok is False if any limit is exceeded.

    later_section: the text is a section after the first of a post written section by section, so a post-opening
    phrase at its start counts as a restart."""
    foreign = non_english_runs(text)
    code = new_code_lines(text, source)
    framing = new_framing(text, source)
    headers = new_headers(text, source)
    restart = restart_opening(text, source) if later_section else []
    holes = placeholders(text, source)
    ok = (len(foreign) <= max_foreign and len(code) <= max_new_code and not framing and len(headers) <= max_headers
          and not restart and not holes)
    return {"ok": ok, "non_english": foreign, "new_code": code, "new_framing": framing, "new_headers": headers,
            "restart": restart, "placeholders": holes}
