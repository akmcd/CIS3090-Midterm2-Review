/* Notes pages (Read, Code, Reference): foldable subsections, contents highlighting, "Section done" ticks. */
(function () {
  'use strict';
  const S = window.Study;

  /* Contents list: highlight the section you are reading. */
  const links = Array.from(document.querySelectorAll('.toc a'));
  const secs = links.map(a => document.querySelector(a.getAttribute('href')));
  function mark() {
    let cur = 0;
    secs.forEach((s, i) => { if (s && s.getBoundingClientRect().top < 120) cur = i; });
    links.forEach((a, i) => a.classList.toggle('active', i === cur));
  }
  if (links.length) { document.addEventListener('scroll', mark, { passive: true }); mark(); }

  /* Collapsible subsections: each top-level bullet with a nested list becomes a toggle. */
  const toggles = [];
  document.querySelectorAll('ul.notes > li').forEach((li, n) => {
    const sub = li.querySelector(':scope > ul');
    if (!sub) return;
    const btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'notes-toggle';
    btn.setAttribute('aria-expanded', 'true');
    sub.id = sub.id || 'sub-' + n;
    btn.setAttribute('aria-controls', sub.id);
    while (li.firstChild && li.firstChild !== sub) btn.appendChild(li.firstChild);
    li.insertBefore(btn, sub);
    li.classList.add('collapsible');
    const set = open => { btn.setAttribute('aria-expanded', String(open)); sub.hidden = !open; };
    btn.addEventListener('click', () => set(btn.getAttribute('aria-expanded') !== 'true'));
    toggles.push({ li, set });
  });
  const all = (id, open) => { const b = document.getElementById(id); if (b) b.addEventListener('click', () => toggles.forEach(t => t.set(open))); };
  all('collapse-all', false);
  all('expand-all', true);

  /* A link into a folded subsection opens it. */
  function openTarget() {
    if (!location.hash) return;
    let t = null;
    try { t = document.querySelector(location.hash); } catch (e) { return; }
    toggles.forEach(x => { if (t && x.li.contains(t)) x.set(true); });
  }
  window.addEventListener('hashchange', openTarget);
  openTarget();

  /* "Section done" ticks, shown in the contents list too. */
  if (!S) return;
  let done = new Set(S.store.get('readDone', []));
  const boxes = Array.from(document.querySelectorAll('input[data-read]'));
  function paint() {
    boxes.forEach(b => { b.checked = done.has(b.dataset.read); });
    links.forEach(a => a.classList.toggle('is-done', done.has(a.getAttribute('href').slice(1))));
  }
  boxes.forEach(b => b.addEventListener('change', () => {
    if (b.checked) done.add(b.dataset.read); else done.delete(b.dataset.read);
    S.store.set('readDone', Array.from(done)); paint();
  }));
  paint();
})();
