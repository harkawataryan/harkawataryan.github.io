"""Build practicepad/index.html from problems.py, refs.py, the Watchlist
assets and template.html.

    python3 build.py
"""
import base64
import html
import json
import re
from pathlib import Path

import problems
from problems import materialize

HERE = Path(__file__).parent
OUT = HERE.parent / "practicepad" / "index.html"
LEGACY = json.loads((HERE / "_legacy_watchlist.json").read_text())

# ---------------------------------------------------------------------
# names and types
# ---------------------------------------------------------------------
def camel(s):
    head, *rest = s.split("_")
    return head + "".join(w[:1].upper() + w[1:] for w in rest)


PY_T = {"int": "int", "int[]": "list[int]", "String[]": "list[str]", "String[][]": "list[list[str]]",
        "int[][]": "list[list[int]]", "String": "str"}
JS_T = {"int": "number", "int[]": "number[]", "String[]": "string[]", "String[][]": "string[][]",
        "int[][]": "number[][]", "String": "string"}

DOCS = {
    ("stack", "run"): "Part 1. Return the strings PRINT produced, in order.",
    ("stack", "instrument"): "Part 2. Return the instrumented program.",
    ("stack", "trace"): 'Part 3. Executed JUMP indices as strings, then "LOOP" or "LIMIT" if it stopped early.',
    ("accum", "run"): "Part 1 (extended in Part 2). Return the final memory.",
    ("accum", "opt"): "Part 3. Return a shorter program with the same final memory.",
    ("fold", "ops"): "Parts 1-3. One output row per operation.",
    ("towers", "sim"): "Part 1. 0-based day West wins on, or -1.",
    ("towers", "win"): "Part 2. Fastest winning West schedule, lexicographically smallest; [] if none.",
    ("towers", "count"): "Part 3. Number of distinct fastest winning schedules (0 if none).",
    ("wizard", "max"): "Part 1. Maximum number of monsters defeated.",
    ("wizard", "days"): "Part 2. Days to fight: max count, then min spend, then lexicographically smallest.",
    ("wizard", "big"): "Part 3. [max count, min spend for that count]. n up to 200,000.",
    ("loadout", "score"): "Part 1. Number of fully mitigated runs.",
    ("loadout", "opt"): "Part 2. Sorted names of the best loadout.",
    ("loadout", "big"): "Part 3. [max mitigated runs, min weight]. Up to 60 items.",
    ("dice", "ev"): 'Part 1. Ten expected face values, then expected net payout, as "num/den".',
    ("dice", "var"): 'Part 2. Variance of the net payout, as "num/den".',
    ("dice", "prob"): 'Part 3. P(net payout > 0), exact, as "num/den".',
}


def signature(fn, lang):
    if lang == "python":
        ps = ", ".join(f"{n}: {PY_T[t]}" for n, t in fn["params"])
        return f'{fn["py"]}({ps}) -> {PY_T[fn["ret"]]}'
    if lang == "javascript":
        ps = ", ".join(f"{camel(n)}: {JS_T[t]}" for n, t in fn["params"])
        return f'{fn["js"]}({ps}) → {JS_T[fn["ret"]]}'
    ps = ", ".join(f"{t} {camel(n)}" for n, t in fn["params"])
    return f'static {fn["ret"]} {fn["js"]}({ps})'


# ---------------------------------------------------------------------
# starters
# ---------------------------------------------------------------------
def starter(P, lang):
    title = P["title"]
    if lang == "python":
        out = [f"# {title} (Jane Street R1 practice)",
               "# Ctrl/Cmd + Enter runs the tests for every part you've unlocked.", ""]
        for fn in P["functions"]:
            ps = ", ".join(n for n, _ in fn["params"])
            out += ["", f'def {fn["py"]}({ps}):', f'    """{DOCS[(P["id"], fn["key"])]}"""',
                    "    raise NotImplementedError", ""]
        return "\n".join(out)
    if lang == "javascript":
        out = [f"// {title} (Jane Street R1 practice)",
               "// Ctrl/Cmd + Enter runs the tests for every part you've unlocked.", ""]
        for fn in P["functions"]:
            ps = ", ".join(camel(n) for n, _ in fn["params"])
            out += [f'/** {DOCS[(P["id"], fn["key"])]} */', f'function {fn["js"]}({ps}) {{',
                    '  throw new Error("TODO");', "}", ""]
        return "\n".join(out)
    out = [f"// {title} (Jane Street R1 practice)",
           "// Runs in your browser on a real Java 21 JDK. The first Run downloads the JDK,",
           "// so give it 20-40 seconds; later runs are quick.",
           "import java.util.*;", "", "public class Solution {", ""]
    for fn in P["functions"]:
        ps = ", ".join(f"{t} {camel(n)}" for n, t in fn["params"])
        out += [f'    /** {DOCS[(P["id"], fn["key"])]} */', f'    static {fn["ret"]} {fn["js"]}({ps}) {{',
                '        throw new UnsupportedOperationException("TODO");', "    }", ""]
    out.append("}")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------------
