# Personal Writing Site

A minimal static site for your writing.

## Add a new piece

Create a `.md` file in `writing/` with frontmatter:

```
---
title: My Piece
date: 2026-06-26
summary: One sentence description.
---

The body of the piece, in Markdown.
```

## Build

```
source .venv/bin/activate
python3 build.py
```

This regenerates everything in `build/`.

## Preview locally

```
cd build && python3 -m http.server 8123
```

Then open http://localhost:8123.

## Publish

The `build/` folder is plain static HTML/CSS — deploy it for free with
GitHub Pages, Netlify, or Vercel (drag-and-drop the `build/` folder, or
connect the repo and set the publish directory to `build/`).
