(function () {
  document.documentElement.classList.add('js');

  // GoatCounter custom events. Each becomes a row in the Pages list.
  // No-ops when the counter script is blocked or hasn't loaded.
  function track(path, title) {
    if (!window.goatcounter || !window.goatcounter.count) return;
    window.goatcounter.count({ path: path, title: title || path, event: true });
  }

  // Scroll reveal, and a "section/<id>" event the first time each section is seen.
  const io = new IntersectionObserver((es) => {
    for (const e of es) {
      if (!e.isIntersecting) continue;
      e.target.classList.add('in');
      io.unobserve(e.target);
      if (e.target.id) track('section/' + e.target.id);
    }
  }, { rootMargin: '0px 0px -10% 0px' });
  document.querySelectorAll('.reveal').forEach((el) => io.observe(el));

  // Outbound and file clicks: "click/<label>", with the project name when inside a card.
  document.addEventListener('click', (ev) => {
    const a = ev.target.closest('a[href]');
    if (!a) return;
    const href = a.getAttribute('href');
    if (!href || href.startsWith('#')) return;
    let label;
    if (href.startsWith('mailto:')) label = 'email';
    else if (href.endsWith('.pdf')) label = 'resume';
    else if (href.includes('goatcounter.com')) return;
    else {
      const card = a.closest('.project');
      const name = card ? card.querySelector('h3').firstChild.textContent.trim().toLowerCase().replace(/\s+/g, '-') : null;
      const text = a.textContent.trim().toLowerCase();
      label = name ? name + '/' + text : text;
    }
    track('click/' + label);
  }, { passive: true });

  // Time on page, bucketed, sent once when the page is hidden or unloaded.
  const start = Date.now();
  let sent = false;
  function sendTime() {
    if (sent) return;
    sent = true;
    const s = (Date.now() - start) / 1000;
    const bucket = s < 10 ? '0-10s' : s < 30 ? '10-30s' : s < 60 ? '30-60s' : s < 180 ? '1-3m' : s < 600 ? '3-10m' : '10m+';
    track('time/' + bucket);
  }
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'hidden') sendTime(); });
  window.addEventListener('pagehide', sendTime);
})();