# harness pieces
# ---------------------------------------------------------------------
def describe(a):
    if isinstance(a, dict) and "gen" in a:
        return f"<{a['n']} generated values>"
    s = json.dumps(a)
    return s if len(s) <= 300 else s[:300] + "…"


def input_preview(name, args):
    s = f"{name}({', '.join(describe(a) for a in args)})"
    return s if len(s) <= 500 else s[:500] + "…"


def expect_json(x):
    return json.dumps(x, separators=(",", ":"), ensure_ascii=True)


PY_HARNESS = r'''
def __run_tests__(ns, max_part):
    import base64, copy, json, traceback
    TESTS = json.loads(base64.b64decode("__B64__").decode("utf-8"))
    NAMES = __NAMES__
    RS = "\x1e"

    def lcg(seed):
        s = seed
        while True:
            s = s * 48271 % 2147483647
            yield s

    def gen(a):
        if isinstance(a, dict) and a.get("gen") == "ints":
            r = lcg(a["seed"])
            return [a["lo"] + next(r) % (a["hi"] - a["lo"] + 1) for _ in range(a["n"])]
        if isinstance(a, dict) and a.get("gen") == "hazards":
            r = lcg(a["seed"])
            out = []
            for _ in range(a["n"]):
                k = 1 + next(r) % a["maxk"]
                picks = []
                for _ in range(k):
                    h = a["hazards"][next(r) % len(a["hazards"])]
                    if h not in picks:
                        picks.append(h)
                out.append(picks)
            return out
        return a

    def norm(x):
        if isinstance(x, (list, tuple)):
            return [norm(v) for v in x]
        return x

    def show(x):
        try:
            s = json.dumps(norm(x))
        except Exception:
            s = repr(x)
        return s if len(s) <= 400 else s[:400] + "…"

    def run_ref(mem, prog):
        mem, acc = list(mem), 0
        for s in prog:
            op, x = s.split(" ")
            x = int(x)
            if op == "LOAD": acc = mem[x]
            elif op == "STORE": mem[x] = acc
            elif op == "ADD": acc += x
            elif op == "SUB": acc -= x
            elif op == "MUL": acc *= x
        return mem

    def check_opt(t, got, inp):
        prog, n = t["args"][0], t["memLen"]
        if not isinstance(got, (list, tuple)):
            raise AssertionError(f"input    {inp}\nexpected a list of instructions\ngot      {show(got)}")
        for s in got:
            parts = s.split(" ") if isinstance(s, str) else []
            ok = len(parts) == 2 and parts[0] in ("LOAD", "STORE", "ADD", "SUB", "MUL")
            if ok:
                try:
                    v = int(parts[1])
                    ok = parts[0] not in ("LOAD", "STORE") or 0 <= v < n
                except ValueError:
                    ok = False
            if not ok:
                raise AssertionError(f"input    {inp}\ninvalid instruction in output: {show(s)}")
        r = lcg(9001)
        for _ in range(25):
            mem = [-50 + next(r) % 101 for _ in range(n)]
            want, have = run_ref(mem, prog), run_ref(mem, got)
            if want != have:
                raise AssertionError(f"input    {inp}\nyour output {show(got)}\nis not equivalent: from memory {mem}\nthe input gives {want}, yours gives {have}")
        if len(got) > t["expect"]:
            raise AssertionError(f"input    {inp}\nequivalent, but {len(got)} instructions; target is {t['expect']} or fewer\ngot      {show(got)}")

    def where(e):
        frames = [f for f in traceback.extract_tb(e.__traceback__) if f.filename == "solution.py"]
        return f" (line {frames[-1].lineno})" if frames else ""

    for t in TESTS:
        if t["part"] > max_part:
            continue
        label = f"{t['part']}|{t['name']}"
        print("START|" + label, flush=True)
        name = NAMES[t["fn"]]
        inp = t["input"]
        try:
            f = ns.get(name)
            if not callable(f):
                raise NameError(f"{name} is not defined")
            args = [gen(copy.deepcopy(a)) for a in t["args"]]
            got = f(*args)
            if t["check"] == "opt":
                check_opt(t, got, inp)
            elif norm(got) != t["expect"]:
                raise AssertionError(f"input    {inp}\nexpected {show(t['expect'])}\ngot      {show(got)}")
            print("PASS|" + label, flush=True)
        except AssertionError as e:
            print(("FAIL|" + label + "|" + str(e)).replace("\n", RS), flush=True)
        except NotImplementedError:
            print("FAIL|" + label + "|NotImplementedError: not written yet", flush=True)
        except BaseException as e:
            msg = f"{type(e).__name__}: {e}{where(e)}" + RS + "input    " + inp
            print(("FAIL|" + label + "|" + msg).replace("\n", RS), flush=True)
'''

