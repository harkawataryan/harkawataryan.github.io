// Live clouds for the Volumetric Cloud Renderer card. A WebGL port of the
// renderer's cloud shader: ray-marched 3D noise with the same
// multiple-scattering lighting, at low resolution. The screenshot stays
// underneath and is all that shows when WebGL is missing, motion is
// reduced, or the card is off screen.
(function () {
  const shot = document.querySelector('.project .shot[data-live-clouds]');
  if (!shot) return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const canvas = document.createElement('canvas');
  canvas.className = 'live';
  canvas.setAttribute('aria-hidden', 'true');
  const gl = canvas.getContext('webgl', { antialias: false, alpha: false, powerPreference: 'low-power', preserveDrawingBuffer: false });
  if (!gl) return;

  const VS = 'attribute vec2 p;varying vec2 v;void main(){v=p*0.5+0.5;gl_Position=vec4(p,0.,1.);}';
  const FS = `
precision highp float;
varying vec2 v;
uniform vec2 uRes;
uniform float uTime;
uniform vec3 uSun;
uniform float uFrame;
uniform float uBlend;
uniform sampler2D uHist;
uniform float uCov;   // coverage 0..1
uniform float uType;  // 0 stratus .. 1 cumulonimbus
uniform int uView;    // 0 shaded, 1 density, 2 march cost

const float BASE = 700.0, THICK = 2200.0;
const float SIGMA = 0.011;          // extinction per metre at density 1
const int STEPS = 34;
const vec3 AMBIENT_TOP = vec3(0.62, 0.74, 0.95);
const vec3 AMBIENT_BOTTOM = vec3(0.36, 0.42, 0.52);
const float PI = 3.14159265;

float remap(float x, float a, float b, float c, float d) { return clamp(c + (x - a) * (d - c) / (b - a), 0.0, 1.0); }
float hash(vec3 p) { p = fract(p * 0.3183099 + vec3(0.1, 0.2, 0.3)); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float noise(vec3 x) {
  vec3 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(hash(i), hash(i + vec3(1, 0, 0)), f.x), mix(hash(i + vec3(0, 1, 0)), hash(i + vec3(1, 1, 0)), f.x), f.y),
             mix(mix(hash(i + vec3(0, 0, 1)), hash(i + vec3(1, 0, 1)), f.x), mix(hash(i + vec3(0, 1, 1)), hash(i + vec3(1, 1, 1)), f.x), f.y), f.z);
}
// Billowy base shape: a Perlin-Worley stand-in built from ridged value noise.
float shape(vec3 p) {
  float n = 0.0, a = 0.5;
  for (int i = 0; i < 3; i++) { n += a * (1.0 - abs(noise(p) * 2.0 - 1.0)); p = p * 2.1 + 31.0; a *= 0.5; }
  return n;
}
float detail(vec3 p) { return 0.55 * noise(p) + 0.3 * noise(p * 2.3 + 7.0) + 0.15 * noise(p * 5.1 + 19.0); }
float heightFrac(vec3 p) { return clamp((p.y - BASE) / THICK, 0.0, 1.0); }
// Vertical profile per cloud type, as in the renderer: stratus flat and low,
// cumulus taller with a rounded top, cumulonimbus filling the layer.
float heightGradient(float h) {
  float stratus = remap(h, 0.0, 0.08, 0.0, 1.0) * remap(h, 0.15, 0.3, 1.0, 0.0);
  float cumulus = remap(h, 0.0, 0.12, 0.0, 1.0) * remap(h, 0.55, 0.95, 1.0, 0.0);
  float cumulonimbus = remap(h, 0.0, 0.1, 0.0, 1.0) * remap(h, 0.75, 1.0, 1.0, 0.0);
  float a = clamp(uType * 2.0, 0.0, 1.0), b = clamp(uType * 2.0 - 1.0, 0.0, 1.0);
  return mix(mix(stratus, cumulus, a), cumulonimbus, b);
}

float density(vec3 p, bool cheap) {
  float h = heightFrac(p);
  vec3 wind = vec3(14.0, 0.0, 5.0) * uTime;
  vec3 sp = p + wind; sp.xz += h * 120.0;
  float coverage = clamp(uCov + 0.3 * noise((p.xz + wind.xz * 0.3).xyy * 0.00022) - 0.15, 0.0, 1.0);
  float base = shape(sp * (1.0 / 2600.0));
  base = remap(base, 0.42, 1.0, 0.0, 1.0) * heightGradient(h);
  base = remap(base, 1.0 - coverage, 1.0, 0.0, 1.0) * coverage;
  if (cheap || base <= 0.0) return base * 3.5;
  float d = detail((sp + vec3(0.0, uTime * 3.0, 0.0)) * (1.0 / 320.0));
  float mod_ = mix(d, 1.0 - d, clamp(h * 4.0, 0.0, 1.0));
  return remap(base, mod_ * 0.4 * exp(-coverage * 0.75), 1.0, 0.0, 1.0) * 3.5;
}
float phaseHG(float c, float g) { float gg = g * g; return (1.0 - gg) / (4.0 * PI * pow(1.0 + gg - 2.0 * g * c, 1.5)); }
float lightDepth(vec3 p) {
  float od = 0.0, st = THICK * 0.07, t = st * 0.6;
  for (int i = 0; i < 5; i++) { od += density(p + uSun * t, i > 2) * st; t += st; st *= 1.35; }
  return od;
}
// Multiple-scattering octaves, powder term and ambient, as in the renderer.
vec3 scattered(float od, float cosT, float h, float sunset) {
  float sun = 0.0, a = 1.0, b = 1.0, c = 1.0;
  for (int k = 0; k < 4; k++) {
    float ph = 0.65 * phaseHG(cosT, 0.6 * c) + 0.35 * phaseHG(cosT, -0.3 * c);
    sun += a * exp(-od * SIGMA * b) * ph;
    a *= 0.55; b *= 0.45; c *= 0.6;
  }
  float powder = 1.0 - exp(-od * SIGMA * 2.0);
  sun *= mix(1.0, powder, clamp(cosT * 0.5 + 0.5, 0.0, 1.0) * 0.5);
  vec3 ambient = mix(AMBIENT_BOTTOM, AMBIENT_TOP, h) * mix(1.0, 0.6, sunset);
  float ambT = exp(-od * SIGMA * 0.2) * 0.7 + 0.1;
  vec3 sunColor = mix(vec3(1.0, 0.96, 0.9), vec3(1.0, 0.62, 0.38), sunset);
  return sunColor * 10.0 * sun + ambient * ambT * (1.0 / PI);
}
vec3 sky(vec3 rd, float sunset) {
  float up = clamp(rd.y, 0.0, 1.0);
  vec3 zenith = mix(vec3(0.18, 0.36, 0.78), vec3(0.16, 0.24, 0.50), sunset);
  vec3 horizon = mix(vec3(0.62, 0.74, 0.90), vec3(0.95, 0.66, 0.48), sunset);
  vec3 s = mix(horizon, zenith, pow(up, 0.55));
  float sa = max(dot(rd, uSun), 0.0);
  s += mix(vec3(1.0, 0.85, 0.6), vec3(1.0, 0.5, 0.25), sunset) * pow(sa, 8.0) * (0.25 + 0.5 * sunset);
  s += vec3(1.0, 0.95, 0.85) * smoothstep(0.9993, 0.9997, sa) * 12.0;
  return s;
}
vec3 tonemap(vec3 x) { return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0); }

void main() {
  vec2 ndc = v * 2.0 - 1.0;
  float aspect = uRes.x / uRes.y;
  // Camera on the ground looking up a little, like the README's first image.
  float pitch = 0.58, fov = 1.15;
  vec3 ro = vec3(0.0, 40.0, 0.0);
  vec3 dir = normalize(vec3(ndc.x * aspect * tan(fov * 0.5), ndc.y * tan(fov * 0.5), -1.0));
  float cp = cos(pitch), sp_ = sin(pitch);
  vec3 rd = vec3(dir.x, dir.y * cp - dir.z * sp_, dir.y * sp_ + dir.z * cp);

  float sunset = 1.0 - smoothstep(0.0, 0.35, uSun.y);
  vec3 bg = sky(rd, sunset);
  if (rd.y < 0.0) bg = mix(vec3(0.22, 0.27, 0.18) * (max(uSun.y, 0.0) * 0.8 + 0.2), sky(vec3(rd.x, 0.0, rd.z), sunset), 1.0);

  vec3 col = bg;
  if (rd.y > 0.02) {
    float t0 = (BASE - ro.y) / rd.y, t1 = (BASE + THICK - ro.y) / rd.y;
    t1 = min(t1, t0 + 16000.0);
    // Interleaved gradient noise, shifted each frame, so accumulated frames converge.
    float jitter = fract(52.9829189 * fract(0.06711056 * gl_FragCoord.x + 0.00583715 * gl_FragCoord.y + 0.0113 * uFrame));
    float stepSize = (t1 - t0) / float(STEPS);
    float cosT = dot(rd, uSun);
    float t = t0 + jitter * stepSize, trans = 1.0, depthAcc = 0.0, depthW = 0.0, lit = 0.0;
    vec3 radiance = vec3(0.0);
    for (int i = 0; i < STEPS; i++) {
      vec3 p = ro + rd * t;
      float dens = density(p, false);
      if (dens > 0.0) {
        lit += 1.0;
        float od = lightDepth(p);
        vec3 light = scattered(od, cosT, heightFrac(p), sunset);
        float st = exp(-dens * SIGMA * stepSize);
        vec3 integ = (light - light * st) / max(dens * SIGMA, 1e-6);
        radiance += trans * integ * dens * SIGMA;
        float w = trans * (1.0 - st);
        depthAcc += t * w; depthW += w;
        trans *= st;
        if (trans < 0.01) { trans = 0.0; break; }
      }
      t += stepSize;
    }
    float depth = depthW > 0.0 ? depthAcc / depthW : 0.0;
    float fade = exp(-max(depth - 5000.0, 0.0) / 9000.0);
    radiance *= fade;
    trans = mix(1.0, trans, fade);
    col = radiance + bg * trans;
    if (uView == 1) {
      // Density: what the noise and weather produce before any lighting.
      col = mix(vec3(0.06, 0.08, 0.14), vec3(0.95), 1.0 - trans);
    } else if (uView == 2) {
      // March cost: how many of the steps along this ray hit cloud and paid
      // for the light samples. Dark is cheap, orange is expensive.
      float c = lit / float(STEPS);
      col = mix(vec3(0.05, 0.05, 0.08), mix(vec3(0.15, 0.3, 0.8), vec3(1.0, 0.3, 0.0), c * 2.2), smoothstep(0.0, 0.3, c));
    }
  } else if (uView != 0) {
    col = vec3(0.06, 0.08, 0.14);
  }
  vec3 fresh = uView == 0 ? pow(tonemap(col), vec3(1.0 / 2.2)) : col;
  vec3 hist = texture2D(uHist, v).rgb;
  gl_FragColor = vec4(mix(hist, fresh, uBlend), 1.0);
}`;

  function compile(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  }
  let prog;
  try {
    prog = gl.createProgram();
    gl.attachShader(prog, compile(gl.VERTEX_SHADER, VS));
    gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
  } catch (e) {
    return; // driver can't run it; the screenshot stays
  }
  // A second tiny program copies the accumulated frame to the screen.
  const COPY = 'precision mediump float;varying vec2 v;uniform sampler2D uTex;void main(){gl_FragColor=texture2D(uTex,v);}';
  const copy = gl.createProgram();
  gl.attachShader(copy, compile(gl.VERTEX_SHADER, VS));
  gl.attachShader(copy, compile(gl.FRAGMENT_SHADER, COPY));
  gl.linkProgram(copy);

  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  for (const pr of [prog, copy]) {
    gl.useProgram(pr);
    const loc = gl.getAttribLocation(pr, 'p');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  }
  gl.useProgram(prog);
  const U = (n) => gl.getUniformLocation(prog, n);
  const uRes = U('uRes'), uTime = U('uTime'), uSun = U('uSun'), uFrame = U('uFrame'), uBlend = U('uBlend'), uHist = U('uHist');
  const uTex = gl.getUniformLocation(copy, 'uTex');
  const uCov = U('uCov'), uType = U('uType'), uView = U('uView');
  let cov = 0.48, type = 0.55, view = 0;

  // Two textures ping-pong: each frame blends the new render into the last
  // one, so the per-pixel jitter averages out into a smooth image.
  const pair = [0, 1].map(() => {
    const tex = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const fbo = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    return { tex, fbo };
  });
  let cur = 0, frames = 0;
  function allocate(w, h) {
    for (const p of pair) { gl.bindTexture(gl.TEXTURE_2D, p.tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null); }
    frames = 0;
  }

  // Sun direction from azimuth/elevation; dragging changes both.
  let az = 0.45, el = 0.6;
  const sunDir = () => [Math.sin(az) * Math.cos(el), Math.sin(el), -Math.cos(az) * Math.cos(el)];

  const SCALE = 0.75;
  function size() {
    const r = shot.getBoundingClientRect();
    const w = Math.max(2, Math.round(r.width * SCALE)), h = Math.max(2, Math.round(r.height * SCALE));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; allocate(w, h); }
  }

  let visible = false, raf = 0, last = 0, t0 = performance.now(), sunMoved = true;
  const FRAME = 1000 / 30;
  function frame(now) {
    raf = 0;
    if (!visible || document.hidden) return;
    if (now - last >= FRAME) {
      last = now;
      size();
      const prev = pair[cur], next = pair[cur ^ 1];
      cur ^= 1;
      // First frames and sun moves blend fast so the picture responds; then
      // settle into a slow blend that smooths the jitter away.
      const blend = frames < 2 ? 1 : sunMoved ? 0.45 : 0.14;
      sunMoved = false;
      gl.useProgram(prog);
      gl.bindFramebuffer(gl.FRAMEBUFFER, next.fbo);
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, prev.tex);
      gl.uniform1i(uHist, 0);
      gl.uniform2f(uRes, canvas.width, canvas.height);
      gl.uniform1f(uTime, (now - t0) / 1000);
      gl.uniform1f(uFrame, frames % 64);
      gl.uniform1f(uBlend, blend);
      gl.uniform3fv(uSun, sunDir());
      gl.uniform1f(uCov, cov);
      gl.uniform1f(uType, type);
      gl.uniform1i(uView, view);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      gl.useProgram(copy);
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      gl.bindTexture(gl.TEXTURE_2D, next.tex);
      gl.uniform1i(uTex, 0);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      frames++;
      if (frames === 3) canvas.classList.add('on');
    }
    raf = requestAnimationFrame(frame);
  }
  const kick = () => { if (!raf && visible && !document.hidden) raf = requestAnimationFrame(frame); };
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; kick(); }, { rootMargin: '80px' }).observe(shot);
  document.addEventListener('visibilitychange', kick);
  gl.canvas.addEventListener('webglcontextlost', (e) => { e.preventDefault(); canvas.classList.remove('on'); });

  // Drag to move the sun. A real drag must not follow the card's link.
  let down = null, dragged = false;
  shot.addEventListener('pointerdown', (e) => { down = { x: e.clientX, y: e.clientY, az, el }; dragged = false; });
  shot.addEventListener('pointermove', (e) => {
    if (!down) return;
    const dx = e.clientX - down.x, dy = e.clientY - down.y;
    if (!dragged && Math.hypot(dx, dy) < 5) return;
    if (!dragged) { dragged = true; shot.setPointerCapture(e.pointerId); shot.classList.add('dragging'); }
    const r = shot.getBoundingClientRect();
    sunMoved = true;
    az = down.az + (dx / r.width) * Math.PI * 1.2;
    el = Math.max(0.03, Math.min(1.35, down.el - (dy / r.height) * 1.6));
    e.preventDefault();
  });
  const up = () => { down = null; shot.classList.remove('dragging'); };
  shot.addEventListener('pointerup', up);
  shot.addEventListener('pointercancel', up);
  shot.addEventListener('click', (e) => { if (dragged) { e.preventDefault(); dragged = false; } });
  shot.addEventListener('dragstart', (e) => e.preventDefault());

  shot.appendChild(canvas);
  // Controls for the things the renderer itself exposes: coverage, cloud
  // type, and debug views of the density field and the march cost.
  const panel = document.createElement('div');
  panel.className = 'cloudctl';
  panel.innerHTML = `
    <label>Coverage <input type="range" min="0.2" max="0.8" step="0.01" value="0.48" aria-label="Cloud coverage"></label>
    <label>Type <input type="range" min="0" max="1" step="0.01" value="0.55" aria-label="Cloud type, stratus to cumulonimbus"><span class="tname">cumulus</span></label>
`;
  const [covIn, typeIn] = panel.querySelectorAll('input');
  const tname = panel.querySelector('.tname');
  const typeName = (v) => (v < 0.33 ? 'stratus' : v < 0.72 ? 'cumulus' : 'cumulonimbus');
  covIn.addEventListener('input', () => { cov = Number(covIn.value); sunMoved = true; });
  typeIn.addEventListener('input', () => { type = Number(typeIn.value); tname.textContent = typeName(type); sunMoved = true; });
  // Pointer events on the panel must not start a sun drag.
  for (const ev of ['pointerdown', 'pointermove', 'pointerup']) panel.addEventListener(ev, (e) => e.stopPropagation());
  panel.addEventListener('click', (e) => { e.stopPropagation(); e.preventDefault(); });
  shot.appendChild(panel);
  const hint = document.createElement('span');
  hint.className = 'hint';
  hint.innerHTML = '<i></i>Live · drag to move the sun';
  shot.appendChild(hint);
  shot.classList.add('has-live');
})();
