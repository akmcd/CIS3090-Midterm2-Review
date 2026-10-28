#!/usr/bin/env python3
"""Build the study site.

    pip install -r requirements.txt
    python build.py

Reads   content/<slug>.md   (or content/<slug>.html for hand-written pages)
Writes  <slug>.html next to this file. Styles and scripts live in assets/.

To add a page: create content/<slug>.md and add a line to PAGES below.

Extras you can use inside the Markdown files
  title: Page title                  first line of every page
  {{walk NAME}}                      code reader from content/walk/NAME.json
                                     (rank lens, message timeline, notes)
  {{code FILE START-END hl=1,2}}     plain listing of examples/FILE, real line numbers
  {{lab match}}  {{lab collective}}  the two interactive labs
  {{diagram memory}}                 shared vs distributed memory picture
  {{progress}}                       got-it / missed-it score for practice questions
  {{map}}                            list of every page with a one-line description
  [[r0]] [[rx]]                      small rank labels
  ::: q ... --- ... :::              practice question (question, a --- line, answer)
  ::: run Caption ... :::            real program output (a first line "$ cmd" is styled)
  ::: warn Title ... :::             red callout
  ::: note Title ... :::             blue callout
Blocks may be indented to sit inside a bullet.
"""
import html
import json
import pathlib
import re

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

SITE_NAME = "CIS*3090 midterm 2"

# (slug, label, group, one-line description). Order here is the order on the site.
PAGES = [
    ("index", "Start here", None, "Midterm 2 study site for CIS*3090. Pick a rank, step through the messages, and practise predicting what MPI programs do."),
    ("concepts", "Big ideas", "Learn", "Each MPI process has its own memory. A rank identifies the process, and messages move data between processes."),
    ("method", "Reading MPI code", "Learn", "A routine for predicting the output and spotting hangs in any MPI code question."),
    ("sendrecv", "Send and receive", "Learn", "How a send finds its receive, what the wildcards do, and when a send waits."),
    ("collectives", "Collective communication", "Learn", "Calls that every process makes together: broadcast, reduce, scatter and gather."),
    ("trapezoid", "The trapezoidal rule", "Learn", "The problem the course programs solve, and how each rank gets its slice."),
    ("hello", "mpi_hello.c", "Code", "Every rank except 0 sends a greeting, and rank 0 receives and prints them in order."),
    ("hello2", "mpi_hello2.c", "Code", "The same idea with wildcard receives and the status object."),
    ("trap_sendrecv", "mpi_SendRec.c", "Code", "The trapezoidal rule using only MPI_Send and MPI_Recv."),
    ("trap_bcast", "mpi_Bcast.c", "Code", "The same program using MPI_Bcast and MPI_Reduce."),
    ("pitfalls", "Hangs and mix-ups", "Code", "Three small programs that go wrong, and how to see why."),
    ("practice", "Code-reading questions", "Practice", "Write your answer first, then open the explanation and mark how you did."),
    ("trace", "Trapezoid trace", "Practice", "Change the inputs and see which slice of the interval each rank computes."),
    ("ref_index", "Find a function", "MPI reference", "Look up any MPI function used in this course: what it does, its arguments, and the mistakes to avoid."),
    ("ref_start", "Setup and shutdown", "MPI reference", "MPI_Init, MPI_Comm_size, MPI_Comm_rank and MPI_Finalize."),
    ("ref_p2p", "Send and receive functions", "MPI reference", "MPI_Send, MPI_Recv, MPI_Ssend, MPI_Sendrecv, status and wildcards."),
    ("ref_coll", "Collective functions", "MPI reference", "MPI_Bcast, MPI_Reduce, MPI_Allreduce, MPI_Scatter, MPI_Gather and more."),
    ("ref_types", "Datatypes and operators", "MPI reference", "Datatypes, reduction operators, constants and common errors."),
    ("reference", "Cheat sheet", "MPI reference", "The most important calls and formulas on one page."),
]
GROUPS = ["Learn", "Code", "Practice", "MPI reference"]

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
        '<label class="notes-toggle"><input type="checkbox" class="allnotes"> Show all line notes</label>'
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


HERO_ART = """<svg viewBox="0 0 420 230" role="img" aria-label="Ranks 1, 2 and 3 each send a message to rank 0.">
<line class="lane" x1="70" y1="52" x2="70" y2="214"/><line class="lane" x1="165" y1="52" x2="165" y2="214"/>
<line class="lane" x1="260" y1="52" x2="260" y2="214"/><line class="lane" x1="355" y1="52" x2="355" y2="214"/>
<rect x="50" y="14" width="40" height="32" rx="8" fill="var(--blue)"/><text class="hl" x="70" y="35" text-anchor="middle">0</text>
<rect x="145" y="14" width="40" height="32" rx="8" fill="var(--orange)"/><text class="ho" x="165" y="35" text-anchor="middle">1</text>
<rect x="240" y="14" width="40" height="32" rx="8" fill="var(--orange)"/><text class="ho" x="260" y="35" text-anchor="middle">2</text>
<rect x="335" y="14" width="40" height="32" rx="8" fill="var(--orange)"/><text class="ho" x="355" y="35" text-anchor="middle">3</text>
<line class="a0" x1="165" y1="90" x2="82" y2="90"/><path class="ah" d="M70 90 l13 -6 v12z"/>
<line class="a0" x1="260" y1="140" x2="82" y2="140"/><path class="ah" d="M70 140 l13 -6 v12z"/>
<line class="a0" x1="355" y1="190" x2="82" y2="190"/><path class="ah" d="M70 190 l13 -6 v12z"/>
</svg>"""