JS_HARNESS = r'''
;(function () {
  const TESTS = __TESTS__;
  const NAMES = __NAMES__;
  const FNS = { __FNS__ };
  const RS = "\x1e";
  class Fail extends Error {}
  function lcg(seed) { let s = seed; return () => (s = (s * 48271) % 2147483647); }
  function gen(a) {
    if (a && a.gen === "ints") { const r = lcg(a.seed); return Array.from({ length: a.n }, () => a.lo + (r() % (a.hi - a.lo + 1))); }
    if (a && a.gen === "hazards") {
      const r = lcg(a.seed), out = [];
      for (let i = 0; i < a.n; i++) {
        const k = 1 + (r() % a.maxk), picks = [];
        for (let j = 0; j < k; j++) { const h = a.hazards[r() % a.hazards.length]; if (!picks.includes(h)) picks.push(h); }
        out.push(picks);
      }
      return out;
    }
    return a;
  }
  function norm(x) { return (Array.isArray(x) || ArrayBuffer.isView(x)) ? Array.from(x, norm) : x; }
  function show(x) {
    let s;
    try { s = JSON.stringify(norm(x), (k, v) => (typeof v === "bigint" ? v.toString() + "n" : v)); } catch (e) { s = String(x); }
    if (s === undefined) s = String(x);
    return s.length > 400 ? s.slice(0, 400) + "…" : s;
  }
  function runRef(mem0, prog) {
    const mem = mem0.slice(); let acc = 0;
    for (const s of prog) {
      const [op, xs] = s.split(" "), x = Number(xs);
      if (op === "LOAD") acc = mem[x]; else if (op === "STORE") mem[x] = acc;
      else if (op === "ADD") acc += x; else if (op === "SUB") acc -= x; else if (op === "MUL") acc *= x;
    }
    return mem;
  }
  function checkOpt(t, got, inp) {
    const prog = t.args[0], n = t.memLen;
    if (!Array.isArray(got)) throw new Fail("input    " + inp + "\nexpected an array of instructions\ngot      " + show(got));
    for (const s of got) {
      const parts = typeof s === "string" ? s.split(" ") : [];
      let ok = parts.length === 2 && ["LOAD", "STORE", "ADD", "SUB", "MUL"].includes(parts[0]) && /^-?\d+$/.test(parts[1]);
      if (ok && (parts[0] === "LOAD" || parts[0] === "STORE")) { const v = Number(parts[1]); ok = v >= 0 && v < n; }
      if (!ok) throw new Fail("input    " + inp + "\ninvalid instruction in output: " + show(s));
    }
    const r = lcg(9001);
    for (let k = 0; k < 25; k++) {
      const mem = Array.from({ length: n }, () => -50 + (r() % 101));
      const want = runRef(mem, prog), have = runRef(mem, got);
      if (JSON.stringify(want) !== JSON.stringify(have))
        throw new Fail("input    " + inp + "\nyour output " + show(got) + "\nis not equivalent: from memory " + JSON.stringify(mem) + "\nthe input gives " + JSON.stringify(want) + ", yours gives " + JSON.stringify(have));
    }
    if (got.length > t.expect) throw new Fail("input    " + inp + "\nequivalent, but " + got.length + " instructions; target is " + t.expect + " or fewer\ngot      " + show(got));
  }
  function where(e) {
    const m = e && e.stack && /<anonymous>:(\d+):(\d+)/.exec(e.stack);
    if (!m) return "";
    const line = Number(m[1]) - 2;
    return line >= 1 && line <= __USER_LINES__ ? " (line " + line + ")" : "";
  }
  for (const t of TESTS) {
    if (t.part > __MAX_PART__) continue;
    const label = t.part + "|" + t.name;
    console.log("START|" + label);
    try {
      const f = FNS[t.fn];
      if (typeof f !== "function") throw new Error(NAMES[t.fn] + " is not defined");
      const args = t.args.map((a) => gen(JSON.parse(JSON.stringify(a))));
      const got = f(...args);
      if (t.check === "opt") checkOpt(t, got, t.input);
      else if (JSON.stringify(norm(got)) !== JSON.stringify(t.expect))
        throw new Fail("input    " + t.input + "\nexpected " + show(t.expect) + "\ngot      " + show(got));
      console.log("PASS|" + label);
    } catch (e) {
      const msg = e instanceof Fail ? e.message
        : (e && e.name && e.name !== "Error" ? e.name + ": " : "") + ((e && e.message) || String(e)) + where(e) + "\ninput    " + t.input;
      console.log(("FAIL|" + label + "|" + msg).replace(/\n/g, RS));
    }
  }
})();
'''

