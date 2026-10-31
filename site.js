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
  const rules = [...document.querySelectorAll('.hero, .row')];
  if (still || !('IntersectionObserver' in window)) {
    revealables.forEach((el) => el.classList.add('in'));
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
  }
  window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();

  // GoatCounter custom events. No-ops when the counter is blocked.
  function track(path) {
    if (!window.goatcounter || !window.goatcounter.count) return;
    window.goatcounter.count({ path: path, title: path, event: true });
  }

  // Deepest section reached.
  const order = ['top', 'work', 'projects', 'about'];
  let deepest = 0;
  const io = new IntersectionObserver((es) => {
    for (const e of es) {
      if (!e.isIntersecting) continue;
      io.unobserve(e.target);
      deepest = Math.max(deepest, order.indexOf(e.target.id));
    }
  }, { rootMargin: '0px 0px -10% 0px' });
  document.querySelectorAll('section[id]').forEach((el) => io.observe(el));

  // Outbound and file clicks: "click/<label>", with the project name when inside a card.
  document.addEventListener('click', (ev) => {
    const a = ev.target.closest('a[href]');
    if (!a) return;
    const href = a.getAttribute('href');
    if (!href || href.startsWith('#')) return;
    let label;
    if (href.startsWith('mailto:')) label = 'email';
    else if (href.endsWith('.pdf')) label = 'resume';
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
