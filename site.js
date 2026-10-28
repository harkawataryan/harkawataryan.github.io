(function () {
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