JAVA_HEAD = r'''import java.util.*;

public class SolutionTests {
    static final String RS = "\u001e";
    static final class Fail extends RuntimeException { Fail(String m) { super(m); } }
    interface Body { void run() throws Exception; }

    static String j(Object o) { StringBuilder sb = new StringBuilder(); j(o, sb); return sb.toString(); }
    static void j(Object o, StringBuilder sb) {
        if (o == null) { sb.append("null"); return; }
        if (o instanceof String) { str((String) o, sb); return; }
        if (o instanceof int[]) { int[] a = (int[]) o; sb.append('['); for (int i = 0; i < a.length; i++) { if (i > 0) sb.append(','); sb.append(a[i]); } sb.append(']'); return; }
        if (o instanceof long[]) { long[] a = (long[]) o; sb.append('['); for (int i = 0; i < a.length; i++) { if (i > 0) sb.append(','); sb.append(a[i]); } sb.append(']'); return; }
        if (o instanceof Object[]) { Object[] a = (Object[]) o; sb.append('['); for (int i = 0; i < a.length; i++) { if (i > 0) sb.append(','); j(a[i], sb); } sb.append(']'); return; }
        if (o instanceof Collection) { boolean first = true; sb.append('['); for (Object x : (Collection<?>) o) { if (!first) sb.append(','); first = false; j(x, sb); } sb.append(']'); return; }
        sb.append(String.valueOf(o));
    }
    static void str(String s, StringBuilder sb) {
        sb.append('"');
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"': sb.append("\\\""); break;
                case '\\': sb.append("\\\\"); break;
                case '\n': sb.append("\\n"); break;
                case '\r': sb.append("\\r"); break;
                case '\t': sb.append("\\t"); break;
                case '\b': sb.append("\\b"); break;
                case '\f': sb.append("\\f"); break;
                default:
                    if (c < 0x20 || c > 0x7e) sb.append(String.format("\\u%04x", (int) c)); else sb.append(c);
            }
        }
        sb.append('"');
    }
    static String clip(String s) { return s.length() > 400 ? s.substring(0, 400) + "…" : s; }
    static void eq(Object got, String expected, String input) {
        String g = j(got);
        if (!g.equals(expected)) throw new Fail("input    " + input + "\nexpected " + clip(expected) + "\ngot      " + clip(g));
    }
    static long[] seed = new long[1];
    static long next(long[] s) { s[0] = s[0] * 48271 % 2147483647L; return s[0]; }
    static int[] ints(int n, long sd, int lo, int hi) {
        long[] s = {sd}; int[] a = new int[n];
        for (int i = 0; i < n; i++) a[i] = (int) (lo + next(s) % (hi - lo + 1));
        return a;
    }
    static String[][] hazards(int n, long sd, String[] hz, int maxk) {
        long[] s = {sd}; String[][] out = new String[n][];
        for (int i = 0; i < n; i++) {
            int k = (int) (1 + next(s) % maxk);
            List<String> picks = new ArrayList<>();
            for (int t = 0; t < k; t++) { String h = hz[(int) (next(s) % hz.length)]; if (!picks.contains(h)) picks.add(h); }
            out[i] = picks.toArray(new String[0]);
        }
        return out;
    }
    static int[] runRef(int[] mem0, String[] prog) {
        int[] mem = mem0.clone(); long acc = 0;
        for (String s : prog) {
            String[] p = s.split(" "); int x = Integer.parseInt(p[1]);
            switch (p[0]) {
                case "LOAD": acc = mem[x]; break;
                case "STORE": mem[x] = (int) acc; break;
                case "ADD": acc += x; break;
                case "SUB": acc -= x; break;
                case "MUL": acc *= x; break;
            }
        }
        return mem;
    }
    static void checkOpt(String[] prog, String[] got, int n, int target, String input) {
        if (got == null) throw new Fail("input    " + input + "\nexpected an array of instructions\ngot      null");
        for (String s : got) {
            String[] p = s == null ? new String[0] : s.split(" ", -1);
            boolean ok = p.length == 2 && Arrays.asList("LOAD", "STORE", "ADD", "SUB", "MUL").contains(p[0]) && p[1].matches("-?\\d+");
            if (ok && (p[0].equals("LOAD") || p[0].equals("STORE"))) { long v = Long.parseLong(p[1]); ok = v >= 0 && v < n; }
            if (!ok) throw new Fail("input    " + input + "\ninvalid instruction in output: " + j(s));
        }
        long[] r = {9001};
        for (int k = 0; k < 25; k++) {
            int[] mem = new int[n];
            for (int i = 0; i < n; i++) mem[i] = (int) (-50 + next(r) % 101);
            int[] want = runRef(mem, prog), have = runRef(mem, got);
            if (!Arrays.equals(want, have))
                throw new Fail("input    " + input + "\nyour output " + clip(j(got)) + "\nis not equivalent: from memory " + j(mem) + "\nthe input gives " + j(want) + ", yours gives " + j(have));
        }
        if (got.length > target) throw new Fail("input    " + input + "\nequivalent, but " + got.length + " instructions; target is " + target + " or fewer\ngot      " + clip(j(got)));
    }
    static String where(Throwable e) {
        for (StackTraceElement el : e.getStackTrace())
            if (el.getClassName().startsWith("Solution") && !el.getClassName().startsWith("SolutionTests"))
                return " (Solution.java line " + el.getLineNumber() + ")";
        return "";
    }
    static void run(int part, String name, String input, Body b, int max) {
        if (part > max) return;
        String label = part + "|" + name;
        System.out.println("START|" + label);
        try {
            b.run();
            System.out.println("PASS|" + label);
        } catch (Fail f) {
            System.out.println(("FAIL|" + label + "|" + f.getMessage()).replace("\n", RS));
        } catch (Throwable e) {
            String msg = e.getClass().getSimpleName() + (e.getMessage() == null ? "" : ": " + e.getMessage()) + where(e) + "\ninput    " + input;
            System.out.println(("FAIL|" + label + "|" + msg).replace("\n", RS));
        }
        System.out.flush();
    }
'''


