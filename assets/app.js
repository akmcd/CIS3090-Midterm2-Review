/* CIS*3090 midterm 2 study site.
   Rank lens + message timeline for the code pages, two small labs, practice marks, trapezoid trace. */
(() => {
"use strict";

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const NS = "http://www.w3.org/2000/svg";
const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function svg(tag, attrs, parent) {
  const n = document.createElementNS(NS, tag);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(n);
  return n;
}
function esc(s) {
  return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}
function mpiSpans(s) {
  return esc(s).replace(/MPI_\w+/g, m => '<span class="mpi">' + m + "</span>");
}
function shuffled(p) {
  const a = [];
  for (let i = 1; i < p; i++) a.push(i);
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/* ---------------------------------------------------------------- who runs which line */

function executes(role, r, p) {
  if (role === "all") return true;
  if (role === "zero") return r === 0;
  if (role === "workers") return r > 0;
  if (role === "zero_loop") return r === 0 && p > 1;
  if (role.startsWith("r:")) return r === +role.slice(2);
  if (role.startsWith("notr:")) return r !== +role.slice(5);
  return true;
}
function neverRuns(role, p) {
  if (role === "workers" || role === "zero_loop") return p === 1;
  if (role.startsWith("r:")) return +role.slice(2) >= p;
  return false;
}

/* ---------------------------------------------------------------- timeline events */

const S = {
  local: (rank, text, lines) => ({ t: "local", rank, text, lines: lines || [] }),
  msg: (from, to, text, lines) => ({ t: "msg", from, to, text, lines: lines || [] }),
  lost: (from, to, text, lines) => ({ t: "lost", from, to, text, lines: lines || [] }),
  block: (rank, text, lines) => ({ t: "block", rank, text, lines: lines || [] }),
  band: (text, lines) => ({ t: "band", text, lines: lines || [] }),
};

function reduceRounds(p, root) {
  const rounds = [];
  for (let step = 1; step < p; step *= 2) {
    const rd = [];
    for (let i = 0; i < p; i++) {
      if (i % (2 * step) === step) rd.push([(i + root) % p, (i - step + root) % p]);
    }
    if (rd.length) rounds.push(rd);
  }
  return rounds;
}
function bcastRounds(p, root) {
  return reduceRounds(p, root).slice().reverse().map(rd => rd.map(([f, t]) => [t, f]));
}
function treeSteps(rounds, textFn, lines) {
  const out = [];
  rounds.forEach((rd, ri) => rd.forEach(([f, t], k) => {
    const s = S.msg(f, t, textFn(f, t, ri + 1, rounds.length), lines);
    if (k > 0) s.same = true;
    out.push(s);
  }));
  return out;
}

const EVENTS = {
  hello(p, c) {
    const R = c.refs;
    const s = [S.local(0, "Rank 0 prints its own greeting. It never sends to itself.", R.own)];
    for (let q = 1; q < p; q++) {
      s.push(S.msg(q, 0, "Rank " + q + " sends its greeting to rank 0 (tag 0). Rank 0's receive for source " + q + " takes it and prints it.", R.send.concat(R.recv)));
    }
    return {
      steps: s,
      note: p > 1
        ? "Rank 0 receives from rank 1, then 2, and so on, so the greetings always print in rank order. The workers can send in any order: a message just waits until rank 0 asks for it."
        : "With one process the receive loop runs zero times. Only rank 0's own greeting is printed.",
    };
  },

  hello2(p, c, st) {
    const R = c.refs;
    if (!st.perm || st.perm.length !== p - 1) st.perm = shuffled(p);
    const s = [S.local(0, "Rank 0 prints its own greeting.", R.own)];
    st.perm.forEach((q, k) => {
      s.push(S.msg(q, 0, "Arrival " + (k + 1) + ": rank " + q + "'s greeting, tagged rand() % 50. The wildcard receive accepts it, and status tells rank 0 the sender, the tag and the length.", R.send.concat(R.recv, R.status)));
    });
    return {
      steps: s,
      controls: [{ label: "Shuffle arrival order", fn() { st.perm = shuffled(p); } }],
      note: p > 1
        ? "MPI_ANY_SOURCE takes whichever message arrives first, so this order can change from run to run. Press the button to see another possible order."
        : "With one process there is nothing to receive.",
    };
  },

  sendrecv(p, c) {
    const R = c.refs;
    const s = [S.local(0, "Rank 0 reads a, b and n with scanf. Only rank 0 can read stdin.", R.scanf)];
    for (let d = 1; d < p; d++) {
      s.push(S.msg(0, d, "Rank 0 sends a, b, then n to rank " + d + " (three MPI_Send calls). Rank " + d + " receives them in the same order.", R.insend.concat(R.inrecv)));
    }
    s.push(S.band("Every rank runs Trap() on its own slice of the interval.", R.compute));
    for (let q = 1; q < p; q++) {
      s.push(S.msg(q, 0, "Rank " + q + " sends its partial integral (local_int) to rank 0, which adds it to total_int.", R.rsend.concat(R.rrecv)));
    }
    s.push(S.local(0, "Rank 0 prints the total.", R.print));
    return {
      steps: s,
      note: "Messages: 3(p - 1) for the input plus (p - 1) for the results, which is " + 4 * (p - 1) + " for p = " + p + ". Every one of them goes to or from rank 0.",
    };
  },

  bcast(p, c) {
    const R = c.refs;
    const s = [S.local(0, "Rank 0 reads a, b and n with scanf.", R.scanf)];
    treeSteps(bcastRounds(p, 0), (f, t, k, n) => "MPI_Bcast, round " + k + " of " + n + ": rank " + f + " passes a, b, n on to rank " + t + ".", R.bcast).forEach(x => s.push(x));
    s.push(S.band("Every rank runs Trap() on its own slice of the interval.", R.compute));
    treeSteps(reduceRounds(p, 0), (f, t, k, n) => "MPI_Reduce, round " + k + " of " + n + ": rank " + f + " sends its partial sum to rank " + t + ", which adds it to its own.", R.reduce).forEach(x => s.push(x));
    s.push(S.local(0, "Rank 0 holds the total and prints it.", R.print));
    return {
      steps: s,
      note: "The tree is illustrative: real MPI libraries choose their own shape. Each collective moves data p - 1 times, but in only " + Math.ceil(Math.log2(Math.max(p, 1))) + " round(s) instead of " + Math.max(p - 1, 0) + " one after another.",
    };
  },

  tag_mismatch(p, c) {
    const R = c.refs;
    return {
      steps: [
        S.lost(1, 0, "Rank 1 sends x with tag 5. Rank 0 only accepts tag 7, so this message matches no receive.", R.send),
        S.block(0, "Rank 0 waits in MPI_Recv for source 1, tag 7. Nothing will ever match, so it never returns and the program hangs.", R.recv),
      ],
      note: "Fix: use the same tag on both sides, or receive with MPI_ANY_TAG.",
    };
  },

  head_to_head(p, c) {
    const R = c.refs;
    return {
      steps: [
        S.block(0, "Rank 0 is inside MPI_Ssend to rank 1. MPI_Ssend does not return until rank 1 has started a matching receive.", R.send),
        S.block(1, "Rank 1 is inside MPI_Ssend to rank 0, waiting for rank 0 to start a receive. Each rank waits for the other, so neither reaches its MPI_Recv.", R.send),
      ],
      note: "Deadlock. Fix: even ranks send first and odd ranks receive first, or use MPI_Sendrecv.",
    };
  },

  reduce_order(p, c) {
    const R = c.refs;
    return {
      steps: [
        S.band("Collective #1. Rank 1 passes c (2) here, ranks 0 and 2 pass a (1). The sum 2 + 1 + 1 = 4 is stored in rank 0's b.", R.first),
        S.band("Collective #2. Rank 1 passes a (1) here, ranks 0 and 2 pass c (2). The sum 1 + 2 + 2 = 5 is stored in rank 0's d.", R.second),
        S.local(0, "Rank 0 prints b = 4, d = 5.", R.print),
      ],
      note: "Collective calls match by the order they are made, never by variable name.",
    };
  },
};

/* ---------------------------------------------------------------- walk widget */

function initWalk(root) {
  const cfg = JSON.parse($('script[type="application/json"]', root).textContent);
  const gen = EVENTS[cfg.example];
  if (!gen) return;
  const listing = $(".listing", root);
  const nodes = $$(".ln, .anno", listing);
  const lineEls = $$(".ln", listing);
  const rankBox = $(".ranks", root);
  const pval = $(".pval", root);
  const summary = $(".summary", root);
  const lanesBox = $(".lanes", root);
  const log = $(".log", root);
  const lnote = $(".lanes-note", root);
  const stepbar = $(".stepbar", root);
  const stepinfo = $(".stepinfo", stepbar);
  const state = { p: cfg.fixed_p || cfg.p || 4, rank: "all", step: null };
  let res = null;
  let stepEls = [];
  let logEls = [];
  let laneEls = [];

  function renderRanks() {
    rankBox.innerHTML = "";
    const mk = (value, label, cls) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "rk " + cls;
      b.textContent = label;
      b.dataset.rank = value;
      b.setAttribute("aria-pressed", String(String(state.rank) === String(value)));
      rankBox.appendChild(b);
    };
    mk("all", "All ranks", "");
    for (let r = 0; r < Math.min(state.p, 8); r++) mk(String(r), "Rank " + r, r === 0 ? "r0" : "rw");
  }

  function applyLens() {
    const r = state.rank, p = state.p;
    listing.dataset.sel = r === "all" ? "all" : r === 0 ? "zero" : "worker";
    nodes.forEach(n => {
      const role = n.dataset.who;
      n.classList.remove("dim", "never", "own");
      if (r === "all") {
        if (neverRuns(role, p)) n.classList.add("never");
      } else if (!executes(role, r, p)) {
        n.classList.add("dim");
      } else if (role !== "all") {
        n.classList.add("own");
      }
    });
  }

  function updateSummary() {
    const sums = cfg.summaries || {};
    const r = state.rank;
    const t = r === "all" ? (sums.all || "") : (sums[String(r)] || sums[r === 0 ? "zero" : "worker"] || "");
    summary.textContent = t.replace(/\{p\}/g, state.p).replace(/\{r\}/g, r).replace(/\{m\}/g, state.p - 1);
  }

  function involves(st, r) {
    if (st.t === "msg" || st.t === "lost") return st.from === r || st.to === r;
    if (st.t === "local" || st.t === "block") return st.rank === r;
    return true;
  }

  function fade() {
    const r = state.rank;
    steps().forEach((st, i) => {
      const f = r !== "all" && !involves(st, r);
      if (stepEls[i]) stepEls[i].classList.toggle("faded", f);
      if (logEls[i]) logEls[i].classList.toggle("faded", f);
    });
    laneEls.forEach((g, i) => g.classList.toggle("faded", r !== "all" && r !== i));
  }

  function steps() { return res ? res.steps : []; }

  function applyHot(i) {
    const want = new Set(i == null || !steps()[i] ? [] : steps()[i].lines);
    lineEls.forEach(e => e.classList.toggle("hot", want.has(+e.dataset.line)));
    stepEls.forEach((g, k) => g.classList.toggle("hot", k === i));
    logEls.forEach((li, k) => li.classList.toggle("hot", k === i));
  }

  function updateSteps(scroll) {
    const n = steps().length;
    stepEls.forEach((g, i) => g.classList.toggle("future", state.step !== null && i > state.step));
    logEls.forEach((li, i) => li.classList.toggle("future", state.step !== null && i > state.step));
    $('[data-s="prev"]', stepbar).disabled = state.step === null || state.step === 0;
    $('[data-s="next"]', stepbar).disabled = n === 0 || state.step === n - 1;
    $('[data-s="all"]', stepbar).disabled = state.step === null;
    stepinfo.textContent = state.step === null ? n + " steps" : "Step " + (state.step + 1) + " of " + n;
    applyHot(state.step);
    if (scroll && state.step !== null) {
      const first = lineEls.find(e => e.classList.contains("hot"));
      if (first) first.scrollIntoView({ block: "nearest", behavior: reduceMotion ? "auto" : "smooth" });
    }
  }

  function drawLanes() {
    const p = state.p;
    const st = res.steps;
    let row = 0;
    st.forEach(s => { if (!s.same) row++; s.row = row; });
    const dx = Math.min(56, Math.floor(400 / p));
    const padX = 22, rowH = 32, top = 62;
    const W = padX * 2 + dx * p;
    const H = top + row * rowH + 14;
    const X = i => padX + dx * i + dx / 2;
    const Y = r => top + (r - 1) * rowH;

    lanesBox.innerHTML = "";
    const root_ = svg("svg", {
      viewBox: "0 0 " + W + " " + H, role: "img",
      "aria-label": "Timeline of " + st.length + " steps across " + p + " rank" + (p > 1 ? "s" : "") + ". The numbered list below describes every step.",
    }, lanesBox);
    root_.style.maxWidth = Math.max(W, 220) + "px";

    const stuck = {};
    st.forEach(s => { if (s.t === "block" && stuck[s.rank] === undefined) stuck[s.rank] = s.row; });

    laneEls = [];
    for (let i = 0; i < p; i++) {
      const g = svg("g", { class: "lanegrp" }, root_);
      const cls = i === 0 ? "c0" : "c1";
      const hdr = svg("g", { class: "hdr" }, g);
      svg("rect", { x: X(i) - 13, y: 8, width: 26, height: 24, rx: 7, class: cls }, hdr);
      svg("text", { x: X(i), y: 25, class: cls }, hdr).textContent = i;
      if (stuck[i] !== undefined) {
        svg("line", { x1: X(i), x2: X(i), y1: 36, y2: Y(stuck[i]), class: "lane" }, g);
        svg("line", { x1: X(i), x2: X(i), y1: Y(stuck[i]), y2: H - 6, class: "lane stuck" }, g);
      } else {
        svg("line", { x1: X(i), x2: X(i), y1: 36, y2: H - 6, class: "lane" }, g);
      }
      laneEls.push(g);
    }

    stepEls = [];
    const badge = (g, cx, cy, n, cls) => {
      svg("circle", { cx, cy, r: 8.5, class: "badge " + cls }, g);
      svg("text", { x: cx, y: cy + 3.6, class: "badge-t " + cls }, g).textContent = n;
    };
    st.forEach((s, i) => {
      const y = Y(s.row);
      const role = (s.t === "msg" || s.t === "lost") ? (s.from === 0 ? "c0" : "c1") : (s.rank === 0 ? "c0" : "c1");
      const g = svg("g", { class: "st", "data-i": i }, root_);
      svg("title", {}, g).textContent = (i + 1) + ". " + s.text;
      if (s.t === "msg") {
        const x1 = X(s.from), x2 = X(s.to), dir = x2 > x1 ? 1 : -1;
        svg("line", { x1, y1: y, x2: x2 - dir * 6, y2: y, class: "arrow " + role }, g);
        svg("path", { d: "M" + x2 + " " + y + " l" + (-dir * 11) + " -5.5 l0 11 z", class: "arrow " + role, "stroke-linejoin": "round" }, g);
        badge(g, (x1 + x2) / 2, y - 12, i + 1, role);
      } else if (s.t === "lost") {
        const x1 = X(s.from), x2 = X(s.to), dir = x2 > x1 ? 1 : -1, ex = x2 - dir * 16;
        svg("line", { x1, y1: y, x2: ex, y2: y, class: "badline" }, g);
        svg("path", { d: "M" + (ex - 5) + " " + (y - 5) + " l10 10 M" + (ex + 5) + " " + (y - 5) + " l-10 10", class: "bad" }, g);
        badge(g, (x1 + ex) / 2, y - 12, i + 1, "cx");
      } else if (s.t === "local") {
        svg("circle", { cx: X(s.rank), cy: y, r: 7, class: "dot " + role }, g);
        badge(g, X(s.rank) + 20, y, i + 1, role);
      } else if (s.t === "block") {
        svg("path", { d: "M" + (X(s.rank) - 6) + " " + (y - 6) + " l12 12 M" + (X(s.rank) + 6) + " " + (y - 6) + " l-12 12", class: "bad" }, g);
        badge(g, X(s.rank) + 20, y, i + 1, "cx");
      } else if (s.t === "band") {
        svg("rect", { x: X(0) - 14, y: y - 8, width: X(p - 1) - X(0) + 28, height: 16, rx: 8, class: "band" }, g);
        badge(g, X(0) - 14, y, i + 1, "c0");
      }
      g.addEventListener("mouseenter", () => applyHot(i));
      g.addEventListener("mouseleave", () => applyHot(state.step));
      stepEls.push(g);
    });

    log.innerHTML = "";
    logEls = st.map((s, i) => {
      const li = document.createElement("li");
      li.tabIndex = 0;
      const cls = s.t === "lost" || s.t === "block" ? "cx" : ((s.t === "msg" ? s.from : s.rank) === 0 ? "c0" : "c1");
      li.innerHTML = '<span class="bn ' + (s.t === "band" ? "c0" : cls) + '">' + (i + 1) + "</span><span>" + esc(s.text) + "</span>";
      li.addEventListener("mouseenter", () => applyHot(i));
      li.addEventListener("mouseleave", () => applyHot(state.step));
      li.addEventListener("focus", () => applyHot(i));
      li.addEventListener("blur", () => applyHot(state.step));
      log.appendChild(li);
      return li;
    });
    lnote.textContent = res.note || "";

    $$(".xbtn", stepbar).forEach(b => b.remove());
    (res.controls || []).forEach(ctl => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "xbtn";
      b.textContent = ctl.label;
      b.addEventListener("click", () => { ctl.fn(); rebuild(false); });
      stepbar.insertBefore(b, stepinfo);
    });
  }

  function rebuild(resetStep) {
    if (state.rank !== "all" && state.rank >= state.p) state.rank = "all";
    pval.textContent = state.p;
    $$('[data-act="p-"]', root).forEach(b => { b.disabled = state.p <= 1; });
    $$('[data-act="p+"]', root).forEach(b => { b.disabled = state.p >= 8; });
    res = gen(state.p, cfg, state);
    if (resetStep) state.step = null;
    if (state.step !== null && state.step >= res.steps.length) state.step = null;
    renderRanks();
    applyLens();
    updateSummary();
    drawLanes();
    fade();
    updateSteps(false);
  }

  root.addEventListener("click", e => {
    const pb = e.target.closest("[data-act]");
    if (pb && root.contains(pb)) {
      state.p = Math.max(1, Math.min(8, state.p + (pb.dataset.act === "p+" ? 1 : -1)));
      rebuild(true);
      return;
    }
    const rb = e.target.closest(".rk");
    if (rb) {
      state.rank = rb.dataset.rank === "all" ? "all" : +rb.dataset.rank;
      $$(".rk", rankBox).forEach(b => b.setAttribute("aria-pressed", String(b === rb)));
      applyLens();
      updateSummary();
      fade();
      return;
    }
    const sb = e.target.closest("button[data-s]");
    if (sb) {
      const n = steps().length;
      if (sb.dataset.s === "all") state.step = null;
      else if (sb.dataset.s === "next") state.step = state.step === null ? 0 : Math.min(n - 1, state.step + 1);
      else state.step = state.step === null ? 0 : Math.max(0, state.step - 1);
      updateSteps(true);
    }
  });

  rebuild(true);
}

/* ---------------------------------------------------------------- match lab */

function initMatch(root) {
  const g = id => $("#" + id, root);
  const comm = c => (c === "world" ? "MPI_COMM_WORLD" : "other_comm");

  function read() {
    const num = (id, min, dflt) => {
      const v = parseInt(g(id).value, 10);
      return Number.isFinite(v) ? Math.max(min, v) : dflt;
    };
    return {
      dest: +g("m-dest").value, stag: num("m-stag", 0, 0), scomm: g("m-scomm").value, stype: g("m-stype").value, scount: num("m-scount", 1, 1),
      src: g("m-src").value, rtag: num("m-rtag", 0, 0), anytag: g("m-anytag").checked, rcomm: g("m-rcomm").value, rtype: g("m-rtype").value, rcount: num("m-rcount", 1, 1),
    };
  }

  function calc() {
    const v = read();
    g("m-rtag").disabled = v.anytag;
    const sendCall = "MPI_Send(&x, " + v.scount + ", " + v.stype + ", " + v.dest + ", " + v.stag + ", " + comm(v.scomm) + ");";
    const recvCall = "MPI_Recv(&y, " + v.rcount + ", " + v.rtype + ", " + (v.src === "any" ? "MPI_ANY_SOURCE" : v.src) + ", " +
      (v.anytag ? "MPI_ANY_TAG" : v.rtag) + ", " + comm(v.rcomm) + ", &status);";
    g("m-calls").innerHTML = mpiSpans(sendCall) + '   <span class="who">// on rank 1</span>\n' + mpiSpans(recvCall) + '   <span class="who">// on rank 0</span>';

    const checks = [
      [v.scomm === v.rcomm, "The communicators agree.", "Different communicators: a message sent on one can never be received on the other.", true],
      [v.dest === 0, "The send is addressed to rank 0.", "The send is addressed to rank " + v.dest + ", but the receiver is rank 0.", true],
      [v.src === "any" || +v.src === 1, v.src === "any" ? "MPI_ANY_SOURCE accepts a message from rank 1." : "Rank 0 is waiting for rank 1, which is the sender.", "Rank 0 is waiting for rank " + v.src + ", but the sender is rank 1.", true],
      [v.anytag || v.rtag === v.stag, v.anytag ? "MPI_ANY_TAG accepts tag " + v.stag + "." : "The tags agree (" + v.stag + ").", "The tags differ: sent " + v.stag + ", wanted " + v.rtag + ".", true],
      [v.stype === v.rtype, "The datatypes agree.", "The datatypes differ (" + v.stype + " sent, " + v.rtype + " expected). MPI requires them to agree.", false],
      [v.rcount >= v.scount, "The receive buffer (" + v.rcount + ") is big enough for the " + v.scount + " element(s) sent.", "The message has " + v.scount + " elements but the buffer holds only " + v.rcount + ".", false],
    ];
    const envelopeOk = checks.slice(0, 4).every(c => c[0]);
    let cls, text;
    if (!envelopeOk) {
      cls = "bad";
      text = "<strong>No match.</strong> Rank 0 waits in MPI_Recv forever, so the program hangs. The send either blocks too, or its message is never delivered.";
    } else if (!checks[4][0]) {
      cls = "bad";
      text = "<strong>The envelope matches but the datatypes do not.</strong> MPI requires matching types, so the data arrives wrong or the call fails.";
    } else if (!checks[5][0]) {
      cls = "bad";
      text = "<strong>Message truncated.</strong> The message is bigger than rank 0's buffer, so MPI aborts with an error (seen with MPICH).";
    } else {
      cls = "good";
      text = "<strong>Match.</strong> Rank 0 receives " + v.scount + " element(s)." +
        (v.src === "any" || v.anytag
          ? " After a wildcard receive, status.MPI_SOURCE is 1, status.MPI_TAG is " + v.stag + ", and MPI_Get_count reports " + v.scount + "."
          : "");
    }
    const vd = g("m-verdict");
    vd.className = "verdict " + cls;
    vd.innerHTML = text;
    g("m-checks").innerHTML = checks.map(c => '<li class="' + (c[0] ? "ok" : "no") + '">' + esc(c[0] ? c[1] : c[2]) + "</li>").join("");
  }

  const base = { "m-dest": "0", "m-stag": "0", "m-scomm": "world", "m-stype": "MPI_INT", "m-scount": "1", "m-src": "1", "m-rtag": "0", "m-rcomm": "world", "m-rtype": "MPI_INT", "m-rcount": "1" };
  const presets = {
    ok: {},
    tag: { "m-stag": "5", "m-rtag": "7" },
    small: { "m-scount": "10", "m-rcount": "5" },
    wild: { "m-stag": "7", "m-src": "any", anytag: true },
  };
  root.addEventListener("click", e => {
    const b = e.target.closest("[data-preset]");
    if (!b) return;
    const pr = presets[b.dataset.preset];
    for (const id in base) g(id).value = base[id];
    g("m-anytag").checked = false;
    for (const id in pr) { if (id === "anytag") g("m-anytag").checked = pr[id]; else g(id).value = pr[id]; }
    calc();
  });
  root.addEventListener("input", calc);
  root.addEventListener("change", calc);
  calc();
}

/* ---------------------------------------------------------------- collective lab */

function initColl(root) {
  const op = $("#c-op", root), pSel = $("#c-p", root), rootSel = $("#c-root", root), rootWrap = $("#c-root-wrap", root);
  const call = $("#c-call", root), cards = $("#c-cards", root), rounds = $("#c-rounds", root);

  function fillRoot(p) {
    const keep = +rootSel.value || 0;
    rootSel.innerHTML = "";
    for (let r = 0; r < p; r++) {
      const o = document.createElement("option");
      o.value = r; o.textContent = "rank " + r;
      rootSel.appendChild(o);
    }
    rootSel.value = String(Math.min(keep, p - 1));
  }

  function render() {
    const p = +pSel.value;
    if (rootSel.options.length !== p) fillRoot(p);
    const k = op.value;
    const root_ = +rootSel.value;
    const uses = k !== "allreduce";
    rootWrap.style.display = uses ? "" : "none";
    const rt = uses ? root_ : 0;

    const calls = {
      bcast: "MPI_Bcast(&buf, 1, MPI_INT, " + rt + ", MPI_COMM_WORLD);",
      reduce: "MPI_Reduce(&in, &out, 1, MPI_INT, MPI_SUM, " + rt + ", MPI_COMM_WORLD);",
      allreduce: "MPI_Allreduce(&in, &out, 1, MPI_INT, MPI_SUM, MPI_COMM_WORLD);",
      scatter: "MPI_Scatter(all, 2, MPI_INT, mine, 2, MPI_INT, " + rt + ", MPI_COMM_WORLD);",
      gather: "MPI_Gather(mine, 2, MPI_INT, all, 2, MPI_INT, " + rt + ", MPI_COMM_WORLD);",
    };
    call.innerHTML = mpiSpans(calls[k]) + '   <span class="who">// every rank makes this call</span>';

    const sum = p * (p + 1) / 2;
    const arr = Array.from({ length: 2 * p }, (_, i) => i + 1);
    const data = [];
    for (let r = 0; r < p; r++) {
      let before = [], after = [];
      if (k === "bcast") {
        before = [["buf", r === rt ? "42" : "?"]];
        after = [["buf", "42", r !== rt]];
      } else if (k === "reduce") {
        before = [["in", String(r + 1)], ["out", "-1"]];
        after = [["in", String(r + 1)], ["out", r === rt ? String(sum) : "-1", r === rt]];
      } else if (k === "allreduce") {
        before = [["in", String(r + 1)], ["out", "-1"]];
        after = [["in", String(r + 1)], ["out", String(sum), true]];
      } else if (k === "scatter") {
        before = [["all", r === rt ? "[" + arr.join(" ") + "]" : "(not used)"], ["mine", "[? ?]"]];
        after = [["mine", "[" + (2 * r + 1) + " " + (2 * r + 2) + "]", true]];
      } else {
        before = [["mine", "[" + (2 * r + 1) + " " + (2 * r + 2) + "]"], ["all", "[?" + " ?".repeat(2 * p - 1) + "]"]];
        after = [["all", r === rt ? "[" + arr.join(" ") + "]" : "[?" + " ?".repeat(2 * p - 1) + "]", r === rt]];
      }
      data.push({ before, after });
    }
    cards.innerHTML = data.map((d, r) => {
      const row = (label, items) => '<div class="row"><b>' + label + "</b>" +
        items.map(it => "<span" + (it[2] ? ' class="changed"' : "") + ">" + esc(it[0]) + " = " + esc(it[1]) + "</span>").join("") + "</div>";
      return '<div class="card ' + (r === 0 ? "c0" : "c1") + '"><h3>rank ' + r + (r === rt && uses ? " (root)" : "") + "</h3>" + row("before", d.before) + row("after", d.after) + "</div>";
    }).join("");

    // rounds
    let html = "";
    const lg = Math.ceil(Math.log2(p));
    if (k === "bcast") {
      const rds = bcastRounds(p, rt);
      html += "<p>A tree needs " + rds.length + " round(s). A loop of sends from the root would need " + (p - 1) + " one after another.</p><ol>";
      rds.forEach((rd, i) => { html += '<li><span class="rd">Round ' + (i + 1) + "</span>" + rd.map(([f, t]) => "rank " + f + " sends 42 to rank " + t).join(", ") + "</li>"; });
      html += "</ol>";
    } else if (k === "reduce") {
      const rds = reduceRounds(p, rt);
      const vals = Array.from({ length: p }, (_, r) => r + 1);
      html += "<p>A tree needs " + rds.length + " round(s). A loop of receives on the root would need " + (p - 1) + " one after another.</p><ol>";
      rds.forEach((rd, i) => {
        const parts = rd.map(([f, t]) => { const sent = vals[f]; vals[t] += sent; return "rank " + f + " sends " + sent + " to rank " + t + " (now " + vals[t] + ")"; });
        html += '<li><span class="rd">Round ' + (i + 1) + "</span>" + parts.join(", ") + "</li>";
      });
      html += "</ol>";
    } else if (k === "allreduce") {
      if ((p & (p - 1)) === 0) {
        let vals = Array.from({ length: p }, (_, r) => r + 1);
        html += "<p>A butterfly needs " + lg + " round(s), and everyone ends with the total.</p><ol>";
        for (let s = 1, i = 1; s < p; s *= 2, i++) {
          const next = vals.map((v, r) => v + vals[r ^ s]);
          const pairs = [];
          for (let r = 0; r < p; r++) if (r < (r ^ s)) pairs.push("ranks " + r + " and " + (r ^ s) + " swap and both hold " + next[r]);
          html += '<li><span class="rd">Round ' + i + "</span>" + pairs.join(", ") + "</li>";
          vals = next;
        }
        html += "</ol>";
      } else {
        html += "<p>Every rank ends with " + sum + ". With " + p + " processes (not a power of two) the exchange pattern depends on the MPI library.</p>";
      }
    }
    rounds.className = "rounds";
    rounds.innerHTML = html;
  }

  root.addEventListener("input", render);
  root.addEventListener("change", render);
  render();
}

/* ---------------------------------------------------------------- practice marks */

function initPractice() {
  const qs = $$("section.q");
  const prog = $(".qprogress");
  if (!qs.length) return;
  const KEY = "cis3090-mt2-marks";
  let store = {};
  try { store = JSON.parse(localStorage.getItem(KEY) || "{}") || {}; } catch (e) { store = {}; }
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(store)); } catch (e) { /* private mode */ } };

  function paint() {
    let got = 0, missed = 0;
    qs.forEach(q => {
      const m = store[q.dataset.q];
      q.classList.toggle("got", m === "got");
      q.classList.toggle("missed", m === "missed");
      if (m === "got") got++;
      if (m === "missed") missed++;
      const st = $(".qstate", q);
      if (st) st.textContent = m === "got" ? "Marked as got it" : m === "missed" ? "Marked as missed" : "";
    });
    if (prog) {
      const only = document.body.classList.contains("only-missed");
      prog.innerHTML = '<span class="score">' + got + " got it, " + missed + " missed, " + (qs.length - got - missed) + " not marked yet</span>" +
        '<button type="button" data-f="missed">' + (only ? "Show all questions" : "Review missed only") + "</button>" +
        '<button type="button" data-f="reset">Clear marks</button>';
    }
  }

  document.addEventListener("click", e => {
    const mb = e.target.closest("[data-mark]");
    if (mb) {
      const q = mb.closest("section.q");
      store[q.dataset.q] = mb.dataset.mark;
      save(); paint();
      return;
    }
    const fb = e.target.closest(".qprogress [data-f]");
    if (fb) {
      if (fb.dataset.f === "reset") { store = {}; save(); document.body.classList.remove("only-missed"); }
      else document.body.classList.toggle("only-missed");
      paint();
    }
  });
  paint();
}

