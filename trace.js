/* Trapezoid trace: mirrors mpi_SendRec.c / mpi_Bcast.c for f(x) = x*x.
   The arithmetic order matches the C code so the printed digits agree with a real run. */
(function () {
  "use strict";

  function f(x) { return x * x; }

  // same as Trap() in the course code
  function trap(left, right, count, h) {
    var estimate = (f(left) + f(right)) / 2.0;
    for (var i = 1; i <= count - 1; i++) {
      estimate += f(left + i * h);
    }
    return estimate * h;
  }

  function cExp(x) { // like printf("%.15e")
    return x.toExponential(15).replace(/e([+-])(\d)$/, "e$10$2");
  }

  function $(id) { return document.getElementById(id); }

  function compute(a, b, n, p) {
    var h = (b - a) / n;
    var localN = Math.floor(n / p);          // C integer division (n, p positive)
    var ranks = [], total = 0;
    for (var r = 0; r < p; r++) {
      var la = a + r * localN * h;
      var lb = la + localN * h;
      var li = trap(la, lb, localN, h);
      ranks.push({ rank: r, localN: localN, la: la, lb: lb, li: li });
      total = (r === 0) ? li : total + li;   // rank 0 starts with its own, then adds in rank order
    }
    return { h: h, localN: localN, ranks: ranks, total: total };
  }

  function chip(r) {
    var cls = r < 4 ? "r" + r : "rx";
    return '<span class="chip ' + cls + '">rank ' + r + "</span>";
  }

  function render() {
    var a = parseFloat($("in-a").value);
    var b = parseFloat($("in-b").value);
    var n = parseInt($("in-n").value, 10);
    var p = parseInt($("in-p").value, 10);
    var note = $("lane-note"), bar = $("bar"), rows = $("rows");

    if (!isFinite(a) || !isFinite(b) || !(n >= 1) || !(p >= 1) || p > 64) {
      note.innerHTML = '<span class="warn">Enter numbers for a and b, n of at least 1, and 1 to 64 ranks.</span>';
      return;
    }

    var res = compute(a, b, n, p);
    var covered = res.localN * p;
    var leftover = n - covered;

    // lane bar
    var html = "";
    res.ranks.forEach(function (rk) {
      var w = (rk.localN / n) * 100;
      html += '<div class="seg c' + (rk.rank % 4) + '" style="width:' + w + '%" title="rank ' + rk.rank +
        ": " + rk.la.toFixed(4) + " to " + rk.lb.toFixed(4) + '">' + (w > 4 ? rk.rank : "") + "</div>";
    });
    if (leftover > 0) {
      html += '<div class="seg skipped" style="width:' + (leftover / n) * 100 +
        '%" title="never computed: ' + leftover + ' trapezoids"></div>';
    }
    bar.innerHTML = html;
    bar.setAttribute("aria-label", p + " ranks each covering " + res.localN + " of " + n + " trapezoids" +
      (leftover > 0 ? "; " + leftover + " trapezoids are never computed" : ""));
    $("ax-a").textContent = "a = " + a;
    $("ax-b").textContent = "b = " + b;

    if (leftover > 0) {
      note.innerHTML = '<span class="warn">' + n + " does not divide evenly by " + p + ".</span> Each rank does " +
        res.localN + " trapezoids, so " + covered + " are covered and " + leftover + " (hatched) never are.";
    } else if (res.localN === 0) {
      note.innerHTML = '<span class="warn">n is smaller than comm_sz, so local_n is 0.</span>';
    } else {
      note.textContent = n + " trapezoids split evenly: " + res.localN + " per rank.";
    }
    if (res.localN === 0) {
      note.innerHTML = '<span class="warn">n is smaller than comm_sz, so local_n is 0 and Trap() returns a meaningless value.</span> The textbook assumes n is at least comm_sz.';
    }

    // table
    var shown = res.ranks.slice(0, 16);
    rows.innerHTML = shown.map(function (rk) {
      return "<tr><td>" + chip(rk.rank) + "</td><td>" + rk.localN + "</td><td>" + rk.la.toFixed(6) +
        "</td><td>" + rk.lb.toFixed(6) + "</td><td>" + rk.li.toPrecision(10) + "</td></tr>";
    }).join("");
    if (res.ranks.length > shown.length) {
      rows.innerHTML += '<tr><td colspan="5">' + (res.ranks.length - shown.length) + " more ranks with the same local_n</td></tr>";
    }

    // summary
    var exact = (b * b * b - a * a * a) / 3;
    $("o-h").textContent = String(res.h);
    $("o-total").textContent = cExp(res.total);
    $("o-exact").textContent = String(exact);
    $("o-err").textContent = (res.total - exact).toExponential(3);
    $("o-used").textContent = covered + " of " + n;
    $("o-msgs").textContent = "Send/Recv version sends " + 4 * (p - 1) +
      " messages through rank 0, collective version makes 4 calls on every rank.";
  }

  ["in-a", "in-b", "in-n", "in-p"].forEach(function (id) {
    $(id).addEventListener("input", render);
  });
  render();
})();