def java_str(s):
    out = ['"']
    for c in s:
        o = ord(c)
        if c == "\\": out.append("\\\\")
        elif c == '"': out.append('\\"')
        elif c == "\n": out.append("\\n")
        elif c == "\t": out.append("\\t")
        elif c == "\r": out.append("\\r")
        elif o < 0x20: out.append("\\%03o" % o)
        elif o > 0x7e: out.append("\\u%04x" % o)
        else: out.append(c)
    out.append('"')
    return "".join(out)


def java_lit(v, t):
    if isinstance(v, dict) and v.get("gen") == "ints":
        return f'ints({v["n"]}, {v["seed"]}L, {v["lo"]}, {v["hi"]})'
    if isinstance(v, dict) and v.get("gen") == "hazards":
        hz = ", ".join(java_str(h) for h in v["hazards"])
        return f'hazards({v["n"]}, {v["seed"]}L, new String[]{{{hz}}}, {v["maxk"]})'
    if t == "int":
        return str(v)
    if t == "String":
        return java_str(v)
    if t == "int[]":
        return "new int[]{" + ", ".join(str(x) for x in v) + "}"
    if t == "String[]":
        return "new String[]{" + ", ".join(java_str(x) for x in v) + "}"
    if t == "int[][]":
        return "new int[][]{" + ", ".join("{" + ", ".join(str(x) for x in row) + "}" for row in v) + "}"
    if t == "String[][]":
        return "new String[][]{" + ", ".join("{" + ", ".join(java_str(x) for x in row) + "}" for row in v) + "}"
    raise ValueError(t)


