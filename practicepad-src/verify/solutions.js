// JavaScript reference solutions, used only to verify the JS harnesses.
const SOL = {};

SOL.stack = String.raw`
function parse(s) { const i = s.indexOf(" "); return i < 0 ? [s, ""] : [s.slice(0, i), s.slice(i + 1)]; }
function step(st, op, arg) {
  if (op === "PUSH") st.push(arg);
  else if (op === "POP") { if (st.length) st.pop(); }
  else if (op === "PRINT") return st.length ? st[st.length - 1] : "";
  else if (op === "TRUNCATE") { if (st.length) { const t = st[st.length - 1]; st[st.length - 1] = t.slice(0, Math.max(0, t.length - Number(arg))); } }
  return null;
}
function nextPc(st, pc, op, arg) {
  if (op === "JUMP") return Number(arg);
  if (op === "JUMP_IF_EMPTY" && (!st.length || st[st.length - 1] === "")) return Number(arg);
  return pc + 1;
}
function runInterpreter(ins) {
  const st = [], out = []; let pc = 0;
  while (pc < ins.length) { const [op, arg] = parse(ins[pc]); const p = step(st, op, arg); if (p !== null) out.push(p); pc = nextPc(st, pc, op, arg); }
  return out;
}
function instrumentJumps(ins) {
  const start = []; let pos = 0;
  for (const s of ins) { start.push(pos); pos += parse(s)[0] === "JUMP" ? 4 : 1; }
  start.push(pos);
  const out = [];
  ins.forEach((s, i) => {
    const [op, arg] = parse(s);
    if (op === "JUMP") out.push("PUSH jump@" + i, "PRINT", "POP", "JUMP " + start[Number(arg)]);
    else if (op === "JUMP_IF_EMPTY") out.push("JUMP_IF_EMPTY " + start[Number(arg)]);
    else out.push(s);
  });
  return out;
}
function traceJumps(ins, limit) {
  const st = [], trace = [], seen = new Set(); let pc = 0, steps = 0;
  while (pc < ins.length) {
    const k = JSON.stringify([pc, st]);
    if (seen.has(k)) return trace.concat(["LOOP"]);
    seen.add(k);
    if (steps === limit) return trace.concat(["LIMIT"]);
    const [op, arg] = parse(ins[pc]);
    if (op === "JUMP") trace.push(String(pc));
    step(st, op, arg); pc = nextPc(st, pc, op, arg); steps++;
  }
  return trace;
}`;

SOL.accum = String.raw`
function runProgram(memory, instructions) {
  const mem = memory.slice();
  const prog = instructions.map((s) => { const [op, x] = s.split(" "); return [op, Number(x)]; });
  let acc = 0, pc = 0;
  while (pc < prog.length) {
    const [op, x] = prog[pc++];
    if (op === "LOAD") acc = mem[x]; else if (op === "STORE") mem[x] = acc;
    else if (op === "ADD") acc += x; else if (op === "SUB") acc -= x; else if (op === "MUL") acc *= x;
    else if (op === "LOADI") acc = mem[mem[x]]; else if (op === "STOREI") mem[mem[x]] = acc;
    else if (op === "JMP") pc = x; else if (op === "JZ") { if (acc === 0) pc = x; } else if (op === "JNEG") { if (acc < 0) pc = x; }
  }
  return mem;
}
function optimize(instructions) {
  let prog = instructions.slice();
  for (;;) { const n = deadStores(fold(prog)); if (JSON.stringify(n) === JSON.stringify(prog)) return n; prog = n; }
}
function fold(prog) {
  const out = []; let known = 0, same = new Set(), load = null, a = 1, b = 0;
  const emit = (op, x) => { out.push(op + " " + x); if (op !== "STORE") same = new Set(); };
  const affine = (a, b) => {
    if (a === 1 && b === 0) return;
    if (known !== null) { const t = a * known + b; if (t !== known) emit("ADD", t - known); known = t; }
    else if (a === 0) { emit("MUL", 0); if (b) emit("ADD", b); known = b; }
    else { if (a !== 1) emit("MUL", a); if (b) emit("ADD", b); }
  };
  const flush = () => {
    if (load !== null && a !== 0) { if (!same.has(load)) { emit("LOAD", load); same = new Set([load]); known = null; } affine(a, b); }
    else if (load !== null) affine(0, b);
    else affine(a, b);
    load = null; a = 1; b = 0;
  };
  for (const s of prog) {
    const [op, xs] = s.split(" "), x = Number(xs);
    if (op === "LOAD") { load = x; a = 1; b = 0; }
    else if (op === "ADD") b += x; else if (op === "SUB") b -= x;
    else if (op === "MUL") { a *= x; b *= x; }
    else if (op === "STORE") { flush(); if (!same.has(x)) { out.push("STORE " + x); same.add(x); } }
  }
  return out;
}
function deadStores(prog) {
  const keep = [], over = new Set();
  for (let i = prog.length - 1; i >= 0; i--) {
    const [op, xs] = prog[i].split(" "), x = Number(xs);
    if (op === "STORE") { if (over.has(x)) continue; over.add(x); }
    else if (op === "LOAD") over.delete(x);
    keep.push(prog[i]);
  }
  keep.reverse();
  while (keep.length && keep[keep.length - 1].split(" ")[0] !== "STORE") keep.pop();
  return keep;
}`;