def render_home():
    rows = []
    for g in GROUPS:
        items = [(s, l) for s, l, gg, _d in PAGES if gg == g]
        first = items[0][0]
        names = ", ".join(l for _s, l in items)
        desc = {
            "Learn": "Separate memory, ranks, send and receive, collectives and the trapezoidal rule.",
            "Code": "Each course program with a rank picker and a message timeline.",
            "Practice": "Predict outputs and find hangs, then check yourself.",
            "MPI reference": "Look up any MPI call used in this course.",
        }[g]
        rows.append(
            f'<li><a href="{first}.html"><span class="name">{html.escape(g)}</span>'
            f'<span class="desc">{html.escape(desc)}<small>{html.escape(names)}</small></span></a></li>'
        )
    return (
        '<section class="hero"><div>'
        '<h1>Understand MPI code by following every rank</h1>'
        '<p class="lede">Midterm 2 study site for CIS*3090. Pick a rank, see the lines it runs, and step through the messages one at a time.</p>'
        '<div class="hero-btns"><a class="primary" href="hello.html">Follow a program</a>'
        '<a class="secondary" href="concepts.html">Start with the big ideas</a></div></div>'
        f'<div class="hero-art">{HERO_ART}<p>Every worker sends to rank 0, and rank 0 receives in order.</p></div></section>'
        '<div class="home-grid"><section><h2>Study</h2>'
        f'<ul class="studylist">{"".join(rows)}</ul></section></div>'
    )


def render_map():
    out = ['<div class="map wide">']
    for g in [None] + GROUPS:
        items = [(s, l, d) for s, l, gg, d in PAGES if gg == g and s != "index"]
        if not items:
            continue
        out.append(f'<div class="mgroup"><h2>{html.escape(g)}</h2><ul>')
        for s, l, d in items:
            out.append(f'<li><a href="{s}.html">{html.escape(l)}</a><span>{html.escape(d)}</span></li>')
        out.append("</ul></div>")
    out.append("</div>")
    return "".join(out)


FN_RE = re.compile(r"^::: fn (\S+)\n([^\n]*)", re.M)


def render_fnindex():
    out = ['<div class="fnindex wide"><label class="fnsearch">Search functions'
           '<input id="fnfilter" type="search" placeholder="Try Reduce, tag or status" autocomplete="off"></label>'
           '<div class="fncols">']
    for slug, label, group, _d in PAGES:
        path = CONTENT / f"{slug}.md"
        if group != "MPI reference" or not path.exists():
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

BLOCK_RE = re.compile(r"^( *)::: (q|warn|note|run|fn)([^\n]*)\n(.*?)\n\1:::[ \t]*$", re.M | re.S)
FENCE_RE = re.compile(r"^( *)```(\w*)\n(.*?)\n\1```[ \t]*$", re.M | re.S)


def dedent(body, indent):
    return "\n".join(l[len(indent):] if l.startswith(indent) else l for l in body.split("\n"))