def harnesses(P):
    fns = {f["key"]: f for f in P["functions"]}
    tests_out = []
    for t in P["tests"]:
        fn = fns[t["fn"]]
        d = {k: t[k] for k in ("part", "name", "fn", "args", "expect", "check")}
        if "memLen" in t:
            d["memLen"] = t["memLen"]
        tests_out.append(d)

    # Python
    py_tests = []
    for d in tests_out:
        e = dict(d)
        e["input"] = input_preview(fns[d["fn"]]["py"], d["args"])
        py_tests.append(e)
    b64 = base64.b64encode(json.dumps(py_tests).encode()).decode()
    py = PY_HARNESS.replace("__B64__", b64).replace("__NAMES__", repr({k: f["py"] for k, f in fns.items()}))

    # JavaScript
    js_tests = []
    for d in tests_out:
        e = dict(d)
        e["input"] = input_preview(fns[d["fn"]]["js"], d["args"])
        js_tests.append(e)
    fn_lookup = ", ".join(f'{k}: (typeof {f["js"]} === "function" ? {f["js"]} : undefined)' for k, f in fns.items())
    js = (JS_HARNESS.replace("__TESTS__", json.dumps(js_tests)).replace("__NAMES__", json.dumps({k: f["js"] for k, f in fns.items()}))
          .replace("__FNS__", fn_lookup))

    # Java
    body, calls = [], []
    for i, d in enumerate(tests_out):
        fn = fns[d["fn"]]
        lits = [java_lit(a, t) for a, (_, t) in zip(d["args"], fn["params"])]
        inp = input_preview(fn["js"], d["args"])
        call = f'Solution.{fn["js"]}({", ".join(lits)})'
        if d["check"] == "opt":
            body.append(f'    static void t{i}() throws Exception {{\n        String[] prog = {lits[0]};\n'
                        f'        checkOpt(prog, Solution.{fn["js"]}(prog.clone()), {d["memLen"]}, {d["expect"]}, {java_str(inp)});\n    }}')
        else:
            body.append(f'    static void t{i}() throws Exception {{\n        {fn["ret"]} got = {call};\n'
                        f'        eq(got, {java_str(expect_json(d["expect"]))}, {java_str(inp)});\n    }}')
        calls.append(f'        run({d["part"]}, {java_str(d["name"])}, {java_str(inp)}, SolutionTests::t{i}, max);')
    java = (JAVA_HEAD + "\n" + "\n".join(body) + "\n\n    public static void main(String[] args) {\n"
            "        int max = Integer.parseInt(args[0]);\n" + "\n".join(calls) + "\n    }\n}\n")
    return {"python": py, "javascript": js, "java": java}


# ---------------------------------------------------------------------
# solution code blocks from refs.py
# ---------------------------------------------------------------------
REFS = (HERE / "refs.py").read_text()


def solution_code(pid):
    m = re.search(r"# SOLUTION %s\n([\s\S]*?)# END SOLUTION" % pid, REFS)
    code = m.group(1).rstrip() + "\n"
    if pid in ("wizard",):
        code = "import heapq\n\n\n" + code
    if pid == "dice":
        code = "from fractions import Fraction\n\n\n" + code
    return code


def esc(s):
    return html.escape(s, quote=False)


# ---------------------------------------------------------------------
# Watchlist (legacy assets, reshaped)
# ---------------------------------------------------------------------
def js_pairs(text):
    """Parse the legacy JS arrays-of-string-arrays into Python lists."""
    t = re.sub(r",\s*$", "", text.strip())
    return json.loads("[" + t + "]")