/* ---------------------------------------------------------------- trapezoid trace */

function initTrace() {
  if (!$("#in-a")) return;
  const f = x => x * x;
  const trap = (l, r, n, h) => {
    let e = (f(l) + f(r)) / 2.0;
    for (let i = 1; i <= n - 1; i++) e += f(l + i * h);
    return e * h;
  };
  const cExp = x => x.toExponential(15).replace(/e([+-])(\d)$/, "e$10$2");
  const $id = id => document.getElementById(id);

  function compute(a, b, n, p) {
    const h = (b - a) / n, localN = Math.floor(n / p), ranks = [];
    let total = 0;
    for (let r = 0; r < p; r++) {
      const la = a + r * localN * h, lb = la + localN * h, li = trap(la, lb, localN, h);
      ranks.push({ rank: r, localN, la, lb, li });
      total = r === 0 ? li : total + li;
    }
    return { h, localN, ranks, total };
  }
  const chip = r => '<span class="chip ' + (r === 0 ? "r0" : "rx") + '">rank ' + r + "</span>";

  function render() {
    const a = parseFloat($id("in-a").value), b = parseFloat($id("in-b").value);
    const n = parseInt($id("in-n").value, 10), p = parseInt($id("in-p").value, 10);
    const note = $id("lane-note"), bar = $id("bar"), rows = $id("rows");
    if (!isFinite(a) || !isFinite(b) || !(n >= 1) || !(p >= 1) || p > 64) {
      note.innerHTML = '<span class="warn-t">Enter numbers for a and b, an n of at least 1, and 1 to 64 ranks.</span>';
      return;
    }
    const res = compute(a, b, n, p);
    const covered = res.localN * p, leftover = n - covered;

    let html = "";
    res.ranks.forEach(rk => {
      const w = (rk.localN / n) * 100;
      const cls = rk.rank === 0 ? "c0" : rk.rank % 2 ? "c1" : "c2";
      html += '<div class="seg ' + cls + '" style="width:' + w + '%" title="rank ' + rk.rank + ": " + rk.la.toFixed(4) + " to " + rk.lb.toFixed(4) + '">' + (w > 4 ? rk.rank : "") + "</div>";
    });
    if (leftover > 0) html += '<div class="seg skipped" style="width:' + (leftover / n) * 100 + '%" title="never computed: ' + leftover + ' trapezoids"></div>';
    bar.innerHTML = html;
    bar.setAttribute("aria-label", p + " ranks each covering " + res.localN + " of " + n + " trapezoids" + (leftover > 0 ? "; " + leftover + " are never computed" : ""));
    $id("ax-a").textContent = "a = " + a;
    $id("ax-b").textContent = "b = " + b;

    if (res.localN === 0) {
      note.innerHTML = '<span class="warn-t">n is smaller than comm_sz, so local_n is 0 and Trap() returns a meaningless value.</span> The textbook assumes n is at least comm_sz.';
    } else if (leftover > 0) {
      note.innerHTML = '<span class="warn-t">' + n + " does not divide evenly by " + p + ".</span> Each rank does " + res.localN + " trapezoids, so " + covered + " are covered and " + leftover + " (hatched) never are.";
    } else {
      note.textContent = n + " trapezoids split evenly: " + res.localN + " per rank.";
    }

    const shown = res.ranks.slice(0, 16);
    rows.innerHTML = shown.map(rk => "<tr><td>" + chip(rk.rank) + "</td><td>" + rk.localN + "</td><td>" + rk.la.toFixed(6) + "</td><td>" + rk.lb.toFixed(6) + "</td><td>" + rk.li.toPrecision(10) + "</td></tr>").join("");
    if (res.ranks.length > shown.length) rows.innerHTML += '<tr><td colspan="5">' + (res.ranks.length - shown.length) + " more ranks with the same local_n</td></tr>";

    const exact = (b * b * b - a * a * a) / 3;
    $id("o-h").textContent = String(res.h);
    $id("o-total").textContent = cExp(res.total);
    $id("o-exact").textContent = String(exact);
    $id("o-err").textContent = (res.total - exact).toExponential(3);
    $id("o-used").textContent = covered + " of " + n;
    $id("o-msgs").textContent = "mpi_SendRec.c sends " + 4 * (p - 1) + " messages, all through rank 0. mpi_Bcast.c makes 4 collective calls on every rank.";
  }
  ["in-a", "in-b", "in-n", "in-p"].forEach(id => $id(id).addEventListener("input", render));
  render();
}