SOL.fold = String.raw`
function codeEditorOperations(lines, operations) {
  const match = new Map(), st = [];
  lines.forEach((l, i) => { const t = l.replace(/[ \t]+$/, ""); if (t.endsWith("{")) st.push(i); else if (t.endsWith("}")) match.set(st.pop(), i); });
  const folded = new Set();
  const view = () => {
    const rows = []; let i = 0;
    while (i < lines.length) {
      if (folded.has(i)) { const l = lines[i]; rows.push([i, l.slice(0, l.lastIndexOf("{") + 1) + " ... }"]); i = match.get(i) + 1; }
      else { rows.push([i, lines[i]]); i++; }
    }
    return rows;
  };
  const tog = (i) => { if (folded.has(i)) folded.delete(i); else folded.add(i); };
  return operations.map((op) => {
    const [name, ...args] = op.split(" ");
    if (name === "MATCH") return [...match.entries()].sort((x, y) => x[0] - y[0]).map(([o, c]) => o + ":" + c);
    if (name === "TOGGLE") { tog(Number(args[0])); return []; }
    if (name === "GET") return view().map((r) => r[1]);
    if (name === "TOGGLE_LINE") { tog(view()[Number(args[0])][0]); return []; }
    if (name === "GET_RANGE") return view().slice(Number(args[0]), Number(args[1])).map((r) => r[1]);
    return [];
  });
}`;

SOL.towers = String.raw`
const ACTIONS = ["BUY", "LOAD", "MOVE_FAR", "MOVE_NEAR", "OBSERVE"];
const fresh = () => ({ near: 5, far: 0, dollies: 0, bricks: 0, transit: 0, locked: false });
function turn(t, a) {
  const n = { ...t };
  if (t.locked) { n.far += n.transit; n.transit = 0; n.locked = false; return n; }
  if (a === "BUY") n.dollies++;
  else if (a === "LOAD") n.bricks += n.dollies;
  else if (a === "MOVE_NEAR") { n.near += n.bricks; n.bricks = 0; }
  else if (a === "MOVE_FAR") { n.transit = n.bricks; n.bricks = 0; n.locked = true; }
  return n;
}
const beats = (a, b) => a.near > b.far && a.far > b.near;
const keyOf = (w, e) => JSON.stringify([w, e]);
function simulateTowers(west, east) {
  let w = fresh(), e = fresh();
  for (let d = 0; d < west.length; d++) {
    w = turn(w, west[d]); if (beats(w, e)) return d;
    e = turn(e, east[d]); if (beats(w, e)) return d;
  }
  return -1;
}
function findWinningTowerStrategy(east, limit) {
  let layer = [[fresh(), fresh(), []]];
  for (let d = 0; d < limit; d++) {
    const nxt = [], seen = new Set();
    for (const [w, e, path] of layer) {
      for (const a of (w.locked ? ["WAIT"] : ACTIONS)) {
        const w2 = turn(w, a); if (beats(w2, e)) return path.concat([a]);
        const e2 = turn(e, east[d]); if (beats(w2, e2)) return path.concat([a]);
        const k = keyOf(w2, e2); if (!seen.has(k)) { seen.add(k); nxt.push([w2, e2, path.concat([a])]); }
      }
    }
    layer = nxt;
  }
  return [];
}
function countFastestWins(east, limit) {
  let layer = new Map([[keyOf(fresh(), fresh()), [fresh(), fresh(), 1]]]);
  for (let d = 0; d < limit; d++) {
    const nxt = new Map(); let wins = 0;
    for (const [w, e, ways] of layer.values()) {
      for (const a of (w.locked ? ["WAIT"] : ACTIONS)) {
        const w2 = turn(w, a), e2 = turn(e, east[d]);
        if (beats(w2, e) || beats(w2, e2)) wins += ways;
        else { const k = keyOf(w2, e2); const cur = nxt.get(k); if (cur) cur[2] += ways; else nxt.set(k, [w2, e2, ways]); }
      }
    }
    if (wins) return wins;
    layer = nxt;
  }
  return 0;
}`;

