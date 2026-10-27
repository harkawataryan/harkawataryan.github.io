// Perspective grid behind the hero. Lines converge on a horizon just below
// the middle of the viewport and roll slowly toward the viewer. Kept faint
// and low-frequency so the type stays the focus.
(function () {
  const canvas = document.getElementById('grid');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let W = 0, H = 0, dpr = 1;

  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = canvas.clientWidth; H = canvas.clientHeight;
    canvas.width = W * dpr; canvas.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  window.addEventListener('resize', resize); resize();

  let visible = true;
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; }).observe(canvas);

  const start = performance.now();
  let pointer = 0.5, pointerTarget = 0.5;
  window.addEventListener('mousemove', (e) => { pointerTarget = e.clientX / innerWidth; }, { passive: true });

  function draw(now) {
    requestAnimationFrame(draw);
    if (!visible || document.hidden) return;
    const t = reduced ? 0 : (now - start) / 1000;
    pointer += (pointerTarget - pointer) * 0.02;
    ctx.clearRect(0, 0, W, H);

    const horizonY = H * 0.62;
    const vx = W * (0.5 + (pointer - 0.5) * 0.15);   // vanishing point drifts a little with the pointer

    // horizon glow
    const glow = ctx.createLinearGradient(0, horizonY - 120, 0, horizonY + 40);
    glow.addColorStop(0, 'rgba(255,45,85,0)');
    glow.addColorStop(0.85, 'rgba(255,45,85,0.10)');
    glow.addColorStop(1, 'rgba(106,61,245,0.0)');
    ctx.fillStyle = glow; ctx.fillRect(0, horizonY - 120, W, 160);

    ctx.lineWidth = 1;
    // vertical lines converging on the vanishing point
    const n = 18;
    for (let i = -n; i <= n; i++) {
      const xb = vx + (i / n) * W * 1.4;
      const a = 0.10 * (1 - Math.abs(i) / (n + 2));
      const g = ctx.createLinearGradient(0, horizonY, 0, H);
      g.addColorStop(0, `rgba(255,45,85,0)`);
      g.addColorStop(0.25, `rgba(255,45,85,${a})`);
      g.addColorStop(1, `rgba(255,45,85,${a * 0.5})`);
      ctx.strokeStyle = g;
      ctx.beginPath(); ctx.moveTo(vx, horizonY); ctx.lineTo(xb, H); ctx.stroke();
    }
    // horizontal lines rolling toward the viewer (perspective spacing)
    const rows = 14, speed = 0.12;
    for (let k = 0; k < rows; k++) {
      const u = ((k + t * speed) % rows) / rows;   // 0 at horizon, 1 at bottom
      const y = horizonY + (H - horizonY) * (u * u);
      const a = 0.14 * u;
      ctx.strokeStyle = `rgba(255,45,85,${a})`;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }
    // horizon line
    ctx.strokeStyle = 'rgba(255,45,85,0.35)';
    ctx.beginPath(); ctx.moveTo(0, horizonY); ctx.lineTo(W, horizonY); ctx.stroke();
  }
  requestAnimationFrame(draw);
})();
