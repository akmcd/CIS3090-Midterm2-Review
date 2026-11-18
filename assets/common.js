/* Shared helpers for every page: header/nav, theme, storage, text formatting, shuffling, answer checking. */
(function () {
  'use strict';

  /* ---------- Exam settings: edit these two lines ---------- */
  /* Set the date once you know it, e.g. new Date('2026-12-10T00:00:00-05:00'). Leave null to hide the countdown. */
  const EXAM_DATE = null;
  const EXAM_NAME = 'Midterm 2 Review';

  const TOPICS = {
    'concepts': '1. Distributed memory and MPI',
    'method': '2. Reading MPI code',
    'sendrecv': '3. Send and receive',
    'collectives': '4. Collective communication',
    'trapezoid': '5. The trapezoidal rule',
    'odd_even': '6. Odd-even sort with MPI',
    'heat': '7. Heat distribution with MPI',
    'performance': '8. Hardware and performance',
    'gpgpu': '9. GPGPU and Warp',
    'imaging': '10. Image processing basics',
    'filters': '11. Sharpening and smoothing'
  };
  const TOPIC_ORDER = Object.keys(TOPICS);

  /* ---------- Storage (per-browser conveniences only; never required) ---------- */
  const NS = 'cis3090-mt2:';
  const store = {
    get(key, fallback) {
      try {
        const raw = window.localStorage.getItem(NS + key);
        return raw === null ? fallback : JSON.parse(raw);
      } catch (e) { return fallback; }
    },
    set(key, value) {
      try { window.localStorage.setItem(NS + key, JSON.stringify(value)); } catch (e) { /* storage unavailable */ }
    },
    remove(key) {
      try { window.localStorage.removeItem(NS + key); } catch (e) { /* ignore */ }
    }
  };

  /* ---------- Text ---------- */
  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  /* Minimal inline markdown: `code` and **bold** on escaped text. */
  function md(s) {
    const parts = String(s).split('`');
    return parts.map((p, i) => {
      if (i % 2 === 1) return '<code>' + esc(p) + '</code>';
      return esc(p).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    }).join('');
  }

  /* ---------- Random ---------- */
  function shuffle(arr) {
    const a = arr.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }
  function optionOrder(q) { const idx = q.options.map((_, i) => i); return q.fixed ? idx : shuffle(idx); }

  /* ---------- Answers: single choice (answer is a number) or select-all (answer is an array) ---------- */
  function isMulti(q) { return Array.isArray(q.answer); }
  function correctSet(q) { return isMulti(q) ? q.answer.slice().sort() : [q.answer]; }
  /* given: a number (single) or an array of option indices (multi); undefined means blank */
  function isCorrect(q, given) {
    if (given === undefined || given === null) return false;
    if (!isMulti(q)) return given === q.answer;
    const want = correctSet(q), got = given.slice().sort();
    return want.length === got.length && want.every((v, i) => v === got[i]);
  }
  function isRightOption(q, oi) { return correctSet(q).indexOf(oi) >= 0; }
  function answered(given) { return given !== undefined && given !== null && !(Array.isArray(given) && !given.length); }
  function answerText(q, given) {
    if (!answered(given)) return 'No answer';
    const list = Array.isArray(given) ? given.slice().sort() : [given];
    return list.map(i => md(q.options[i])).join('<br>');
  }

  /* Question stem: scenario (context and/or code) first, then the question itself. */
  function stemHTML(q) {
    let h = q.src ? '<p class="q-src">' + esc(q.src) + '</p>' : '';
    if (q.ctx || q.code || q.figure) {
      h += '<div class="q-scenario">' + (q.ctx ? String(q.ctx).split('\n').map(p => '<p>' + md(p) + '</p>').join('') : '') +
        (q.figure ? '<figure class="kc-fig">' + q.figure + '</figure>' : '') +
        (q.code ? '<pre><code>' + esc(q.code) + '</code></pre>' : '') + '</div>';
    }
    h += '<div class="q-text">' + md(q.q) + '</div>';
    if (isMulti(q)) h += '<p class="multi-note">Select all that apply.</p>';
    return h;
  }

  /* Follow-up questions asked in class, and a note when the quiz choices were written for this site. */
  function extrasHTML(q) {
    let h = '';
    if (q.followups && q.followups.length) {
      h += '<div class="followups"><p class="followups-h">Additional clarification</p>' + q.followups.map(f =>
        '<div class="followup"><p class="followup-q">You asked: ' + f.asked.map(a => '<q>' + esc(a) + '</q>').join(' then ') + '</p>' +
        f.answer.map(a => '<p>' + md(a) + '</p>').join('') + '</div>').join('') + '</div>';
    }
    if (q.answerFigure) h += '<figure class="kc-fig answer-fig">' + q.answerFigure + (q.answerFigureCaption ? '<figcaption class="lanes-caption">' + md(q.answerFigureCaption) + '</figcaption>' : '') + '</figure>';
    const src = q.choiceSource || (q.choicesNote ? 'written' : null);
    if (src === 'written') {
      h += '<p class="choices-note">The quiz\'s answer choices weren\'t recorded, so these choices were written for this site.</p>';
    } else if (src === 'recalled') {
      const list = idx => (idx || []).map(i => '<q>' + md(String(q.options[i]).replace(/\.$/, '')) + '</q>').join('; ');
      h += '<p class="choices-note">Choices as recalled from the quiz.' +
        ((q.completedChoices || []).length ? ' Only partly recalled, finished for this site: ' + list(q.completedChoices) + '.' : '') +
        ((q.addedChoices || []).length ? ' Added for practice (not from the quiz): ' + list(q.addedChoices) + '.' : '') + '</p>';
    }
    return h;
  }

  const KIND_LABEL = { concept: 'Concept', scenario: 'Scenario', calc: 'Calculation' };

  /* ---------- Header, nav and theme ---------- */
  const PAGES = [
    ['read.html', 'Read', 'read'],
    ['code.html', 'Code', 'code'],
    ['quiz.html', 'Quizzes', 'quiz'],
    ['short.html', 'Short answers', 'short'],
    ['flashcards.html', 'Flashcards', 'flashcards'],
    ['exam.html', 'Exam', 'exam'],
    ['ref_index.html', 'Reference', 'ref']
  ];

  function applyTheme(t) {
    if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
    else document.documentElement.removeAttribute('data-theme');
  }
  applyTheme(store.get('theme', null));

  function currentTheme() {
    const set = document.documentElement.getAttribute('data-theme');
    if (set) return set;
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function buildHeader() {
    const host = document.getElementById('site-header');
    if (!host) return;
    const page = document.body.getAttribute('data-page');
    const links = PAGES.map(p => '<a href="' + p[0] + '"' + (p[2] === page ? ' aria-current="page"' : '') + '>' + p[1] + '</a>').join('');
    host.className = 'site-header';
    host.innerHTML = '<div class="inner">' +
      '<a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true"><span></span><span></span><span></span><span></span></span>CIS*3090 ' + esc(EXAM_NAME) + '</a>' +
      '<nav class="site-nav" aria-label="Main">' + links + '</nav>' +
      '<button class="theme-toggle" type="button"></button></div>';
    const btn = host.querySelector('.theme-toggle');
    const label = () => { btn.textContent = currentTheme() === 'dark' ? 'Light mode' : 'Dark mode'; };
    label();
    btn.addEventListener('click', () => {
      const next = currentTheme() === 'dark' ? 'light' : 'dark';
      applyTheme(next); store.set('theme', next); label();
    });
  }

  /* Whole days until the exam, or null when no date is set. */
  function daysUntilExam(now) {
    if (!EXAM_DATE) return null;
    const ms = EXAM_DATE.getTime() - (now || new Date()).getTime();
    return Math.ceil(ms / 86400000);
  }

  document.addEventListener('DOMContentLoaded', buildHeader);

  window.Study = {
    TOPICS, TOPIC_ORDER, store, esc, md, shuffle, optionOrder, stemHTML, extrasHTML, KIND_LABEL,
    isMulti, isCorrect, isRightOption, correctSet, answered, answerText, daysUntilExam, EXAM_DATE, EXAM_NAME
  };
})();