def preprocess(text, stash):
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
        if kind == "map":
            return indent + keep(render_map())
        if kind == "fnindex":
            return indent + keep(render_fnindex())
        if kind == "home":
            return indent + keep(render_home())
        raise SystemExit(f"unknown directive: {m.group(0)}")

    text = re.sub(
        r"^( *)\{\{(walk|code|lab|diagram|progress|map|fnindex|home)([^}\n]*)\}\}[ \t]*$",
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
            q, a = body.split("\n---\n", 1) if "\n---\n" in body else (body, "(no answer written yet)")
            markup = (
                f'<section class="q" id="q{n}" data-q="{n}"><div class="qnum">Q{n}</div>'
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
            default = "Watch out" if kind == "warn" else "Note"
            markup = (
                f'<aside class="callout {kind}"><div class="ctitle">{html.escape(caption or default)}</div>'
                f'{md_engine().convert(body.strip())}</aside>'
            )
        return indent + keep(markup)

    text = BLOCK_RE.sub(block, text)

    def chip(m):
        cls, label = CHIPS[m.group(1)]
        return f'<span class="chip {cls}">{label}</span>'

    return re.sub(r"\[\[(r0|r1|r2|r3|rx)\]\]", chip, text)


def postprocess(htmltext, stash):
    for _ in range(4):  # stashed blocks can contain stashed blocks
        if "@@STASH" not in htmltext:
            break
        for i, markup in enumerate(stash):
            token = f"@@STASH{i}@@"
            htmltext = htmltext.replace(f"<p>{token}</p>", markup).replace(token, markup)
    htmltext = re.sub(r"(<table>.*?</table>)", r'<div class="tablewrap">\1</div>', htmltext, flags=re.S)
    return htmltext


def split_title(text, default):
    m = re.match(r"title:\s*(.+)\n", text)
    if m:
        return m.group(1).strip(), text[m.end():]
    return default, text


# ---------------------------------------------------------------- page shell

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%%TITLE%% | %%SITE%%</title>
<meta name="description" content="%%DESC%%">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=JetBrains+Mono:wght@400;700&display=swap">
<script>try{var t=localStorage.getItem("theme");if(t)document.documentElement.dataset.theme=t}catch(e){}</script>
<link rel="stylesheet" href="assets/style.css">
</head>
<body class="%%BODYCLASS%%">
<a class="skip" href="#main">Skip to content</a>
%%HEADER%%
<div class="shell">
%%PAGELIST%%
<main id="main">
%%INTRO%%
%%BODY%%
<nav class="pager" aria-label="Previous and next page">%%PREV%%%%NEXT%%</nav>
</main>
</div>
<footer class="foot">Built from the CIS*3090 slides, textbook chapter 3 and real MPICH runs.</footer>
<script src="assets/app.js" defer></script>
</body>
</html>
"""


def group_of(slug):
    return next((g for s, _l, g, _d in PAGES if s == slug), None)


def header(current):
    group = group_of(current)
    links = ['<a href="index.html"{}>Home</a>'.format(' aria-current="true"' if current == "index" else "")]
    for g in GROUPS:
        first = next(s for s, _l, gg, _d in PAGES if gg == g)
        cur = ' aria-current="true"' if g == group else ""
        links.append(f'<a href="{first}.html"{cur}>{html.escape(g)}</a>')
    return (
        '<header class="top"><div class="topin">'
        '<a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true"><span></span><span></span><span></span></span>'
        f'{html.escape(SITE_NAME)}</a>'
        f'<nav class="groups" aria-label="Sections">{"".join(links)}</nav>'
        '<button type="button" class="themebtn" id="themebtn" aria-pressed="false">Dark mode</button></div></header>'
    )


def pagelist(current):
    """Short numbered list of the pages in the current group. Nothing nested."""
    group = group_of(current)
    if group is None:
        return ""
    items = [(s, l) for s, l, gg, _d in PAGES if gg == group]
    links = "".join(
        '<a href="{}.html"{}>{}. {}</a>'.format(s, ' aria-current="page"' if s == current else "", i, html.escape(l))
        for i, (s, l) in enumerate(items, 1)
    )
    label = next(l for s, l in items if s == current)
    return (
        f'<nav class="pagelist" aria-label="{html.escape(group)} pages"><p class="gl">{html.escape(group)}</p>{links}</nav>'
        f'<details class="mobilenav"><summary>{html.escape(group)}: {html.escape(label)}</summary>'
        f'<nav aria-label="{html.escape(group)} pages">{links}</nav></details>'
    )


def main():
    for i, (slug, label, _group, desc) in enumerate(PAGES):
        md_path, html_path = CONTENT / f"{slug}.md", CONTENT / f"{slug}.html"
        if md_path.exists():
            stash = []
            title, text = split_title(md_path.read_text(encoding="utf-8"), label)
            body = postprocess(md_engine().convert(preprocess(text, stash)), stash)
        elif html_path.exists():
            title, body = split_title(html_path.read_text(encoding="utf-8"), label)
        else:
            print(f"skip {slug}: no content file")
            continue

        prev = nxt = ""
        if i > 0:
            ps, pl = PAGES[i - 1][0], PAGES[i - 1][1]
            prev = f'<a class="prev" href="{ps}.html"><span>Previous</span>{html.escape(pl)}</a>'
        if i < len(PAGES) - 1:
            ns, nl = PAGES[i + 1][0], PAGES[i + 1][1]
            nxt = f'<a class="next" href="{ns}.html"><span>Next</span>{html.escape(nl)}</a>'

        intro = "" if slug == "index" else f'<h1>{html.escape(title)}</h1>\n<p class="lede">{html.escape(desc)}</p>'
        page = (
            PAGE.replace("%%INTRO%%", intro)
            .replace("%%TITLE%%", html.escape(title))
            .replace("%%SITE%%", html.escape(SITE_NAME))
            .replace("%%DESC%%", html.escape(desc))
            .replace("%%BODYCLASS%%", f"page-{slug}" + (" home" if slug == "index" else ""))
            .replace("%%HEADER%%", header(slug))
            .replace("%%PAGELIST%%", pagelist(slug))
            .replace("%%BODY%%", body)
            .replace("%%PREV%%", prev)
            .replace("%%NEXT%%", nxt)
        )
        (ROOT / f"{slug}.html").write_text(page, encoding="utf-8")
        print("built", f"{slug}.html")


if __name__ == "__main__":
    main()
