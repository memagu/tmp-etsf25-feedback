#!/usr/bin/env python3
"""Turn the peer-review .txt files into one readable HTML page."""

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REVIEWS = ROOT / "reviews"

DRAFT_NAME = "ETSF25 project draft"


SECTION_RE = re.compile(r"^[A-Z][A-Z0-9 &/,.\-]{2,48}$")
Q_RE = re.compile(r"^(\d+)\.\s*(.*)$", re.S)
QUOTE_RE = re.compile(r"“[^”]{1,260}”")


def read_lines(path: Path):
    text = path.read_text(encoding="utf-8-sig")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return [line.rstrip() for line in text.split("\n")]


def is_rule(line: str) -> bool:
    stripped = line.strip()
    return len(stripped) >= 3 and (set(stripped) == {"-"} or set(stripped) == {"*"} or set(stripped) == {"_"})


def is_section(line: str) -> bool:
    stripped = line.strip()
    return (
        len(stripped) <= 50
        and bool(SECTION_RE.match(stripped))
        and stripped.upper() == stripped
        and not Q_RE.match(stripped)
    )


def parse(path: Path):
    lines = read_lines(path)
    sections = []
    current = None
    current_q = None
    i = 0

    def new_section(title, kind="section"):
        nonlocal current, current_q
        current = {
            "title": title.capitalize() if title.isupper() else title,
            "kind": kind,
            "questions": [],
        }
        if kind == "instructions":
            current["bullets"] = []
        sections.append(current)
        current_q = None

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        if is_rule(line):
            i += 1
            continue

        # "INSTRUCTIONS:" callout
        if line.rstrip(":").strip().upper() == "INSTRUCTIONS":
            new_section("Instructions", "instructions")
            i += 1
            while i < len(lines):
                candidate = lines[i].strip()
                if not candidate:
                    i += 1
                    continue
                if is_section(candidate) or Q_RE.match(candidate):
                    break
                if candidate.startswith(("-", "•")):
                    current["bullets"].append(candidate.lstrip("-• ").strip())
                elif current["bullets"]:
                    current["bullets"][-1] += " " + candidate
                i += 1
            continue

        if is_section(line):
            new_section(line.rstrip(":").strip())
            i += 1
            continue

        if current is None:
            new_section("Summary", "intro")
            current["paragraphs"] = []

        match = Q_RE.match(line)
        if match:
            number = int(match.group(1))
            question = match.group(2).strip()
            i += 1

            # Wrapped question lines (files without blank lines between Q and A)
            while i < len(lines):
                candidate = lines[i].strip()
                if not candidate:
                    break
                if candidate.lower().startswith("answer:"):
                    break
                if is_section(candidate) or Q_RE.match(candidate):
                    break
                question += " " + candidate
                i += 1

            current_q = {"number": number, "question": question, "answers": []}
            current["questions"].append(current_q)

            # Optional blank line before the answer
            while i < len(lines) and not lines[i].strip():
                i += 1

            marker = Q_RE.match(lines[i].strip()) if i < len(lines) else None
            if (
                i < len(lines)
                and not is_section(lines[i])
                and not marker
            ):
                answer_line = lines[i].strip()
                if answer_line.lower().startswith("answer:"):
                    answer_line = answer_line[len("Answer:") :].strip()
                answer = answer_line
                i += 1
                while i < len(lines):
                    candidate = lines[i].strip()
                    if not candidate:
                        break
                    if is_section(candidate) or Q_RE.match(candidate):
                        break
                    if candidate.lower().startswith("answer:"):
                        break
                    answer += " " + candidate
                    i += 1
                if answer:
                    current_q["answers"].append(answer)
            continue

        # Stray paragraph after a question: treat it as another answer block
        if current_q is not None:
            paragraph = line
            i += 1
            while i < len(lines):
                candidate = lines[i].strip()
                if not candidate or is_section(candidate) or Q_RE.match(candidate):
                    break
                paragraph += " " + candidate
                i += 1
            current_q["answers"].append(paragraph)
            continue

        if current.get("kind") == "intro":
            paragraph = line
            i += 1
            while i < len(lines):
                candidate = lines[i].strip()
                if (
                    not candidate
                    or is_rule(candidate)
                    or is_section(candidate)
                    or Q_RE.match(candidate)
                ):
                    break
                paragraph += " " + candidate
                i += 1
            current["paragraphs"].append(paragraph)
            continue

        i += 1

    return sections


def inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = QUOTE_RE.sub(lambda m: f'<span class="quote">{m.group(0)}</span>', escaped)
    return escaped


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def display_name(stem: str) -> str:
    words = re.split(r"[-_\s]+", stem)
    return " ".join(word[:1].upper() + word[1:] for word in words if word)


def discover_docs():
    paths = sorted(REVIEWS.glob("*.txt"), key=lambda path: path.name.casefold())
    docs = []
    for path in paths:
        name = display_name(path.stem)
        docs.append(
            {
                "file": path.name,
                "slug": slugify(path.stem),
                "tab": name,
                "short": name.split()[0] if name else path.stem,
                "title": f"Peer review by {name}",
                "note": f"Review of the {DRAFT_NAME}.",
            }
        )
    return docs


def render_doc(doc, sections, index):
    slug = doc["slug"]
    questions = [q for s in sections for q in s["questions"]]
    words = sum(len(q["question"].split()) + sum(len(a.split()) for a in q["answers"]) for q in questions)
    words += sum(len(p.split()) for s in sections if s["kind"] == "intro" for p in s["paragraphs"])

    out = []
    out.append(f'<section class="doc" id="doc-{slug}" data-doc="{slug}" role="tabpanel" aria-labelledby="tab-{slug}" hidden>')
    out.append('<div class="doc-head">')
    out.append(f'<p class="doc-kicker">Document {index:02d}</p>')
    out.append(f"<h2>{html.escape(doc['title'])}</h2>")
    out.append('<div class="doc-meta">')
    out.append(f"<code>{html.escape(doc['file'])}</code><span>{len(questions)} answers</span><span>~{words:,} words</span>")
    out.append("</div>")
    out.append(f'<p class="doc-note">{doc["note"]}</p>')
    out.append("</div>")

    for section in sections:
        if section["kind"] == "intro":
            out.append('<div class="doc-summary">')
            out.append('<p class="summary-label">Reviewer’s summary</p>')
            for paragraph in section["paragraphs"]:
                out.append(f'<p class="summary-text">{inline(paragraph)}</p>')
            out.append("</div>")
            continue

        sec_slug = f"{slug}-{slugify(section['title'])}"
        out.append(f'<section class="section" id="{sec_slug}" data-title="{html.escape(section["title"])}">')

        if section["kind"] == "instructions":
            out.append('<div class="callout">')
            out.append('<p class="callout-label">Instructions for the reviewer</p>')
            out.append("<ul>")
            for bullet in section["bullets"]:
                out.append(f"<li>{inline(bullet)}</li>")
            out.append("</ul></div>")
            out.append("</section>")
            continue

        numbers = [q["number"] for q in section["questions"]]
        range_label = f"Q{min(numbers)}–{max(numbers)}" if numbers else ""
        out.append('<div class="section-head">')
        out.append(f"<h2>{html.escape(section['title'])}</h2>")
        out.append(f'<span class="section-range">{range_label}</span>')
        out.append("</div>")

        for q in section["questions"]:
            qid = f"{slug}-q{q['number']}"
            search_blob = " ".join([q["question"]] + q["answers"]).lower()
            out.append(f'<article class="qa" id="{qid}" data-search="{html.escape(search_blob, quote=True)}">')
            out.append('<div class="qa-q">')
            out.append(f'<span class="num">{q["number"]:02d}</span>')
            out.append(f"<h3>{inline(q['question'])}</h3>")
            out.append("</div>")
            if q["answers"]:
                out.append('<div class="qa-a">')
                for paragraph in q["answers"]:
                    out.append(f"<p>{inline(paragraph)}</p>")
                out.append("</div>")
            else:
                out.append('<div class="qa-a empty"><p>No answer written.</p></div>')
            out.append("</article>")

        out.append("</section>")

    out.append("</section>")
    return "\n".join(out), questions, words


