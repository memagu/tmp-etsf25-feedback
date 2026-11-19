# AGENTS.md

Context for coding agents working on this repository. Read this before changing the generator or the review content.

## What this is

A static reading and review-tracking site for the **ETSF25 project draft** (the venture draft is called *sqware*). It presents several reviewers' plain-text feedback side by side with the reviewed PDF.

- **Live site:** <https://feedback.memagu.com/>
- **Repository:** <https://github.com/memagu/tmp-etsf25-feedback>
- **Branch:** `main`
- **Deployment:** GitHub Pages, root of `main`, custom domain via `CNAME`

There is no backend, database, account system, package manager, or runtime dependency. Everything is a static GitHub Pages site.

## Stack

- **Generator:** `build_page.py` — Python 3 standard library only
- **Output:** `index.html` — fully self-contained (inline CSS and JS)
- **Content:** `reviews/<round>/*.txt` and `reviews/<round>/report.pdf`
- **Hosting:** GitHub Pages with `.nojekyll` and `CNAME`

The site source of truth is `build_page.py` plus the review files. **Never hand-edit `index.html`**; it is regenerated and overwritten.

## Repository layout

```text
.
├── build_page.py          # generator: reviews -> index.html
├── index.html             # generated, committed static site
├── reviews/
│   └── draft-1/
│       ├── report.pdf     # reviewed draft, embedded in split view
│       ├── aksel-sjögärd.txt
│       ├── alexander-sörensen-ristinmaa.txt
│       ├── johannes-persson.txt
│       ├── maxwell-kav.txt
│       ├── valdemar-rasmusson.txt
│       └── viktor-lindström.txt
├── favicon.svg
├── CNAME                  # feedback.memagu.com — do not remove/overwrite
├── .nojekyll
├── README.md              # user-facing project/deploy docs
└── AGENTS.md              # this file
```

The current round is `reviews/draft-1/`. The filename stem becomes the reviewer's display name (hyphens → spaces, title-cased); e.g. `aksel-sjögärd.txt` → “Aksel Sjögärd”.

## Build

```sh
python3 build_page.py
```

This parses every `.txt` in every `reviews/<round>/` directory and rewrites `index.html`. It prints the output path and question count.

If two reviews in the same round have identical question + answer bodies (summary blocks excluded), the build prints a warning naming both files. Do not ignore this unless the duplication is intentional.

There is no separate lint or test suite. Smoke-test changes by rebuilding and serving locally:

```sh
python3 -m http.server 8080
# open http://localhost:8080/
```

The generator assumes one `report.pdf` per round directory. Put the draft PDF inside the round folder; it is embedded with a native PDF iframe in Compare mode.

## Review text format

Each file can contain, in order:

1. **Optional summary** — free text at the very top, followed by a line containing only `---`. It is rendered as the “Reviewer’s summary” block.
2. **Optional `INSTRUCTIONS:` block** — rendered as an instruction callout.
3. **Sections** — all-caps lines such as `OVERALL`, `BUSINESS MODEL`, `MARKET ANALYSIS`.
4. **Numbered questions** — `1. …`, `2. …`, etc., followed by an answer.

The parser accepts answers in three shapes:

- a blank line after the question, then the answer;
- an `Answer:` prefix;
- an answer on the line immediately after a question ending in `?` (used by Aksel, Alexander, and Viktor).

The “line ends with `?`” check separates wrapped questions from inline answers. If adding a new format, prefer explicit `Answer:` markers or blank lines. Verify the parsed answer count after editing.

Each round is expected to contain the standard 15 review questions. Missing answers are shown as “No answer written.” **Do not invent or copy an answer** — content is the reviewers' source material.

## Parser and generator internals

`build_page.py` contains:

- `discover_rounds()` — scans `reviews/*/` and `*.txt`; finds `report.pdf`; assigns display names and ASCII slugs.
- `read_lines()`, `is_rule()`, `is_section()`, `parse()` — line-based parser for summaries, instructions, sections, questions and answers.
- `review_body()` — used for duplicate detection; compares question/answer bodies only.
- `render_doc()` — document header, question cards, completion controls, summary and sections.
- `render_toc()` — per-reviewer section navigation.
- `main()` — builds all rounds/documents into `index.html`.

Slugs are normalized to ASCII (`ö` → `o`) via `unicodedata`, so `alexander-sörensen-ristinmaa.txt` has slug `draft-1-alexander-sorensen-ristinmaa`. Slugs are stable IDs used in browser storage; renaming a review file changes its slug and resets its local completion state.

## Site behavior

- **Round row** at the top; reviewer tabs are grouped under the active round. A round switcher appears automatically when a second round exists.
- **Read / Compare toggle:** Compare (default on desktop) shows the PDF left and the selected review right; Read restores the normal sidebar layout. Mobile defaults to Read and stacks Compare vertically.
- **Question cards are clickable.** Clicking anywhere on a card toggles it as handled; the hint reads “Click to complete” and changes to a green “Completed” pill. The whole card turns green. Text selection is guarded so selecting answer text doesn’t toggle the card.
- **Per-question state** is stored in `localStorage` under `etsf25-question-handled-v1`, as a JSON object keyed by `<doc-slug>|<question-number>`. The legacy `etsf25-feedback-complete-v1` key is ignored.
- A review becomes **complete automatically** when all its questions are handled. The header shows `n / 15 handled` → `Complete`; the tab gets a ✓; the round shows `x / N complete`.
- **Celebrations:** completing a review launches a small confetti rain; completing every review in the round launches a larger one. Card/hint/status animations and short haptics accompany completion. All motion and confetti are skipped when `prefers-reduced-motion: reduce` is set.
- **Search:** `/` focuses, `Esc` clears; search filters the active review only.
- **Print / PDF:** prints the active review; split PDF and controls are hidden.
- **PDF pane:** native browser PDF viewer. A blank/black iframe in headless screenshots is often a headless limitation, not necessarily a page bug; use the “Open PDF” link to verify the file. Never replace the PDF file without checking with the user.

## Design conventions

- Editorial, warm paper theme. Key colors: paper `#f2ecdf`, ink `#201c16`, rust accent `#a63f27`, gold `#c2954f`, completion green `#3e6b50`.
- Fonts are local stacks (IBM Plex Serif/Sans/Mono with fallbacks). Do not add external font/CDN dependencies.
- The shell scales up to ~1880px; split view uses most of the viewport. Keep the layout responsive between FHD and UHD. Avoid regressions to narrow fixed widths.
- Keep the site self-contained and offline-capable apart from the PDF; no frameworks, bundlers, analytics, or network calls.
- Preserve the editorial look and existing interaction language (“Read / Compare”, “Handled”, “Completed”).

## Deployment workflow

GitHub Pages is configured for **`main` / root** and the custom domain `feedback.memagu.com`.

```sh
python3 build_page.py
git add -A
git commit -m "…"
git push origin main
```

Pages rebuilds automatically. If relevant, check the latest build:

```sh
gh api repos/memagu/tmp-etsf25-feedback/pages/builds/latest --jq .status
```

Do not rewrite history or force-push on `main`; do not remove or overwrite `CNAME`.

## Current caveats (as of 19 Nov 2026)

- Maxwell Kav's Q15 is missing in `maxwell-kav.txt`; the site correctly shows “No answer written.” Do not fabricate it.
- All current reviews are distinct; duplicate detection produced no warnings after the latest content fix.
- Some reviewer text is Swedish; keep source language and characters intact (files are UTF-8, often with a BOM/CRLF).
- The live site and `index.html` must be rebuilt together after any content or generator change.
- Browser completion state is local to each browser/device. There is no shared completion state.
