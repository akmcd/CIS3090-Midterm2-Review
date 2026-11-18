#!/usr/bin/env python3
"""Build the study site.

    pip install -r requirements.txt
    python build.py

Writes, next to this file:
  index.html                 home page
  read.html                  every section in READ, then the cheat sheet (content/reference.md)
  code.html + CODE pages     the course programs with the rank lens and message timeline
  REF pages                  the MPI function reference
  data/short.js              short-answer prompts, from content/practice.md and practice2.md
  redirect stubs             for page names used by the first version of the site
quiz.html, short.html, flashcards.html and exam.html are hand-written and read the files in data/.

Extras you can use inside the Markdown files
  title: / source: / lead:           first lines of a file (source and lead are shown on the Read page)
  {{walk NAME}}                      code reader from content/walk/NAME.json
  {{code FILE START-END hl=1,2}}     plain listing of examples/FILE, real line numbers
  {{lab match}}  {{lab collective}}  the two interactive labs
  {{diagram memory}}                 shared vs distributed memory picture
  {{fnindex}}                        searchable list of the ::: fn entries on the reference pages
  [[r0]] [[rx]]                      small rank labels
  ::: eg Title ... :::               amber worked example
  ::: warn Title ... :::             red exam trap
  ::: note Title ... :::             blue note
  ::: run Caption ... :::            real program output (a first line "$ cmd" is styled)
  ::: q ... --- ... :::              question and answer (practice*.md, turned into short answers)
  ::: fn NAME ... :::                MPI reference entry
Blocks may be indented to sit inside a bullet. A table or block placed between two bullets folds with
the subsection above it.
"""
import html
import json
import math
import pathlib
import re

from bs4 import BeautifulSoup, NavigableString

import markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import CLexer, TextLexer

ROOT = pathlib.Path(__file__).resolve().parent
CONTENT = ROOT / "content"
WALKS = CONTENT / "walk"
EXAMPLES = ROOT / "examples"

SITE_NAME = "CIS*3090 Midterm 2 Review"
VER = "20261118a"  # bump after editing assets so browsers fetch the new files

# Read page sections: (slug, label, group). The slug is also the quiz topic key in assets/common.js.
READ = [
    ("concepts", "Distributed memory and MPI", "MPI (lectures 09 to 11)"),
    ("method", "Reading MPI code", "MPI (lectures 09 to 11)"),
    ("sendrecv", "Send and receive", "MPI (lectures 09 to 11)"),
    ("collectives", "Collective communication", "MPI (lectures 09 to 11)"),
    ("trapezoid", "The trapezoidal rule", "MPI (lectures 09 to 11)"),
    ("odd_even", "Odd-even sort with MPI", "Distributed-memory case studies (12, 13)"),
    ("heat", "Heat distribution with MPI", "Distributed-memory case studies (12, 13)"),
    ("performance", "Hardware and performance", "Performance (14)"),
    ("gpgpu", "GPGPU and Warp", "GPUs and images (15 to 17)"),
    ("imaging", "Image processing basics", "GPUs and images (15 to 17)"),
    ("filters", "Sharpening and smoothing", "GPUs and images (15 to 17)"),
]
CHEAT = "reference"  # content/reference.md becomes the cheat sheet at the end of the Read page (#cheat)

# Code pages: (slug, label, description)
CODE = [
    ("hello", "mpi_hello.c", "Every rank except 0 sends a greeting, and rank 0 receives and prints them in order."),
    ("hello2", "mpi_hello2.c", "The same idea with wildcard receives and the status object."),
    ("trap_sendrecv", "mpi_SendRec.c", "The trapezoidal rule using only MPI_Send and MPI_Recv."),
    ("trap_bcast", "mpi_Bcast.c", "The same program using MPI_Bcast and MPI_Reduce."),
    ("heat_code", "heatDiffusionMpi.c", "The heat diffusion program: halo exchange, Allreduce and Gatherv, rank by rank."),
    ("pitfalls", "Hangs and mix-ups", "Three small programs that go wrong, and how to see why."),
    ("trace", "Trapezoid trace", "Change the inputs and see which slice of the interval each rank computes."),
]

# MPI reference pages: (slug, label, description)
REF = [
    ("ref_index", "Find a function", "Look up any MPI function used in this course: what it does, its arguments, and the mistakes to avoid."),
    ("ref_start", "Setup and shutdown", "MPI_Init, MPI_Comm_size, MPI_Comm_rank, MPI_Wtime, MPI_Abort and MPI_Finalize."),
    ("ref_p2p", "Send and receive", "MPI_Send, MPI_Recv, MPI_Ssend, MPI_Sendrecv, status and wildcards."),
    ("ref_coll", "Collectives", "MPI_Bcast, MPI_Reduce, MPI_Allreduce, MPI_Scatter, MPI_Gather, MPI_Gatherv and more."),
    ("ref_types", "Datatypes and operators", "Datatypes, reduction operators, constants and common errors."),
]

# Question pages turned into short-answer prompts, with the Read section each question belongs to.
SHORT_SOURCES = [
    ("practice", ["method", "sendrecv", "sendrecv", "sendrecv", "sendrecv", "sendrecv", "sendrecv", "collectives",
                  "collectives", "collectives", "trapezoid", "collectives", "collectives", "collectives", "trapezoid", "sendrecv"]),
    ("practice2", ["odd_even"] * 4 + ["heat"] * 7 + ["performance"] * 4 + ["gpgpu"] * 3 + ["filters", "imaging", "imaging"] + ["filters"] * 4),
]

# Old page names from the first version of the site, kept working as redirects.
REDIRECTS = {s: f"read.html#{s}" for s, _l, _g in READ}
REDIRECTS.update({"reference": "read.html#cheat", "practice": "short.html", "practice2": "short.html"})

CHIPS = {
    "r0": ("r0", "rank 0"),
    "r1": ("rx", "rank 1"),
    "r2": ("rx", "rank 2"),
    "r3": ("rx", "rank 3"),
    "rx": ("rx", "other ranks"),
}


