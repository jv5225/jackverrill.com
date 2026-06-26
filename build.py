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
CATEGORY_ORDER = ["On AI", "On Foreign Policy", "On Electoral Politics"]


def slugify(stem: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", stem.lower()).strip("-")


def piece_list_html(pieces, heading):
    html = f"<h1>{heading}</h1><ul class=\"piece-list\">"
    for p in pieces:
        href = p["external_url"] or f'/{p["slug"]}.html'
        target = ' target="_blank" rel="noopener"' if p["external_url"] else ""
        html += (
            "<li>"
            f'<a class="piece-title" href="{href}"{target}>{p["title"]}</a>'
            + (f'<span class="piece-meta">{p["date"]}</span>' if p["date"] else "")
            + (f"<p>{p['summary']}</p>" if p["summary"] else "")
            + "</li>"
        )
    html += "</ul>"
    return html


def main():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir()
    (BUILD_DIR / "category").mkdir()
    shutil.copy(ROOT / "assets" / "style.css", BUILD_DIR / "style.css")
    shutil.copy(ROOT / "assets" / "about-photo.jpg", BUILD_DIR / "about-photo.jpg")

    env = Environment(loader=FileSystemLoader(ROOT / "templates"))
    template = env.get_template("base.html")
    year = datetime.date.today().year

    categories = [{"title": c, "slug": slugify(c)} for c in CATEGORY_ORDER]

    pieces = []
    for md_path in sorted(WRITING_DIR.glob("*.md")):
        post = frontmatter.load(md_path)
        title = post.get("title", md_path.stem)
        date = post.get("date", "")
        summary = post.get("summary", "")
        category = post.get("category", "")
        external_url = post.get("external_url", "")
        slug = slugify(md_path.stem)
        html_body = markdown.markdown(post.content, extensions=["extra"])

        page_html = template.render(
            title=title,
            site_name=SITE_NAME,
            root="/",
            year=year,
            categories=categories,
            content=(
                f"<h1>{title}</h1>"
                + (f'<p class="piece-meta">{date}</p>' if date else "")
                + (f'<a class="category-tag" href="/category/{slugify(category)}.html">{category}</a>' if category else "")
                + html_body
            ),
        )
        (BUILD_DIR / f"{slug}.html").write_text(page_html)

        pieces.append(
            {
                "title": title,
                "date": date,
                "summary": summary,
                "slug": slug,
                "category": category,
                "external_url": external_url,
            }
        )

    pieces.sort(key=lambda p: str(p["date"]), reverse=True)

    writing_html = template.render(
        title="Writing",
        site_name=SITE_NAME,
        root="/",
        year=year,
        categories=categories,
        content=piece_list_html(pieces, "Writing"),
    )
    (BUILD_DIR / "writing.html").write_text(writing_html)

    for cat in categories:
        cat_pieces = [p for p in pieces if slugify(p["category"]) == cat["slug"]]
        cat_html = template.render(
            title=cat["title"],
            site_name=SITE_NAME,
            root="/",
            year=year,
            categories=categories,
            content=piece_list_html(cat_pieces, cat["title"]),
        )
        (BUILD_DIR / "category" / f"{cat['slug']}.html").write_text(cat_html)

    about_content = (
        '<img class="about-photo" src="/about-photo.jpg" alt="Jack Verrill">'
        "<p>I am a student at the University of Michigan and London School of "
        "Economics, passionate about the intersection of politics and emerging "
        "technology. I've written op-eds and long-form essays about those "
        "things, and more, in publications including the <em>Boston Globe</em>, "
        "<em>Daily Caller</em>, and <em>Midwestern Citizen</em>. You can find "
        "it all on this website.</p>"
        '<p class="social-links">'
        '<a href="https://twitter.com/jack_verri11" target="_blank" rel="noopener">Twitter</a>'
        ' · <a href="https://www.linkedin.com/in/jackverrill/" target="_blank" rel="noopener">LinkedIn</a>'
        ' · <a href="mailto:jverrill5225@outlook.com">jverrill5225@outlook.com</a>'
        "</p>"
        '<h2>Latest tweet</h2>'
        '<a class="twitter-timeline" data-tweet-limit="1" data-chrome="noheader nofooter noborders transparent" '
        'href="https://twitter.com/jack_verri11?ref_src=twsrc%5Etfw">Tweets by jack_verri11</a>'
        '<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>'
    )
    index_html = template.render(
        title="Home",
        site_name=SITE_NAME,
        root="/",
        year=year,
        categories=categories,
        content=about_content,
    )
    (BUILD_DIR / "index.html").write_text(index_html)

    print(f"Built {len(pieces)} piece(s) into {BUILD_DIR}")


if __name__ == "__main__":
    main()