def watchlist():
    A = LEGACY
    tabq = A["tabq"]

    def part_body(n):
        m = re.search(r'<div class="part[^"]*" id="part%d">([\s\S]*?)\n        </div>\n' % n, tabq)
        body = m.group(1)
        body = re.sub(r'\s*<div class="ph">.*?</div>', "", body, count=1)
        body = re.sub(r'\s*<div class="lockmsg"[\s\S]*?</div>', "", body, count=1)
        body = re.sub(r'<div class="body hid">([\s\S]*)</div>\s*$', r"\1", body.strip())
        return body.strip()

    api1, api3 = {}, {}
    for src, dst in ((A["API1"], api1), (A["API3"], api3)):
        for lang in ("python", "javascript", "java"):
            m = re.search(r"%s: `([\s\S]*?)`" % lang, src)
            dst[lang] = m.group(1)
    p1 = part_body(1).replace('<div class="api" id="api1"></div>', "{api}")
    p3 = part_body(3).replace('<div class="api" id="api3"></div>', "{api}")
    intro = re.search(r'(<div class="quote">[\s\S]*?</div>)', tabq).group(1)
    tree = re.search(r'(<h3>The sample tree the tests use</h3>\s*<pre class="treebox">[\s\S]*?</pre>)', tabq).group(1)

    sol_js = A["solutionHTML_js"]
    sol = re.search(r"return `([\s\S]*)`;", sol_js).group(1)
    sol = sol.replace("<pre><code>${code}</code></pre>", '<pre><code class="lang-python">' + esc(A["solution-python"]) + "</code></pre>")

    def fix_fail_newlines(code, lang):
        if lang == "python":
            return code.replace('print(f"FAIL|{part}|{name}|{msg}")', 'print(f"FAIL|{part}|{name}|{msg}".replace("\\n", "\\x1e"))')
        if lang == "javascript":
            return code.replace('console.log("FAIL|" + part + "|" + name + "|" + nm + ((e && e.message) || e));',
                                'console.log(("FAIL|" + part + "|" + name + "|" + nm + ((e && e.message) || e)).replace(/\\n/g, "\\x1e"));')
        return (code.replace('System.out.println("FAIL|" + e.getKey() + "|" + ex.getMessage());',
                             'System.out.println(("FAIL|" + e.getKey() + "|" + ex.getMessage()).replace("\\n", "\\u001e"));')
                .replace('System.out.println("FAIL|" + e.getKey() + "|" + ex.getClass().getSimpleName() + ": " + ex.getMessage());',
                         'System.out.println(("FAIL|" + e.getKey() + "|" + ex.getClass().getSimpleName() + ": " + ex.getMessage()).replace("\\n", "\\u001e"));'))

    harness = {lang: fix_fail_newlines(A["harness-" + lang], lang) for lang in ("python", "javascript", "java")}
    for lang in harness:
        assert "x1e" in harness[lang] or "u001e" in harness[lang], lang
    names = {1: ["empty watchlist displays nothing", "single watch with extension filter", "two disjoint watches, remove one, remove both", "watch on a path that doesn't exist is a no-op"],
             2: ["overlapping watches: removing one keeps shared files (ref counting)", "display() returns a copy; caller can't corrupt the cache", "display() does not re-walk the tree (hot path)"],
             3: ["file added under two live watches, then one watch removed", "file removed while watched; unwatched file added is ignored"]}
    java_names = {1: ["empty watchlist displays nothing", "single watch with extension filter", "two disjoint watches, remove one, remove both", "watch on a path that doesn't exist is a no-op"],
                  2: names[2], 3: names[3]}
    return dict(
        id="watchlist", title="Watchlist", tagline="Recompute → cached display with reference counting → live tree updates",
        source="Modeled on a real Jane Street SWE intern phone screen: a tree search whose display is called constantly, with given traversal helpers. Statement authored for practice.",
        intro=intro + "\n" + tree,
        parts=[
            dict(title="Make it work", body=p1, api=api1),
            dict(title="Make it fast", body=part_body(2)),
            dict(title="The tree changes under you", body=p3, api=api3),
            dict(title="Discussion", body=part_body(4), discussion=True),
        ],
        clarify=js_pairs(A["CLARIFY_js"]),
        nudges=js_pairs(A["NUDGES_js"]),
        solution=sol,
        starters={"python": A["starter-python"].lstrip("\n"), "javascript": A["starter-javascript"].lstrip("\n"), "java": A["starter-java"].lstrip("\n")},
        harness=harness,
        javaClass="Watchlist", javaTestClass="WatchlistTests",
        testNames={str(k): v for k, v in names.items()},
        fnames={},
    )


# ---------------------------------------------------------------------
# generic problems
# ---------------------------------------------------------------------
def generic(P):
    fns = {f["key"]: f for f in P["functions"]}
    fnames = {k: {"python": f["py"], "javascript": f["js"], "java": f["js"]} for k, f in fns.items()}
    parts = []
    for i, part in enumerate(P["parts"]):
        d = dict(title=part["title"], body=part["body"], discussion=part.get("discussion", False), tag=part.get("tag", ""))
        if part.get("fns"):
            d["api"] = {lang: "\n".join(esc(signature(fns[k], lang)) for k in part["fns"]) for lang in ("python", "javascript", "java")}
            d["body"] = "{api}" + d["body"]
        parts.append(d)
    names = {}
    for t in P["tests"]:
        names.setdefault(str(t["part"]), []).append(t["name"])
    for part, ns in names.items():
        assert len(ns) == len(set(ns)), (P["id"], part, "duplicate test names")
    sol = (P["solution_notes"] + '\n<h3>Reference solution (Python)</h3>\n<pre><code class="lang-python">' + esc(solution_code(P["id"]))
           + "</code></pre>\n<h3>Part 4, briefly</h3>\n" + P["discussion_answers"])
    return dict(
        id=P["id"], title=P["title"], tagline=P["tagline"], source=P["source"], intro=P["intro"], parts=parts,
        clarify=[list(x) for x in P["clarify"]], nudges=[list(x) for x in P["nudges"]], solution=sol,
        starters={lang: starter(P, lang) for lang in ("python", "javascript", "java")},
        harness=harnesses(P), javaClass="Solution", javaTestClass="SolutionTests",
        testNames=names, fnames=fnames,
    )