# ---------------------------------------------------------------- markdown

class SectionLabels(Treeprocessor):
    """A list item that ends in a colon and has a nested list is a section label."""

    def run(self, root):
        for li in root.iter("li"):
            sub = next((c for c in li if c.tag in ("ul", "ol")), None)
            if sub is None:
                continue
            idx = list(li).index(sub)
            before = li.text if idx == 0 else li[idx - 1].tail
            lead = "".join(li[0].itertext()) if len(li) and li[0].tag == "p" else ""
            if any(t and t.rstrip().endswith(":") for t in (before, lead)):
                li.set("class", (li.get("class", "") + " sec").strip())


class SectionLabelsExt(Extension):
    def extendMarkdown(self, md):
        md.treeprocessors.register(SectionLabels(md), "sectionlabels", 5)


def md_engine():
    return markdown.Markdown(extensions=["tables", "sane_lists", SectionLabelsExt()])


# ---------------------------------------------------------------- code

MPI_TOKEN = re.compile(r'<span class="(n|nf|nb|nl|nx|kt)">(MPI_\w+)</span>')


def hl_lines(code):
    """Highlight C and return one balanced HTML string per line."""
    out = highlight(code, CLexer(), HtmlFormatter(nowrap=True))
    out = MPI_TOKEN.sub(r'<span class="\1 mpi">\2</span>', out)
    return out.split("\n")


def code_block(code, lang):
    if lang in ("c", "cpp"):
        body = "\n".join(hl_lines(code + "\n")).rstrip("\n")
    else:
        body = html.escape(code)
    return f'<figure class="snippet"><pre><code>{body}</code></pre></figure>'


def inline(text):
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(text))


def listing_html(fname, segments, roles=None, notes=None, marks=()):
    path = EXAMPLES / fname
    if not path.exists():
        raise SystemExit(f"missing example file: {path}")
    src = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out, prev_end = [], None
    for seg in segments:
        s, e = seg["start"], seg["end"]
        if prev_end is not None and s > prev_end + 1:
            out.append(f'<div class="gap" aria-hidden="true">lines {prev_end + 1} to {s - 1} not shown</div>')
        rendered = hl_lines("\n".join(src[s - 1:e]) + "\n")
        for i, h in enumerate(rendered[: e - s + 1]):
            n = s + i
            role = (roles or {}).get(n, "all")
            has_note = bool(notes and str(n) in notes)
            btn = (
                f'<button type="button" class="notebtn" aria-expanded="false" aria-label="Show the note for line {n}" title="Note for line {n}">i</button>'
                if has_note else ""
            )
            out.append(
                f'<div class="ln{" mark" if n in marks else ""}" data-line="{n}" data-who="{role}">'
                f'<span class="no">{n}</span><code class="tx">{h or "&#8203;"}</code>{btn}</div>'
            )
            if has_note:
                out.append(f'<div class="anno" data-who="{role}"><span>{inline(notes[str(n)])}</span></div>')
        prev_end = e
    return "\n".join(out)


def render_code(spec):
    m = re.match(r"\{\{code\s+(\S+)\s+(\d+)-(\d+)(?:\s+hl=([\d,]+))?\s*\}\}", spec)
    if not m:
        raise SystemExit(f"bad code directive: {spec}")
    fname, a, b = m.group(1), int(m.group(2)), int(m.group(3))
    marks = {int(x) for x in m.group(4).split(",")} if m.group(4) else set()
    body = listing_html(fname, [{"start": a, "end": b}], marks=marks)
    return (
        f'<figure class="code"><figcaption>{html.escape(fname)}, lines {a} to {b}</figcaption>'
        f'<div class="listing static">{body}</div></figure>'
    )


def render_walk(name):
    path = WALKS / f"{name}.json"
    if not path.exists():
        raise SystemExit(f"missing walk file: {path}")
    cfg = json.loads(path.read_text(encoding="utf-8"))
    roles = {}
    for a, b, role in cfg.get("who", []):
        for n in range(a, b + 1):
            roles[n] = role
    segments = cfg.get("segments") or [{"start": cfg["start"], "end": cfg["end"]}]
    listing = listing_html(cfg["file"], segments, roles, cfg.get("notes"))
    client = {k: cfg[k] for k in ("example", "refs", "summaries", "p", "fixed_p") if k in cfg}
    data = json.dumps(client).replace("</", "<\\/")
    fixed = cfg.get("fixed_p")
    if fixed:
        pctl = f'<div class="ctl"><span class="ctl-label">Number of processes</span><output class="pval">{fixed}</output></div>'
    else:
        pctl = (
            '<div class="ctl"><span class="ctl-label" id="pl-{id}">Number of processes</span>'
            '<button type="button" class="stepper" data-act="p-" aria-label="Fewer processes">&minus;</button>'
            '<output class="pval" aria-labelledby="pl-{id}"></output>'
            '<button type="button" class="stepper" data-act="p+" aria-label="More processes">+</button></div>'
        ).replace("{id}", name)
    title = html.escape(cfg["file"])
    has_notes = bool(cfg.get("notes"))
    toggle = (
        '<label class="linenotes-toggle"><input type="checkbox" class="allnotes"> Show all line notes</label>'
        if has_notes else ""
    )
    help_ = (
        '<p class="codehelp">Press the <b>i</b> button on a line to read its note.</p>' if has_notes else ""
    )
    return f"""<section class="walk" id="walk-{name}" data-example="{html.escape(cfg['example'])}" aria-label="{title}, rank by rank">
<script type="application/json">{data}</script>
<div class="walkbar">
<div class="walkctl">{pctl}<div class="ctl"><span class="ctl-label">Show the lines run by</span><div class="ranks" role="group" aria-label="Choose a rank"></div></div></div>
<p class="summary" aria-live="polite"></p>
</div>
<div class="walkbody">
<div class="codecol">
<div class="codehead"><span class="fname">{title}</span>{toggle}</div>
{help_}
<div class="listing" role="region" aria-label="{title}" tabindex="0">
{listing}
</div>
</div>
<aside class="lanesbox" aria-label="Follow the messages">
<h3 class="lanes-title">Follow the messages</h3>
<p class="stepcaption idle" aria-live="polite"></p>
<div class="stepbar"><button type="button" data-s="prev">Back</button><button type="button" data-s="next">Next step</button><button type="button" data-s="all">Reset</button><span class="stepinfo" aria-live="polite"></span></div>
<div class="lanes"></div>
<p class="lanes-note"></p>
<details class="steplist"><summary>All steps as a list</summary><ol class="log"></ol></details>
</aside>
</div>
</section>"""


