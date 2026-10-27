#!/usr/bin/env python3
"""Build the study site.

Usage:  python build.py          (needs:  pip install markdown pygments)

Reads  content/<slug>.md  (or <slug>.html for hand-written pages)
Writes <slug>.html + style.css (pygments colours included) in this folder.

To add a page: create content/<slug>.md, then add it to PAGES below.

Markdown extras supported in content files:
  title: Page title          first line of a page (sets the <title> and the page heading)
  {{code FILE START-END hl=45,47}}
                             show lines START-END of examples/FILE with their real
                             line numbers; hl= highlights absolute line numbers
  [[r0]] [[r1]] [[r2]] [[r3]] [[rx]]
                             coloured rank chips: rank 0, 1, 2, 3, and "other ranks"
  ::: q ... --- ... :::      a practice question: text above the ---, answer below it
"""
import html
import pathlib
import re

import markdown
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import CLexer, TextLexer

ROOT = pathlib.Path(__file__).parent
CONTENT = ROOT / "content"
EXAMPLES = ROOT / "examples"

SITE_NAME = "CIS*3090 midterm"

# (slug, nav label, group)   -- order here is the order in the sidebar
PAGES = [
    ("index", "Start here", None),
    ("concepts", "Big ideas", "Notes"),
    ("sendrecv", "Send and receive", "Notes"),
    ("collectives", "Collective communication", "Notes"),
    ("trapezoid", "The trapezoidal rule", "Notes"),
    ("hello", "mpi_hello.c", "Code walkthroughs"),
    ("hello2", "mpi_hello2.c", "Code walkthroughs"),
    ("trap_sendrecv", "mpi_SendRec.c", "Code walkthroughs"),
    ("trap_bcast", "mpi_Bcast.c", "Code walkthroughs"),
    ("trace", "Trapezoid trace", "Practice"),
    ("practice", "Code-reading questions", "Practice"),
    ("reference", "Cheat sheet", "Reference"),
]

CHIPS = {
    "r0": ("r0", "rank 0"),
    "r1": ("r1", "rank 1"),
    "r2": ("r2", "rank 2"),
    "r3": ("r3", "rank 3"),
    "rx": ("rx", "other ranks"),
}


def md_engine():
    return markdown.Markdown(
        extensions=["fenced_code", "codehilite", "tables", "sane_lists"],
        extension_configs={
            "codehilite": {"guess_lang": False, "css_class": "highlight", "use_pygments": True}
        },
    )


def render_code(spec):
    """{{code FILE START-END hl=1,2}} -> highlighted table with real line numbers."""
    m = re.match(r"\{\{code\s+(\S+)\s+(\d+)-(\d+)(?:\s+hl=([\d,]+))?\s*\}\}", spec)
    if not m:
        raise SystemExit(f"bad code directive: {spec}")
    fname, start, end = m.group(1), int(m.group(2)), int(m.group(3))
    hl = [int(x) for x in m.group(4).split(",")] if m.group(4) else []
    path = EXAMPLES / fname
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    snippet = "\n".join(lines[start - 1 : end]) + "\n"
    fmt = HtmlFormatter(
        linenos="table",
        linenostart=start,
        hl_lines=[h - start + 1 for h in hl if start <= h <= end],
        cssclass="highlight",
        wrapcode=True,
    )
    body = highlight(snippet, CLexer(), fmt)
    cap = f'<div class="codecap">{html.escape(fname)}, lines {start} to {end}</div>'
    return f'<figure class="code">{cap}{body}</figure>'


def preprocess(text, stash):
    """Pull out directives so Markdown does not touch them."""

    def stash_it(markup):
        token = f"@@STASH{len(stash)}@@"
        stash.append(markup)
        return token

    # fenced code blocks (may be indented to stay inside a bullet)
    def fence(m):
        lang = m.group(2) or "text"
        indent = m.group(1)
        code = "\n".join(
            l[len(indent):] if l.startswith(indent) else l for l in m.group(3).split("\n")
        )
        lexer = CLexer() if lang == "c" else TextLexer()
        body = highlight(code + "\n", lexer, HtmlFormatter(cssclass="highlight", wrapcode=True))
        return indent + stash_it(body)

    text = re.sub(
        r"^( *)```(\w*)\n(.*?)\n\1```[ \t]*$", fence, text, flags=re.M | re.S
    )

    # code directives
    text = re.sub(
        r"^( *)(\{\{code .*?\}\})[ \t]*$",
        lambda m: m.group(1) + stash_it(render_code(m.group(2).strip())),
        text,
        flags=re.M,
    )

    # practice questions
    def q_block(m):
        body = m.group(1)
        if "\n---\n" in body:
            q, a = body.split("\n---\n", 1)
        else:
            q, a = body, "(no answer written yet)"
        qh = md_engine().convert(q.strip())
        ah = md_engine().convert(a.strip())
        markup = (
            '<section class="q"><div class="qbody">'
            + qh
            + '</div><details><summary>Show answer</summary><div class="abody">'
            + ah
            + "</div></details></section>"
        )
        return "\n" + stash_it(markup) + "\n"

    text = re.sub(r"^::: q\n(.*?)\n:::\s*$", q_block, text, flags=re.M | re.S)

    # rank chips
    def chip(m):
        cls, label = CHIPS[m.group(1)]
        return f'<span class="chip {cls}">{label}</span>'

    text = re.sub(r"\[\[(r0|r1|r2|r3|rx)\]\]", chip, text)
    return text


