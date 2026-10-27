// Live cloud sky behind the hero. A single-layer version of the volumetric
// renderer: a ray from the camera hits a cloud plane, density comes from
// value-noise fbm scrolled by wind, and shading compares density toward the
// sun. Rendered at reduced resolution and only while the hero is on screen.
(function () {
  const canvas = document.getElementById('sky');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const gl = canvas.getContext('webgl', { antialias: false, alpha: false, powerPreference: 'low-power' });
  if (!gl) { canvas.style.display = 'none'; return; }

  const vs = `attribute vec2 p; void main(){ gl_Position = vec4(p, 0.0, 1.0); }`;
  const fs = `
precision mediump float;
uniform vec2 uRes; uniform float uTime; uniform vec2 uSun; uniform float uDark;

float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float noise(vec2 p){
  vec2 i = floor(p), f = fract(p);
  vec2 u = f*f*(3.0-2.0*f);
  return mix(mix(hash(i), hash(i+vec2(1,0)), u.x), mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), u.x), u.y);
}
float fbm(vec2 p){
  float a = 0.0, w = 0.5;
  mat2 m = mat2(1.6, 1.2, -1.2, 1.6);
  for (int i = 0; i < 5; i++){ a += w * noise(p); p = m * p; w *= 0.5; }
  return a;
}
float density(vec2 uv){
  float d = fbm(uv) ;
  return smoothstep(0.42, 0.72, d);
}
void main(){
  vec2 ndc = (gl_FragCoord.xy / uRes) * 2.0 - 1.0;
  ndc.x *= uRes.x / uRes.y;
  vec3 rd = normalize(vec3(ndc.x, ndc.y * 0.9 + 0.25, 2.0));
  vec3 sunDir = normalize(vec3(uSun.x, max(uSun.y, 0.08), 0.8));
  float sunAmt = max(dot(rd, sunDir), 0.0);

  // sky gradient, cooler and darker in dark mode
  vec3 zenith = mix(vec3(0.20, 0.38, 0.80), vec3(0.03, 0.05, 0.11), uDark);
  vec3 horizon = mix(vec3(0.70, 0.80, 0.92), vec3(0.16, 0.19, 0.28), uDark);
  vec3 sky = mix(horizon, zenith, clamp(rd.y * 1.6, 0.0, 1.0));
  sky += mix(vec3(1.0, 0.85, 0.6), vec3(0.9, 0.6, 0.35), uDark) * pow(sunAmt, 14.0) * 0.35;
  sky += vec3(1.0, 0.95, 0.85) * (smoothstep(0.9990, 0.9996, sunAmt) * 0.9 + pow(sunAmt, 180.0) * 0.5);

  vec3 col = sky;
  if (rd.y > 0.02) {
    float t = 1.0 / rd.y;                       // hit the plane y = 1
    vec2 uv = rd.xz * t * 0.9 + vec2(uTime * 0.02, uTime * 0.006);
    float d = density(uv);
    // light: density a little further toward the sun
    vec2 toSun = normalize(sunDir.xz + vec2(0.0001)) * 0.12;
    float dS = density(uv + toSun);
    float lit = clamp(1.0 - (dS - d) * 2.2, 0.0, 1.0);
    vec3 cloudCol = mix(mix(vec3(0.62, 0.66, 0.74), vec3(0.22, 0.24, 0.30), uDark),
                        mix(vec3(1.0, 0.98, 0.95), vec3(0.78, 0.76, 0.74), uDark), lit);
    cloudCol += vec3(1.0, 0.9, 0.7) * pow(sunAmt, 6.0) * 0.25 * (1.0 - uDark * 0.5);
    float fade = exp(-t * 0.08);                 // thin out toward the horizon
    col = mix(sky, cloudCol, d * fade);
  }
  gl_FragColor = vec4(col, 1.0);
}`;

  function shader(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) { console.warn(gl.getShaderInfoLog(s)); return null; }
    return s;
  }
  const prog = gl.createProgram();
  const v = shader(gl.VERTEX_SHADER, vs), f = shader(gl.FRAGMENT_SHADER, fs);
  if (!v || !f) { canvas.style.display = 'none'; return; }
  gl.attachShader(prog, v); gl.attachShader(prog, f); gl.linkProgram(prog); gl.useProgram(prog);
  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, 'p');
  gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  const uRes = gl.getUniformLocation(prog, 'uRes'), uTime = gl.getUniformLocation(prog, 'uTime');
  const uSun = gl.getUniformLocation(prog, 'uSun'), uDark = gl.getUniformLocation(prog, 'uDark');

  let sun = { x: 0.55, y: 0.32 }, target = { x: 0.55, y: 0.32 };
  let dark = document.documentElement.dataset.theme !== 'light' ? 1 : 0, darkTarget = dark;
  window.addEventListener('mousemove', (e) => {
    target.x = (e.clientX / innerWidth - 0.5) * 1.6;
    target.y = 0.6 - (e.clientY / innerHeight) * 0.7;
  }, { passive: true });
  new MutationObserver(() => { darkTarget = document.documentElement.dataset.theme === 'light' ? 0 : 1; })
    .observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  darkTarget = document.documentElement.dataset.theme === 'light' ? 0 : 1;

  function resize() {
    const scale = Math.min(window.devicePixelRatio || 1, 1.5) * 0.5;   // half-res, like the real thing
    canvas.width = Math.max(320, Math.floor(innerWidth * scale));
    canvas.height = Math.max(200, Math.floor(innerHeight * scale));
    gl.viewport(0, 0, canvas.width, canvas.height);
  }
  window.addEventListener('resize', resize); resize();

  let visible = true;
  new IntersectionObserver((es) => { visible = es[0].isIntersecting; }).observe(document.querySelector('.hero'));

  const start = performance.now();
  let last = 0;
  function frame(now) {
    requestAnimationFrame(frame);
    if (!visible || document.hidden) return;
    if (now - last < 1000 / 30) return;           // 30 fps is plenty for clouds
    last = now;
    sun.x += (target.x - sun.x) * 0.04; sun.y += (target.y - sun.y) * 0.04;
    dark += (darkTarget - dark) * 0.08;
    gl.uniform2f(uRes, canvas.width, canvas.height);
    gl.uniform1f(uTime, reduced ? 0 : (now - start) / 1000);
    gl.uniform2f(uSun, sun.x, sun.y);
    gl.uniform1f(uDark, dark);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }
  requestAnimationFrame(frame);
})();