# ---------------------------------------------------------------- labs and pictures

MATCH_LAB = """<section class="lab" id="matchlab" aria-label="Send and receive matching lab">
<div class="labcols">
<fieldset class="side send"><legend>Rank 1 sends</legend>
<label>destination<select id="m-dest"><option value="0">rank 0</option><option value="2">rank 2</option><option value="3">rank 3</option></select></label>
<label>tag<input id="m-stag" type="number" min="0" value="0"></label>
<label>communicator<select id="m-scomm"><option value="world">MPI_COMM_WORLD</option><option value="other">another communicator</option></select></label>
<label>datatype<select id="m-stype"><option>MPI_INT</option><option>MPI_DOUBLE</option><option>MPI_CHAR</option></select></label>
<label>count<input id="m-scount" type="number" min="1" value="1"></label>
</fieldset>
<fieldset class="side recv"><legend>Rank 0 receives</legend>
<label>source<select id="m-src"><option value="1">rank 1</option><option value="2">rank 2</option><option value="any">MPI_ANY_SOURCE</option></select></label>
<label>tag<input id="m-rtag" type="number" min="0" value="0"></label>
<label class="chk"><input id="m-anytag" type="checkbox"> use MPI_ANY_TAG</label>
<label>communicator<select id="m-rcomm"><option value="world">MPI_COMM_WORLD</option><option value="other">another communicator</option></select></label>
<label>datatype<select id="m-rtype"><option>MPI_INT</option><option>MPI_DOUBLE</option><option>MPI_CHAR</option></select></label>
<label>count (buffer size)<input id="m-rcount" type="number" min="1" value="1"></label>
</fieldset>
</div>
<pre class="calls" id="m-calls" aria-label="The two calls"></pre>
<div class="verdict" id="m-verdict" aria-live="polite"></div>
<ul class="checks" id="m-checks"></ul>
<div class="presets" role="group" aria-label="Examples">
<button type="button" data-preset="ok">Everything matches</button>
<button type="button" data-preset="tag">Different tags (tag_mismatch.c)</button>
<button type="button" data-preset="small">Buffer too small (recv_small.c)</button>
<button type="button" data-preset="wild">Wildcards</button>
</div>
</section>"""

COLL_LAB = """<section class="lab" id="colllab" aria-label="Collective communication lab">
<div class="labbar">
<label>collective<select id="c-op"><option value="bcast">MPI_Bcast</option><option value="reduce" selected>MPI_Reduce (MPI_SUM)</option><option value="allreduce">MPI_Allreduce (MPI_SUM)</option><option value="scatter">MPI_Scatter</option><option value="gather">MPI_Gather</option></select></label>
<label>processes<select id="c-p"><option>2</option><option>3</option><option selected>4</option><option>5</option><option>6</option><option>7</option><option>8</option></select></label>
<label id="c-root-wrap">root rank<select id="c-root"></select></label>
</div>
<pre class="calls" id="c-call" aria-label="The call every rank makes"></pre>
<div class="cards" id="c-cards"></div>
<div id="c-rounds"></div>
</section>"""

MEMORY_DIAGRAM = """<figure class="diagram wide">
<svg viewBox="0 0 660 210" role="img" aria-label="Left: four threads reach one shared memory over a bus. Right: four MPI processes each have their own memory and talk over a network.">
<text class="dg-title" x="150" y="18" text-anchor="middle">Shared memory (pthreads)</text>
<g class="dg-line"><path d="M42 62V104M114 62V104M186 62V104M258 62V104M150 126V152"/></g>
<g><rect class="dg-0" x="14" y="34" width="56" height="28" rx="6"/><text x="42" y="53" text-anchor="middle">thread 0</text>
<rect class="dg-1" x="86" y="34" width="56" height="28" rx="6"/><text x="114" y="53" text-anchor="middle">thread 1</text>
<rect class="dg-1" x="158" y="34" width="56" height="28" rx="6"/><text x="186" y="53" text-anchor="middle">thread 2</text>
<rect class="dg-1" x="230" y="34" width="56" height="28" rx="6"/><text x="258" y="53" text-anchor="middle">thread 3</text></g>
<rect class="dg-bar" x="14" y="104" width="272" height="22" rx="5"/><text x="150" y="119" text-anchor="middle">bus</text>
<rect class="dg-mem" x="70" y="152" width="160" height="40" rx="6"/><text x="150" y="176" text-anchor="middle">one memory, seen by all</text>
<text class="dg-title" x="500" y="18" text-anchor="middle">Distributed memory (MPI)</text>
<g class="dg-line"><path d="M368 96V140M432 96V140M496 96V140M560 96V140"/><path d="M368 62V70M432 62V70M496 62V70M560 62V70"/></g>
<g><rect class="dg-0" x="340" y="34" width="56" height="28" rx="6"/><text x="368" y="53" text-anchor="middle">rank 0</text>
<rect class="dg-1" x="404" y="34" width="56" height="28" rx="6"/><text x="432" y="53" text-anchor="middle">rank 1</text>
<rect class="dg-1" x="468" y="34" width="56" height="28" rx="6"/><text x="496" y="53" text-anchor="middle">rank 2</text>
<rect class="dg-1" x="532" y="34" width="56" height="28" rx="6"/><text x="560" y="53" text-anchor="middle">rank 3</text></g>
<g><rect class="dg-mem" x="340" y="70" width="56" height="26" rx="6"/><text x="368" y="87" text-anchor="middle">memory</text>
<rect class="dg-mem" x="404" y="70" width="56" height="26" rx="6"/><text x="432" y="87" text-anchor="middle">memory</text>
<rect class="dg-mem" x="468" y="70" width="56" height="26" rx="6"/><text x="496" y="87" text-anchor="middle">memory</text>
<rect class="dg-mem" x="532" y="70" width="56" height="26" rx="6"/><text x="560" y="87" text-anchor="middle">memory</text></g>
<rect class="dg-bar" x="340" y="140" width="248" height="22" rx="5"/><text x="464" y="155" text-anchor="middle">network</text>
<text class="dg-note" x="464" y="188" text-anchor="middle">Data moves only when a process sends a message.</text>
</svg>
<figcaption>Lecture 09, slides 3 and 4. Threads share variables; MPI processes do not.</figcaption>
</figure>"""