# ---------------------------------------------------------------------
# run-only pad: no tests, problems in priority order
# ---------------------------------------------------------------------
def bank_starters(title):
    py = (f"# {title}\n# Ctrl/Cmd + Enter runs this file. Whatever you print shows up in Output.\n\n\n"
          "def main():\n    pass\n\n\nif __name__ == \"__main__\":\n    main()\n")
    js = (f"// {title}\n// Ctrl/Cmd + Enter runs this file. console.log output shows up in Output.\n\n\n"
          "function main() {\n}\n\nmain();\n")
    java = (f"// {title}\n// Runs in your browser on a real Java 21 JDK. The first Run downloads the JDK,\n"
            "// so give it 20-40 seconds; later runs are quick.\nimport java.util.*;\n\npublic class Solution {\n\n"
            "    public static void main(String[] args) {\n    }\n}\n")
    return {"python": py, "javascript": js, "java": java}


def _fix(s, fixes):
    for old, new in fixes:
        s = s.replace(old, new)
    return s


def run_only(p):
    """Turn a tested problem into a run-only one: drop the harness, give the starter a main."""
    st = dict(p["starters"])
    for lang in st:
        s = st[lang]
        for old, new in (("Ctrl/Cmd + Enter runs the tests for every part you've unlocked.", "Ctrl/Cmd + Enter runs this file."),
                         ("Run: Ctrl/Cmd + Enter. Tests run for every part you've unlocked.", "Run: Ctrl/Cmd + Enter runs this file."),
                         ("Tests run for every part you've unlocked.", "")):
            s = s.replace(old, new)
        st[lang] = s
    st["python"] = st["python"].rstrip() + "\n\n\nif __name__ == \"__main__\":\n    # Try your functions here; Run prints whatever you print.\n    pass\n"
    st["javascript"] = st["javascript"].rstrip() + "\n\n// Try your functions here; Run executes this file.\n"
    j = st["java"].rstrip()
    assert j.endswith("}"), p["id"]
    st["java"] = j[:-1].rstrip() + ("\n\n    public static void main(String[] args) {\n"
                                     "        // Try your code here; Run prints whatever you print.\n    }\n}\n")
    out = {k: p[k] for k in ("id", "title", "tagline", "source", "intro", "parts", "clarify", "nudges", "solution", "fnames", "javaClass")}
    out["intro"] = out["intro"].replace("the tests use", "the examples use")
    fixes = (("That's what the tests here do.", ""),
             ("Each test checks equivalence on 25 random memories (values −50…50) and has a length target that a careful optimizer reaches. Literals in tests are small, so folded constants never overflow 32 bits.",
              "Check yours for equivalence on random memories (values −50…50). Literals are small, so folded constants never overflow 32 bits."),
             ("All Part 1 tests must still pass.", "Everything from Part 1 must still work."),
             ("The tests check that", "Make sure that"))
    out["parts"] = [dict(pt, body=_fix(pt["body"], fixes)) for pt in out["parts"]]
    out["solution"] = _fix(out["solution"], fixes)
    out["starters"] = st
    return out


def main():
    import bank_a, bank_b, bank_c
    legacy = {P["id"]: run_only(generic(P)) for P in problems.ALL}
    legacy["watchlist"] = run_only(watchlist())

    def bank(ps):
        out = []
        for p in ps:
            d = dict(p, fnames={}, javaClass="Solution", starters=bank_starters(p["title"]))
            out.append(d)
        return out

    fold = dict(legacy["fold"], source=legacy["fold"]["source"] + " Reported 10 times in round one, the most of any question.")
    groups = [
        ("Most reported: do these first", [fold] + bank(bank_a.TIER1)),
        ("Reported onsite", bank(bank_a.TIER2)),
        ("Other reported questions", bank(bank_b.TIER3)),
        ("Earlier pad problems (reported variants)", [legacy[k] for k in ("watchlist", "stack", "accum", "towers", "wizard", "loadout", "dice")]),
        ("Experimental onsite formats", bank(bank_c.TIER4)),
        ("Unverified reports", bank(bank_c.TIER5)),
    ]
    probs = []
    for label, ps in groups:
        for p in ps:
            p["group"] = label
            probs.append(p)
    ids = [p["id"] for p in probs]
    assert len(ids) == len(set(ids)), "duplicate ids"
    data = {"problems": probs}
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = (HERE / "template.html").read_text().replace("/*__PAD_DATA__*/", blob).replace("/*__LEGACY_CSS__*/", LEGACY["css"])
    OUT.write_text(page)
    gen_dir = HERE / "_gen"
    gen_dir.mkdir(exist_ok=True)
    for p in probs:
        d = gen_dir / p["id"]
        d.mkdir(exist_ok=True)
        (d / "starter.py").write_text(p["starters"]["python"])
        (d / "starter.js").write_text(p["starters"]["javascript"])
        (d / f'{p["javaClass"]}.java').write_text(p["starters"]["java"])
    print(f"wrote {OUT} ({len(page):,} bytes), {len(probs)} problems")


if __name__ == "__main__":
    main()