def render_toc(doc, sections):
    slug = doc["slug"]
    out = [f'<nav class="toc-list" data-doc="{slug}" aria-label="Sections of {html.escape(doc["title"])}" hidden>']
    for section in sections:
        if section["kind"] != "section" or not section["questions"]:
            continue
        numbers = [q["number"] for q in section["questions"]]
        out.append(
            f'<a class="toc-link" href="#{slug}-{slugify(section["title"])}" data-section="{slug}-{slugify(section["title"])}">'
            f'<span class="toc-name">{html.escape(section["title"])}</span>'
            f'<span class="toc-range">{min(numbers)}–{max(numbers)}</span></a>'
        )
    out.append("</nav>")
    return "\n".join(out)


CSS = r"""
:root{
  --paper:#f2ecdf;
  --paper-2:#ece4d4;
  --card:#fffdf8;
  --ink:#201c16;
  --ink-soft:#3d372d;
  --muted:#776d5e;
  --line:#ddd2bf;
  --line-strong:#cbbca5;
  --accent:#a63f27;
  --accent-deep:#83301d;
  --accent-wash:#f3e4da;
  --gold:#c2954f;
  --serif:"IBM Plex Serif", "Charter", "Iowan Old Style", Georgia, "Liberation Serif", serif;
  --sans:"IBM Plex Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
  --mono:"IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  --shadow:0 1px 2px rgba(72,48,24,.05), 0 14px 34px -22px rgba(72,48,24,.32);
}

*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0;
  color:var(--ink);
  background:
    radial-gradient(900px 420px at 8% -8%, rgba(194,149,79,.16), transparent 70%),
    radial-gradient(760px 460px at 100% 0%, rgba(166,63,39,.09), transparent 70%),
    var(--paper);
  font-family:var(--serif);
  font-size:17px;
  line-height:1.6;
  -webkit-font-smoothing:antialiased;
  text-rendering:optimizeLegibility;
}
body::before{
  content:"";
  position:fixed;
  inset:0;
  pointer-events:none;
  opacity:.35;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.055'/%3E%3C/svg%3E");
  z-index:0;
}
::selection{background:rgba(166,63,39,.18)}
a{color:var(--accent-deep)}
kbd{font-family:var(--mono);font-size:.82em;background:rgba(32,28,22,.06);padding:.14em .42em;border-radius:4px}
code{font-family:var(--mono);font-size:.82em;background:rgba(32,28,22,.06);padding:.14em .42em;border-radius:4px}
.wrap{width:min(1060px, calc(100% - 56px));margin-inline:auto;position:relative;z-index:1}
.progress{position:fixed;top:0;left:0;height:2px;width:0;background:linear-gradient(90deg,var(--gold),var(--accent));z-index:60;transition:width .1s linear}

/* Masthead */
.masthead{padding:clamp(52px,7vw,86px) 0 34px}
.kicker{
  margin:0 0 18px;font-family:var(--mono);font-size:12px;font-weight:500;
  letter-spacing:.14em;text-transform:uppercase;color:var(--accent);
  display:flex;align-items:center;gap:10px;
}
.kicker .dot{width:6px;height:6px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px rgba(166,63,39,.12)}
h1{
  margin:0;font-size:clamp(2.5rem,5.6vw,4.1rem);line-height:1.02;
  font-weight:600;letter-spacing:-.035em;max-width:15ch;
}
h1 em{font-style:italic;font-weight:400;color:var(--accent)}
.lede{margin:22px 0 0;max-width:56ch;font-size:1.08rem;color:var(--ink-soft);line-height:1.55}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:26px}
.chip{
  font-family:var(--mono);font-size:11px;letter-spacing:.05em;color:var(--muted);
  border:1px solid var(--line-strong);border-radius:999px;padding:5px 11px;
  background:rgba(255,253,248,.45);
}
.chip.accent{color:var(--accent-deep);border-color:rgba(166,63,39,.3);background:var(--accent-wash)}

/* Tabs */
.tabbar{
  position:sticky;top:0;z-index:40;
  background:rgba(242,236,223,.88);
  -webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);
  border-top:1px solid var(--line);
  border-bottom:1px solid var(--line-strong);
}
.tabbar-inner{display:flex;align-items:stretch;justify-content:space-between;gap:18px}
.tabs{display:flex;gap:6px;overflow-x:auto;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.doc-tab{
  appearance:none;background:none;border:0;border-bottom:2px solid transparent;
  color:var(--muted);font-family:var(--sans);font-size:13.5px;font-weight:500;
  padding:17px 14px 15px;cursor:pointer;white-space:nowrap;
  display:flex;align-items:center;gap:9px;transition:color .18s ease,border-color .18s ease;
  margin-bottom:-1px;
}
.doc-tab:hover{color:var(--ink)}
.doc-tab[aria-selected="true"]{color:var(--ink);border-bottom-color:var(--accent)}
.doc-tab .tab-num{font-family:var(--mono);font-size:10.5px;color:var(--accent);letter-spacing:.04em}
.doc-tab[aria-selected="false"] .tab-num{color:var(--muted)}
.tab-label .mini{display:none}
.doc-tab .tab-count{
  font-family:var(--mono);font-size:10px;color:var(--muted);
  background:rgba(32,28,22,.055);border-radius:999px;padding:2px 7px;
}
.print-btn{
  align-self:center;display:inline-flex;align-items:center;gap:7px;
  font-family:var(--sans);font-size:12px;font-weight:500;color:var(--muted);
  background:none;border:1px solid var(--line-strong);border-radius:999px;
  padding:7px 13px;cursor:pointer;transition:.18s ease;flex:0 0 auto;
}
.print-btn:hover{color:var(--ink);border-color:var(--muted);background:rgba(255,253,248,.6)}
.print-btn svg{width:13px;height:13px}

/* Layout */
.layout{display:grid;grid-template-columns:236px minmax(0,1fr);gap:clamp(32px,5vw,64px);padding:46px 0 80px;align-items:start}
main{max-width:760px;width:100%}
.sidebar{position:sticky;top:84px;display:flex;flex-direction:column;gap:26px}
.search{
  display:flex;align-items:center;gap:9px;background:var(--card);
  border:1px solid var(--line-strong);border-radius:9px;padding:9px 11px;
  box-shadow:0 1px 0 rgba(255,255,255,.7) inset;
  transition:border-color .18s ease,box-shadow .18s ease;
}
.search:focus-within{border-color:var(--accent);box-shadow:0 0 0 3px rgba(166,63,39,.1)}
.search svg{width:14px;height:14px;color:var(--muted);flex:0 0 auto}
.search input{
  appearance:none;border:0;background:none;outline:0;width:100%;
  font-family:var(--sans);font-size:13px;color:var(--ink);
}
.search input::placeholder{color:var(--muted)}
.search kbd{
  font-family:var(--mono);font-size:10px;color:var(--muted);
  border:1px solid var(--line);border-bottom-width:2px;border-radius:4px;padding:1px 5px;
}
.result-count{margin:-14px 0 0;font-family:var(--mono);font-size:10.5px;line-height:1.5;color:var(--accent-deep)}
.toc{display:flex;flex-direction:column;gap:16px}
.toc-label{margin:0 0 2px;font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.toc-list{display:flex;flex-direction:column;gap:2px}
.toc-link{
  display:flex;justify-content:space-between;align-items:baseline;gap:10px;
  text-decoration:none;color:var(--muted);font-family:var(--sans);font-size:13px;
  padding:7px 0 7px 13px;border-left:2px solid var(--line);
  transition:color .16s ease,border-color .16s ease,background .16s ease;
}
.toc-link:hover{color:var(--ink);border-left-color:var(--line-strong)}
.toc-link.active{color:var(--accent-deep);border-left-color:var(--accent);font-weight:500}
.toc-range{font-family:var(--mono);font-size:9.5px;color:var(--muted);opacity:.8}
.side-note{margin:0;padding-top:18px;border-top:1px solid var(--line);font-family:var(--sans);font-size:11.5px;line-height:1.6;color:var(--muted)}

/* Document */
.doc{animation:docIn .32s ease both}
@keyframes docIn{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
.doc-head{padding-bottom:34px;border-bottom:1px solid var(--line-strong);margin-bottom:36px}
.doc-kicker{margin:0 0 10px;font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent)}
.doc-head h2{margin:0;font-size:clamp(1.7rem,3vw,2.3rem);line-height:1.15;letter-spacing:-.02em;font-weight:600;max-width:24ch}
.doc-meta{display:flex;flex-wrap:wrap;gap:4px 6px;margin-top:16px;font-family:var(--mono);font-size:10.5px;color:var(--muted)}
.doc-meta > * + *::before{content:"·";margin-right:10px;color:var(--line-strong)}
.doc-note{margin:14px 0 0;font-family:var(--sans);font-size:12px;color:var(--muted)}
.doc-note code{font-size:.92em}

.section{margin-bottom:44px;scroll-margin-top:84px}
.section-head{display:flex;align-items:baseline;justify-content:space-between;gap:16px;margin:0 0 18px;padding-bottom:9px;border-bottom:1px solid var(--line)}
.section-head h2{margin:0;font-family:var(--sans);font-size:11px;font-weight:600;letter-spacing:.17em;text-transform:uppercase;color:var(--ink-soft)}
.section-range{font-family:var(--mono);font-size:10px;color:var(--muted);letter-spacing:.04em}
.section:first-of-type{margin-top:0}

.qa{
  background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:21px 23px 22px;margin-bottom:12px;box-shadow:var(--shadow);
  transition:border-color .2s ease,transform .2s ease,box-shadow .2s ease;
}
.qa:hover{border-color:var(--line-strong);transform:translateY(-1px);box-shadow:0 1px 2px rgba(72,48,24,.05),0 20px 40px -26px rgba(72,48,24,.4)}
.qa-q{display:flex;gap:13px;align-items:flex-start}
.num{
  flex:0 0 auto;width:27px;height:27px;margin-top:2px;border:1px solid rgba(166,63,39,.5);border-radius:50%;
  display:inline-flex;align-items:center;justify-content:center;
  font-family:var(--mono);font-size:9.5px;font-weight:500;color:var(--accent);letter-spacing:.02em;
}
.qa h3{margin:0;font-size:1.06rem;line-height:1.42;font-weight:600;letter-spacing:-.005em;color:var(--ink)}
.qa-a{margin:13px 0 0 40px;padding-left:17px;border-left:2px solid var(--accent-wash)}
.qa-a p{margin:0;font-size:1.01rem;line-height:1.74;color:var(--ink-soft)}
.qa-a p + p{margin-top:.7em}
.qa-a.empty p{color:var(--muted);font-style:italic}
.quote{
  font-style:italic;
  box-shadow:inset 0 -0.5em 0 rgba(194,149,79,.2);
  -webkit-box-decoration-break:clone;box-decoration-break:clone;
}
.qa[hidden],.section[hidden],.doc[hidden],.toc-list[hidden]{display:none}

/* Document summary */
.doc-summary{
  margin:0 0 34px;padding:18px 22px;
  border-left:3px solid var(--gold);border-radius:0 10px 10px 0;
  background:linear-gradient(90deg,rgba(194,149,79,.12),rgba(194,149,79,.02) 75%,transparent);
}
.summary-label{margin:0 0 6px;font-family:var(--mono);font-size:9.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-deep)}
.summary-text{margin:0;font-size:1.12rem;line-height:1.64;color:var(--ink-soft)}

/* Instructions callout */
.callout{
  background:linear-gradient(180deg,rgba(255,253,248,.85),rgba(255,253,248,.45));
  border:1px solid var(--line);border-left:3px solid var(--gold);
  border-radius:10px;padding:19px 23px;
}
.callout-label{margin:0 0 10px;font-family:var(--mono);font-size:10px;letter-spacing:.13em;text-transform:uppercase;color:var(--muted)}
.callout ul{margin:0;padding-left:18px;color:var(--ink-soft);font-size:.94rem}
.callout li{margin:5px 0;line-height:1.55}
.callout li::marker{color:var(--gold)}

/* Footer + misc */
.foot{padding:26px 0 38px;border-top:1px solid var(--line);}
.foot p{margin:0;font-family:var(--sans);font-size:11.5px;line-height:1.7;color:var(--muted)}
.to-top{
  position:fixed;right:26px;bottom:26px;z-index:30;width:38px;height:38px;border-radius:50%;
  border:1px solid var(--line-strong);background:rgba(255,253,248,.9);color:var(--muted);
  display:flex;align-items:center;justify-content:center;cursor:pointer;
  opacity:0;pointer-events:none;transform:translateY(6px);transition:.2s ease;
  box-shadow:0 6px 18px -10px rgba(0,0,0,.4);
}
.to-top.show{opacity:1;pointer-events:auto;transform:none}
.to-top:hover{color:var(--accent);border-color:var(--accent)}
.to-top svg{width:15px;height:15px}

@media (max-width:900px){
  .layout{grid-template-columns:1fr;gap:30px;padding-top:32px}
  .sidebar{position:static;display:grid;grid-template-columns:1fr 1fr;gap:18px 26px;align-items:start}
  .search{grid-column:1/-1}
  .result-count{margin:0;grid-column:1/-1}
  .toc-label{display:none}
  .toc{gap:0}
  .toc-list{flex-direction:row;flex-wrap:wrap;gap:6px}
  .toc-link{border-left:0;border:1px solid var(--line);border-radius:999px;padding:5px 11px;font-size:11.5px;gap:6px}
  .toc-link.active{border-color:var(--accent);background:var(--accent-wash)}
  .side-note{display:none}
  .masthead{padding-top:46px}
}
@media (max-width:620px){
  .wrap{width:calc(100% - 32px)}
  .layout{padding-bottom:56px}
  .doc-tab{padding:14px 9px 12px;font-size:12.5px}
  .doc-tab .tab-count{display:none}
  .tab-label .full{display:none}
  .tab-label .mini{display:inline}
  .print-btn span{display:none}
  .print-btn{padding:8px}
  .qa{padding:18px 17px;border-radius:10px}
  .qa-a{margin-left:0;padding-left:14px}
  .qa h3{font-size:1rem}
  .num{width:24px;height:24px;font-size:9px}
  .sidebar{grid-template-columns:1fr}
  .doc-meta > * + *::before{content:"";margin-right:0}
  .doc-meta{gap:4px 12px}
}
@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{animation:none!important;transition:none!important}
}
@media print{
  body{background:#fff;font-size:11pt}
  body::before,.tabbar,.sidebar,.progress,.to-top,.masthead .chips,.masthead .lede,.doc-note,.foot{display:none!important}
  .wrap{width:100%}
  .masthead{padding:0 0 16px}
  .layout{display:block;padding:0}
  .doc[hidden]{display:none}
  .qa{break-inside:avoid;box-shadow:none;border-color:#ccc;padding:10px 0;margin:0;border-width:0 0 1px}
  .qa:hover{transform:none;box-shadow:none}
  .section{margin-bottom:22px}
  .doc-head{margin-bottom:20px}
}
"""