def postprocess(htmltext, stash):
    # stashed blocks can contain other stashed blocks (code inside a question), so repeat
    for _ in range(4):
        if "@@STASH" not in htmltext:
            break
        for i, markup in enumerate(stash):
            token = f"@@STASH{i}@@"
            htmltext = htmltext.replace(f"<p>{token}</p>", markup).replace(token, markup)
    # let wide tables scroll sideways on small screens
    htmltext = re.sub(r"(<table>.*?</table>)", r'<div class="tablewrap">\1</div>', htmltext, flags=re.S)
    return htmltext


def split_title(text, default):
    m = re.match(r"title:\s*(.+)\n", text)
    if m:
        return m.group(1).strip(), text[m.end():]
    return default, text


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | {site}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap">
<link rel="stylesheet" href="style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<nav class="side" aria-label="Pages">
<a class="brand" href="index.html">{site}</a>
{nav}
</nav>
<main id="main">
<h1>{title}</h1>
{body}
<div class="pager">{prev}{next}</div>
</main>
{script}
<script>(function(){{var n=document.querySelector("nav.side"),c=n&&n.querySelector("[aria-current]");if(n&&c&&n.scrollWidth>n.clientWidth){{n.scrollLeft=Math.max(0,c.offsetLeft-24);}}}})();</script>
</body>
</html>
"""


def build_nav(current):
    out, last_group = [], object()
    for slug, label, group in PAGES:
        if group != last_group and group:
            out.append(f'<div class="grp">{html.escape(group)}</div>')
        last_group = group
        cur = ' aria-current="page"' if slug == current else ""
        out.append(f'<a href="{slug}.html"{cur}>{html.escape(label)}</a>')
    return "\n".join(out)


def main():
    stylesheet = (ROOT / "style.base.css").read_text(encoding="utf-8")
    light = HtmlFormatter(style="default").get_style_defs(".highlight")
    dark = HtmlFormatter(style="monokai").get_style_defs(".highlight")
    # keep the page's own background/line-number colours; only token colours come from pygments
    strip = lambda css: "\n".join(
        l for l in css.splitlines() if "background" not in l.split("{")[0] and not l.startswith(".highlight .hll")
    )
    css = (
        stylesheet
        + "\n/* pygments (generated by build.py) */\n"
        + strip(light)
        + "\n@media (prefers-color-scheme: dark) {\n"
        + strip(dark)
        + "\n}\n"
    )
    (ROOT / "style.css").write_text(css, encoding="utf-8")

    for i, (slug, label, _group) in enumerate(PAGES):
        md_path, html_path = CONTENT / f"{slug}.md", CONTENT / f"{slug}.html"
        script = ""
        if md_path.exists():
            stash = []
            title, text = split_title(md_path.read_text(encoding="utf-8"), label)
            text = preprocess(text, stash)
            body = postprocess(md_engine().convert(text), stash)
        elif html_path.exists():
            title, text = split_title(html_path.read_text(encoding="utf-8"), label)
            body = text
            script = '<script src="trace.js"></script>' if slug == "trace" else ""
        else:
            print(f"skip {slug}: no content file")
            continue

        prev = nxt = ""
        if i > 0:
            ps, pl, _ = PAGES[i - 1]
            prev = f'<a class="prev" href="{ps}.html">Previous: {html.escape(pl)}</a>'
        if i < len(PAGES) - 1:
            ns, nl, _ = PAGES[i + 1]
            nxt = f'<a class="next" href="{ns}.html">Next: {html.escape(nl)}</a>'

        page = TEMPLATE.format(
            title=html.escape(title),
            site=html.escape(SITE_NAME),
            nav=build_nav(slug),
            body=body,
            prev=prev,
            next=nxt,
            script=script,
        )
        (ROOT / f"{slug}.html").write_text(page, encoding="utf-8")
        print("built", f"{slug}.html")


if __name__ == "__main__":
    main()
