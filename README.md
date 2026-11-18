# ETSF25 peer reviews

A single-page, self-contained reading edition of three plain-text peer reviews for the ETSF25 project draft. Built as a static site with no dependencies or build step required to serve it.

**Live preview:** run `python3 -m http.server 8080` and open <http://localhost:8080/>.

## What’s inside

| File | Purpose |
| --- | --- |
| `index.html` | The generated site — complete, self-contained, and ready to serve |
| `favicon.svg` | Site icon |
| `build_page.py` | Generator that turns the review files into `index.html` |
| `reviews/draft-1/report.pdf` | The reviewed draft, shown beside the comments |
| `reviews/draft-1/johannes-persson.txt` | Peer review by Johannes Persson |
| `reviews/draft-1/maxwell-kav.txt` | Peer review by Maxwell Kav |
| `reviews/draft-1/valdemar-rasmusson.txt` | Peer review by Valdemar Rasmusson |
| `.nojekyll` | Tells GitHub Pages to serve the files as-is |

The page includes tabs for each file, section navigation, full-text search (`/`), a reading-progress bar, and print / PDF styling. The reviewed draft is displayed in a split view beside the comments. Each review can be marked complete; completion is stored in the browser (`localStorage`) on that device, with a per-round progress count.

Review rounds live in subdirectories of `reviews/` (for example `reviews/draft-1/`, `reviews/draft-2/`). Each round folder contains the reviewed draft as `report.pdf` plus one `.txt` file per reviewer. Each `.txt` file becomes a reviewer tab, named from its filename and ordered alphabetically. The active round is shown above the reviewer tabs; when more than one round exists, the round buttons switch between them.

## Regenerate the page

After editing a review file, or adding a new round:

```sh
python3 build_page.py
```

If two reviews in the same round have identical answers, the build prints a warning naming both files so accidental copies can be caught before publishing.

The script uses only the Python standard library. The generated `index.html` embeds all CSS and JavaScript, so it also works when opened directly from disk.

## Publish with GitHub Pages

1. Create an empty repository on GitHub (do not initialise it with a README).
2. Connect this local repo and push:

   ```sh
   git remote add origin git@github.com:<username>/<repo>.git
   git push -u origin main
   ```

3. In the GitHub repository, open **Settings → Pages**.
4. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
5. Choose branch **`main`** and folder **`/ (root)`**, then save.

GitHub will publish the site at:

```
https://<username>.github.io/<repo>/
```

No workflow or build action is needed: `index.html` is committed and ready to serve.

## Notes

- Each review opens with a short overall comment, separated from the numbered criteria by `---`. The generator renders that opening as the summary block at the top of the document.
- All document text is presented unchanged. Only the layout, typography, navigation, and local completion tracking were added.
- Completion is per browser and per device — there is no backend, account, or shared state.
- To add another round, create `reviews/draft-2/`, add `report.pdf` and the reviewer `.txt` files, then run `python3 build_page.py`.