JS = r"""
const tabs = Array.from(document.querySelectorAll('.doc-tab'));
const docs = Array.from(document.querySelectorAll('.doc'));
const tocLists = Array.from(document.querySelectorAll('.toc-list'));
const search = document.getElementById('search');
const resultCount = document.getElementById('resultCount');
const progress = document.getElementById('progress');
const toTop = document.querySelector('.to-top');

function activeDoc() {
  return document.querySelector('.doc:not([hidden])');
}

function updateCount() {
  const doc = activeDoc();
  const q = search.value.trim().toLowerCase();
  if (!doc) return;
  const cards = Array.from(doc.querySelectorAll('.qa'));
  const shown = cards.filter(card => !card.hidden).length;
  if (q) {
    resultCount.textContent = `${shown} of ${cards.length} answers match “${search.value.trim()}”`;
  } else {
    resultCount.textContent = '';
  }
}

function applySearch() {
  const doc = activeDoc();
  if (!doc) return;
  const q = search.value.trim().toLowerCase();
  doc.querySelectorAll('.qa').forEach(card => {
    card.hidden = Boolean(q) && !card.dataset.search.includes(q);
  });
  doc.querySelectorAll('.section').forEach(section => {
    const cards = Array.from(section.querySelectorAll('.qa'));
    section.hidden = cards.length > 0 && cards.every(card => card.hidden);
  });
  updateCount();
}

function setActiveDoc(slug, { scroll = false } = {}) {
  tabs.forEach(tab => tab.setAttribute('aria-selected', String(tab.dataset.target === slug)));
  docs.forEach(doc => { doc.hidden = doc.dataset.doc !== slug; });
  tocLists.forEach(list => { list.hidden = list.dataset.doc !== slug; });
  if (search.value) { search.value = ''; }
  resultCount.textContent = '';
  applySearch();
  if (scroll) window.scrollTo({ top: 0, behavior: 'smooth' });
  updateActiveSection();
  try { history.replaceState(null, '', '#' + slug); } catch (e) {}
}

function updateActiveSection() {
  const doc = activeDoc();
  if (!doc) return;
  const sections = Array.from(doc.querySelectorAll('.section')).filter(section => section.querySelector('.qa'));
  if (!sections.length) return;
  const offset = 120;
  let current = sections[0];
  for (const section of sections) {
    if (section.getBoundingClientRect().top <= offset) current = section;
    else break;
  }
  const list = tocLists.find(l => l.dataset.doc === doc.dataset.doc);
  if (!list) return;
  list.querySelectorAll('.toc-link').forEach(link => {
    link.classList.toggle('active', current && link.dataset.section === current.id);
  });
}

tabs.forEach(tab => {
  tab.addEventListener('click', () => setActiveDoc(tab.dataset.target, { scroll: true }));
});

search.addEventListener('input', applySearch);
search.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    search.value = '';
    applySearch();
    search.blur();
  }
});

document.addEventListener('keydown', event => {
  const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
  if (event.key === '/' && !typing) {
    event.preventDefault();
    search.focus();
  }
});

let ticking = false;
function onScroll() {
  if (ticking) return;
  ticking = true;
  requestAnimationFrame(() => {
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docHeight > 0 ? (window.scrollY / docHeight) * 100 : 0;
    progress.style.width = Math.min(100, Math.max(0, pct)) + '%';
    toTop.classList.toggle('show', window.scrollY > 700);
    updateActiveSection();
    ticking = false;
  });
}
window.addEventListener('scroll', onScroll, { passive: true });
window.addEventListener('resize', onScroll);

toTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
document.querySelector('.print-btn').addEventListener('click', () => window.print());

const initial = (location.hash || '').replace('#', '');
const valid = tabs.some(tab => tab.dataset.target === initial);
setActiveDoc(valid ? initial : tabs[0].dataset.target);
onScroll();
"""


