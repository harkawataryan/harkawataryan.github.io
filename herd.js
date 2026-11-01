// Live Herd demo for the project card: a small load-balancing simulation.
// Requests arrive at eight LLM servers and the visitor picks how they're
// routed. Cache-aware routing is what Herd does. Everything here is derived
// from the simulation; nothing is scripted to look good.
(function () {
  const shot = document.querySelector('.project .shot[data-live-herd]');
  if (!shot) return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const sim = document.createElement('div');
  sim.className = 'sim';
  sim.innerHTML = `
    <div class="bar">
      <div class="seg" role="group" aria-label="Routing policy">
        <button type="button" data-p="rr" aria-pressed="true">Round-robin</button>
        <button type="button" data-p="ll">Least-loaded</button>
        <button type="button" data-p="p2c">Power of two</button>
        <button type="button" data-p="herd">Herd</button>
      </div>
      <label class="traffic">Traffic <input type="range" min="3" max="12" step="1" value="7" aria-label="Requests per second"> <span class="rps">7/s</span></label>
      <span class="tip">Click a server to slow it down</span>
    </div>
    <canvas aria-label="Requests flowing to eight servers"></canvas>
    <div class="stats">
      <div class="stat"><div class="k">p99 first token</div><div class="v" data-s="p99">–</div></div>
      <div class="stat"><div class="k">Cache hits</div><div class="v" data-s="hits">–</div></div>
      <div class="stat"><div class="k">Longest queue</div><div class="v" data-s="q">–</div></div>
    </div>`;
  const cv = sim.querySelector('canvas'), ctx = cv.getContext('2d');
  if (!ctx) return;

  const N = 8, PROMPTS = 5, SPEED = 2;
  let RATE = 7;
  const SLOW = new Set([2, 5]); // servers 3 and 6 start at a third of the speed
  const W_ZIPF = [0.42, 0.24, 0.15, 0.11, 0.08];
  const PCOL = ['#ff4d00', '#3b82f6', '#16a34a', '#a855f7', '#eab308'];
  let policy = 'rr', rr = 0, t = 0, nextArrival = 0;
  const servers = Array.from({ length: N }, () => ({ q: [], busy: null, cache: [] }));
  const flying = [], lat = [];
  let hitN = 0, totalN = 0;

  const zipf = () => { let r = Math.random(), i = 0; while (r > W_ZIPF[i] && i < PROMPTS - 1) { r -= W_ZIPF[i]; i++; } return i; };
  const load = (i) => servers[i].q.length + (servers[i].busy ? 1 : 0);
  const isSlow = (i) => SLOW.has(i);
  const cost = (i, p) => (servers[i].cache.includes(p) ? 0.35 : 1) * (isSlow(i) ? 3 : 1);
  function pick(p) {
    if (policy === 'rr') { rr = (rr + 1) % N; return rr; }
    let best = 0; for (let i = 1; i < N; i++) if (load(i) < load(best)) best = i;
    if (policy === 'll') return best;
    if (policy === 'p2c') { const a = Math.floor(Math.random() * N); let b = Math.floor(Math.random() * (N - 1)); if (b >= a) b++; return load(a) <= load(b) ? a : b; }
    // Herd: a server that already holds the prompt, unless it's noticeably busier than the least-loaded one.
    const holders = [...Array(N).keys()].filter((i) => servers[i].cache.includes(p) && load(i) <= load(best) + 1);
    if (!holders.length) return best;
    let b = holders[0]; for (const i of holders) if (load(i) < load(b)) b = i; return b;
  }
  function remember(i, p) { const c = servers[i].cache, k = c.indexOf(p); if (k >= 0) c.splice(k, 1); c.unshift(p); if (c.length > 2) c.pop(); }
  function reset() { servers.forEach((s) => { s.q = []; s.busy = null; }); flying.length = 0; lat.length = 0; hitN = totalN = 0; }

  function step(dt) {
    t += dt;
    while (nextArrival <= t) {
      const p = zipf();
      flying.push({ p, s: pick(p), born: nextArrival, prog: 0 });
      nextArrival += -Math.log(1 - Math.random()) / RATE;
    }
    for (let i = flying.length - 1; i >= 0; i--) {
      const f = flying[i]; f.prog += dt * 1.6;
      if (f.prog >= 1) { servers[f.s].q.push(f); flying.splice(i, 1); }
    }
    servers.forEach((sv, i) => {
      if (sv.busy && t >= sv.busy.done) {
        lat.push(t - sv.busy.born); if (lat.length > 300) lat.shift();
        totalN++; if (sv.busy.hit) hitN++; remember(i, sv.busy.p); sv.busy = null;
      }
      if (!sv.busy && sv.q.length) { const r = sv.q.shift(); r.hit = sv.cache.includes(r.p); r.done = t + 0.95 * cost(i, r.p); sv.busy = r; }
    });
  }
  // Waiting requests count at their current age, so a backed-up queue shows in p99 right away.
  function p99() {
    if (lat.length < 20) return null;
    const all = lat.concat(servers.flatMap((sv) => sv.q.map((r) => t - r.born))).sort((a, b) => a - b);
    return all[Math.max(0, Math.ceil(all.length * 0.99) - 1)];
  }

  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  let W = 0, H = 0;
  function size() {
    const dpr = Math.min(2, devicePixelRatio || 1), r = cv.getBoundingClientRect();
    if (!r.width) return;
    W = r.width; H = r.height;
    const bw = Math.round(W * dpr), bh = Math.round(H * dpr);
    if (cv.width !== bw || cv.height !== bh) { cv.width = bw; cv.height = bh; }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  function draw() {
    ctx.clearRect(0, 0, W, H);
    const fg = css('--fg'), mut = css('--muted'), line = css('--line'), acc = css('--acc'), bg = css('--bg');
    const sx = Math.round(W * 0.46), sy = (i) => 16 + i * ((H - 32) / (N - 1));
    geom = { sx, y0: 16, dy: (H - 32) / (N - 1) };
    ctx.font = '500 11px Inter, sans-serif';
    ctx.fillStyle = mut; ctx.fillText('requests', 10, H / 2 - 12);
    for (const f of flying) {
      const k = f.prog, x = 30 + (sx - 30 - 30) * k, y = H / 2 + (sy(f.s) - H / 2) * (k * k * (3 - 2 * k));
      ctx.fillStyle = PCOL[f.p]; ctx.beginPath(); ctx.arc(x, y, 3, 0, 7); ctx.fill();
    }
    servers.forEach((sv, i) => {
      const x = sx, y = sy(i), sl = isSlow(i);
      ctx.strokeStyle = sl ? acc : line; ctx.fillStyle = bg;
      ctx.beginPath(); ctx.roundRect ? ctx.roundRect(x, y - 9, 18, 18, 4) : ctx.rect(x, y - 9, 18, 18); ctx.fill(); ctx.stroke();
      if (sv.busy) { ctx.fillStyle = PCOL[sv.busy.p]; ctx.fillRect(x + 5, y - 4, 8, 8); }
      ctx.fillStyle = sl ? acc : mut; ctx.textAlign = 'right'; ctx.fillText(sl ? 'slow gpu ' + (i + 1) : 'gpu ' + (i + 1), x - 8, y + 4); ctx.textAlign = 'left';
      sv.cache.forEach((p, j) => { ctx.fillStyle = PCOL[p]; ctx.globalAlpha = .45; ctx.fillRect(x + 24 + j * 6, y - 10, 4, 4); ctx.globalAlpha = 1; });
      const q = sv.q.length, room = Math.max(4, Math.floor((W - x - 52) / 7));
      for (let j = 0; j < Math.min(q, room); j++) { ctx.fillStyle = PCOL[sv.q[j].p]; ctx.fillRect(x + 24 + j * 7, y - 3, 5, 8); }
      if (q > room) { ctx.fillStyle = fg; ctx.fillText('+' + (q - room), x + 24 + room * 7, y + 4); }
    });
  }
  const out = {}; sim.querySelectorAll('[data-s]').forEach((el) => { out[el.dataset.s] = el; });
  function readout() {
    const v = p99();
    out.p99.innerHTML = v == null ? '–' : v.toFixed(1) + '<small>s</small>';
    out.p99.classList.toggle('hot', v != null && v > 8);
    out.hits.textContent = totalN ? Math.round((100 * hitN) / totalN) + '%' : '–';
    out.q.textContent = Math.max(...servers.map((s) => s.q.length));
  }

  let visible = false, raf = 0, last = 0, acc = 0;
  function frame(now) {
    raf = 0;
    if (!visible || document.hidden) { last = 0; return; }
    const dt = last ? Math.min(0.05, (now - last) / 1000) : 0.016;
    last = now;
    size();
    step(dt * SPEED);
    draw();
    acc += dt;
    if (acc > 0.25) { acc = 0; readout(); }
    if (!sim.classList.contains('on')) sim.classList.add('on');
    raf = requestAnimationFrame(frame);
  }
  const kick = () => { if (!raf && visible && !document.hidden) raf = requestAnimationFrame(frame); };
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; kick(); }, { rootMargin: '80px' }).observe(shot);
  document.addEventListener('visibilitychange', kick);

  sim.querySelectorAll('.seg button').forEach((b) => b.addEventListener('click', () => {
    policy = b.dataset.p; reset();
    sim.querySelectorAll('.seg button').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
    readout();
  }));
  const range = sim.querySelector('input[type="range"]'), rps = sim.querySelector('.rps');
  range.addEventListener('input', () => { RATE = Number(range.value); rps.textContent = RATE + '/s'; });
  // Clicking a server toggles it between healthy and slow.
  let geom = null;
  cv.addEventListener('click', (e) => {
    if (!geom) return;
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    if (x < geom.sx - 70 || x > geom.sx + 60) return;
    const i = Math.round((y - geom.y0) / geom.dy);
    if (i < 0 || i >= N || Math.abs(y - (geom.y0 + i * geom.dy)) > geom.dy / 2) return;
    if (SLOW.has(i)) SLOW.delete(i); else SLOW.add(i);
    sim.querySelector('.tip').textContent = SLOW.size ? `${SLOW.size} slow server${SLOW.size > 1 ? 's' : ''} · click to toggle` : 'All healthy · click a server to slow it';
  });
  cv.addEventListener('mousemove', (e) => {
    if (!geom) return;
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    const i = Math.round((y - geom.y0) / geom.dy);
    cv.style.cursor = x >= geom.sx - 70 && x <= geom.sx + 60 && i >= 0 && i < N && Math.abs(y - (geom.y0 + i * geom.dy)) <= geom.dy / 2 ? 'pointer' : 'default';
  });

  shot.appendChild(sim);
  shot.classList.add('has-sim');
})();
