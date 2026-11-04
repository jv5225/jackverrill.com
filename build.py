import datetime
import hashlib
import json
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
SITE_URL = "https://jackverrill.com"
HOME_TITLE = "Jack Verrill — Writing on Politics, Technology & National Security"
CATEGORY_ORDER = ["On AI", "On Foreign Policy", "On Electoral Politics", "On Free Speech", "On Everything Else"]
ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
CATEGORIES_NO_SUMMARY = {"on-everything-else"}
CONTACT_PILLS = (
    '<div class="pills">'
    '<a class="pill" href="mailto:jverrill5225@outlook.com">Email</a>'
    '<a class="pill" href="https://x.com/jack_verri11" target="_blank" rel="noopener">X @jack_verri11</a>'
    "</div>"
)

PERSON_LD = {
    "@context": "https://schema.org",
    "@type": "Person",
    "name": SITE_NAME,
    "url": SITE_URL + "/",
    "jobTitle": "Writer",
    "description": (
        "LSE and University of Michigan, writing about politics, emerging "
        "technology, national security, and how it all comes together."
    ),
    "alumniOf": [
        "The London School of Economics and Political Science",
        "University of Michigan",
    ],
    "sameAs": [
        "https://x.com/jack_verri11",
        "https://www.linkedin.com/in/jackverrill/",
    ],
}

EPIGRAPHS = {
    "On AI": (
        "How much of what then seemed so wonderful and unattainable has "
        "become insignificant, and what there was then is now forever "
        "unattainable.",
        "Leo Tolstoy, Anna Karenina",
    ),
    "On Foreign Policy": (
        "It seems to me it’s always the evil we refuse to see that does "
        "us the greatest harm.",
        "Robert Baer",
    ),
    "On Electoral Politics": (
        "Kürti had believed in politics, and politics had deceived him, "
        "the way politics deceives everyone.",
        "Imre Kertész",
    ),
    "On Free Speech": None,
    "On Everything Else": None,
}

PUBLICATIONS = {
    "bostonglobe.com": "The Boston Globe",
    "dailycaller.com": "The Daily Caller",
    "michigandaily.com": "The Michigan Daily",
    "spectator.org": "The American Spectator",
    "dcjournal.com": "DC Journal",
    "washingtonexaminer.com": "Washington Examiner",
    "counterpunch.org": "CounterPunch",
    "effort.news": "Effort.News",
    "pivotbyyv.substack.com": "Pivot",
    "midwesterncitizen.substack.com": "Midwestern Citizen",
}


def slugify(stem: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", stem.lower()).strip("-")


def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()


def publication_for(url: str) -> str:
    for domain, name in PUBLICATIONS.items():
        if domain in url:
            return name
    return ""


def format_date(date) -> str:
    if not date:
        return ""
    if hasattr(date, "strftime"):
        return date.strftime("%B %Y")
    try:
        d = datetime.date.fromisoformat(str(date))
        return d.strftime("%B %Y")
    except Exception:
        return str(date)


def clean_summary(html_summary: str) -> str:
    text = re.sub(r"<[^>]+>", "", html_summary)
    for ch in ["“", "”", "‘", "’"]:
        text = text.replace(ch, "")
    return text.strip().strip('"').strip("'").strip()


def article_ld(piece, page_url):
    data = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": piece["title"],
        "url": page_url,
        "author": {"@type": "Person", "name": SITE_NAME, "url": SITE_URL + "/"},
        "mainEntityOfPage": page_url,
    }
    if piece["date"]:
        data["datePublished"] = str(piece["date"])
    if piece["summary"]:
        data["description"] = strip_tags(piece["summary"])
    if piece["external_url"]:
        data["isBasedOn"] = piece["external_url"]
    if piece["publication"]:
        data["publisher"] = {"@type": "Organization", "name": piece["publication"]}
    return json.dumps(data, ensure_ascii=False)


def piece_item_html(p: dict, show_summary: bool = True) -> str:
    href = p["external_url"] or f'/{p["slug"]}.html'
    target = ' target="_blank" rel="noopener"' if p["external_url"] else ""
    date_str = format_date(p["date"])
    meta_parts = []
    if p["publication"]:
        meta_parts.append(f'<em>{p["publication"]}</em>')
    if date_str:
        meta_parts.append(date_str)
    meta_html = ", ".join(meta_parts)
    summary_html = ""
    if show_summary and p["summary"]:
        clean = clean_summary(p["summary"])
        if clean:
            summary_html = f'<p class="piece-summary">{clean}</p>'
    return (
        f'<a class="piece-item" href="{href}"{target}>'
        f'<span class="piece-title">{p["title"]}</span>'
        + (f'<span class="piece-meta">{meta_html}</span>' if meta_html else "")
        + summary_html
        + "</a>"
    )