SOL.wizard = String.raw`
function maxMonsters(costs) { return maxMonstersAndCost(costs)[0]; }
function maxMonstersAndCost(costs) {
  const heap = []; let spent = 0;
  const push = (v) => { heap.push(v); let i = heap.length - 1; while (i > 0) { const p = (i - 1) >> 1; if (heap[p] >= heap[i]) break; [heap[p], heap[i]] = [heap[i], heap[p]]; i = p; } };
  const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let i = 0; for (;;) { const l = 2 * i + 1, r = l + 1; let m = i; if (l < heap.length && heap[l] > heap[m]) m = l; if (r < heap.length && heap[r] > heap[m]) m = r; if (m === i) break; [heap[m], heap[i]] = [heap[i], heap[m]]; i = m; } } return top; };
  costs.forEach((c, d) => { push(c); spent += c; if (spent > 10 * (d + 1)) spent -= pop(); });
  return [heap.length, spent];
}
function chooseMonsterDays(costs) {
  const n = costs.length; let best = null;
  for (let mask = 0; mask < (1 << n); mask++) {
    let spent = 0, ok = true; const days = [];
    for (let d = 0; d < n; d++) { if (mask >> d & 1) { spent += costs[d]; days.push(d); } if (spent > 10 * (d + 1)) { ok = false; break; } }
    if (!ok) continue;
    const better = !best || days.length > best.days.length || (days.length === best.days.length && (spent < best.spent || (spent === best.spent && less(days, best.days))));
    if (better) best = { days, spent };
  }
  return best.days;
}
function less(a, b) { for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) return a[i] < b[i]; return a.length < b.length; }`;

SOL.loadout = String.raw`
function mitigatedRuns(protections, runs, selected) {
  const cov = new Set(); for (const i of selected) for (const h of protections[i]) cov.add(h);
  return runs.filter((r) => r.every((h) => cov.has(h))).length;
}
function masks(protections, runs) {
  const hz = [...new Set(runs.flat())].sort(); const bit = new Map(hz.map((h, i) => [h, 1 << i]));
  const item = protections.map((p) => p.reduce((m, h) => m | (bit.get(h) || 0), 0));
  const run = runs.map((r) => r.reduce((m, h) => m | bit.get(h), 0));
  return { hz, item, run };
}
function optimizeLoadout(capacity, names, weights, protections, runs) {
  const { item, run } = masks(protections, runs); const n = names.length; let best = null;
  for (let s = 0; s < (1 << n); s++) {
    let w = 0, cov = 0;
    for (let i = 0; i < n; i++) if (s >> i & 1) { w += weights[i]; cov |= item[i]; }
    if (w > capacity) continue;
    const score = run.filter((m) => (m & cov) === m).length;
    if (best && (score < best.score || (score === best.score && w > best.w))) continue;
    const chosen = names.filter((_, i) => s >> i & 1).sort();
    if (!best || score > best.score || w < best.w || cmp(chosen, best.chosen) < 0) best = { score, w, chosen };
  }
  return best.chosen;
}
function cmp(a, b) { for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1; return a.length - b.length; }
function bestLoadoutScore(capacity, weights, protections, runs) {
  const { hz, item, run } = masks(protections, runs); const full = 1 << hz.length;
  const exact = new Array(full).fill(Infinity); exact[0] = 0;
  item.forEach((m, i) => { for (let s = full - 1; s >= 0; s--) if (exact[s] + weights[i] < exact[s | m]) exact[s | m] = exact[s] + weights[i]; });
  const cheap = exact.slice();
  for (let b = 0; b < hz.length; b++) for (let s = 0; s < full; s++) if (!(s >> b & 1) && cheap[s | (1 << b)] < cheap[s]) cheap[s] = cheap[s | (1 << b)];
  let best = [0, 0];
  for (let c = 0; c < (1 << run.length); c++) {
    let need = 0; run.forEach((m, r) => { if (c >> r & 1) need |= m; });
    const w = cheap[need]; if (w > capacity) continue;
    const score = run.filter((m) => (m & need) === m).length;
    if (score > best[0] || (score === best[0] && w < best[1])) best = [score, w];
  }
  return best;
}`;

SOL.dice = String.raw`
const gcd = (a, b) => { a = a < 0n ? -a : a; b = b < 0n ? -b : b; while (b) [a, b] = [b, a % b]; return a; };
function frac(n, d) { if (d < 0n) { n = -n; d = -d; } const g = gcd(n, d) || 1n; return (n / g) + "/" + (d / g); }
function modifiedDiceExpectations(dice, counts) {
  const sums = dice.map((f) => f.reduce((s, x) => s + BigInt(x), 0n));
  let total = 0n; sums.forEach((s, i) => { total += BigInt(counts[i]) * s; });
  return sums.map((s) => frac(s, 6n)).concat([frac(total - 2100n, 6n)]);
}
function netPayoutVariance(dice, counts) {
  let num = 0n;
  dice.forEach((f, i) => { const s = f.reduce((a, x) => a + BigInt(x), 0n), q = f.reduce((a, x) => a + BigInt(x) * BigInt(x), 0n); num += BigInt(counts[i]) * (6n * q - s * s); });
  return frac(num, 36n);
}
function probabilityNetPositive(dice, counts) {
  let ways = new Map([[0, 1n]]); let rolls = 0;
  dice.forEach((faces, i) => {
    for (let k = 0; k < counts[i]; k++) {
      const nxt = new Map(); rolls++;
      for (const [s, w] of ways) for (const f of faces) nxt.set(s + f, (nxt.get(s + f) || 0n) + w);
      ways = nxt;
    }
  });
  let win = 0n; for (const [s, w] of ways) if (s > 350) win += w;
  return frac(win, 6n ** BigInt(rolls));
}`;

if (typeof module !== "undefined") module.exports = SOL;