FN_RE = re.compile(r"^::: fn (\S+)\n([^\n]*)", re.M)


def render_fnindex():
    out = ['<div class="fnindex wide"><label class="fnsearch">Search functions'
           '<input id="fnfilter" type="search" placeholder="Try Reduce, tag or status" autocomplete="off"></label>'
           '<div class="fncols">']
    for slug, label, _d in REF:
        path = CONTENT / f"{slug}.md"
        if not path.exists():
            continue
        found = FN_RE.findall(path.read_text(encoding="utf-8"))
        if not found:
            continue
        out.append(f'<div class="fngroup"><h2>{html.escape(label)}</h2><ul>')
        for name, purpose in found:
            out.append(
                f'<li class="fnrow"><a href="{slug}.html#{name}"><code>{name}</code></a>'
                f'<span>{inline(purpose.strip())}</span></li>'
            )
        out.append("</ul></div>")
    out.append('</div><p class="fnempty" hidden>No function matches that search.</p></div>')
    return "".join(out)


# ---------------------------------------------------------------- preprocessing

BLOCK_RE = re.compile(r"^( *)::: (q|warn|note|eg|run|fn)([^\n]*)\n(.*?)\n\1:::[ \t]*$", re.M | re.S)
FENCE_RE = re.compile(r"^( *)```(\w*)\n(.*?)\n\1```[ \t]*$", re.M | re.S)


def dedent(body, indent):
    return "\n".join(l[len(indent):] if l.startswith(indent) else l for l in body.split("\n"))


def preprocess(text, stash, slug=""):
    qn = [0]

    def keep(markup):
        token = f"@@STASH{len(stash)}@@"
        stash.append(markup)
        return token

    def fence(m):
        indent, lang = m.group(1), m.group(2)
        return indent + keep(code_block(dedent(m.group(3), indent), lang))

    text = FENCE_RE.sub(fence, text)

    def directive(m):
        indent, kind, arg = m.group(1), m.group(2), (m.group(3) or "").strip()
        if kind == "walk":
            return indent + keep(render_walk(arg))
        if kind == "code":
            return indent + keep(render_code(m.group(0).strip()))
        if kind == "lab":
            return indent + keep({"match": MATCH_LAB, "collective": COLL_LAB}[arg])
        if kind == "diagram":
            return indent + keep(MEMORY_DIAGRAM)
        if kind == "progress":
            return indent + keep('<div class="qprogress wide" aria-live="polite"></div>')
        if kind == "fnindex":
            return indent + keep(render_fnindex())
        raise SystemExit(f"unknown directive: {m.group(0)}")

    text = re.sub(
        r"^( *)\{\{(walk|code|lab|diagram|progress|fnindex)([^}\n]*)\}\}[ \t]*$",
        directive,
        text,
        flags=re.M,
    )

    def block(m):
        indent, kind, caption = m.group(1), m.group(2), m.group(3).strip()
        body = dedent(m.group(4), indent)
        if kind == "q":
            qn[0] += 1
            n = qn[0]
            key = str(n) if slug in ("", "practice") else f"{slug}-{n}"  # marks are stored per question key
            q, a = body.split("\n---\n", 1) if "\n---\n" in body else (body, "(no answer written yet)")
            markup = (
                f'<section class="q" id="q{n}" data-q="{key}"><div class="qnum">Q{n}</div>'
                f'<div class="qbody">{md_engine().convert(q.strip())}</div>'
                '<details><summary><span class="s-show">Show answer</span><span class="s-hide">Hide answer</span></summary>'
                f'<div class="abody">{md_engine().convert(a.strip())}</div>'
                '<div class="qmark"><button type="button" data-mark="got">I got it</button>'
                '<button type="button" data-mark="missed">I missed it</button><span class="qstate"></span></div>'
                "</details></section>"
            )
        elif kind == "fn":
            name = caption
            purpose, _, rest = body.strip().partition("\n")
            markup = (
                f'<section class="fn" id="{html.escape(name)}"><header class="fn-head">'
                f'<h2>{html.escape(name)}</h2><p>{inline(purpose.strip())}</p></header>'
                f'<div class="fn-body">{md_engine().convert(rest.strip())}</div></section>'
            )
        elif kind == "run":
            lines = []
            for l in body.split("\n"):
                esc = html.escape(l)
                lines.append(f'<span class="cmd">{esc}</span>' if l.startswith("$ ") else esc)
            markup = (
                f'<figure class="run"><figcaption>{html.escape(caption or "Output")}</figcaption>'
                f'<pre><code>{chr(10).join(lines)}</code></pre></figure>'
            )
        else:
            default = {"warn": "Watch out", "note": "Note", "eg": "Worked example"}[kind]
            cls = {"warn": "trap", "note": "note", "eg": "eg"}[kind]
            markup = (
                f'<div class="callout {cls}"><p class="callout-h">{html.escape(caption or default)}</p>'
                f'{md_engine().convert(body.strip())}</div>'
            )
        return indent + keep(markup)

    text = BLOCK_RE.sub(block, text)

    def chip(m):
        cls, label = CHIPS[m.group(1)]
        return f'<span class="rchip {cls}">{label}</span>'

    return re.sub(r"\[\[(r0|r1|r2|r3|rx)\]\]", chip, text)