def main():
    docs = discover_docs()
    if not docs:
        raise SystemExit(f"No .txt review files found in {REVIEWS}")

    docs_html = []
    tocs_html = []
    all_questions = 0
    all_words = 0
    counts = []

    for index, doc in enumerate(docs, start=1):
        sections = parse(REVIEWS / doc["file"])
        html_doc, questions, words = render_doc(doc, sections, index)
        docs_html.append(html_doc)
        tocs_html.append(render_toc(doc, sections))
        all_questions += len(questions)
        all_words += words
        counts.append(len(questions))

    tabs_html = "\n".join(
        (
            f'<button class="doc-tab" id="tab-{doc["slug"]}" role="tab" '
            f'aria-controls="doc-{doc["slug"]}" aria-selected="false" data-target="{doc["slug"]}">'
            f'<span class="tab-num">{i:02d}</span>'
            f'<span class="tab-label"><span class="full">{html.escape(doc["tab"])}</span><span class="mini">{html.escape(doc["short"])}</span></span>'
            f'<span class="tab-count">{count}</span>'
            "</button>"
        )
        for i, (doc, count) in enumerate(zip(docs, counts), start=1)
    )

    source_list = " · ".join(f'<code>{html.escape(doc["file"])}</code>' for doc in docs)
    css = CSS
    js = JS

    page = []
    page.append(
        """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>ETSF25 · Peer reviews</title>
<meta name="description" content="Peer-review documents for the ETSF25 project draft, formatted for reading.">
<meta name="theme-color" content="#f2ecdf">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<meta property="og:title" content="ETSF25 · Peer reviews">
<meta property="og:description" content="Peer-review documents for the ETSF25 project draft, formatted for reading.">
<meta property="og:type" content="website">
<style>"""
    )
    page.append(css)
    page.append(
        """</style>
</head>
<body>
<div class="progress" id="progress"></div>
<header class="masthead">
  <div class="wrap">
    <p class="kicker"><span class="dot"></span>ETSF25 · Project draft 1</p>
    <h1>Peer reviews,<br><em>set to read.</em></h1>
    <p class="lede">Written feedback on the ETSF25 project draft, lifted out of plain text and laid out question by question.</p>
    <div class="chips">
      <span class="chip accent">"""
        + str(len(docs))
        + """ files</span>
      <span class="chip">"""
        + str(all_questions)
        + """ answers</span>
      <span class="chip">~"""
        + f"{all_words:,}"
        + """ words</span>
      <span class="chip">Press <code>/</code> to search</span>
    </div>
  </div>
</header>

<div class="tabbar">
  <div class="wrap tabbar-inner">
    <div class="tabs" role="tablist" aria-label="Documents">
      """
        + tabs_html
        + """
    </div>
    <button class="print-btn" type="button" aria-label="Print or save as PDF">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
      <span>Print / PDF</span>
    </button>
  </div>
</div>

<div class="wrap layout">
  <aside class="sidebar">
    <label class="search" for="search">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input id="search" type="search" placeholder="Search this review…" autocomplete="off" spellcheck="false">
      <kbd>/</kbd>
    </label>
    <p class="result-count" id="resultCount" aria-live="polite"></p>
    <div class="toc">
      <p class="toc-label">In this document</p>
      """
        + "\n".join(tocs_html)
        + """
    </div>
    <p class="side-note">Generated from the original <code>.txt</code> files. Text is unchanged — only the presentation is new.</p>
  </aside>
  <main>
    """
        + "\n".join(docs_html)
        + """
  </main>
</div>

<footer class="foot">
  <div class="wrap">
    <p>Source files: """
        + source_list
        + """.<br>
    Compiled 18 November 2026. <kbd>/</kbd> to search, <kbd>Esc</kbd> to clear.</p>
  </div>
</footer>

<button class="to-top" type="button" aria-label="Back to top">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m18 15-6-6-6 6"/></svg>
</button>

<script>"""
    )
    page.append(js)
    page.append("</script>\n</body>\n</html>\n")

    output = ROOT / "index.html"
    output.write_text("".join(page), encoding="utf-8")
    print(f"wrote {output} ({output.stat().st_size:,} bytes, {all_questions} answers)")


if __name__ == "__main__":
    main()
