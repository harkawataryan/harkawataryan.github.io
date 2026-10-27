// Load balancing simulation: eight backends, two at half capacity, Poisson
// arrivals, three policies. Deliberately small and honest; the point is the
// shape of the queues, not the absolute numbers.
(function () {
  const canvas = document.getElementById('simcanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const N = 8, CONC = 4, QMAX = 24, BASE = 1.0;  // service time in sim seconds at capacity 1

  const notes = {
    rr: 'Round robin gives every backend an equal share, so the two slow ones fall behind and never catch up.',
    lc: 'Least connections helps, but it only sees how many requests it has sent, not how far behind a backend is.',
    p2c: 'Power-of-two-choices by utilization samples two backends and picks the less loaded one. The slow backends get less traffic and the tail stays flat.',
  };

  let policy = 'rr', rps = 20, rrIdx = 0, served = 0, shed = 0;
  const lat = [];
  const backends = Array.from({ length: N }, (_, i) => ({
    cap: i === 2 || i === 5 ? 0.5 : 1.0,
    active: [],   // {done}
    queue: [],    // {arrived}
    sent: 0,
  }));
  const flights = [];   // request dots in transit {from, to, t}

  function pick() {
    if (policy === 'rr') return rrIdx++ % N;
    if (policy === 'lc') {
      let best = 0, bv = Infinity;
      for (let i = 0; i < N; i++) { const v = backends[i].active.length + backends[i].queue.length; if (v < bv) { bv = v; best = i; } }
      return best;
    }
    const a = Math.floor(Math.random() * N); let b = Math.floor(Math.random() * (N - 1)); if (b >= a) b++;
    const util = (i) => (backends[i].active.length + backends[i].queue.length) / backends[i].cap;
    return util(a) <= util(b) ? a : b;
  }

  function admit(i, now) {
    const b = backends[i];
    if (b.queue.length >= QMAX) { shed++; return; }
    b.queue.push({ arrived: now });
  }

  let simT = 0, nextArrival = 0, lastReal = 0;
  function step(dt) {
    simT += dt;
    while (nextArrival <= simT) {
      const i = pick();
      flights.push({ to: i, t: 0 });
      nextArrival += -Math.log(1 - Math.random()) / rps;
    }
    for (const f of flights) f.t += dt * 3;
    for (let k = flights.length - 1; k >= 0; k--) if (flights[k].t >= 1) { admit(flights[k].to, simT); flights.splice(k, 1); }
    for (const b of backends) {
      b.active = b.active.filter((r) => r.done > simT);
      while (b.active.length < CONC && b.queue.length) {
        const r = b.queue.shift();
        const svc = BASE / b.cap * (0.7 + Math.random() * 0.6) * (1 + b.active.length * 0.15);
        b.active.push({ done: simT + svc });
        lat.push(simT - r.arrived + svc);
        if (lat.length > 400) lat.shift();
        served++;
      }
    }
  }

  function pct(p) {
    if (!lat.length) return null;
    const s = [...lat].sort((a, b) => a - b);
    return s[Math.min(s.length - 1, Math.floor(p * s.length))];
  }

  const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
  function draw() {
    const fg = css('--fg'), muted = css('--muted'), line = css('--line'), accent = css('--accent'), warn = css('--accent2');
    ctx.clearRect(0, 0, W, H);
    const left = 40, right = W - 40, gw = (right - left) / N, barW = gw * 0.52;
    const baseY = H - 70, top = 90;
    // gateway
    ctx.fillStyle = fg; ctx.font = '500 15px Inter, system-ui, sans-serif'; ctx.textAlign = 'center';
    ctx.fillRect(W / 2 - 60, 24, 120, 30);
    ctx.fillStyle = css('--bg'); ctx.fillText('gateway', W / 2, 45);
    // in-flight dots
    for (const f of flights) {
      const x0 = W / 2, y0 = 54, x1 = left + gw * (f.to + 0.5), y1 = top;
      const x = x0 + (x1 - x0) * f.t, y = y0 + (y1 - y0) * f.t;
      ctx.fillStyle = accent; ctx.beginPath(); ctx.arc(x, y, 3.2, 0, Math.PI * 2); ctx.fill();
    }
    for (let i = 0; i < N; i++) {
      const b = backends[i], cx = left + gw * (i + 0.5);
      ctx.strokeStyle = line; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(W / 2, 54); ctx.lineTo(cx, top); ctx.stroke();
      // queue bar
      const qh = (b.queue.length / QMAX) * (baseY - top - 20);
      ctx.fillStyle = line; ctx.fillRect(cx - barW / 2, top, barW, baseY - top - 20);
      ctx.fillStyle = b.queue.length >= QMAX ? warn : accent;
      ctx.fillRect(cx - barW / 2, baseY - 20 - qh, barW, qh);
      // active slots
      for (let s = 0; s < CONC; s++) {
        ctx.fillStyle = s < b.active.length ? fg : line;
        ctx.fillRect(cx - barW / 2 + s * (barW / CONC) + 1, baseY - 14, barW / CONC - 2, 10);
      }
      ctx.fillStyle = muted; ctx.font = '12px "JetBrains Mono", ui-monospace, monospace';
      ctx.fillText(`b${i + 1}${b.cap < 1 ? ' ½' : ''}`, cx, baseY + 18);
      ctx.fillText(`q=${b.queue.length}`, cx, baseY + 36);
    }
    ctx.fillStyle = muted; ctx.font = '12px Inter, system-ui, sans-serif'; ctx.textAlign = 'left';
    ctx.fillText('bar = queue depth · squares = in-flight slots · ½ = half-capacity backend', left, H - 8);
  }

  const $ = (id) => document.getElementById(id);
  function updateStats() {
    const p50 = pct(0.5), p99 = pct(0.99);
    $('p50').textContent = p50 == null ? '–' : (p50 * 100).toFixed(0) + ' ms';
    $('p99').textContent = p99 == null ? '–' : (p99 * 100).toFixed(0) + ' ms';
    $('shed').textContent = shed;
    $('served').textContent = served;
  }

  function reset() {
    for (const b of backends) { b.active = []; b.queue = []; }
    flights.length = 0; lat.length = 0; served = 0; shed = 0; simT = 0; nextArrival = 0;
  }

  document.querySelectorAll('.pol').forEach((btn) => btn.addEventListener('click', () => {
    document.querySelectorAll('.pol').forEach((b) => { b.classList.toggle('active', b === btn); b.setAttribute('aria-selected', b === btn); });
    policy = btn.dataset.policy; $('simnote').textContent = notes[policy]; reset();
  }));
  $('rps').addEventListener('input', (e) => { rps = +e.target.value; $('rpsOut').textContent = rps + ' rps'; });

  let visible = false;
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; }).observe(canvas);
  let acc = 0;
  function frame(now) {
    requestAnimationFrame(frame);
    if (!visible || document.hidden) { lastReal = now; return; }
    const dt = Math.min((now - lastReal) / 1000, 0.1); lastReal = now;
    const simDt = dt * 1.5;                     // sim seconds per real second
    for (let t = 0; t < simDt; t += 0.01) step(0.01);
    draw();
    acc += dt; if (acc > 0.25) { updateStats(); acc = 0; }
  }
  requestAnimationFrame(frame);
})();
