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
  // While the page is moving, the live demos skip their drawing so the
  // scroll itself gets every frame. The flag clears shortly after the last
  // scroll event.
  let scrollTimer = null;
  function markScrolling() {
    root.classList.add('scrolling');
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(() => { root.classList.remove('scrolling'); settle(); }, 140);
  }

  // Gentle paging: once a scroll ends near the top of a screen, ease the rest
  // of the way there. Any user input cancels it. Only on desktop-sized
  // windows, where the screens are one viewport tall.
  const screens = [...document.querySelectorAll('section.screen')];
  let settling = null, lastInput = 0;
  const paging = () => matchMedia('(min-width: 900px) and (min-height: 600px)').matches && !still;
  function settle() {
    if (!paging() || settling || performance.now() - lastInput < 120) return;
    const y = window.scrollY, vh = innerHeight;
    let best = null, bestD = Infinity;
    for (const el of screens) {
      const top = el.getBoundingClientRect().top + y;
      const d = top - y;
      if (Math.abs(d) < bestD) { bestD = Math.abs(d); best = top; }
    }
    if (best == null || bestD < 2 || bestD > vh * 0.35) return;
    const from = y, to = Math.min(best, document.documentElement.scrollHeight - vh), t0 = performance.now(), dur = 520 + Math.min(300, bestD);
    const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
    settling = (now) => {
      const k = Math.min(1, (now - t0) / dur);
      window.scrollTo(0, from + (to - from) * ease(k));
      if (k < 1 && settling) requestAnimationFrame(settling); else settling = null;
    };
    requestAnimationFrame(settling);
  }
  const cancelSettle = () => { lastInput = performance.now(); settling = null; };
  for (const ev of ['wheel', 'touchstart', 'pointerdown', 'keydown']) window.addEventListener(ev, cancelSettle, { passive: true });

  let ticking = false;
  function onScroll() {
    markScrolling();
    ticking = false;
    const y = window.scrollY;
    const max = document.documentElement.scrollHeight - innerHeight;
    if (bar) bar.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, y / max) : 0) + ')';
    if (heroName && !still && y < innerHeight * 1.2) {
      heroName.style.transform = 'translate3d(0,' + (y * 0.22).toFixed(1) + 'px,0)';
      heroName.style.opacity = Math.max(0, 1 - y / 650).toFixed(3);
    }
  }
  window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  window.addEventListener('resize', () => requestAnimationFrame(onScroll));
  onScroll();

  // GoatCounter custom events. No-ops when the counter is blocked.
  function track(path) {
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

  // One summary event per visit: visit/<deepest section>/<time bucket>.
  const start = Date.now();
  let sent = false;
  function sendSummary() {
    if (sent) return;
    sent = true;
    const s = (Date.now() - start) / 1000;
    const bucket = s < 3 ? '0-3s' : s < 8 ? '3-8s' : s < 20 ? '8-20s' : s < 60 ? '20-60s' : s < 180 ? '1-3m' : '3m+';
    track('visit/' + order[deepest] + '/' + bucket);
  }
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') sendSummary(); });
  window.addEventListener('pagehide', sendSummary);
})();
