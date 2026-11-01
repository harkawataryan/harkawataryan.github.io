// Live Herd demo. Four routing policies run side by side on identical
// traffic; the canvas shows the one selected and the scoreboard underneath
// ranks all four by p99 time to first token, updating live. Nothing is
// scripted: the numbers come from the simulation.
(function () {
  const shot = document.querySelector('.project .shot[data-live-herd]');
  if (!shot) return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const POLICIES = [
    { id: 'herd', name: 'Herd', note: 'cached prompt, if not busy' },
    { id: 'prefix', name: 'Prefix only', note: 'cached prompt, always' },
    { id: 'kv', name: 'Cache fullness', note: 'most free cache' },
    { id: 'll', name: 'Least-loaded', note: 'shortest queue' },
    { id: 'rr', name: 'Round-robin', note: 'take turns' },
  ];
  const N = 8, PROMPTS = 5, SPEED = 2;
  const ZIPF = [0.42, 0.24, 0.15, 0.11, 0.08];
  const PCOL = ['#ff4d00', '#3b6cff', '#14a085', '#8b5cf6', '#e0a100'];

  const sim = document.createElement('div');
  sim.className = 'sim';
  sim.innerHTML = `
    <div class="bar">
      <span class="lbl">Viewing</span>
      <div class="seg" role="group" aria-label="Routing policy">${POLICIES.map((p) => `<button type="button" data-p="${p.id}" aria-pressed="${p.id === 'herd'}">${p.name}</button>`).join('')}</div>
      <label class="traffic"><span class="lbl">Traffic</span><input type="range" min="3" max="12" step="1" value="7" aria-label="Requests per second"><span class="rps">7/s</span></label>
    </div>
    <div class="cv"><canvas aria-label="Requests flowing to eight GPU servers"></canvas><span class="tip">Tap a GPU to slow it down</span></div>
    <div class="board">
      <div class="bhead"><span>p99 first token · same traffic for all</span><span class="bnote"></span></div>
      <ol>${POLICIES.map((p) => `<li data-p="${p.id}"><span class="nm">${p.name}<small>${p.note}</small></span><span class="track"><i></i></span><span class="val">–</span></li>`).join('')}</ol>
    </div>`;
  const cv = sim.querySelector('canvas'), ctx = cv.getContext('2d');
  if (!ctx) return;

  // One shared traffic script so every policy sees the same requests.
  let rate = 7;
  const slow = new Set([2, 5]);
  let seedA = 12345;
  const randA = () => { seedA = (seedA * 1103515245 + 12345) & 0x7fffffff; return seedA / 0x7fffffff; };
  const script = []; // { t, p }
  let scriptT = 0;
  function nextArrival(upTo) {
    while (scriptT <= upTo) {
      let r = randA(), i = 0; while (r > ZIPF[i] && i < PROMPTS - 1) { r -= ZIPF[i]; i++; }
      script.push({ t: scriptT, p: i });
      scriptT += -Math.log(1 - randA()) / rate;
    }
  }

  function makeWorld(policy) {
    let seed = 777;
    const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
    const w = { policy, t: 0, cursor: 0, rr: 0, servers: Array.from({ length: N }, () => ({ q: [], busy: null, cache: [] })), flying: [], lat: [], hit: 0, done: 0 };
    const load = (i) => w.servers[i].q.length + (w.servers[i].busy ? 1 : 0) + w.flying.filter((r) => r.s === i).length;
    const cost = (i, p) => (w.servers[i].cache.includes(p) ? 0.35 : 1) * (slow.has(i) ? 3 : 1);
    // Cache fullness: how much work is sitting on a server right now, which is
    // what fills its cache memory. Queued requests count at their real cost,
    // so a cache hit is cheap and a slow server is expensive. Lower is freer.
    const fullness = (i) => {
      const sv = w.servers[i];
      let f = sv.busy ? Math.max(0, sv.busy.done - w.t) : 0;
      for (const r of sv.q) f += 0.95 * cost(i, r.p);
      // Requests still travelling toward this server are already committed.
      for (const r of w.flying) if (r.s === i) f += 0.95 * cost(i, r.p);
      return f;
    };
    const holders = (p) => [...Array(N).keys()].filter((i) => w.servers[i].cache.includes(p));
    const lightest = (ids, f) => { let b = ids[0]; for (const i of ids) if (f(i) < f(b)) b = i; return b; };
    w.pick = (p) => {
      if (policy === 'rr') { w.rr = (w.rr + 1) % N; return w.rr; }
      const all = [...Array(N).keys()];
      if (policy === 'll') return lightest(all, load);
      // Cache fullness: the server that would finish soonest judging by the
      // work queued on it, without knowing what each server has cached.
      if (policy === 'kv') return lightest(all, (i) => fullness(i) + 0.95 * cost(i, -1));
      // Prefix only: always a server that has the prompt cached, however busy.
      if (policy === 'prefix') { const h = holders(p); return h.length ? lightest(h, (i) => w.servers[i].cache.indexOf(p)) : lightest(all, (i) => fullness(i) + 0.95 * cost(i, -1)); }
      // Herd: the server where this request would finish soonest, counting
      // the work ahead of it, the server's speed, and whether the prompt is
      // already cached there.
      return lightest(all, (i) => fullness(i) + 0.95 * cost(i, p));
    };
    void rnd;
    w.step = (dt) => {
      w.t += dt;
      nextArrival(w.t);
      while (w.cursor < script.length && script[w.cursor].t <= w.t) {
        const a = script[w.cursor++];
        w.flying.push({ p: a.p, s: w.pick(a.p), born: a.t, prog: 0 });
      }
      for (let i = w.flying.length - 1; i >= 0; i--) {
        const f = w.flying[i]; f.prog += dt * 1.6;
        if (f.prog >= 1) { w.servers[f.s].q.push(f); w.flying.splice(i, 1); }
      }
      w.servers.forEach((sv, i) => {
        if (sv.busy && w.t >= sv.busy.done) {
          w.lat.push(w.t - sv.busy.born); if (w.lat.length > 300) w.lat.shift();
          w.done++; if (sv.busy.hit) w.hit++;
          const c = sv.cache, k = c.indexOf(sv.busy.p); if (k >= 0) c.splice(k, 1); c.unshift(sv.busy.p); if (c.length > 2) c.pop();
          sv.busy = null;
        }
        if (!sv.busy && sv.q.length) { const r = sv.q.shift(); r.hit = sv.cache.includes(r.p); r.done = w.t + 0.95 * cost(i, r.p); sv.busy = r; }
      });
    };
    w.p99 = () => {
      if (w.lat.length < 20) return null;
      const all = w.lat.concat(w.servers.flatMap((sv) => sv.q.map((r) => w.t - r.born))).sort((a, b) => a - b);
      return all[Math.max(0, Math.ceil(all.length * 0.99) - 1)];
    };
    return w;
  }
  let worlds = POLICIES.map((p) => makeWorld(p.id));
  let viewing = 'herd';
  function reset() { script.length = 0; scriptT = 0; seedA = 12345; worlds = POLICIES.map((p) => makeWorld(p.id)); }

  // ---- drawing ----
  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  let W = 0, H = 0, geom = null;
  function size() {
    const dpr = Math.min(2, devicePixelRatio || 1), r = cv.parentElement.getBoundingClientRect();
    if (!r.width) return;
    W = r.width; H = r.height;
    const bw = Math.round(W * dpr), bh = Math.round(H * dpr);
    if (cv.width !== bw || cv.height !== bh) { cv.width = bw; cv.height = bh; }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  function rrect(x, y, w, h, r) { if (ctx.roundRect) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); } else { ctx.beginPath(); ctx.rect(x, y, w, h); } }
  function draw(w) {
    ctx.clearRect(0, 0, W, H);
    const fg = css('--fg'), mut = css('--muted'), line = css('--line'), acc = css('--acc'), bg = css('--bg'), panel = css('--panel') || line;
    const sx = Math.round(W * 0.44), top = 22, dy = (H - 44) / (N - 1), sy = (i) => top + i * dy;
    geom = { sx, y0: top, dy };
    // lanes
    ctx.strokeStyle = line; ctx.lineWidth = 1;
    for (let i = 0; i < N; i++) { ctx.beginPath(); ctx.moveTo(sx - 110, sy(i)); ctx.lineTo(sx - 6, sy(i)); ctx.stroke(); }
    ctx.font = '600 10px Inter, sans-serif'; ctx.fillStyle = mut; ctx.textAlign = 'left';
    ctx.fillText('INCOMING', 12, 14);
    ctx.textAlign = 'right'; ctx.fillText('GPU', sx - 12, 14); ctx.textAlign = 'left';
    ctx.fillText('QUEUE', sx + 40, 14);
    // requests in flight
    for (const f of w.flying) {
      const k = f.prog, x = 18 + (sx - 24 - 18) * k, y = H / 2 + (sy(f.s) - H / 2) * (k * k * (3 - 2 * k));
      ctx.fillStyle = PCOL[f.p]; ctx.beginPath(); ctx.arc(x, y, 3.5, 0, 7); ctx.fill();
    }
    w.servers.forEach((sv, i) => {
      const x = sx, y = sy(i), sl = slow.has(i);
      // server body
      ctx.fillStyle = sl ? 'rgba(255,77,0,.10)' : css('--bg');
      ctx.strokeStyle = sl ? acc : mut;
      rrect(x, y - 10, 30, 20, 5); ctx.fill(); ctx.stroke();
      if (sv.busy) { ctx.fillStyle = PCOL[sv.busy.p]; rrect(x + 4, y - 6, 12, 12, 3); ctx.fill(); }
      // cached prompts as two small pips
      sv.cache.forEach((p, j) => { ctx.fillStyle = PCOL[p]; ctx.globalAlpha = .55; rrect(x + 20, y - 7 + j * 8, 5, 5, 1.5); ctx.fill(); ctx.globalAlpha = 1; });
      // label
      ctx.font = (sl ? '600' : '500') + ' 11px Inter, sans-serif'; ctx.fillStyle = sl ? acc : fg; ctx.textAlign = 'right';
      ctx.fillText('GPU ' + (i + 1), x - 12, y + 4);
      if (sl) { ctx.font = '600 9px Inter, sans-serif'; ctx.fillStyle = acc; ctx.fillText('SLOW', x - 12, y - 8); }
      ctx.textAlign = 'left';
      // queue
      const q = sv.q.length, room = Math.max(4, Math.floor((W - x - 60) / 8));
      for (let j = 0; j < Math.min(q, room); j++) { ctx.fillStyle = PCOL[sv.q[j].p]; rrect(x + 40 + j * 8, y - 5, 6, 10, 1.5); ctx.fill(); }
      if (q > room) { ctx.font = '600 10px Inter, sans-serif'; ctx.fillStyle = fg; ctx.fillText('+' + (q - room), x + 42 + room * 8, y + 4); }
    });
  }

  // ---- scoreboard ----
  const rows = Object.fromEntries([...sim.querySelectorAll('.board li')].map((li) => [li.dataset.p, li]));
  const bnote = sim.querySelector('.bnote');
  const WARM = 80; // completed requests per policy before the board shows numbers
  function board() {
    const warm = worlds.every((w) => w.done >= WARM);
    sim.querySelector('.board').classList.toggle('warming', !warm);
    const vals = worlds.map((w) => ({ id: w.policy, v: warm ? w.p99() : null, hit: w.done ? w.hit / w.done : 0 }));
    const max = Math.max(1, ...vals.map((x) => x.v || 0));
    const sorted = [...vals].sort((a, b) => (a.v ?? 1e9) - (b.v ?? 1e9));
    const ol = sim.querySelector('.board ol');
    sorted.forEach((x, i) => {
      const li = rows[x.id];
      li.style.order = i;
      li.classList.toggle('best', i === 0 && x.v != null);
      li.classList.toggle('viewing', x.id === viewing);
      li.querySelector('i').style.width = x.v == null ? '0%' : Math.max(3, (100 * x.v) / max) + '%';
      li.querySelector('.val').textContent = x.v == null ? '–' : x.v.toFixed(1) + 's';
    });
    const herd = vals.find((x) => x.id === 'herd'), rr = vals.find((x) => x.id === 'rr');
    if (!warm) bnote.textContent = 'warming up…';
    else if (herd.v && rr.v && rr.v / herd.v >= 1.05) bnote.textContent = `Herd ${(rr.v / herd.v).toFixed(1)}× faster than round-robin`;
    else bnote.textContent = `${Math.round(100 * herd.hit)}% of Herd's requests hit a cache`;
    void ol;
  }

  // ---- loop ----
  let visible = false, raf = 0, last = 0, acc = 0;
  function frame(now) {
    raf = 0;
    if (!visible || document.hidden) { last = 0; return; }
    if (window.__scrollIdle && !window.__scrollIdle()) { last = 0; raf = requestAnimationFrame(frame); return; }
    const dt = last ? Math.min(0.05, (now - last) / 1000) : 0.016;
    last = now;
    size();
    for (const w of worlds) w.step(dt * SPEED);
    draw(worlds.find((w) => w.policy === viewing));
    acc += dt;
    if (acc > 0.3) { acc = 0; board(); }
    if (!sim.classList.contains('on')) sim.classList.add('on');
    raf = requestAnimationFrame(frame);
  }
  const kick = () => { if (!raf && visible && !document.hidden) raf = requestAnimationFrame(frame); };
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; kick(); }, { rootMargin: '80px' }).observe(shot);
  document.addEventListener('visibilitychange', kick);

  // ---- controls ----
  sim.querySelectorAll('.seg button').forEach((b) => b.addEventListener('click', () => {
    viewing = b.dataset.p;
    sim.querySelectorAll('.seg button').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
    board();
  }));
  sim.querySelectorAll('.board li').forEach((li) => li.addEventListener('click', () => sim.querySelector(`.seg [data-p="${li.dataset.p}"]`).click()));
  const range = sim.querySelector('input[type="range"]'), rps = sim.querySelector('.rps');
  range.addEventListener('input', () => { rate = Number(range.value); rps.textContent = rate + '/s'; });
  range.addEventListener('change', () => { reset(); board(); });
  const tip = sim.querySelector('.tip');
  function hitServer(e) {
    if (!geom) return -1;
    const r = cv.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    const i = Math.round((y - geom.y0) / geom.dy);
    return x >= geom.sx - 70 && x <= geom.sx + 40 && i >= 0 && i < N && Math.abs(y - (geom.y0 + i * geom.dy)) <= geom.dy / 2 ? i : -1;
  }
  cv.addEventListener('click', (e) => {
    const i = hitServer(e); if (i < 0) return;
    if (slow.has(i)) slow.delete(i); else slow.add(i);
    reset(); board();
    tip.textContent = slow.size ? `${slow.size} slow · tap a GPU to toggle` : 'All healthy · tap a GPU to slow it';
  });
  cv.addEventListener('mousemove', (e) => { cv.style.cursor = hitServer(e) >= 0 ? 'pointer' : 'default'; });

  shot.appendChild(sim);
  shot.classList.add('has-sim');
})();
