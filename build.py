import datetime
import re
import shutil
from pathlib import Path

import frontmatter
import markdown
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).parent
WRITING_DIR = ROOT / "writing"
BUILD_DIR = ROOT / "build"
SITE_NAME = "Jack Verrill"


def slugify(stem: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", stem.lower()).strip("-")


def main():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir()
    shutil.copy(ROOT / "assets" / "style.css", BUILD_DIR / "style.css")

    env = Environment(loader=FileSystemLoader(ROOT / "templates"))
    template = env.get_template("base.html")
    year = datetime.date.today().year

    pieces = []
    for md_path in sorted(WRITING_DIR.glob("*.md")):
        post = frontmatter.load(md_path)
        title = post.get("title", md_path.stem)
        date = post.get("date", "")
        summary = post.get("summary", "")
        slug = slugify(md_path.stem)
        html_body = markdown.markdown(post.content, extensions=["extra"])

        page_html = template.render(
            title=title,
            site_name=SITE_NAME,
            root="",
            year=year,
            content=(
                f"<h1>{title}</h1>"
                + (f'<p class="piece-meta">{date}</p>' if date else "")
                + html_body
            ),
        )
        (BUILD_DIR / f"{slug}.html").write_text(page_html)

        pieces.append({"title": title, "date": date, "summary": summary, "slug": slug})

    pieces.sort(key=lambda p: str(p["date"]), reverse=True)

    list_html = "<h1>Writing</h1><ul class=\"piece-list\">"
    for p in pieces:
        list_html += (
            "<li>"
            f'<a class="piece-title" href="{p["slug"]}.html">{p["title"]}</a>'
            + (f'<span class="piece-meta">{p["date"]}</span>' if p["date"] else "")
            + (f"<p>{p['summary']}</p>" if p["summary"] else "")
            + "</li>"
        )
    list_html += "</ul>"

    index_html = template.render(
        title="Home", site_name=SITE_NAME, root="", year=year, content=list_html
    )
    (BUILD_DIR / "index.html").write_text(index_html)

    print(f"Built {len(pieces)} piece(s) into {BUILD_DIR}")


if __name__ == "__main__":
    main()