def postprocess(htmltext, stash):
    for _ in range(4):  # stashed blocks can contain stashed blocks
        if "@@STASH" not in htmltext:
            break
        for i, markup in enumerate(stash):
            token = f"@@STASH{i}@@"
            htmltext = htmltext.replace(f"<p>{token}</p>", markup).replace(token, markup)
    htmltext = re.sub(r"(<table>.*?</table>)", r'<div class="table-wrap">\1</div>', htmltext, flags=re.S)
    return htmltext


def split_title(text, default):
    m = re.match(r"title:\s*(.+)\n", text)
    if m:
        return m.group(1).strip(), text[m.end():]
    return default, text


# ---------------------------------------------------------------- page shell

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E"
           "%3Crect x='0' y='1' width='16' height='3' rx='1' fill='%232546c9'/%3E"
           "%3Crect x='2' y='5' width='14' height='3' rx='1' fill='%23b4510d'/%3E"
           "%3Crect x='4' y='9' width='12' height='3' rx='1' fill='%23b4510d'/%3E"
           "%3Crect x='7' y='13' width='9' height='3' rx='1' fill='%23b4510d'/%3E%3C/svg%3E")

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>%%TITLE%%</title>
  <meta name="description" content="%%DESC%%">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/style.css?v=%%VER%%">
  <link rel="icon" href="%%FAVICON%%">
</head>
<body data-page="%%NAV%%">
  <header id="site-header"></header>
  <main%%MAINCLASS%%>
%%BODY%%
  </main>
  <script src="assets/common.js?v=%%VER%%"></script>
