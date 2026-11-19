# ETSF25 peer reviews

A single-page, self-contained reading edition of the peer reviews for the ETSF25 project draft. Built as a static site with no dependencies or build step required to serve it.

**Live site:** <https://feedback.memagu.com/>

**Local preview:** run `python3 -m http.server 8080` and open <http://localhost:8080/>.

## What’s inside

| File | Purpose |
| --- | --- |
| `index.html` | The generated site — complete, self-contained, and ready to serve |
| `favicon.svg` | Site icon |
| `build_page.py` | Generator that turns the review files into `index.html` |
| `reviews/draft-1/report.pdf` | The reviewed draft, shown beside the comments |
| `reviews/draft-1/aksel-sjögärd.txt` | Peer review by Aksel Sjögärd |
| `reviews/draft-1/alexander-sörensen-ristinmaa.txt` | Peer review by Alexander Sörensen Ristinmaa |
| `reviews/draft-1/johannes-persson.txt` | Peer review by Johannes Persson |
| `reviews/draft-1/maxwell-kav.txt` | Peer review by Maxwell Kav |
| `reviews/draft-1/valdemar-rasmusson.txt` | Peer review by Valdemar Rasmusson |
| `reviews/draft-1/viktor-lindström.txt` | Peer review by Viktor Lindström |
| `AGENTS.md` | Repository context and conventions for coding agents |
| `.nojekyll` | Tells GitHub Pages to serve the files as-is |

The page includes tabs for each file, section navigation, full-text search (`/`), a reading-progress bar, and print / PDF styling. The reviewed draft is displayed in a split view beside the comments. Click anywhere on a question card (or the “Click to complete” hint) to mark it handled; it gets a green tint, and clicking again reopens it. A review is marked complete automatically once all its questions are handled. Per-question state is stored in the browser (`localStorage`) on that device, with a per-round progress count.

Review rounds live in subdirectories of `reviews/` (for example `reviews/draft-1/`, `reviews/draft-2/`). Each round folder contains the reviewed draft as `report.pdf` plus one `.txt` file per reviewer. Each `.txt` file becomes a reviewer tab, named from its filename and ordered alphabetically. The active round is shown above the reviewer tabs; when more than one round exists, the round buttons switch between them.

## Regenerate the page

After editing a review file, or adding a new round:

```sh
python3 build_page.py
```

If two reviews in the same round have identical answers, the build prints a warning naming both files so accidental copies can be caught before publishing.

The script uses only the Python standard library. The generated `index.html` embeds all CSS and JavaScript, so it also works when opened directly from disk.

## Deployment

The site is published from the **`main`** branch (`/` root) with GitHub Pages at:

**https://feedback.memagu.com/**

The custom domain is configured through `CNAME` (`feedback.memagu.com`). After changing a review or the generator:

```sh
python3 build_page.py
git add -A
git commit -m "Update reviews"
git push origin main
```

GitHub Pages rebuilds automatically. No GitHub Actions workflow is required, and `index.html` is committed and ready to serve.

## Notes

- Each review opens with a short overall comment, separated from the numbered criteria by `---`. The generator renders that opening as the summary block at the top of the document.
- All document text is presented unchanged. Only the layout, typography, navigation, and local completion tracking were added.
- Completing a review triggers a small confetti celebration; completing every review in the round triggers a larger one. Confetti is skipped when the browser requests reduced motion.
- Question handling and review completion are per browser and per device — there is no backend, account, or shared state.
- To add another round, create `reviews/draft-2/`, add `report.pdf` and the reviewer `.txt` files, then run `python3 build_page.py`.
