/* Home page: progress on each study tool and a "continue" button. */
(function () {
  'use strict';
  const S = window.Study;
  const set = (id, text) => { const e = document.getElementById(id); if (e) e.textContent = text; };

  set('n-quiz', window.QUIZ_BANK.length);
  set('n-short', window.SHORT_BANK.length);
  set('n-exam', window.EXAM_A.length);

  const read = S.store.get('readDone', []);
  set('stat-read', read.length + ' of ' + S.TOPIC_ORDER.length + ' sections done');
  const next = S.TOPIC_ORDER.filter(t => read.indexOf(t) < 0)[0];
  const cont = document.getElementById('continue');
  if (read.length && next) { cont.textContent = 'Continue: ' + S.TOPICS[next]; cont.href = 'read.html#' + next; }
  else if (read.length) { cont.textContent = 'Review the cheat sheet'; cont.href = 'read.html#cheat'; }
  document.querySelectorAll('a[data-plan]').forEach(a => { if (read.indexOf(a.dataset.plan) >= 0) a.classList.add('is-done'); });

  const known = S.store.get('cardsKnown', []);
  set('stat-cards', known.length + ' of ' + window.FLASHCARDS.length + ' known');
  const sdone = S.store.get('shortDone', []);
  set('stat-short', sdone.length + ' of ' + window.SHORT_BANK.length + ' done');
  const best = S.store.get('quizBest', {});
  set('stat-quiz', S.TOPIC_ORDER.filter(t => best[t]).length + ' of ' + S.TOPIC_ORDER.length + ' sections tried');
  const attempts = S.store.get('examAttempts', []);
  set('stat-exam', attempts.length
    ? 'Best ' + Math.max.apply(null, attempts.map(a => Math.round(100 * a.score / a.total))) + '%'
    : 'Not taken yet');
})();