%%SCRIPTS%%
</body>
</html>
"""


def page(title, desc, nav, body, scripts=(), main_class=""):
    full_title = SITE_NAME if title is None else f"{title} — {SITE_NAME}"
    tags = "\n".join(f'  <script src="{s}?v={VER}"></script>' for s in scripts)
    return (
        PAGE.replace("%%TITLE%%", html.escape(full_title))
        .replace("%%DESC%%", html.escape(desc))
        .replace("%%NAV%%", nav)
        .replace("%%MAINCLASS%%", f' class="{main_class}"' if main_class else "")
        .replace("%%VER%%", VER)
        .replace("%%FAVICON%%", FAVICON)
        .replace("%%SCRIPTS%%", tags)
        .replace("%%BODY%%", body)
    )


def write(slug, text):
    (ROOT / f"{slug}.html").write_text(text, encoding="utf-8")
    print("built", f"{slug}.html")


# ---------------------------------------------------------------- notes layout

def split_meta(text):
    """Leading 'key: value' lines (title, source, lead), then the body."""
    meta = {}
    lines = text.split("\n")
    i = 0
    while i < len(lines) and re.match(r"^(title|source|lead):\s", lines[i]):
        k, v = lines[i].split(":", 1)
        meta[k] = v.strip()
        i += 1
    return meta, "\n".join(lines[i:])


def render_md(text, slug, layout=False):
    """Markdown to HTML. With layout=True the result is reshaped into the notes layout first, while code
    blocks are still placeholders (BeautifulSoup would collapse the indentation inside them)."""
    stash = []
    out = md_engine().convert(preprocess(text, stash, slug))
    if layout:
        out = notes_layout(out, stash)
    return postprocess(out, stash)


KEEP_TOP = {"walk", "fn"}  # blocks that stay full width instead of nesting under a subsection


def notes_layout(fragment, stash):
    """Turn the Markdown output into the Read-page shape: one <ul class="notes"> whose top-level items are
    subsection labels with a nested list. Tables, figures and callouts that sit between lists are moved into
    the subsection above them as <li class="blk">, so they fold with it."""
    soup = BeautifulSoup(fragment, "html.parser")
    out = []
    cur = None
    for el in list(soup.contents):
        if isinstance(el, NavigableString):
            if el.strip():
                out.append(el.extract())
            continue
        if el.name == "ul":
            if cur is None:
                cur = soup.new_tag("ul", attrs={"class": "notes"})
                out.append(cur)
            for li in el.find_all("li", recursive=False):
                cur.append(li.extract())
            el.decompose()
            continue
        classes = set(el.get("class", []))
        tok = re.fullmatch(r"\s*@@STASH(\d+)@@\s*", el.get_text()) if el.name == "p" else None
        if tok:
            m = re.match(r'\s*<section class="(\w+)', stash[int(tok.group(1))])
            if m:
                classes.add(m.group(1))
        items = cur.find_all("li", recursive=False) if cur is not None else []
        if classes & KEEP_TOP or not items:
            out.append(el.extract())
            if classes & KEEP_TOP:
                cur = None
            continue
        last = items[-1]
        sub = last.find("ul", recursive=False)
        if sub is None:
            sub = soup.new_tag("ul")
            last.append(sub)
        li = soup.new_tag("li", attrs={"class": "blk"})
        li.append(el.extract())
        sub.append(li)
    # a subsection label written as a loose-list paragraph: unwrap the <p> so the label becomes the toggle text
    for ul in [x for x in out if getattr(x, "name", None) == "ul"]:
        for li in ul.find_all("li", recursive=False):
            # "- Label:" followed by an indented block (a code listing, a worked example) before or instead of its
            # bullets: move every block after the label into the sub-list, so the label alone becomes the toggle
            paras = li.find_all("p", recursive=False)
            if len(paras) >= 2:
                sub = li.find("ul", recursive=False)
                if sub is None:
                    sub = soup.new_tag("ul")
                    li.append(sub)
                for para in reversed(paras[1:]):
                    item = soup.new_tag("li", attrs={"class": "blk"})
                    item.append(para.extract())
                    sub.insert(0, item)
            first = next((c for c in li.contents if not (isinstance(c, NavigableString) and not c.strip())), None)
            if getattr(first, "name", None) == "p" and li.find("ul", recursive=False):
                first.unwrap()
            if li.get("class"):
                li["class"] = [c for c in li["class"] if c != "sec"] or None
                if li["class"] is None:
                    del li["class"]
    return "\n".join(str(x) for x in out)


def minutes(text):
    words = len(re.findall(r"[A-Za-z0-9_]+", re.sub(r"```.*?```", "", text, flags=re.S)))
    return max(5, int(math.ceil(words / 130 / 5.0)) * 5)


def bank_counts():
    path = ROOT / "data" / "bank.js"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    counts = {}
    for t in re.findall(r'"topic"\s*:\s*"([\w-]+)"', text):
        counts[t] = counts.get(t, 0) + 1
    return counts


# ---------------------------------------------------------------- pages

def build_read():
    counts = bank_counts()
    toc, secs, group = [], [], None
    for n, (slug, label, g) in enumerate(READ, 1):
        meta, text = split_meta((CONTENT / f"{slug}.md").read_text(encoding="utf-8"))
        if g != group:
            toc.append(f'<li class="toc-h">{html.escape(g)}</li>')
            group = g
        toc.append(f'<li><a href="#{slug}">{n}. {html.escape(label)}</a></li>')
        k = counts.get(slug, 0)
        quiz = (f'<a class="btn secondary" href="quiz.html?topic={slug}&amp;all=1">Quiz this section ({k} questions)</a>'
                if k else "")
        secs.append(
            f'<!-- ================= {n} ================= -->\n'
            f'<section id="{slug}" class="k3">\n<h2>{n}. {html.escape(label)}</h2>\n'
            f'<p class="source">{html.escape(meta.get("source", ""))} · about {minutes(text)} minutes</p>\n'
            f'<p class="lead">{inline(meta.get("lead", ""))}</p>\n'
            f'{render_md(text, slug, layout=True)}\n'
            f'<p class="btn-row section-quiz">{quiz}<label class="ex-done read-done"><input type="checkbox" data-read="{slug}"> Section done</label></p>\n'
            f'</section>'
        )
    meta, text = split_meta((CONTENT / f"{CHEAT}.md").read_text(encoding="utf-8"))
    toc.append('<li class="toc-h">Reference</li><li><a href="#cheat">Cheat sheet</a></li>')
    secs.append(
        f'<!-- ================= cheat sheet ================= -->\n'
        f'<section id="cheat" class="k3">\n<h2>Cheat sheet</h2>\n<p class="lead">{inline(meta.get("lead", ""))}</p>\n'
        f'{render_md(text, CHEAT, layout=True)}\n</section>'
    )
    total = sum(minutes(split_meta((CONTENT / f"{s}.md").read_text(encoding="utf-8"))[1]) for s, _l, _g in READ)
    body = f"""    <div class="page-head">
      <h1>Read</h1>
      <p>Lectures 09 to 17, rebuilt from the slides as {len(READ)} sections (about {round(total / 60 * 2) / 2:g} hours of reading). Each section opens with the idea in plain words, then the notes. Amber boxes are worked examples to redo by hand, red boxes are exam traps, and the blue-edged panels are labs you can play with. The full programs, with a rank picker, are on the <a href="code.html">Code</a> pages.</p>
      <div class="btn-row notes-bar">
        <button class="btn quiet" type="button" id="collapse-all">Collapse all subsections</button>
        <button class="btn quiet" type="button" id="expand-all">Expand all</button>
        <span class="muted">Click any subsection title to fold it.</span>
      </div>
    </div>

    <div class="reading">
      <nav class="toc" aria-label="Sections">
        <ol>
          {chr(10).join("          " + t for t in toc).strip()}
        </ol>
      </nav>

      <article class="article">
{chr(10).join(secs)}
      </article>
    </div>"""
    write("read", page("Read", "Notes for every lecture from 09 to 17.", "read", body,
                       ["assets/app.js", "assets/site.js"]))


def subnav(items, current, all_link=None):
    links = []
    if all_link:
        href, label = all_link
        links.append(f'<a class="chip" href="{href}">{html.escape(label)}</a>')
    for s, l, _d in items:
        cur = ' aria-current="page"' if s == current else ""
        links.append(f'<a class="chip" href="{s}.html"{cur}>{html.escape(l)}</a>')
    return f'<nav class="chip-row subnav" aria-label="Pages in this part">{"".join(links)}</nav>'


def build_group(items, nav, all_link, intro_label):
    for slug, label, desc in items:
        md_path, html_path = CONTENT / f"{slug}.md", CONTENT / f"{slug}.html"
        if md_path.exists():
            meta, text = split_meta(md_path.read_text(encoding="utf-8"))
            title = meta.get("title", label)
            content = render_md(text, slug, layout=True)
        else:
            meta, content = split_meta(html_path.read_text(encoding="utf-8"))
            title = meta.get("title", label)
        body = (
            f'    <div class="page-head"><h1>{html.escape(title)}</h1><p>{inline(desc)}</p></div>\n'
            f'    {subnav(items, slug, all_link)}\n'
            f'    <div class="k3 page-body">\n{content}\n    </div>'
        )
        write(slug, page(title, desc, nav, body, ["assets/app.js", "assets/site.js"]))


def build_code_index():
    rows = "".join(
        f'<li><a href="{s}.html"><span class="name">{html.escape(l)}</span><span class="desc">{inline(d)}</span></a></li>'
        for s, l, d in CODE
    )
    body = f"""    <div class="page-head">
      <h1>Code</h1>
      <p>The course programs, line by line. Pick a rank to see only the lines it runs, then press Next step to follow the messages one send or receive at a time. Press the <b>i</b> button on a line to read its note. Every output shown was produced by compiling and running the code.</p>
    </div>
    <ul class="code-list">{rows}</ul>
    <h2>Trip-ups in the course zip</h2>
    <ul class="notes plain">
      <li><code>mpi_SendRec.c</code> is the textbook's <code>mpi_trap2.c</code>, and <code>mpi_Bcast.c</code> is <code>mpi_trap3.c</code>. The comments inside still use the old names.</li>
      <li>The makefile builds <code>mpi_hello</code>, <code>mpi_SendRec</code> and <code>mpi_Bcast</code>, but not <code>mpi_hello2</code>.</li>
      <li>The trapezoid programs read from the keyboard, so pipe the input in: <code>echo "0 3 1024" | mpiexec -n 4 ./mpi_Bcast</code></li>
      <li><code>mpi_odd_even.c</code> and the Warp example <code>arrAdd.py</code> were not in the project files, so the Read page uses the code from the slides for those.</li>
    </ul>"""
    write("code", page("Code", "The CIS*3090 course programs with a rank picker and a message timeline.", "code", body))


HOME_ART = """<svg viewBox="0 0 420 210" role="img" aria-label="Ranks 1, 2 and 3 each send a message to rank 0." font-family="var(--font)">
<g stroke="var(--rule)" stroke-width="2" stroke-dasharray="3 5"><line x1="70" y1="52" x2="70" y2="200"/><line x1="165" y1="52" x2="165" y2="200"/><line x1="260" y1="52" x2="260" y2="200"/><line x1="355" y1="52" x2="355" y2="200"/></g>
<rect x="50" y="14" width="40" height="32" rx="8" fill="var(--k-blue)"/><text x="70" y="36" text-anchor="middle" font-size="15" font-weight="700" fill="var(--k-on-blue)">0</text>
<rect x="145" y="14" width="40" height="32" rx="8" fill="var(--k-orange)"/><text x="165" y="36" text-anchor="middle" font-size="15" font-weight="700" fill="var(--k-on-orange)">1</text>
<rect x="240" y="14" width="40" height="32" rx="8" fill="var(--k-orange)"/><text x="260" y="36" text-anchor="middle" font-size="15" font-weight="700" fill="var(--k-on-orange)">2</text>
<rect x="335" y="14" width="40" height="32" rx="8" fill="var(--k-orange)"/><text x="355" y="36" text-anchor="middle" font-size="15" font-weight="700" fill="var(--k-on-orange)">3</text>
<g stroke="var(--k-orange)" stroke-width="3"><line x1="165" y1="86" x2="84" y2="86"/><line x1="260" y1="132" x2="84" y2="132"/><line x1="355" y1="178" x2="84" y2="178"/></g>
<g fill="var(--k-orange)"><path d="M70 86 l14 -7 v14z"/><path d="M70 132 l14 -7 v14z"/><path d="M70 178 l14 -7 v14z"/></g>
</svg>"""


def build_home():
    plan_rows = []
    groups = []
    for slug, label, g in READ:
        if not groups or groups[-1][0] != g:
            groups.append((g, []))
        groups[-1][1].append((slug, label))
    num = {s: i for i, (s, _l, _g) in enumerate(READ, 1)}
    for g, secs in groups:
        links = "<br>".join(f'<a href="read.html#{s}" data-plan="{s}">{num[s]}. {html.escape(l)}</a>' for s, l in secs)
        mins = sum(minutes(split_meta((CONTENT / f"{s}.md").read_text(encoding="utf-8"))[1]) for s, _l in secs)
        then = {
            "MPI (lectures 09 to 11)": 'Open each program on the <a href="code.html">Code</a> pages and predict the output before reading the notes. Then take each section\'s quiz.',
            "Distributed-memory case studies (12, 13)": 'Step through <a href="heat_code.html">heatDiffusionMpi.c</a>. Redo the odd-even phase table by hand.',
            "Performance (14)": "Do the Amdahl and efficiency calculations without looking, then take the quiz.",
            "GPUs and images (15 to 17)": "Redo the convolution and unsharp-mask worked examples by hand, then take each quiz.",
        }.get(g, "Take each section's quiz.")
        plan_rows.append(
            f'<tr><td><strong>{html.escape(g)}</strong><br><span class="muted">about {mins} min of reading</span></td>'
            f'<td>{links}</td><td>{then}</td></tr>'
        )
    plan_rows.append(
        '<tr><td><strong>Last</strong><br><span class="muted">about 1 h 30</span></td>'
        '<td><a href="exam.html">Practice exam A</a><br><a href="short.html">Short answers</a><br><a href="read.html#cheat">Cheat sheet</a></td>'
        '<td>Reread the sections the exam marks as weak. Use flashcards for vocabulary that is still shaky.</td></tr>'
    )
    n_code = len(CODE) - 1
    body = f"""    <section class="hero">
      <div>
        <h1>CIS*3090 Parallel Programming: midterm 2 review</h1>
        <p class="when">Lectures 09 to 17: MPI and collective communication, the odd-even sort and heat distribution rebuilt for distributed memory, parallel hardware and performance, GPGPU with Nvidia Warp, and image filtering.</p>
        <div class="btn-row">
          <a class="btn" href="read.html" id="continue">Start reading</a>
          <a class="btn secondary" href="exam.html">Take the practice exam</a>
        </div>
      </div>
      <figure class="hero-fig" aria-label="Every worker rank sends to rank 0">{HOME_ART}<figcaption class="lanes-caption">Blue is rank 0, orange is every other rank. The code pages draw every program this way, one message at a time.</figcaption></figure>
    </section>

    <div class="home-grid">
      <section aria-labelledby="study-h">
        <h2 id="study-h" style="margin-top:0">Study</h2>
        <ul class="study-list">
          <li><a href="read.html"><span class="name">Read</span><span class="desc">{len(READ)} sections built from the lecture slides, each starting from the idea, with worked examples, two labs and a cheat sheet.</span><span class="stat" id="stat-read"></span></a></li>
          <li><a href="code.html"><span class="name">Code</span><span class="desc">{n_code} pages that walk through the course programs rank by rank, plus a trapezoid trace.</span><span class="stat"></span></a></li>
          <li><a href="quiz.html"><span class="name">Topic quizzes</span><span class="desc"><span id="n-quiz"></span> multiple-choice questions, one quiz per section, with an explanation after every answer.</span><span class="stat" id="stat-quiz"></span></a></li>
          <li><a href="short.html"><span class="name">Short answers</span><span class="desc"><span id="n-short"></span> code-reading and explain-why prompts, with model answers to open once you've tried them.</span><span class="stat" id="stat-short"></span></a></li>
          <li><a href="flashcards.html"><span class="name">Flashcards</span><span class="desc">Every definition from the lectures, by section.</span><span class="stat" id="stat-cards"></span></a></li>
          <li><a href="exam.html"><span class="name">Practice exam</span><span class="desc"><span id="n-exam"></span> questions, timed, scored by section and by question type. Exam A uses questions that appear nowhere else.</span><span class="stat" id="stat-exam"></span></a></li>
          <li><a href="ref_index.html"><span class="name">MPI reference</span><span class="desc">Every MPI call used in the course, with its arguments and the mistakes to avoid.</span><span class="stat"></span></a></li>
        </ul>

        <h2 id="plan-h">Suggested order</h2>
        <div class="table-wrap"><table class="plan">
          <thead><tr><th>Part</th><th>Read</th><th>Then</th></tr></thead>
          <tbody>
          {chr(10).join(plan_rows)}
          </tbody>
        </table></div>
        <p class="muted">Short on time? Do these first: <a href="read.html#method">2 reading MPI code</a>, <a href="read.html#collectives">4 collectives</a>, <a href="read.html#heat">7 heat distribution</a>, <a href="read.html#performance">8 performance</a>, <a href="read.html#filters">11 sharpening and smoothing</a>.</p>
      </section>

      <aside aria-labelledby="facts-h">
        <h2 id="facts-h" style="margin-top:0">About this site</h2>
        <dl class="facts">
          <dt>Coverage</dt>
          <dd>Lectures 09 to 17 and textbook chapter 2 (2.3, 2.6.1 to 2.6.2) and chapter 3 (3.1 to 3.4).</dd>
          <dt>Not covered here</dt>
          <dd>The pthreads lectures (01 to 08). Lectures 12 and 13 recap the pthreads versions where they compare them.</dd>
          <dt>Course code</dt>
          <dd><code>mpi_hello.c</code>, <code>mpi_hello2.c</code>, <code>mpi_SendRec.c</code>, <code>mpi_Bcast.c</code> and <code>heatDiffusionMpi.c</code>, all compiled and run. <code>mpi_odd_even.c</code> and <code>arrAdd.py</code> were not in the project files, so those use the slide code.</dd>
          <dt>How outputs were made</dt>
          <dd>MPICH for lectures 09 to 11, Open MPI for the heat program, Warp 1.16 on the CPU for the GPU example.</dd>
          <dt>Sources</dt>
          <dd>The CIS*3090 slides and <em>An Introduction to Parallel Programming</em> (Pacheco and Malensek, 2nd ed.). Lecture 13 also uses Grama et al. for the neighbour computation.</dd>
          <dt>Progress</dt>
          <dd>Saved in this browser only. Nothing is sent anywhere.</dd>
        </dl>
      </aside>
    </div>"""
    write("index", page(None, "Reading notes, code walkthroughs, quizzes, short answers, flashcards and a practice exam for CIS*3090 midterm 2.",
                        "home", body, ["data/flashcards.js", "data/bank.js", "data/short.js", "data/exam.js", "assets/home.js"]))


def build_short():
    out = []
    for src, topics in SHORT_SOURCES:
        text = (CONTENT / f"{src}.md").read_text(encoding="utf-8")
        blocks = re.findall(r"^::: q\n(.*?)\n:::[ \t]*$", text, re.M | re.S)
        if len(blocks) != len(topics):
            raise SystemExit(f"{src}.md has {len(blocks)} questions but {len(topics)} topics are listed")
        for i, (b, t) in enumerate(zip(blocks, topics), 1):
            q, a = b.split("\n---\n", 1)
            out.append({"id": f"s-{src}-{i}", "topic": t,
                        "qhtml": render_md(q.strip(), src), "answer": render_md(a.strip(), src)})
    js = ("/* Short-answer prompts: { id, topic, qhtml, answer }. Generated by build.py from content/practice*.md. */\n"
          "window.SHORT_BANK = [\n" + ",\n".join("  " + json.dumps(o, ensure_ascii=False) for o in out) + "\n];\n")
    (ROOT / "data" / "short.js").write_text(js, encoding="utf-8")
    print("built data/short.js", len(out), "prompts")


def build_redirects():
    for slug, target in REDIRECTS.items():
        (ROOT / f"{slug}.html").write_text(
            f'<!doctype html>\n<meta charset="utf-8">\n<title>Moved</title>\n'
            f'<meta http-equiv="refresh" content="0; url={target}">\n'
            f'<link rel="canonical" href="{target}">\n<p>This page moved to <a href="{target}">{target}</a>.</p>\n',
            encoding="utf-8")
    print("built", len(REDIRECTS), "redirects")


def main():
    import subprocess
    import sys
    subprocess.run([sys.executable, str(CONTENT / "data_src" / "make_data.py")], check=True)
    build_short()
    build_home()
    build_read()
    build_code_index()
    build_group(CODE, "code", ("code.html", "All code"), "Code")
    build_group(REF, "ref", None, "MPI reference")
    build_redirects()


if __name__ == "__main__":
    main()
