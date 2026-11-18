# ETSF25 peer reviews

A single-page, self-contained reading edition of three plain-text peer reviews for the ETSF25 project draft. Built as a static site with no dependencies or build step required to serve it.

**Live preview:** run `python3 -m http.server 8080` and open <http://localhost:8080/>.

## What’s inside

| File | Purpose |
| --- | --- |
| `index.html` | The generated site — complete, self-contained, and ready to serve |
| `favicon.svg` | Site icon |
| `build_page.py` | Generator that turns `reviews/*.txt` into `index.html` |
| `reviews/johannes-persson.txt` | Peer review by Johannes Persson |
| `reviews/maxwell-kav.txt` | Peer review by Maxwell Kav |
| `reviews/valdemar-rasmusson.txt` | Peer review by Valdemar Rasmusson |
| `.nojekyll` | Tells GitHub Pages to serve the files as-is |

The page includes tabs for each file, section navigation, full-text search (`/`), a reading-progress bar, and print / PDF styling. Every `.txt` file in `reviews/` becomes a tab; the filename supplies the reviewer label, and files are ordered alphabetically.

## Regenerate the page

After editing any file in `reviews/`:

```sh
python3 build_page.py
```

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
- All document text is presented unchanged. Only the layout, typography, and navigation were added.
- To add another review, drop a new `.txt` file into `reviews/` and run `python3 build_page.py`.