def piece_group_html(pieces: list, label=None, show_summary: bool = True) -> str:
    items = "".join(f"<li>{piece_item_html(p, show_summary)}</li>" for p in pieces)
    label_html = f'<h2 class="group-label">{label}</h2>' if label else ""
    return (
        '<div class="piece-group">'
        + label_html
        + f'<ul class="piece-list-new">{items}</ul>'
        + "</div>"
    )


def main():
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir()
    (BUILD_DIR / "category").mkdir()
    shutil.copy(ROOT / "assets" / "style.css", BUILD_DIR / "style.css")
    shutil.copy(ROOT / "assets" / "about-photo.jpg", BUILD_DIR / "about-photo.jpg")

    env = Environment(loader=FileSystemLoader(ROOT / "templates"))
    css_bytes = (ROOT / "assets" / "style.css").read_bytes()
    env.globals["asset_version"] = hashlib.md5(css_bytes).hexdigest()[:10]
    photo_bytes = (ROOT / "assets" / "about-photo.jpg").read_bytes()
    photo_version = hashlib.md5(photo_bytes).hexdigest()[:10]
    env.globals["photo_version"] = photo_version

    from PIL import Image

    with Image.open(ROOT / "assets" / "about-photo.jpg") as im:
        im.save(BUILD_DIR / "about-photo.webp", "WEBP", quality=82)

    PERSON_LD["image"] = f"{SITE_URL}/about-photo.jpg?v={photo_version}"
    template = env.get_template("base.html")
    year = datetime.date.today().year

    categories = [{"title": c, "slug": slugify(c)} for c in CATEGORY_ORDER]

    # --- Load all pieces ---
    pieces = []
    for md_path in sorted(WRITING_DIR.glob("*.md")):
        post = frontmatter.load(md_path)
        title = post.get("title", md_path.stem)
        date = post.get("date", "")
        summary = post.get("summary", "")
        category = post.get("category", "")
        external_url = post.get("external_url", "")
        featured = bool(post.get("featured", False))
        publication = post.get("publication", "") or publication_for(external_url)
        piece_type = post.get("type", "article")
        slug = slugify(md_path.stem)
        html_body = markdown.markdown(post.content, extensions=["extra"])

        piece = {
            "title": title,
            "date": date,
            "type": piece_type,
            "summary": summary,
            "slug": slug,
            "category": category,
            "external_url": external_url,
            "featured": featured,
            "publication": publication,
        }
        pieces.append(piece)

        # Individual piece page
        date_str = format_date(date)
        meta_parts = []
        if publication:
            meta_parts.append(f'<em>{publication}</em>')
        if date_str:
            meta_parts.append(date_str)
        meta_html = ", ".join(meta_parts)
        piece_url = f"{SITE_URL}/{slug}.html"
        page_html = template.render(
            title=title,
            full_title=f"{title} — {SITE_NAME}",
            site_name=SITE_NAME,
            root="/",
            year=year,
            categories=categories,
            description=strip_tags(summary),
            page_url=piece_url,
            og_type="article",
            json_ld=article_ld(piece, piece_url),
            content=(
                "<main>"
                f"<h1>{title}</h1>"
                + (f'<p class="piece-meta">{meta_html}</p>' if meta_html else "")
                + (f'<a class="category-tag" href="/category/{slugify(category)}.html">{category}</a>' if category else "")
                + html_body
                + "</main>"
            ),
        )
        (BUILD_DIR / f"{slug}.html").write_text(page_html)

    pieces.sort(key=lambda p: str(p["date"]), reverse=True)

    # --- Category pages ---
    for idx, cat in enumerate(categories):
        roman = ROMAN[idx] if idx < len(ROMAN) else str(idx + 1)
        cat_pieces = [p for p in pieces if slugify(p["category"]) == cat["slug"]]
        no_summary = cat["slug"] in CATEGORIES_NO_SUMMARY

        essays = [p for p in cat_pieces if p["type"] == "essay"]
        articles = [p for p in cat_pieces if p["type"] != "essay"]

        if essays:
            pieces_html = (
                piece_group_html(articles, "Articles", not no_summary)
                + piece_group_html(essays, "Essays", not no_summary)
            )
        else:
            pieces_html = piece_group_html(cat_pieces, None, not no_summary)

        # Epigraph
        epigraph_html = ""
        epigraph = EPIGRAPHS.get(cat["title"])
        if epigraph:
            quote, citation = epigraph
            epigraph_html = (
                '<blockquote class="epigraph">'
                f'“{quote}”'
                f'<cite class="epigraph-cite">— {citation}</cite>'
                "</blockquote>"
            )

        # Other topics
        other_cats = [c for c in categories if c["slug"] != cat["slug"]]
        other_links = "".join(
            f'<a href="/category/{c["slug"]}.html">{c["title"]}</a>'
            for c in other_cats
        )

        cat_content = (
            '<div class="page page--topic">'
            '<div class="top-bar">'
            '<a class="site-name-link" href="/index.html">Jack Verrill</a>'
            + CONTACT_PILLS
            + "</div>"
            '<div class="cat-heading">'
            f'<span class="roman-label">{roman}</span>'
            f'<h1 class="cat-title">{cat["title"]}</h1>'
            + epigraph_html
            + "</div>"
            + f'<div class="pieces">{pieces_html}</div>'
            + '<div class="other-topics">'
            + '<span class="other-label">Other topics</span>'
            + f'<div class="other-links">{other_links}</div>'
            + "</div>"
            + "</div>"
        )

        cat_html = template.render(
            title=cat["title"],
            full_title=f"{cat['title']} — Writing by {SITE_NAME}",
            site_name=SITE_NAME,
            root="/",
            year=year,
            categories=categories,
            description=f"{cat['title']}: writing by {SITE_NAME}.",
            page_url=f"{SITE_URL}/category/{cat['slug']}.html",
            content=cat_content,
        )
        (BUILD_DIR / "category" / f"{cat['slug']}.html").write_text(cat_html)

    # --- Homepage ---
    cat_counts = {
        cat["slug"]: sum(1 for p in pieces if slugify(p["category"]) == cat["slug"])
        for cat in categories
    }

    topic_rows_html = ""
    for idx, cat in enumerate(categories):
        roman = ROMAN[idx] if idx < len(ROMAN) else str(idx + 1)
        count = cat_counts[cat["slug"]]
        topic_rows_html += (
            f'<li><a href="/category/{cat["slug"]}.html">'
            f'<span class="roman">{roman}</span>'
            f'<span class="topic-name">{cat["title"]}</span>'
            f'<span class="topic-count">{count}</span>'
            "</a></li>"
        )

    featured = next((p for p in pieces if p["featured"]), pieces[0] if pieces else None)
    feat_html = ""
    if featured:
        feat_href = featured["external_url"] or f'/{featured["slug"]}.html'
        feat_target = ' target="_blank" rel="noopener"' if featured["external_url"] else ""
        feat_date_str = format_date(featured["date"])
        feat_meta_parts = []
        if featured["publication"]:
            feat_meta_parts.append(f'<em>{featured["publication"]}</em>')
        if feat_date_str:
            feat_meta_parts.append(feat_date_str)
        feat_meta_html = ", ".join(feat_meta_parts)
        feat_html = (
            '<div class="featured-section">'
            '<h2 class="section-head">Featured</h2>'
            f'<a class="feat-link" href="{feat_href}"{feat_target}>{featured["title"]}</a>'
            + (f'<p class="feat-meta">{feat_meta_html}</p>' if feat_meta_html else "")
            + "</div>"
        )

    photo_html = (
        '<picture class="photo-wrap">'
        f'<source srcset="/about-photo.webp?v={photo_version}" type="image/webp">'
        f'<img class="photo" src="/about-photo.jpg?v={photo_version}" '
        'width="240" height="240" loading="eager" decoding="async" alt="Jack Verrill">'
        "</picture>"
    )

    # --- Reading page ---
    READING = [
        ("Fiction", [
            ("Anna Karenina", "Leo Tolstoy"),
            ("The Great Gatsby", "F. Scott Fitzgerald"),
            ("For Whom the Bell Tolls", "Ernest Hemingway"),
            ("The Sun Also Rises", "Ernest Hemingway"),
            ("Old Man and the Sea", "Ernest Hemingway"),
            ("A Farewell to Arms", "Ernest Hemingway"),
            ("A Moveable Feast", "Ernest Hemingway"),
            ("Killer Angels", "Michael Shaara"),
            ("The Things They Carried", "Tim O’Brien"),
        ]),
        ("Philosophy", [
            ("The Republic", "Plato"),
            ("Nicomachean Ethics", "Aristotle"),
            ("Beyond Good and Evil", "Friedrich Nietzsche"),
            ("The Prince", "Niccolò Machiavelli"),
            ("Violence and the Sacred", "René Girard"),
        ]),
        ("Essays", [
            ("The Straussian Moment", "Peter Thiel"),
            ("Three Waves of Modernity", "Leo Strauss"),
            ("Nuclear Peace as the Mock Version of the Gospel", "René Girard"),
            ("The Cardamom Game", "Will Manidis"),
            ("Nobody Walks to Canterbury", "Will Manidis"),
            ("The Pyramid and the Tomb", "Will Manidis"),
            ("The Great Zombification", "Owen Yingling"),
            ("The League of Extraordinary Gentlemen – Tucker Carlson", "Tucker Carlson"),
            ("Closure of the Internet", "Archtotherium"),
        ]),
        ("Nonfiction", [
            ("Too Big to Fail", "Andrew Ross Sorkin"),
            ("Against the Machine", "Paul Kingsnorth"),
            ("Rise and Kill First", "Ronen Bergman"),
            ("The Creature from Jekyll Island", "G. Edward Griffin"),
            ("Four", "Scott Galloway"),
            ("The Contrarian", "Max Chafkin"),
            ("Philosopher in the Valley", "Michael Steinberger"),
            ("The Power of Myth", "Joseph Campbell"),
            ("Camelot’s Court", "Robert Dallek"),
            ("An Unfinished Life", "Robert Dallek"),
            ("Greenlights", "Matthew McConaughey"),
            ("Man’s Search for Meaning", "Viktor Frankl"),
            ("See No Evil", "Robert Baer"),
            ("Pilgrim’s Way", "John Buchan"),
        ]),
    ]

    sections_html = ""
    for section_title, books in READING:
        items = "".join(
            f'<li><span class="reading-title">{title}</span>'
            f'<span class="reading-author">{author}</span></li>'
            for title, author in books
        )
        sections_html += (
            f'<div class="reading-section">'
            f'<h2 class="reading-head">{section_title}</h2>'
            f'<ul class="reading-list">{items}</ul>'
            f'</div>'
        )

    reading_content = (
        '<div class="page page--topic">'
        '<div class="top-bar">'
        '<a class="site-name-link" href="/index.html">Jack Verrill</a>'
        + CONTACT_PILLS
        + "</div>"
        '<div class="cat-heading">'
        '<h1 class="cat-title" style="font-size:32px">Some of the stuff I’ve been reading</h1>'
        '<p style="font-style:italic;color:#76716A;font-size:16px">in no particular order</p>'
        "</div>"
        f'<div class="reading-sections">{sections_html}</div>'
        "</div>"
    )
    reading_html = template.render(
        title="Reading",
        full_title=f"Reading — {SITE_NAME}",
        site_name=SITE_NAME,
        root="/",
        year=year,
        categories=categories,
        description=f"Books and essays {SITE_NAME} has been reading.",
        page_url=f"{SITE_URL}/reading.html",
        content=reading_content,
    )
    (BUILD_DIR / "reading.html").write_text(reading_html)

    home_content = (
        '<div class="page page--home">'
        '<div class="intro">'
        + photo_html
        + '<div class="name-row">'
        '<h1 class="site-title">Jack Verrill</h1>'
        + CONTACT_PILLS
        + "</div>"
        "<p>Freelance writer thinking a lot about technology, philosophy, and politics.</p>"
        "</div>"
        + feat_html
        + '<div class="by-topic">'
        '<h2 class="section-head">By topic</h2>'
        f'<ul class="topic-list">{topic_rows_html}</ul>'
        "</div>"
        '<div class="reading-link">'
        '<a href="/reading.html">Some of the stuff I’ve been reading</a>'
        "</div>"
        "</div>"
    )

    index_html = template.render(
        title="Home",
        full_title=HOME_TITLE,
        site_name=SITE_NAME,
        root="/",
        year=year,
        categories=categories,
        description=(
            "Jack Verrill — freelance writer on AI, philosophy, politics, and national security."
        ),
        page_url=f"{SITE_URL}/",
        json_ld=json.dumps(PERSON_LD, ensure_ascii=False),
        content=home_content,
    )
    (BUILD_DIR / "index.html").write_text(index_html)

    # --- sitemap.xml ---
    today = datetime.date.today().isoformat()
    urls = [(f"{SITE_URL}/", today, "1.0")]
    for cat in categories:
        urls.append((f"{SITE_URL}/category/{cat['slug']}.html", today, "0.8"))
    for p in pieces:
        lastmod = str(p["date"]) if p["date"] else today
        urls.append((f"{SITE_URL}/{p['slug']}.html", lastmod, "0.7"))

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for loc, lastmod, priority in urls:
        sitemap.append(
            f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod>"
            f"<priority>{priority}</priority></url>"
        )
    sitemap.append("</urlset>")
    (BUILD_DIR / "sitemap.xml").write_text("\n".join(sitemap) + "\n")

    # --- robots.txt ---
    (BUILD_DIR / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: " + SITE_URL + "/sitemap.xml\n"
    )

    print(f"Built {len(pieces)} piece(s) into {BUILD_DIR}")


if __name__ == "__main__":
    main()
