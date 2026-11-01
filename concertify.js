// Live Concertify demo for the project card. A visitor names a few artists
// and a city, and the real Concertify backend ranks the shows near them with
// the same ranker logged-in users get. A precomputed example shows at once so
// the card is never empty while the free-tier server wakes up.
(function () {
  const shot = document.querySelector('.project .shot[data-live-concertify]');
  if (!shot) return;

  const API = 'https://concertify-cm6k.onrender.com/api/demo';
  const CITIES = [
    ['Austin, TX', 30.2672, -97.7431], ['New York, NY', 40.7128, -74.006], ['Los Angeles, CA', 34.0522, -118.2437],
    ['Chicago, IL', 41.8781, -87.6298], ['San Francisco, CA', 37.7749, -122.4194], ['Seattle, WA', 47.6062, -122.3321],
    ['Nashville, TN', 36.1627, -86.7816], ['Boston, MA', 42.3601, -71.0589], ['Denver, CO', 39.7392, -104.9903], ['Atlanta, GA', 33.749, -84.388],
  ];
  const SAMPLE = {"artists":[{"id":"2uYWxilOVlUdk4oV9DvwqK","name":"Mitski","image":"https://i.scdn.co/image/ab6761610000e5ebaf731fe1a006c29152075c89"},{"id":"1r1uxoy19fzMxunt3ONAkG","name":"Phoebe Bridgers","image":"https://i.scdn.co/image/ab6761610000e5eb6e2d4ab2b84463aa4c349311"},{"id":"0Y6dVaC9DZtPNH4591M42W","name":"TV Girl","image":"https://i.scdn.co/image/ab6761610000e5ebd80695211689a9c8c3fee3b0"}],"scanned":303,"radiusMiles":50,"city":"Austin, TX","recommendations":[{"affinity":0.403,"reasons":["Matches your taste in alternative, rock, alternative rock","New to you"],"artist":{"name":"Holywatr","image":null},"event":{"id":"G5dIZ_1YdMUBy","name":"Holywatr: Deo Gratias Tour","date":"2026-11-18","url":"https://www.ticketmaster.com/holywatr-deo-gratias-tour-austin-texas-11-18-2026/event/3A0064AC03DF6EB9","image":"https://s1.ticketm.net/dam/a/0ae/7226e100-41ea-4d30-bb48-b8a6c29880ae_TABLET_LANDSCAPE_LARGE_16_9.jpg","venue":"Scoot Inn","city":"Austin","distanceMi":1}},{"affinity":0.357,"reasons":["Matches your taste in alternative, indie pop","New to you"],"artist":{"name":"Adrianne Lenker","image":null},"event":{"id":"Z7r9jZ1AA7vf-","name":"Adrianne Lenker w/ Staci Foster","date":"2026-11-23","url":"https://www.ticketmaster.com/event/Z7r9jZ1AA7vf-","image":"https://s1.ticketm.net/dam/a/878/b9338403-304f-4a42-be75-c5e7b9572878_SOURCE","venue":"Austin City Limits Live at The Moody Theater","city":"Austin","distanceMi":0}},{"affinity":0.258,"reasons":["Matches your taste in rock","New to you"],"artist":{"name":"The Aces","image":null},"event":{"id":"Z7r9jZ1AAZ_uo","name":"The Aces w/ Gatlin","date":"2026-11-12","url":"https://www.ticketmaster.com/event/Z7r9jZ1AAZ_uo","image":"https://s1.ticketm.net/dam/a/7d9/4c75dd58-09fb-4190-bf1f-a65c628317d9_SOURCE","venue":"Brushy Street Commons","city":"Austin","distanceMi":0}},{"affinity":0.361,"reasons":["Matches your taste in alternative, rock, alternative rock","New to you"],"artist":{"name":"Medium Build","image":null},"event":{"id":"G5dIZ_uewq1dy","name":"KTSN Presents: Medium Build Presents The King of Having Fun on Tour","date":"2026-11-10","url":"https://www.ticketmaster.com/ktsn-presents-medium-build-presents-the-austin-texas-11-10-2026/event/3A0064D0B274A0F9","image":"https://s1.ticketm.net/dam/a/705/0d5a5e8f-676c-4f24-bdd8-61a92e46f705_SOURCE","venue":"Emo's Austin","city":"Austin","distanceMi":2}},{"affinity":0.35,"reasons":["Matches your taste in rock, alternative rock","New to you"],"artist":{"name":"Dinosaur Jr.","image":null},"event":{"id":"G5dIZ_uSqkioQ","name":"Dinosaur Jr. - Fall Tour 2026 with special guest Stef Chura","date":"2026-11-05","url":"https://www.ticketmaster.com/dinosaur-jr-fall-tour-2026-with-austin-texas-11-05-2026/event/3A0064DCDD1AC45A","image":"https://s1.ticketm.net/dam/a/148/6f9098fe-e645-4636-bdcd-2c63d5ced148_TABLET_LANDSCAPE_LARGE_16_9.jpg","venue":"Stubb's Waller Creek Amphitheater","city":"Austin","distanceMi":0}}]};

  const ui = document.createElement('div');
  ui.className = 'demo';
  ui.innerHTML = `
    <form class="bar" autocomplete="off">
      <div class="chips" aria-label="Artists"></div>
      <div class="pick">
        <input type="text" placeholder="Add an artist…" aria-label="Add an artist" maxlength="60">
        <ul class="sugg" role="listbox" hidden></ul>
      </div>
      <select aria-label="City"></select>
      <select class="radius" aria-label="Radius"><option value="25">25 mi</option><option value="50" selected>50 mi</option><option value="100">100 mi</option></select>
      <select class="when" aria-label="When"><option value="">Any time</option><option value="30">Next 30 days</option><option value="weekend">Weekends</option></select>
      <button type="submit">Rank shows</button>
    </form>
    <div class="genres" aria-label="Genres"></div>
    <ol class="results" aria-live="polite"></ol>
    <div class="foot"><span class="status"></span></div>`;
  const form = ui.querySelector('form'), chips = ui.querySelector('.chips'), input = ui.querySelector('input'), sugg = ui.querySelector('.sugg'),
    select = ui.querySelector('select'), radiusSel = ui.querySelector('.radius'), whenSel = ui.querySelector('.when'),
    button = ui.querySelector('button[type=submit]'), list = ui.querySelector('.results'), status = ui.querySelector('.status'), genreBox = ui.querySelector('.genres');
  let genresOn = new Set(), lastGenres = [];
  CITIES.forEach(([name], i) => { const o = document.createElement('option'); o.value = i; o.textContent = name; select.append(o); });
  const near = document.createElement('option'); near.value = 'near'; near.textContent = 'Near me'; select.append(near);

  let artists = SAMPLE.artists.slice();
  let live = false, busy = false, seq = 0;
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };

  function renderChips() {
    chips.textContent = '';
    for (const a of artists) {
      const c = el('span', 'chip');
      if (a.image) { const im = el('img'); im.src = a.image; im.alt = ''; im.loading = 'lazy'; c.append(im); }
      c.append(el('span', '', a.name));
      const x = el('button', 'x', '×'); x.type = 'button'; x.setAttribute('aria-label', 'Remove ' + a.name);
      x.addEventListener('click', () => { artists = artists.filter((b) => b.id !== a.id); renderChips(); });
      c.append(x);
      chips.append(c);
    }
    input.placeholder = artists.length ? 'Add another…' : 'Add an artist…';
    input.disabled = artists.length >= 5;
  }

  const LABEL = { direct: 'artist match', genre: 'genre fit', proximity: 'distance', soon: 'date' };
  function renderGenres(genres) {
    lastGenres = genres || [];
    genreBox.textContent = '';
    genreBox.hidden = !lastGenres.length;
    for (const { genre, count } of lastGenres.slice(0, 10)) {
      const b = el('button', 'g' + (genresOn.has(genre) ? ' on' : ''), genre);
      b.type = 'button';
      b.append(el('small', '', ' ' + count));
      b.addEventListener('click', () => { genresOn.has(genre) ? genresOn.delete(genre) : genresOn.add(genre); renderGenres(lastGenres); rank(); });
      genreBox.append(b);
    }
  }

  function renderResults(data, note) {
    list.textContent = '';
    renderGenres(data.genres);
    if (!data.recommendations.length) {
      list.append(el('li', 'empty', 'No shows near there line up with those artists in the next few months. Try a bigger city.'));
    }
    for (const r of data.recommendations) {
      const li = el('li');
      const a = el('a'); a.href = r.event.url || '#'; a.target = '_blank'; a.rel = 'noopener';
      const img = el('span', 'cover');
      const src = (r.artist && r.artist.image) || r.event.image;
      if (src) { const im = el('img'); im.src = src; im.alt = ''; im.loading = 'lazy'; img.append(im); }
      const body = el('span', 'body');
      body.append(el('b', '', (r.artist && r.artist.name) || r.event.name));
      const when = r.event.date ? new Date(r.event.date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';
      body.append(el('span', 'meta', [r.event.venue, when, r.event.distanceMi != null ? r.event.distanceMi + ' mi' : ''].filter(Boolean).join(' · ')));
      body.append(el('span', 'why', (r.reasons || []).slice(0, 2).join('. ')));
      const score = el('span', 'score');
      const pct = Math.round(Math.min(1, r.affinity / 0.6) * 100);
      score.append(el('b', '', pct + '%'));
      const bar = el('span', 'meter'); const fill = el('i'); fill.style.width = pct + '%'; bar.append(fill); score.append(bar);
      a.append(img, body, score);
      li.append(a);
      // Score breakdown: the four signals the ranker weighs, shown on hover or tap.
      if (r.components) {
        const why = el('span', 'breakdown');
        for (const k of ['direct', 'genre', 'proximity', 'soon']) {
          const v = Math.round(100 * (r.components[k] || 0));
          const row = el('span', 'brow');
          row.append(el('span', 'bk', LABEL[k]));
          const m = el('span', 'bm'); const f = el('i'); f.style.width = v + '%'; m.append(f); row.append(m);
          row.append(el('span', 'bv', v + ''));
          why.append(row);
        }
        li.append(why);
        li.addEventListener('click', (e) => { if (e.target.closest('a') && !e.target.closest('.breakdown')) return; li.classList.toggle('open'); });
      }
      list.append(li);
    }
    status.textContent = note;
  }

  function cityOf() {
    const v = select.value;
    if (v !== 'near') { const [name, lat, lng] = CITIES[+v]; return Promise.resolve({ name, lat, lng }); }
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) return reject(new Error('no geolocation'));
      navigator.geolocation.getCurrentPosition((p) => resolve({ name: 'near you', lat: p.coords.latitude, lng: p.coords.longitude }), () => reject(new Error('denied')), { timeout: 8000 });
    });
  }

  async function rank() {
    if (busy || !artists.length) return;
    busy = true; button.disabled = true;
    const my = ++seq;
    let city;
    try { city = await cityOf(); } catch (e) { status.textContent = 'Location was blocked; pick a city instead.'; select.value = '0'; busy = false; button.disabled = false; return; }
    status.textContent = 'Ranking…';
    const q = new URLSearchParams({ artists: artists.map((a) => a.id).join(','), lat: city.lat, lng: city.lng, radius: radiusSel.value, limit: 6 });
    if (whenSel.value === 'weekend') q.set('weekend', '1');
    if (whenSel.value === '30') q.set('to', new Date(Date.now() + 30 * 864e5).toISOString().slice(0, 10));
    if (genresOn.size) q.set('genres', [...genresOn].join(','));
    const slow = setTimeout(() => { if (my === seq) status.textContent = 'Waking the server (free tier, up to 30s)…'; }, 3000);
    try {
      const res = await fetch(`${API}/recommendations?${q}`);
      if (my !== seq) return;
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const data = await res.json();
      live = true;
      const kept = data.filteredOut ? `${data.scanned - data.filteredOut} of ${data.scanned}` : `${data.scanned}`;
      renderResults(data, `Ranked ${kept} shows within ${data.radiusMiles} mi of ${city.name} for ${data.artists.map((a) => a.name).join(', ')}. Tap a show for its score breakdown.`);
    } catch (e) {
      if (my === seq) status.textContent = 'Could not reach Concertify right now. Showing the example instead.';
    } finally {
      clearTimeout(slow);
      if (my === seq) { busy = false; button.disabled = false; }
    }
  }

  // Autocomplete from Spotify through the demo endpoint.
  let timer, sel = -1, found = [];
  async function search(q) {
    try {
      const res = await fetch(`${API}/artists?q=${encodeURIComponent(q)}`);
      if (!res.ok) return [];
      return (await res.json()).artists.filter((a) => !artists.some((b) => b.id === a.id));
    } catch (e) { return []; }
  }
  function showSugg() {
    sugg.textContent = '';
    sugg.hidden = !found.length;
    found.forEach((a, i) => {
      const li = el('li'); li.setAttribute('role', 'option'); li.setAttribute('aria-selected', String(i === sel));
      if (a.image) { const im = el('img'); im.src = a.image; im.alt = ''; li.append(im); }
      li.append(el('span', '', a.name));
      li.addEventListener('mousedown', (e) => { e.preventDefault(); add(a); });
      sugg.append(li);
    });
  }
  function add(a) { if (artists.length < 5) artists.push(a); input.value = ''; found = []; sel = -1; showSugg(); renderChips(); input.focus(); }
  input.addEventListener('input', () => {
    clearTimeout(timer);
    const q = input.value.trim();
    if (q.length < 2) { found = []; showSugg(); return; }
    timer = setTimeout(async () => { const r = await search(q); if (input.value.trim() === q) { found = r; sel = r.length ? 0 : -1; showSugg(); } }, 220);
  });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown' && found.length) { sel = (sel + 1) % found.length; showSugg(); e.preventDefault(); }
    else if (e.key === 'ArrowUp' && found.length) { sel = (sel - 1 + found.length) % found.length; showSugg(); e.preventDefault(); }
    else if (e.key === 'Enter') { e.preventDefault(); if (found[sel]) add(found[sel]); else if (!input.value) rank(); }
    else if (e.key === 'Escape') { found = []; showSugg(); }
    else if (e.key === 'Backspace' && !input.value && artists.length) { artists.pop(); renderChips(); }
  });
  input.addEventListener('blur', () => setTimeout(() => { found = []; showSugg(); }, 150));
  form.addEventListener('submit', (e) => { e.preventDefault(); rank(); });
  for (const sel of [select, radiusSel, whenSel]) sel.addEventListener('change', () => { if (live || artists.length) rank(); });

  // Wake the free-tier server as soon as the card scrolls near, so the first
  // real request is quick.
  let woke = false;
  new IntersectionObserver((es) => {
    if (!es[0].isIntersecting || woke) return;
    woke = true;
    fetch('https://concertify-cm6k.onrender.com/health', { mode: 'no-cors' }).catch(() => {});
  }, { rootMargin: '400px' }).observe(shot);

  renderChips();
  renderResults(SAMPLE, `Example: ${SAMPLE.scanned} shows within ${SAMPLE.radiusMiles} mi of ${SAMPLE.city}, ranked for ${SAMPLE.artists.map((a) => a.name).join(', ')}. Add your own.`);
  shot.appendChild(ui);
  shot.classList.add('has-demo');
  requestAnimationFrame(() => ui.classList.add('on'));
})();
