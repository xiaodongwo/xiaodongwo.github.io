# Xiaodong Wang's personal website

Website: https://xiaodongwo.github.io/

A minimal academic website with Home, a PDF CV, Papers, and Blogs. Blogs contains Magic, Movie, and Thoughts. Thoughts has two selectable categories: **Life Thoughts** and **Technical Thoughts**. Each category has its own URL and works without JavaScript.

## Build locally

Requires Python 3.12 or later.

```sh
python -m pip install -r requirements.txt
python build.py
python check_site.py
python -m http.server 8765 --directory dist
```

Open http://localhost:8765/. Do not open HTML files directly; links use site-root paths.

## Editing

- Biography and profile links: `content/profile.json`
- Papers: `content/papers.json`; homepage selection: `content/home-selection.json`
- Talks and recordings: `content/talks.json`
- Blog posts: `content/posts/*.md`
- Magic videos and captions: `static/assets/video/magic/` and `content/magic-videos.json`
- PDF CV: `static/assets/pdf/CV_Xiaodong_Wang_Academic.pdf`
- Layout and styles: `build.py`, `static/styles.css`, `static/app.js`

Thoughts posts use `category: Thoughts` and either `topic: Life Thoughts` or `topic: Technical Thoughts` in their YAML frontmatter. Other categories are `Magic` and `Movie`. Set `draft: true` to exclude a post. Use a unique lowercase, hyphenated `slug`.

Generated files are in `dist/` and are not committed to `main`. Build into a fresh output directory when removing or renaming pages; GitHub Actions always builds from a clean checkout.

## Deployment and backup

Pushing to `main` runs the build, checks internal links and assets, and publishes `dist/` to the existing `gh-pages` branch. GitHub Pages should use **Deploy from a branch → gh-pages → /(root)**. The public address stays https://xiaodongwo.github.io/.

The original al-folio site remains in Git history at `79cb72ce61d487641297ba1411c6f570c6364d32` and in the backup branch `codex/original-site-2026-10-22`. Deployment preserves branch history and does not force-push.

The new layout was independently implemented, with visual references to [Keunhong Park](https://keunhong.com/) and [Jason Wei](https://www.jasonwei.net/). The original site's license is retained in `LICENSE`. Bundled fonts and MathJax retain their license files in their asset folders. Photos, papers, videos, and personal writing remain their respective authors' content.
