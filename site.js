(function () {
  // Light/dark switch. The initial theme is set by the inline script in
  // <head>; this handles clicks, remembers the choice, and follows the
  // system setting until someone picks one.
  const root = document.documentElement;
  const btn = document.querySelector('.theme');
  const meta = document.querySelector('meta[name="theme-color"]');
  function apply(theme) {
    root.dataset.theme = theme;
    if (meta) meta.setAttribute('content', theme === 'dark' ? '#0e0e0e' : '#ffffff');
    if (btn) btn.setAttribute('aria-label', theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
  }
  function switchTo(theme) {
    // Browsers with view transitions cross-fade the whole page in one pass.
    // Others fade each element's colors, which is close enough.
    if (document.startViewTransition && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      document.startViewTransition(() => apply(theme));
      return;
    }
    root.classList.add('theme-switching');
    apply(theme);
    clearTimeout(switchTo.t);
    switchTo.t = setTimeout(() => root.classList.remove('theme-switching'), 450);
  }
  apply(root.dataset.theme || 'light');
  if (btn) {
    btn.addEventListener('click', () => {
      const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem('theme', next); } catch (e) {}
      btn.classList.remove('spin');
      void btn.offsetWidth; // restart the animation on quick repeat clicks
      btn.classList.add('spin');
      switchTo(next);
    });
    btn.addEventListener('animationend', () => btn.classList.remove('spin'));
  }
  const mq = matchMedia('(prefers-color-scheme: dark)');
  mq.addEventListener('change', (e) => {
    let saved = null;
    try { saved = localStorage.getItem('theme'); } catch (err) {}
    if (!saved) switchTo(e.matches ? 'dark' : 'light');
  });

  // Scroll motion: reveals, drawn section rules, hero parallax, progress bar.
  const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  requestAnimationFrame(() => requestAnimationFrame(() => root.classList.add('loaded')));

  const revealables = [...document.querySelectorAll('[data-rv]')];
  const rules = [...document.querySelectorAll('.screen')];
  if (still || !('IntersectionObserver' in window)) {
    revealables.forEach((el) => el.classList.add('in'));
    document.querySelectorAll('.screen').forEach((el) => el.classList.add('in'));
    rules.forEach((el) => el.classList.add('drawn'));
  } else {
    // Items that enter together are staggered so a section cascades in.
    let batch = 0, batchTimer = null;
    const rio = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        rio.unobserve(e.target);
        const inHero = e.target.closest('.hero');
        e.target.style.transitionDelay = (inHero ? 0.35 : 0) + Math.min(batch, 6) * 0.09 + 's';
        e.target.classList.add('in');
        batch++;
      }
      clearTimeout(batchTimer);
      batchTimer = setTimeout(() => { batch = 0; }, 120);
    }, { rootMargin: '0px 0px -8% 0px' });
    revealables.forEach((el) => rio.observe(el));
    // At the very bottom of the page nothing more can scroll into the
    // trigger zone, so reveal whatever is left.
    window.addEventListener('scroll', () => {
      if (window.scrollY + innerHeight >= document.documentElement.scrollHeight - 4) revealables.forEach((el) => { if (!el.classList.contains('in')) { rio.unobserve(el); el.classList.add('in'); } });
    }, { passive: true });

    // A rule sits at the bottom of its section, so a 1px marker there
    // decides when it draws.
    const lio = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        lio.unobserve(e.target);
        e.target.parentElement.classList.add('drawn');
      }
    }, { rootMargin: '0px 0px -10% 0px' });
    rules.forEach((el) => {
      const mark = document.createElement('span');
      mark.setAttribute('aria-hidden', 'true');
      mark.style.cssText = 'position:absolute;bottom:0;left:0;width:1px;height:1px;pointer-events:none';
      el.appendChild(mark);
      lio.observe(mark);
    });
  }

  const bar = document.querySelector('.progress');
  const heroName = document.querySelector('.hero h1');
  // The live demos ask this every frame and only draw once the page has
  // been still for a moment. It reads the scroll position directly, so it
  // can't be fooled by scroll events arriving late behind a slow frame.
  let lastY = -1, lastMove = 0;
  window.__scrollIdle = () => {
    const y = window.scrollY, now = performance.now();
    if (y !== lastY) { lastY = y; lastMove = now; }
    return now - lastMove > 150;
  };

  let ticking = false;
  function onScroll() {
    ticking = false;
    const y = window.scrollY;
    const max = document.documentElement.scrollHeight - innerHeight;
    if (bar) bar.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, y / max) : 0) + ')';
    if (heroName && !still && y < innerHeight * 1.2) {
      heroName.style.transform = 'translate3d(0,' + (y * 0.22).toFixed(1) + 'px,0)';
      heroName.style.opacity = Math.max(0, 1 - y / 650).toFixed(3);
    }
    fadeScreens();
  }

  // One screen per wheel gesture. Native snapping can skip a screen when a
  // trackpad flick arrives with momentum, so on desktop the wheel is taken
  // over. A gesture is a run of wheel events with no gap longer than 80ms
  // between them, which separates a flick's momentum tail from a deliberate
  // second swipe. Each gesture moves one screen from wherever the last move
  // was headed, so quick successive swipes chain without waiting. Keyboard,
  // scrollbar and touch still use the browser's own snapping.
  const screens = [...document.querySelectorAll('section.screen')];
  const snapping = () => matchMedia('(min-width: 900px) and (min-height: 600px)').matches && !still;
  let lastWheel = 0, lastDy = 0, decaying = true, heading = -1, headingAt = 0;
  window.addEventListener('wheel', (e) => {
    if (!snapping() || e.ctrlKey) return;
    const inner = e.target.closest && e.target.closest('.results');
    if (inner && inner.scrollHeight > inner.clientHeight + 1) return;
    e.preventDefault();
    const now = performance.now();
    const dy = e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY;
    // A momentum tail only ever slows down, so a gap, or a speed-up after
    // the tail has started, means a new swipe. A swipe's own rising edge
    // fires once because nothing has decayed yet.
    const a = Math.abs(dy), la = Math.abs(lastDy);
    // A stalled frame can open a gap inside a tail, so a gap only counts
    // when the delta is not still shrinking.
    const since = now - lastWheel;
    const gap = since > 400 || (since > 120 && a >= la);
    if (a < la) decaying = true;
    const fresh = gap || (decaying && a > la * 1.3 && a > 12);
    lastWheel = now; lastDy = dy;
    if (!fresh || a < 4) return;
    decaying = false;
    const y = window.scrollY;
    let cur = 0, bestD = Infinity;
    screens.forEach((el, i) => { const d = Math.abs(el.getBoundingClientRect().top); if (d < bestD) { bestD = d; cur = i; } });
    // If a move is still in flight, count from where it is going.
    if (heading >= 0 && now - headingAt < 900) cur = heading;
    const next = Math.max(0, Math.min(screens.length - 1, cur + (dy > 0 ? 1 : -1)));
    if (next === cur) return;
    heading = next; headingAt = now;
    window.scrollTo({ top: screens[next].getBoundingClientRect().top + y, behavior: 'smooth' });
  }, { passive: false });

  // Scroll-linked fade on desktop, where the page snaps screen to screen. A
  // screen is fully opaque when it fills the viewport and gone once it has
  // moved half a viewport away, so the move between screens reads as one
  // fading out while the next fades in, instead of content sliding past.
  const fading = [...document.querySelectorAll('section.screen > .wrap')];
  let fadeOn = false;
  function fadeScreens() {
    const on = snapping();
    if (!on) { if (fadeOn) fading.forEach((w) => { w.style.opacity = ''; }); fadeOn = false; return; }
    fadeOn = true;
    const vh = innerHeight;
    for (const w of fading) {
      const d = Math.abs(w.parentElement.getBoundingClientRect().top) / vh;
      w.style.opacity = Math.max(0, Math.min(1, 1 - (d - 0.08) / 0.5)).toFixed(3);
    }
  }
  window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  window.addEventListener('resize', () => requestAnimationFrame(onScroll));
  onScroll();

  // Every page view and event also goes to the live visit log on the
  // Concertify server, which the /stats/ dashboard reads within seconds.
  // Sent as text/plain so sendBeacon needs no preflight. Skipped when the
  // dashboard has flagged this browser as the owner's.
  const VISITS_API = 'https://concertify-cm6k.onrender.com/api/visits/hit';
  // A random id kept in this browser, so a returning visitor is recognized
  // even after switching networks or updating the browser. It identifies
  // nothing about the person.
  let vid = null;
  try {
    vid = localStorage.getItem('aryanh.vid');
    if (!vid) {
      vid = window.crypto && crypto.randomUUID ? crypto.randomUUID().replace(/-/g, '') : (Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2) + Date.now().toString(36));
      localStorage.setItem('aryanh.vid', vid);
    }
  } catch (e) {}
  function beacon(path, event, extra) {
    try {
      if (localStorage.getItem('skipgc')) return;
      const body = JSON.stringify(Object.assign({ p: path, e: !!event, ref: document.referrer, w: screen.width, v: vid, tp: navigator.maxTouchPoints || 0 }, extra));
      if (navigator.sendBeacon) navigator.sendBeacon(VISITS_API, new Blob([body], { type: 'text/plain' }));
      else fetch(VISITS_API, { method: 'POST', body: body, keepalive: true, headers: { 'Content-Type': 'text/plain' } }).catch(() => {});
    } catch (e) {}
  }
  beacon(location.pathname, false);

  // GoatCounter custom events. No-ops when the counter is blocked.
  function track(path) {
    beacon(path, true);
    if (!window.goatcounter || !window.goatcounter.count) return;
    window.goatcounter.count({ path: path, title: path, event: true });
  }

  // Deepest section reached.
  const order = ['top', 'work', 'herd', 'concertify', 'clouds', 'about'];
  let deepest = 0;
  const io = new IntersectionObserver((es) => {
    for (const e of es) {
      if (!e.isIntersecting) continue;
      io.unobserve(e.target);
      deepest = Math.max(deepest, order.indexOf(e.target.id));
    }
  }, { rootMargin: '0px 0px -10% 0px' });
  document.querySelectorAll('section[id]').forEach((el) => io.observe(el));

  // Side dots follow whichever screen fills most of the viewport.
  const dots = [...document.querySelectorAll('.dots a')];
  if (dots.length && 'IntersectionObserver' in window) {
    const ratio = new Map();
    const dio = new IntersectionObserver((es) => {
      for (const e of es) { ratio.set(e.target.id, e.intersectionRatio); if (e.intersectionRatio >= 0.25) e.target.classList.add('in'); }
      let best = null, bestR = 0;
      for (const [id, r] of ratio) if (r > bestR) { best = id; bestR = r; }
      dots.forEach((d) => d.classList.toggle('on', d.dataset.dot === best));
    }, { threshold: [0, 0.25, 0.5, 0.75, 1] });
    document.querySelectorAll('section.screen[id]').forEach((el) => dio.observe(el));
  }

  // Outbound and file clicks: "click/<label>", with the project name when inside a card.
  document.addEventListener('click', (ev) => {
    const a = ev.target.closest('a[href]');
    if (!a) return;
    const href = a.getAttribute('href');
    if (!href || href.startsWith('#')) return;
    let label;
    if (href.startsWith('mailto:')) label = 'email';
    else if (/\.pdf(\?|$)/.test(href)) label = 'resume';
    else {
      const card = a.closest('.project');
      const name = card ? card.querySelector('h3').textContent.trim().toLowerCase().replace(/\s+/g, '-') : null;
      const text = a.textContent.trim().toLowerCase();
      label = name ? name + '/' + text : text;
    }
    track('click/' + label);
  }, { passive: true });

  // Time on the page counts only while it's visible, so a tab left open in
  // the background doesn't read as a 3-hour visit.
  let activeMs = 0;
  let visibleSince = document.visibilityState === 'visible' ? Date.now() : null;
  const activeS = () => Math.round((activeMs + (visibleSince ? Date.now() - visibleSince : 0)) / 1000);

  // Scrolling, clicking, typing or touching marks a visit as a person's,
  // which is how scanners that load the page from data centers get told apart.
  let interacted = false;
  ['scroll', 'wheel', 'pointerdown', 'keydown', 'touchstart', 'mousemove'].forEach((ev) =>
    window.addEventListener(ev, () => { interacted = true; }, { passive: true, once: true }));

  // Heartbeats while the page is visible: at 10s, 30s, then every 30s for up
  // to half an hour. The closing beacon below is easy to lose (a phone kills
  // the tab, a window is never closed, the server is still waking up), so
  // the last heartbeat is what usually tells the dashboard how long someone
  // stayed. They go only to the live log, not to GoatCounter.
  let pings = 0, pingTimer = null;
  const ping = () => beacon('ping', true, { k: 'ping', s: activeS(), d: order[deepest], i: interacted });
  function schedulePing() {
    clearTimeout(pingTimer);
    if (document.visibilityState !== 'visible' || activeS() > 1800) return;
    pingTimer = setTimeout(() => { pings++; ping(); schedulePing(); }, pings === 0 ? 10e3 : pings === 1 ? 20e3 : 30e3);
  }
  schedulePing();

  // One summary event per visit: visit/<deepest section>/<time bucket>.
  let sent = false;
  function sendSummary() {
    if (sent) return;
    sent = true;
    const s = activeS();
    const bucket = s < 3 ? '0-3s' : s < 8 ? '3-8s' : s < 20 ? '8-20s' : s < 60 ? '20-60s' : s < 180 ? '1-3m' : '3m+';
    track('visit/' + order[deepest] + '/' + bucket);
  }
  function leaving() {
    if (visibleSince) { activeMs += Date.now() - visibleSince; visibleSince = null; }
    clearTimeout(pingTimer);
    ping();
    sendSummary();
  }
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') leaving();
    else { visibleSince = Date.now(); schedulePing(); }
  });
  window.addEventListener('pagehide', leaving);
})();