/* ---------------------------------------------------------------- start */

$$(".walk").forEach(initWalk);
const ml = $("#matchlab"); if (ml) initMatch(ml);
const cl = $("#colllab"); if (cl) initColl(cl);
initPractice();
initTrace();
})();

/* Page furniture: jump links, notes toggle, function search, sidebar position. */
(() => {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const main = $("main");
  if (!main) return;

  function secLabel(li) {
    const first = li.firstElementChild;
    if (first && first.tagName === "P" && !li.firstChild.textContent.trim()) return first.textContent;
    let t = "";
    for (const c of li.childNodes) {
      if (c.nodeType === 1 && /^(UL|OL|FIGURE|SECTION|DIV|ASIDE)$/.test(c.tagName)) break;
      t += c.textContent;
    }
    return t;
  }

  // Under the current page in the sidebar, list the sections (or functions) on this page
  const targets = $$(":scope > ul > li.sec, :scope > .fn", main);
  const items = [];
  targets.forEach((t, i) => {
    const isFn = t.classList.contains("fn");
    const label = (isFn ? $("h2", t).textContent : secLabel(t)).trim().replace(/:$/, "");
    if (!label) return;
    t.id = t.id || "section-" + (i + 1);
    items.push({ id: t.id, label, fn: isFn });
  });
  if (items.length >= 2) {
    $$('.sidebar [aria-current="page"], .mobilenav nav [aria-current="page"]').forEach(link => {
      const toc = document.createElement("div");
      toc.className = "toc";
      items.forEach(it => {
        const a = document.createElement("a");
        a.href = "#" + it.id;
        if (it.fn) { const c = document.createElement("code"); c.textContent = it.label; a.append(c); }
        else a.textContent = it.label;
        toc.append(a);
      });
      link.after(toc);
    });
  }

  // hide or show the notes under the code
  $$(".walk").forEach(w => {
    const box = $(".notes-toggle input", w);
    if (box) box.addEventListener("change", () => w.classList.toggle("nonotes", !box.checked));
  });

  // search on the function index
  const f = $("#fnfilter");
  if (f) {
    const rows = $$(".fnrow");
    const groups = $$(".fngroup");
    const none = $(".fnempty");
    f.addEventListener("input", () => {
      const q = f.value.trim().toLowerCase();
      rows.forEach(r => { r.hidden = q !== "" && !r.textContent.toLowerCase().includes(q); });
      groups.forEach(g => { g.hidden = $$(".fnrow:not([hidden])", g).length === 0; });
      if (none) none.hidden = groups.some(g => !g.hidden);
    });
  }

  // keep the current page visible in the sidebar
  const side = $(".sidebar");
  const cur = side && $('[aria-current="page"]', side);
  if (cur) side.scrollTop = Math.max(0, cur.offsetTop - side.clientHeight / 3);
})();
