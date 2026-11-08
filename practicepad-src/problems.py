"""Problem definitions: statement, interviewer content, solution notes and
test cases. build.py turns these into the page, starters and harnesses.

Statements are rewritten in our own words from interview reports; parts
marked "extension" are new.

Prose tokens: {fn:key} renders as the current language's name for function
`key`.
"""
import random
import refs

# ---------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------
def T(part, name, fn, *args, expect=None, check="eq", **extra):
    return dict(part=part, name=name, fn=fn, args=list(args), expect=expect, check=check, **extra)


def ints(n, seed, lo, hi):
    return {"gen": "ints", "n": n, "seed": seed, "lo": lo, "hi": hi}


def hazard_sets(n, seed, hazards, maxk):
    return {"gen": "hazards", "n": n, "seed": seed, "hazards": hazards, "maxk": maxk}


class LCG:
    def __init__(self, seed):
        self.s = seed

    def next(self):
        self.s = self.s * 48271 % 2147483647
        return self.s


def materialize(a):
    if isinstance(a, dict) and a.get("gen") == "ints":
        r = LCG(a["seed"])
        return [a["lo"] + r.next() % (a["hi"] - a["lo"] + 1) for _ in range(a["n"])]
    if isinstance(a, dict) and a.get("gen") == "hazards":
        r = LCG(a["seed"])
        out = []
        for _ in range(a["n"]):
            k = 1 + r.next() % a["maxk"]
            picks = []
            for _ in range(k):
                h = a["hazards"][r.next() % len(a["hazards"])]
                if h not in picks:
                    picks.append(h)
            out.append(picks)
        return out
    return a


def fill(tests, impl):
    """Compute `expect` with the reference implementation where missing."""
    for t in tests:
        if t["expect"] is None:
            args = [materialize(a) for a in t["args"]]
            if t["check"] == "opt":
                t["expect"] = len(impl[t["fn"]](*args))
            else:
                t["expect"] = impl[t["fn"]](*args)
    return tests


def q(who, text):
    return f'<div class="quote"><span class="who">{who}</span>{text}</div>'


# =====================================================================
# 0. Watchlist (custom harness, defined in build.py)
# =====================================================================

# =====================================================================
# 1. Stack Machine
# =====================================================================
STACK = dict(
    id="stack",
    title="Stack Machine",
    tagline="Interpreter → jump instrumentation → tracing and loop detection",
    source="Reported Jane Street SWE intern question (interpreter and jump instrumentation, reported again October 2025). Rewritten for practice; Part 3 is an extension.",
    functions=[
        dict(key="run", py="run_interpreter", js="runInterpreter", params=[("instructions", "String[]")], ret="String[]"),
        dict(key="instrument", py="instrument_jumps", js="instrumentJumps", params=[("instructions", "String[]")], ret="String[]"),
        dict(key="trace", py="trace_jumps", js="traceJumps", params=[("instructions", "String[]"), ("limit", "int")], ret="String[]"),
    ],
    intro=q("Interviewer", "We have a tiny stack language. A program is a list of strings, and the machine has one stack of strings. First we'll write the interpreter, then a tool that rewrites programs, then we'll use both to debug."),
    parts=[
        dict(title="Run it", fns=["run"], body="""
<p>Run the program from index 0 with an empty stack and return everything <code>PRINT</code> produced, in order.</p>
<ul>
<li><code>PUSH value</code>: push everything after the first space, spaces included. <code>"PUSH "</code> pushes the empty string.</li>
<li><code>POP</code>: remove the top. Does nothing on an empty stack.</li>
<li><code>PRINT</code>: output the top without removing it. On an empty stack, output <code>""</code>.</li>
<li><code>TRUNCATE k</code>: drop up to <code>k</code> characters from the right end of the top string. Does nothing on an empty stack.</li>
<li><code>JUMP t</code>: continue at index <code>t</code>.</li>
<li><code>JUMP_IF_EMPTY t</code>: jump if the stack is empty <em>or</em> its top is <code>""</code>; otherwise fall through.</li>
</ul>
<p>Reaching index <code>len(instructions)</code> ends the program. Programs in this part always halt (at most 10,000 steps).</p>
<p>Example: <code>["PUSH hello", "PRINT", "TRUNCATE 2", "PRINT"]</code> → <code>["hello", "hel"]</code>.</p>"""),
        dict(title="Instrument the jumps", fns=["instrument"], body=q("Interviewer", "We want to see which jumps fire. Write a tool that rewrites a program so that, right before every original unconditional <code>JUMP</code>, it prints which jump it is.") + """
<p>Before each original <code>JUMP t</code> at index <code>i</code>, insert <code>PUSH jump@i</code>, <code>PRINT</code>, <code>POP</code>. Then fix every jump target (both <code>JUMP</code> and <code>JUMP_IF_EMPTY</code>) so it points at the start of the same instruction's new block, including its new prefix. A target equal to the old length becomes the new length. Don't instrument <code>JUMP_IF_EMPTY</code>, and don't run anything.</p>
<p>Example: <code>["PUSH x", "JUMP 3", "PUSH skip", "PRINT"]</code> →<br><code>["PUSH x", "PUSH jump@1", "PRINT", "POP", "JUMP 6", "PUSH skip", "PRINT"]</code>.</p>
<p>Careful: <code>"PUSH JUMP 0"</code> is a push of the string <code>"JUMP 0"</code>, not a jump.</p>"""),
        dict(title="Trace it, and catch loops", fns=["trace"], tag="extension", body=q("Interviewer", "The debugging team wants the sequence of unconditional jumps a program actually executes. A teammate suggests: instrument it, run it, and grep the output for <code>jump@</code>. Also, programs can now loop forever.") + """
<p>Return the indices (as strings) of the original unconditional <code>JUMP</code>s in the order they execute. Then:</p>
<ul>
<li>Before executing each instruction, if the machine is in a state it has been in before (same index <em>and</em> same full stack), append <code>"LOOP"</code> and stop.</li>
<li>Otherwise, if <code>limit</code> instructions have already executed, append <code>"LIMIT"</code> and stop.</li>
<li>If the program halts normally, add nothing.</li>
</ul>
<p>Example: <code>["PUSH a", "PUSH b", "POP", "JUMP 1"]</code>, limit 100 → <code>["3", "LOOP"]</code>.</p>
<p class="meta">Think about whether your teammate's suggestion is safe before you take it.</p>"""),
        dict(title="Discussion", discussion=True, body="""
<ol>
<li>Your teammate's grep idea: when exactly does it give a wrong answer? How would you make instrumentation output impossible to forge?</li>
<li>Your loop check stores every (index, stack) state. What does that cost in memory and time per step? What would you do if programs ran for a billion steps?</li>
<li>Write a program that never halts and that your <code>LOOP</code> check never catches. What does that tell you about loop detection in general?</li>
<li>Now instrument <code>JUMP_IF_EMPTY</code> too, but only print when the jump is <em>taken</em>. What's awkward about that with this instruction set?</li>
<li>An editor calls {fn:instrument} after every keystroke on a 100k-instruction program. What would you cache, and how do you update the index map after one inserted instruction?</li>
</ol>"""),
    ],
    clarify=[
        ("Does PUSH keep leading and trailing spaces in the value?", "Yes, everything after the first space, exactly. <code>\"PUSH  a \"</code> pushes <code>\" a \"</code>."),
        ("What does PRINT do on an empty stack? And POP?", "PRINT outputs the empty string; POP does nothing. Neither is an error."),
        ("Is JUMP_IF_EMPTY taken when the top is the empty string?", "Yes: empty stack <em>or</em> empty top string."),
        ("Can a jump target be out of range?", "Targets are always valid indices or exactly <code>len(instructions)</code>, which ends the program."),
        ("For Part 2, does a target pointing at an instrumented JUMP land on the PUSH jump@ line or on the JUMP itself?", "On the first inserted line, so the diagnostic prints whenever that jump is reached. <b>Great question to ask; it's the main trap.</b>"),
    ],
    nudges=[
        ("You're parsing with split(' ')", "What happens to <code>\"PUSH a b\"</code> with your parsing?",
         "Split on the first space only (<code>partition</code> / <code>indexOf</code>). The value can contain spaces, or be empty."),
        ("Part 2: you shift targets by counting jumps on the fly", "Walk me through the target of a backward jump.",
         "Build an old-index → new-index table in one pass first (a prefix sum of block sizes, plus one entry for the end). Then rewriting is a lookup. Two passes, no special cases."),
        ("Part 3: you grep the instrumented output", "What if the program itself pushes and prints the string <code>jump@0</code>?",
         "That's in-band signalling: data and diagnostics share a channel, so data can forge diagnostics. Record jumps inside the interpreter (a hook or a flag), not by parsing output."),
        ("Part 3: you only track the index for loops", "Is being at the same index twice enough to call it a loop?",
         "No. The stack is part of the state. Same index with a different stack can still halt. Hash (index, whole stack)."),
    ],
    solution_notes="""
<div class="say"><span class="lbl">Part 1</span><p>"I'll parse each instruction by splitting on the first space only, because PUSH values keep their spaces. Then it's a loop over a program counter: every instruction except a taken jump moves to pc + 1. I'll keep the jump decision in one helper so Part 2 and 3 can reuse it."</p></div>
<div class="say"><span class="lbl">Part 2</span><p>"The tricky bit is targets. I'll do it in two passes. First pass: for each original index, where does its block start in the new program? A JUMP becomes 4 lines, everything else 1, and I add one entry for the end. Second pass: emit, and rewrite every target through that table. Backward and self-jumps need no special case."</p></div>
<div class="say"><span class="lbl">Part 3</span><p>"I'm not going to grep the output: a program can print <code>jump@0</code> itself, so the diagnostics can be forged. I'll record jumps in the interpreter directly. For loops, a state is (pc, whole stack). If I see a state twice the machine is deterministic, so it will repeat forever. That costs memory per step, so the step limit matters."</p></div>""",
    discussion_answers="""
<ol>
<li>Grep fails whenever program data can look like a diagnostic. Fix it out of band: a separate channel (a hook, a distinct opcode like <code>TRACE i</code>), or an escape scheme that makes markers impossible in data.</li>
<li>O(steps × stack size) memory if you store whole stacks. Hash states instead (with collision risk), or use Floyd/Brent cycle detection, which needs O(1) extra states but re-runs the machine.</li>
<li><code>["PUSH a", "JUMP 0"]</code>: the stack grows forever, so no state repeats. Exact loop detection is the halting problem; you can only catch some loops, so you always need a step limit.</li>
<li>You'd need code on the taken path only: rewrite <code>JUMP_IF_EMPTY t</code> to jump to a new trampoline block (<code>PUSH jump@i, PRINT, POP, JUMP t'</code>), but PUSH/POP change emptiness, so the order inside the trampoline matters.</li>
<li>Cache the old → new table. One inserted instruction shifts every later start by 1 or 4; with a Fenwick tree over block sizes, each update and lookup is O(log n).</li>
</ol>""",
)
STACK["tests"] = fill([
    T(1, "example: print, truncate, print", "run", ["PUSH hello", "PRINT", "TRUNCATE 2", "PRINT"]),
    T(1, "example: empty top takes JUMP_IF_EMPTY", "run", ["PUSH ", "JUMP_IF_EMPTY 4", "PUSH skip", "PRINT", "PUSH ok", "PRINT"]),
    T(1, "example: POP and PRINT on empty stack", "run", ["POP", "PRINT", "PUSH abc", "JUMP 5", "PRINT"]),
    T(1, "empty program", "run", []),
    T(1, "PUSH keeps every space", "run", ["PUSH  two  spaces ", "PRINT", "PUSH a b c", "PRINT"]),
    T(1, "TRUNCATE past the start leaves an empty string", "run", ["PUSH abc", "TRUNCATE 50", "PRINT", "TRUNCATE 3", "PRINT"]),
    T(1, "TRUNCATE on empty stack does nothing", "run", ["TRUNCATE 3", "PRINT", "PUSH x", "PRINT"]),
    T(1, "loop: pop until empty", "run", ["PUSH a", "PUSH bb", "PUSH ccc", "PRINT", "POP", "JUMP_IF_EMPTY 7", "JUMP 3"]),
    T(1, "loop: count down with TRUNCATE", "run", ["PUSH xxxx", "PRINT", "TRUNCATE 1", "JUMP_IF_EMPTY 5", "JUMP 1"]),
    T(1, "PUSH of text that looks like an instruction", "run", ["PUSH JUMP 0", "PRINT", "PUSH POP", "PRINT"]),
    T(2, "example: forward jump", "instrument", ["PUSH x", "JUMP 3", "PUSH skip", "PRINT"]),
    T(2, "example: conditional target lands on a diagnostic block", "instrument", ["JUMP_IF_EMPTY 2", "JUMP 3", "JUMP 3"]),
    T(2, "example: pushed text is data", "instrument", ["PUSH JUMP 0", "PRINT"]),
    T(2, "empty program", "instrument", []),
    T(2, "self-jump", "instrument", ["JUMP 0"]),
    T(2, "backward jump into the middle", "instrument", ["PUSH a", "PRINT", "JUMP 1", "JUMP 0", "POP"]),
    T(2, "jump to the end", "instrument", ["JUMP 2", "PRINT"]),
    T(2, "conditional jump to the end", "instrument", ["JUMP_IF_EMPTY 3", "JUMP 0", "PRINT"]),
    T(2, "no jumps: unchanged", "instrument", ["PUSH a", "TRUNCATE 1", "PRINT", "POP"]),
    T(2, "many jumps", "instrument", ["JUMP 4", "JUMP 0", "PUSH q", "JUMP 2", "JUMP_IF_EMPTY 1", "JUMP 6"]),
    T(3, "example: loop with a non-empty stack", "trace", ["PUSH a", "PUSH b", "POP", "JUMP 1"], 100),
    T(3, "halting program: just the trace", "trace", ["PUSH x", "JUMP 3", "PUSH skip", "PRINT"], 100),
    T(3, "self-jump is a LOOP", "trace", ["JUMP 0"], 100),
    T(3, "the program prints jump@0 itself", "trace", ["PUSH jump@0", "PRINT", "POP", "PUSH x", "JUMP 6", "PUSH never", "PRINT"], 100),
    T(3, "growing stack never repeats: LIMIT", "trace", ["PUSH a", "JUMP 0"], 7),
    T(3, "halts exactly at the limit: no suffix", "trace", ["PUSH a", "PRINT"], 2),
    T(3, "same index, different stack is not a loop", "trace", ["PUSH xxx", "TRUNCATE 1", "JUMP_IF_EMPTY 4", "JUMP 1", "PUSH done", "PRINT"], 100),
    T(3, "pop-until-empty loop halts", "trace", ["PUSH a", "PUSH bb", "PUSH ccc", "PRINT", "POP", "JUMP_IF_EMPTY 7", "JUMP 3"], 100),
    T(3, "loop that only conditional jumps drive", "trace", ["PUSH ", "JUMP_IF_EMPTY 0"], 100),
], {"run": refs.run_interpreter, "instrument": refs.instrument_jumps, "trace": refs.trace_jumps})


# =====================================================================
# 2. Accumulator VM
# =====================================================================
def _acc_prog_tests():
    r = random.Random(2024)
    out = []
    for i in range(6):
        ml = r.randint(2, 4)
        prog = []
        for _ in range(r.randint(10, 18)):
            o = r.choice(["LOAD", "STORE", "ADD", "SUB", "MUL", "LOAD", "STORE", "ADD"])
            x = r.randrange(ml) if o in ("LOAD", "STORE") else r.randint(-3, 4)
            prog.append(f"{o} {x}")
        out.append(T(3, f"random straight-line program #{i + 1}", "opt", prog, check="opt", memLen=ml))
    return out


ACCUM = dict(
    id="accum",
    title="Accumulator VM",
    tagline="Interpreter → jumps and pointers → a peephole optimizer",
    source="Reported Jane Street question (an interpreter with load, store and arithmetic). Rewritten for practice; Parts 2 and 3 are extensions.",
    functions=[
        dict(key="run", py="run_program", js="runProgram", params=[("memory", "int[]"), ("instructions", "String[]")], ret="int[]"),
        dict(key="opt", py="optimize", js="optimize", params=[("instructions", "String[]")], ret="String[]"),
    ],
    intro=q("Interviewer", "A tiny machine: an array of integer memory cells and one integer accumulator. Programs are lists of strings. Let's write the interpreter first."),
    parts=[
        dict(title="Run it", fns=["run"], body="""
<p>The accumulator starts at 0. Run each instruction once, in order, and return the final memory (not the accumulator). Don't modify the caller's array.</p>
<ul>
<li><code>LOAD i</code>: acc = mem[i]</li>
<li><code>STORE i</code>: mem[i] = acc</li>
<li><code>ADD v</code>, <code>SUB v</code>, <code>MUL v</code>: acc = acc + v, acc − v, acc × v, where <code>v</code> is a literal integer, possibly negative</li>
</ul>
<p>Example: memory <code>[4, 1]</code>, <code>["LOAD 0", "ADD 3", "STORE 1", "MUL 2"]</code> → <code>[4, 7]</code>. The last MUL only changes the accumulator.</p>"""),
        dict(title="Jumps and pointers", fns=[], tag="extension", body=q("Interviewer", "Straight-line code is boring. Let's add control flow and indirect addressing. Same function.") + """
<ul>
<li><code>JMP t</code>: continue at instruction <code>t</code></li>
<li><code>JZ t</code>: jump to <code>t</code> if acc == 0</li>
<li><code>JNEG t</code>: jump to <code>t</code> if acc &lt; 0</li>
<li><code>LOADI i</code>: acc = mem[mem[i]] (cell <code>i</code> holds an address)</li>
<li><code>STOREI i</code>: mem[mem[i]] = acc</li>
</ul>
<p>Reaching index <code>len(instructions)</code> halts. Every program halts within 100,000 steps and every address is valid. All Part 1 tests must still pass.</p>
<p class="meta">Before typing: will your Part 1 design stretch to this, or does something need restructuring?</p>"""),
        dict(title="Optimize it", fns=["opt"], tag="extension", body=q("Interviewer", "This VM runs the same program over millions of memory arrays, so shorter programs matter. Write an optimizer for straight-line programs.") + """
<p>Input uses only the Part 1 instructions. Return a program, also using only Part 1 instructions, that leaves <em>exactly the same final memory</em> as the input for every starting memory, and is as short as you can make it.</p>
<p>Each test checks equivalence on 25 random memories (values −50…50) and has a length target that a careful optimizer reaches. Literals in tests are small, so folded constants never overflow 32 bits.</p>
<p>Example: <code>["LOAD 0", "ADD 3", "MUL 2", "ADD 1", "STORE 1"]</code> can become <code>["LOAD 0", "MUL 2", "ADD 7", "STORE 1"]</code>.</p>
<p class="meta">Look for things that can never be observed, and for runs of arithmetic you can merge.</p>"""),
        dict(title="Discussion", discussion=True, body="""
<ol>
<li>Your optimizer works on straight-line code. What breaks once there are jumps? What analysis would you need?</li>
<li>Folding <code>MUL 100000</code> twice into one MUL: what happens in a 32-bit implementation? Is the optimized program still equivalent?</li>
<li>The same program runs over a million memories. What would you do once, up front, so each run is cheap?</li>
<li>Is your optimizer optimal? Give a program where it isn't, or argue why it is.</li>
<li>How would you test an optimizer like this if you couldn't trust a reference implementation?</li>
</ol>"""),
    ],
    clarify=[
        ("Can memory values or the accumulator be negative?", "Yes. Literals can be negative too: <code>SUB -3</code> adds 3."),
        ("Do I return a new array or modify the input?", "Return a new one. Callers reuse their array."),
        ("What about overflow?", "Inputs keep every value in 32-bit range for Parts 1 and 2. Worth saying how you'd handle it if they didn't."),
        ("Part 3: equivalent for which starting memories?", "All of them, with the same memory length. The final accumulator doesn't count; only final memory does."),
    ],
    nudges=[
        ("You re-split each string every time it executes", "Part 2 programs loop. How many times does each string get parsed?",
         "Parse once into (op, int) pairs, then execute. It's the same 'move work out of the hot path' idea as caching."),
        ("Part 2: your loop increments pc after a jump", "Trace JMP 0 through your code.",
         "Decide the next pc in one place: default pc + 1, overridden by a taken jump. Off-by-one jumps are the classic bug here."),
        ("Part 3: you only merge adjacent ADDs", "What does <code>ADD 3, MUL 2, ADD 1</code> do to acc, as a formula?",
         "Any run of ADD/SUB/MUL is an affine map acc → a·acc + b, and affine maps compose. So any run becomes at most <code>MUL a, ADD b</code>. If acc is a known constant, it becomes one ADD."),
        ("Part 3: you're not removing stores", "If cell 1 is stored twice with no LOAD 1 between, which store matters?",
         "Only the last. Walk backwards: a STORE to a cell that's overwritten later before any LOAD of it is dead. Arithmetic after the final STORE is dead too, because the accumulator isn't part of the result."),
    ],
    solution_notes="""
<div class="say"><span class="lbl">Part 1–2</span><p>"I'll parse each line once into an opcode and an int, then run a loop with a program counter. Next pc defaults to pc + 1; jumps override it. Copy the memory first so I don't mutate the caller's array."</p></div>
<div class="say"><span class="lbl">Part 3</span><p>"Two observations. One: a run of ADD/SUB/MUL is an affine function of the accumulator, a·acc + b, and those compose, so any run becomes at most MUL a then ADD b, or a single ADD if I know acc is a constant, like at the start, where it's 0. Two: some writes are never observed. A STORE that's overwritten before anyone loads that cell is dead, and anything after the last STORE is dead. Each pass can expose more work for the other, so I'll alternate them until nothing changes."</p>
<p>"Then I'd test it differentially: random programs, random memories, compare against the interpreter. That's what the tests here do."</p></div>""",
    discussion_answers="""
<ol>
<li>Jumps split the program into basic blocks. Folding still works inside a block, but dead-store elimination needs liveness analysis over the control-flow graph (a fixed-point dataflow pass), and a jump target can't be removed or merged across.</li>
<li>In 32-bit two's complement, multiplication wraps modulo 2³², and wrapping is still a ring homomorphism, so folded MULs stay equivalent <em>if every step wraps the same way</em>. In Python or with long, it's only equivalent if the original never overflowed. Say which semantics you're assuming.</li>
<li>Parse once, optimize once, and maybe compile to closures or a flat int array so the inner loop does no string work. Same idea as the Watchlist cache: move work from the hot path to the rare path.</li>
<li>Not optimal. It never reorders stores, and it treats memory cells independently, so it can't, for example, shorten a program whose final state is a permutation of cells done through a temporary. Finding the true minimum is a search problem.</li>
<li>Differential testing against the interpreter on random programs and memories, plus small exhaustive cases. Shrink failing cases to a minimal program.</li>
</ol>""",
)
ACCUM["tests"] = fill([
    T(1, "example: only STORE changes memory", "run", [4, 1], ["LOAD 0", "ADD 3", "STORE 1", "MUL 2"]),
    T(1, "example: acc starts at 0; SUB of a negative", "run", [9, -2], ["STORE 0", "LOAD 1", "SUB -3", "STORE 1"]),
    T(1, "example: no instructions", "run", [2, 5], []),
    T(1, "multiply and negate", "run", [3, 0, 0], ["LOAD 0", "MUL -4", "STORE 1", "ADD 2", "STORE 2"]),
    T(1, "later LOAD sees an earlier STORE", "run", [1, 2], ["LOAD 0", "ADD 10", "STORE 1", "LOAD 1", "MUL 2", "STORE 0"]),
    T(1, "32-bit extremes", "run", [-2147483648, 0], ["LOAD 0", "ADD 2147483647", "STORE 1"]),
    T(2, "JMP skips code", "run", [0, 0], ["ADD 5", "JMP 3", "ADD 100", "STORE 0"]),
    T(2, "loop: add 2 per countdown step", "run", [5, 0], ["LOAD 0", "JZ 8", "SUB 1", "STORE 0", "LOAD 1", "ADD 2", "STORE 1", "JMP 0"]),
    T(2, "absolute value with JNEG", "run", [-7, 0], ["LOAD 0", "JNEG 4", "STORE 1", "JMP 6", "MUL -1", "STORE 1"]),
    T(2, "absolute value, non-negative input", "run", [7, 0], ["LOAD 0", "JNEG 4", "STORE 1", "JMP 6", "MUL -1", "STORE 1"]),
    T(2, "STOREI fills a range through a pointer", "run", [3, 3, 9, 7, 7, 7],
      ["LOAD 1", "JZ 11", "SUB 1", "STORE 1", "MUL 0", "ADD 42", "STOREI 0", "LOAD 0", "ADD 1", "STORE 0", "JMP 0"]),
    T(2, "LOADI reads through a pointer", "run", [3, 0, 0, 55], ["LOADI 0", "STORE 1", "LOAD 0", "SUB 1", "STORE 0", "LOADI 0", "STORE 2"]),
    T(2, "jump straight to the end", "run", [1], ["JMP 3", "ADD 1", "STORE 0"]),
    T(3, "fold constant arithmetic at the start", "opt", ["ADD 1", "ADD 2", "SUB 4", "STORE 0"], check="opt", memLen=1),
    T(3, "fold an affine run after a LOAD", "opt", ["LOAD 0", "ADD 3", "MUL 2", "ADD 1", "MUL 3", "STORE 1"], check="opt", memLen=2),
    T(3, "drop a store that's overwritten", "opt", ["LOAD 0", "STORE 1", "ADD 1", "STORE 1"], check="opt", memLen=2),
    T(3, "drop arithmetic after the last store", "opt", ["LOAD 1", "STORE 0", "MUL 5", "ADD 2"], check="opt", memLen=2),
    T(3, "drop a LOAD of the cell just stored", "opt", ["LOAD 0", "ADD 1", "STORE 2", "LOAD 2", "ADD 1", "STORE 3"], check="opt", memLen=4),
    T(3, "MUL 0 makes a LOAD irrelevant", "opt", ["LOAD 0", "MUL 0", "ADD 7", "STORE 1"], check="opt", memLen=2),
    T(3, "storing a cell into itself does nothing", "opt", ["LOAD 0", "STORE 0"], check="opt", memLen=1),
    T(3, "empty program", "opt", [], check="opt", memLen=1),
    *_acc_prog_tests(),
], {"run": refs.run_program, "opt": refs.optimize})


# =====================================================================
# 3. Code Folding
# =====================================================================
_SRC = ["def outer() {", " before();", " if (ready) {", " work();", " }", " after();", "}", "done();"]
_DEEP = ["class A {", "\tvoid f() {  ", "\t\tif (x) {", "\t\t\ty();", "\t\t}", "\t\twhile (z) {", "\t\t\tw();", "\t\t}", "\t}", "\tint g;", "}", "", "main() {", "\trun();", "}"]
FOLD = dict(
    id="fold",
    title="Code Folding",
    tagline="Brace matching → fold/unfold with nested state → viewport and display indices",
    source="Reported Jane Street question (brace matching and code folding, including folding a hidden block and mapping display lines). Rewritten for practice; Part 3 makes the display-index extension concrete.",
    functions=[
        dict(key="ops", py="code_editor_operations", js="codeEditorOperations", params=[("lines", "String[]"), ("operations", "String[]")], ret="String[][]"),
    ],
    intro=q("Interviewer", "You're building code folding for an editor. You get the file as a list of lines and a list of operations, and you return one row of output per operation."),
    parts=[
        dict(title="Match the braces", fns=["ops"], body="""
<p>Braces are balanced and properly nested. Each line has at most one brace, and it's the last non-whitespace character. A closing line is only indentation plus <code>}</code>. Indices are 0-based positions in the original file.</p>
<p>Support <code>MATCH</code>: return every block as <code>"open:close"</code>, sorted by opening line.</p>
<p>Example: the file below gives <code>["0:6", "2:4"]</code>.</p>
<pre class="treebox">0  def outer() {
1   before();
2   if (ready) {
3   work();
4   }
5   after();
6  }
7  done();</pre>"""),
        dict(title="Fold and unfold", fns=[], body=q("Interviewer", "Now the actual folding. Same function, two more operations.") + """
<ul>
<li><code>TOGGLE i</code>: flip the folded state of the block that opens on original line <code>i</code>, even if it's currently hidden inside a folded parent. Output an empty row.</li>
<li><code>GET</code>: output the visible lines. A visible folded block shows its opening line cut right after the <code>{</code>, plus <code>" ... }"</code>, and hides everything through its closing line. Other lines are shown exactly as they are.</li>
</ul>
<p>Each block remembers its own state. Folding a parent doesn't change the children: unfold the parent later and any folded child is still folded.</p>
<p>Example: <code>TOGGLE 2</code>, <code>GET</code> gives <code>["def outer() {", " before();", " if (ready) { ... }", " after();", "}", "done();"]</code>.</p>"""),
        dict(title="Display indices and the viewport", fns=[], tag="extension", body=q("Interviewer", "Users click on what they <em>see</em>, and the screen only shows a window of the file.") + """
<ul>
<li><code>TOGGLE_LINE d</code>: toggle the block whose opening line is currently shown at display row <code>d</code> (0-based, among visible rows). It's guaranteed to be an opening line. Output an empty row.</li>
<li><code>GET_RANGE a b</code>: output visible rows <code>a</code> through <code>b − 1</code>. Clamp to what exists; an empty range is fine.</li>
</ul>
<p class="meta">Before you code: say how a display row maps back to an original line, and what that costs.</p>"""),
        dict(title="Discussion", discussion=True, body="""
<ol>
<li><code>GET_RANGE</code> runs on every scroll event of a 200,000-line file with thousands of folds. What do you cache? What invalidates it?</li>
<li>Make <code>TOGGLE</code> and display-row lookup both O(log n). (Hint: a line is hidden when the number of folded blocks around it is above zero.)</li>
<li>The user types a new line inside a block. Every index after it shifts. How do you avoid rebuilding everything?</li>
<li>Real code has braces in strings and comments. Where does that change your design?</li>
</ol>"""),
    ],
    clarify=[
        ("Can a toggle target a line that isn't an opening brace?", "No, toggle indices are always opening lines."),
        ("When a block is folded, is trailing whitespace after the { kept?", "No: cut right after the <code>{</code>, then add <code>\" ... }\"</code>."),
        ("Does folding a parent reset the children?", "No. Each block keeps its own state. That's the main thing being tested in Part 2."),
        ("Can the file be empty?", "Yes. MATCH and GET return empty rows."),
        ("How big can it get? How often is GET called?", "Small here. But in the real editor, GET runs on every repaint. <b>Same \"called a lot\" signal as Watchlist.</b>"),
    ],
    nudges=[
        ("You're matching braces by scanning forward for the next }", "What does your matcher do with a nested block?",
         "Use a stack of open line indices: push on {, pop on }. One pass, O(n)."),
        ("Part 2: toggling a parent also flips its children", "Fold line 2, fold line 0, unfold line 0. What should GET show?",
         "Keep a per-block boolean and never touch children. Hiding is computed when you render: skip from a folded opening line straight past its match."),
        ("Part 3: you search the original lines for the display row", "How do you know which original line is on screen at row 3?",
         "Render once into a list of (original index, text) pairs. Row d is entry d. That list is also exactly what you'd cache."),
    ],
    solution_notes="""
<div class="say"><span class="lbl">Part 1</span><p>"One pass with a stack of opening indices gives me the match map. I'll compute it once up front because the file doesn't change."</p></div>
<div class="say"><span class="lbl">Part 2</span><p>"State is a set of folded opening lines, nothing else. Rendering walks the lines; at a folded opening line I emit the shortened line and jump to its match + 1. That skips nested blocks whatever their state, so children keep their state for free."</p></div>
<div class="say"><span class="lbl">Part 3</span><p>"Rendering produces (original index, text) pairs, so display row d maps to an original line by indexing. Right now that's O(n) per operation. If this were hot I'd cache the rendered list and invalidate on toggle, and at scale I'd keep a hidden-count per line in a Fenwick tree so both toggle and row lookup are O(log n)."</p></div>""",
    discussion_answers="""
<ol>
<li>Cache the rendered (index, text) list; invalidate on TOGGLE. Scrolling then costs O(rows shown).</li>
<li>Give each line a counter of folded blocks strictly around it (excluding the opening line itself): folding adds +1 over the block's inner range, unfolding −1. Range add plus "count of zeros" queries fit a segment tree (store the min and the count of the min). Display row d becomes the d-th zero, found by descending the tree.</li>
<li>Identify blocks by stable ids, not line numbers, and use a balanced tree or rope over lines, so inserting a line is O(log n).</li>
<li>Matching needs a tokenizer that knows strings and comments. Folding logic stays the same; only the matcher changes. Keep them separate.</li>
</ol>""",
)
FOLD["tests"] = fill([
    T(1, "example: MATCH", "ops", _SRC, ["MATCH"]),
    T(1, "empty file", "ops", [], ["MATCH"]),
    T(1, "two-line block", "ops", ["{", "}"], ["MATCH"]),
    T(1, "deep nesting, tabs and trailing spaces", "ops", _DEEP, ["MATCH"]),
    T(1, "siblings and no braces", "ops", ["a {", "}", "b", "c {", "}", "d"], ["MATCH", "MATCH"]),
    T(2, "example: nested state survives the parent", "ops", _SRC, ["TOGGLE 2", "GET", "TOGGLE 0", "GET", "TOGGLE 0", "GET"]),
    T(2, "example: empty file GET", "ops", [], ["MATCH", "GET"]),
    T(2, "example: two-line block folds and unfolds", "ops", ["{", "}"], ["GET", "TOGGLE 0", "GET", "TOGGLE 0", "GET"]),
    T(2, "toggle a hidden child, then unfold the parent", "ops", _DEEP, ["TOGGLE 0", "TOGGLE 2", "GET", "TOGGLE 0", "GET"]),
    T(2, "fold drops whitespace after the brace, keeps tabs before", "ops", _DEEP, ["TOGGLE 1", "GET"]),
    T(2, "fold every block", "ops", _DEEP, ["TOGGLE 2", "TOGGLE 5", "GET", "TOGGLE 12", "GET", "TOGGLE 1", "GET"]),
    T(2, "GET with nothing folded is the file", "ops", _DEEP, ["GET"]),
    T(3, "TOGGLE_LINE on rows that match original lines", "ops", _SRC, ["TOGGLE 2", "TOGGLE_LINE 0", "GET", "TOGGLE_LINE 0", "GET"]),
    T(3, "TOGGLE_LINE after rows above were folded", "ops", _DEEP, ["TOGGLE 2", "TOGGLE_LINE 3", "GET", "TOGGLE_LINE 8", "GET", "TOGGLE_LINE 2", "GET"]),
    T(3, "GET_RANGE windows and clamping", "ops", _DEEP, ["GET_RANGE 0 3", "TOGGLE 1", "GET_RANGE 1 4", "GET_RANGE 3 100", "GET_RANGE 50 60", "GET_RANGE 2 2"]),
    T(3, "mixed operations", "ops", _SRC + ["x {", "y();", "}"], ["MATCH", "TOGGLE_LINE 8", "GET_RANGE 6 9", "TOGGLE 0", "GET", "TOGGLE_LINE 2", "GET"]),
], {"ops": refs.code_editor_operations})


# =====================================================================
# 4. Brick Towers
# =====================================================================
def _tower_random(part, fn, count, seed, lim_lo, lim_hi):
    r = random.Random(seed)
    acts = ["BUY", "LOAD", "MOVE_FAR", "MOVE_NEAR", "OBSERVE"]
    out = []
    for i in range(count):
        lim = r.randint(lim_lo, lim_hi)
        east = [r.choice(acts) for _ in range(lim)]
        out.append(T(part, f"random East schedule #{i + 1} ({lim} days)", fn, east, lim))
    return out


TOWERS = dict(
    id="towers",
    title="Brick Towers",
    tagline="Simulate the game → fastest win (BFS) → count every fastest win",
    source="Reported Jane Street question (two towers, dollies, a delayed far transfer, a win condition). Rewritten for practice; the opponent schedule, tie-breaks and Part 3 are authored.",
    functions=[
        dict(key="sim", py="simulate_towers", js="simulateTowers", params=[("west_actions", "String[]"), ("east_actions", "String[]")], ret="int"),
        dict(key="win", py="find_winning_tower_strategy", js="findWinningTowerStrategy", params=[("east_actions", "String[]"), ("day_limit", "int")], ret="String[]"),
        dict(key="count", py="count_fastest_wins", js="countFastestWins", params=[("east_actions", "String[]"), ("day_limit", "int")], ret="int"),
    ],
    intro=q("Interviewer", "Two teams, West and East, each have a <em>near</em> tower and a <em>far</em> tower. Every day each team takes one action. We'll simulate it, then search for a strategy."),
    parts=[
        dict(title="Simulate", fns=["sim"], body="""
<p>Each team starts with near = 5, far = 0, no dollies, no bricks. On an unlocked turn a team does one of:</p>
<ul>
<li><code>BUY</code>: get one more dolly (permanent).</li>
<li><code>LOAD</code>: put one brick on every dolly.</li>
<li><code>MOVE_NEAR</code>: add all dolly bricks to the near tower; dollies empty.</li>
<li><code>MOVE_FAR</code>: send all dolly bricks to the far tower; dollies empty. The team is <em>locked</em> on its next turn, and the bricks arrive at the start of that locked turn.</li>
<li><code>OBSERVE</code>: nothing.</li>
</ul>
<p>On a locked turn the team's listed action is ignored (West writes <code>WAIT</code> there). Each day, West moves, then East. West <em>wins</em> right after any turn where West near &gt; East far <em>and</em> West far &gt; East near.</p>
<p>Return the 0-based day West wins on, or −1. Both schedules have the same length and West's is valid.</p>"""),
        dict(title="Find the fastest win", fns=["win"], body=q("Interviewer", "East follows a fixed script. Find West's fastest winning schedule.") + """
<p>Return a winning West schedule with the fewest days, at most <code>day_limit</code> (≤ 8), with <code>WAIT</code> on locked days. Break ties by the lexicographically smallest schedule, comparing action names as strings: <code>BUY &lt; LOAD &lt; MOVE_FAR &lt; MOVE_NEAR &lt; OBSERVE &lt; WAIT</code>. Return <code>[]</code> if West can't win in time.</p>
<p>Example: East always OBSERVEs, limit 7 → <code>["BUY", "BUY", "BUY", "LOAD", "LOAD", "MOVE_FAR", "WAIT"]</code>: six bricks reach the far tower on day 6, and 6 &gt; 5.</p>"""),
        dict(title="How many ways?", fns=["count"], tag="extension", body=q("Interviewer", "Product wants to show players how many different fastest wins exist. And games are longer now.") + """
<p>Return how many distinct West schedules win in the minimum number of days (0 if West can't win within <code>day_limit</code>). <code>day_limit ≤ 12</code>, so there are up to 6¹² schedules to think about.</p>
<p>Example: East always OBSERVEs, limit 7 → 2: three dollies and two loads, or two dollies and three loads.</p>
<p class="meta">Your Part 2 search threw duplicate states away. What should it do with them now?</p>"""),
        dict(title="Discussion", discussion=True, body="""
<ol>
<li>What's your search state? Why is it safe to throw away a second schedule that reaches the same state on the same day in Part 2, but not in Part 3?</li>
<li><code>day_limit</code> becomes 40. Which part of your search blows up first, and what would you prune? Is <code>OBSERVE</code> ever useful?</li>
<li>East stops following a script and plays to beat you, and East wins with the mirror condition. What algorithm now? Can West ever force a win, given that both sides have the same resources and East starts with a near tower of 5?</li>
<li>The original report says "optimize using earlier information". If you only see East's actions as they happen, how does your strategy change?</li>
</ol>"""),
    ],
    clarify=[
        ("When does West's MOVE_FAR land?", "At the start of West's next turn, which is locked. West writes WAIT there. The win check happens after that turn, with the bricks counted."),
        ("Does LOAD with zero dollies do anything?", "No: it puts a brick on every dolly, and there are none."),
        ("Is the win check strict?", "Yes, strictly greater on both comparisons."),
        ("Is East's action on East's locked day ignored even if it's BUY?", "Yes, ignored entirely."),
        ("What exactly is lexicographic order here?", "Compare day by day by action name as a string; the first difference decides."),
    ],
    nudges=[
        ("You enumerate all 6^8 schedules", "How many of those schedules lead to exactly the same towers and dollies?",
         "Most. Search over states, not schedules: BFS by day, and drop a schedule if another one already reached the same (West, East) state on that day."),
        ("You're unsure your dedup keeps the lexicographically smallest", "In what order do you generate schedules within one day?",
         "If each layer is in lexicographic order and you expand actions in sorted order, the next layer is too, so the first schedule to reach a state is the smallest one. Say this argument out loud."),
        ("Part 3: you enumerate schedules and count", "With a limit of 12, how many schedules is that?",
         "Too many. Keep the BFS, but each state now carries a count: when two schedules reach the same state, add their counts instead of dropping one. The answer is the sum of counts that win on the first winning day."),
    ],
    solution_notes="""
<div class="say"><span class="lbl">Part 1</span><p>"I'll make a team an immutable value with a take_turn(action) method, so the simulator is a loop: West turn, check, East turn, check. Immutable states also make Part 2's dedup trivial because they're hashable."</p></div>
<div class="say"><span class="lbl">Part 2</span><p>"Brute force over schedules is 6^8, fine here, but most schedules collide on state. I'll BFS by day: each layer is a list of (west, east, path), expanded in sorted action order, so each layer stays in lexicographic order. The first win I see is minimal length and lexicographically smallest. I'll keep a seen-set per day."</p></div>
<div class="say"><span class="lbl">Part 3</span><p>"Same layers, but a state maps to the number of schedules that reach it. Merging adds counts. On the first day any successor wins, the answer is the sum of those counts. It's the same trick as counting paths in a DAG: memoize on state, add."</p></div>""",
    discussion_answers="""
<ol>
<li>State = (West team, East team) on a given day. Futures depend only on state and day. In Part 2 the earlier-found schedule is lexicographically smaller, so any continuation of the duplicate is beaten by the same continuation of the first. In Part 3 every schedule counts, so duplicates are merged with their multiplicity, not dropped.</li>
<li>States explode through dolly and brick counts. Prune dominated states (same day, every field ≥ another's, and not locked) and drop OBSERVE when another action is at least as good. Then bound: if even best-case growth can't beat East by the limit, stop.</li>
<li>Minimax over alternating turns with memoization: West can force a win if some West move leads to a position where every East reply is still a forced win. Here East can likely always defend by raising its near tower, so the interesting answer is a proof or a counterexample, not code.</li>
<li>Online play: you can't plan the whole schedule; replan each day from the current state (receding horizon), or use a strategy computed by minimax that reacts to East.</li>
</ol>""",
)
_W1 = ["BUY", "BUY", "BUY", "LOAD", "LOAD", "MOVE_FAR", "WAIT"]
TOWERS["tests"] = fill([
    T(1, "example schedule wins on day 6", "sim", _W1, ["OBSERVE"] * 7),
    T(1, "not enough bricks: no win", "sim", ["BUY", "BUY", "LOAD", "LOAD", "MOVE_FAR", "WAIT"], ["OBSERVE"] * 6),
    T(1, "East's MOVE_NEAR raises the bar", "sim", _W1, ["BUY", "LOAD", "MOVE_NEAR", "OBSERVE", "OBSERVE", "OBSERVE", "OBSERVE"]),
    T(1, "East's action on its locked day is ignored", "sim", _W1, ["OBSERVE", "MOVE_FAR", "BUY", "BUY", "LOAD", "MOVE_NEAR", "OBSERVE"]),
    T(1, "MOVE_NEAR then far tower", "sim", ["BUY", "BUY", "BUY", "LOAD", "LOAD", "LOAD", "MOVE_FAR", "WAIT"], ["BUY", "BUY", "LOAD", "MOVE_FAR", "OBSERVE", "OBSERVE", "OBSERVE", "OBSERVE"]),
    T(1, "one day, no win", "sim", ["OBSERVE"], ["OBSERVE"]),
    T(2, "example: East only observes", "win", ["OBSERVE"] * 7, 7),
    T(2, "example: four days is too short", "win", ["BUY", "LOAD", "MOVE_NEAR", "BUY"], 4),
    T(2, "East builds near: West needs more bricks", "win", ["BUY", "LOAD", "MOVE_NEAR", "OBSERVE", "OBSERVE", "OBSERVE", "OBSERVE", "OBSERVE"], 8),
    T(2, "limit 6 is one short", "win", ["OBSERVE"] * 6, 6),
    *_tower_random(2, "win", 8, 11, 6, 8),
    T(3, "example: two fastest wins", "count", ["OBSERVE"] * 7, 7),
    T(3, "no win in time", "count", ["BUY", "LOAD", "MOVE_NEAR", "BUY"], 4),
    T(3, "East keeps raising its near tower", "count", ["BUY", "LOAD", "MOVE_NEAR", "LOAD", "MOVE_NEAR", "LOAD", "MOVE_NEAR", "OBSERVE", "OBSERVE", "OBSERVE", "OBSERVE", "OBSERVE"], 12),
    T(3, "fastest win takes 10 days", "count", ['BUY', 'BUY', 'LOAD', 'LOAD', 'MOVE_NEAR', 'LOAD', 'LOAD', 'MOVE_NEAR', 'BUY', 'OBSERVE', 'LOAD', 'LOAD'], 12),
    T(3, "East builds a big far tower", "count", ["BUY", "BUY", "BUY", "LOAD", "LOAD", "LOAD", "MOVE_FAR", "OBSERVE", "OBSERVE", "OBSERVE", "OBSERVE", "OBSERVE"], 12),
    *_tower_random(3, "count", 4, 99, 9, 12),
], {"sim": refs.simulate_towers, "win": refs.find_winning_tower_strategy, "count": refs.count_fastest_wins})


# =====================================================================
# 5. Wizard Scrolls
# =====================================================================
def _wiz_random(part, fn, count, seed, n_lo, n_hi):
    r = random.Random(seed)
    out = []
    for i in range(count):
        n = r.randint(n_lo, n_hi)
        costs = [r.choice([r.randint(1, 15), r.randint(1, 40)]) for _ in range(n)]
        out.append(T(part, f"random, {n} days #{i + 1}", fn, costs))
    return out


WIZARD = dict(
    id="wizard",
    title="Wizard Scrolls",
    tagline="Max monsters → exact best schedule with tie-breaks → 200,000 days",
    source="Reported Jane Street question (ten scrolls a day, one monster a day, optimize using earlier information). Rewritten for practice; persistence, costs, tie-breaks and Part 3 are authored.",
    functions=[
        dict(key="max", py="max_monsters", js="maxMonsters", params=[("costs", "int[]")], ret="int"),
        dict(key="days", py="choose_monster_days", js="chooseMonsterDays", params=[("costs", "int[]")], ret="int[]"),
        dict(key="big", py="max_monsters_and_cost", js="maxMonstersAndCost", params=[("costs", "int[]")], ret="int[]"),
    ],
    intro=q("Interviewer", "A wizard gets 10 scrolls at the start of every day, and unused scrolls carry over. On day <code>i</code> one monster appears that costs <code>costs[i]</code> scrolls to defeat, and it's only there that day."),
    parts=[
        dict(title="How many can you defeat?", fns=["max"], body="""
<p>Return the maximum number of monsters the wizard can defeat. A set of days is feasible if, for every day <code>d</code>, the total spent on days 0…d is at most <code>10 × (d + 1)</code>. <code>1 ≤ n ≤ 20</code>.</p>
<p>Example: <code>[5, 25, 5]</code> → 2 (days 0 and 2).</p>"""),
        dict(title="Which days, exactly?", fns=["days"], body=q("Interviewer", "Now tell me which days. There can be several answers, so here's how to pick.") + """
<p>Return the days (0-based, ascending). Maximize the number defeated, then minimize total scrolls spent, then pick the lexicographically smallest list of days. <code>n ≤ 20</code>.</p>
<p>Example: <code>[10, 20, 30]</code> → <code>[0]</code>. Each of day 0, 1 or 2 alone is feasible; day 0 spends least.</p>"""),
        dict(title="200,000 days", fns=["big"], tag="extension", body=q("Interviewer", "Now n is up to 200,000. Just give me the count and the minimum spend for that count.") + """
<p>Return <code>[max count, minimum total scrolls among schedules with that count]</code>. <code>n ≤ 200,000</code>, costs ≤ 10,000.</p>
<p class="meta">Anything exponential, or quadratic, won't finish. What's true about the best set as you sweep forward in time?</p>"""),
        dict(title="Discussion", discussion=True, body="""
<ol>
<li>Prove your Part 3 algorithm is right. Why is dropping the most expensive monster the right move, and why does it also minimize the spend?</li>
<li>Does your Part 3 approach also give the lexicographically smallest days? If not, can you fix it cheaply?</li>
<li>Now the wizard must decide on the spot, without knowing future costs, and can't undo a decision. What's a reasonable policy, and how would you evaluate it?</li>
<li>Scrolls now expire after 3 days. What breaks?</li>
</ol>"""),
    ],
    clarify=[
        ("Can the wizard spend scrolls from future days?", "No. Spending through day d can't exceed what has arrived by then, 10 × (d + 1)."),
        ("Is defeating a monster optional?", "Yes, skipping is always allowed."),
        ("In Part 2, what does lexicographically smallest mean for lists of the same length?", "Compare element by element; the first smaller day wins. [0, 2] beats [1, 2]."),
        ("How large can n get?", "20 for Parts 1–2. Part 3 goes to 200,000; ask what that rules out."),
    ],
    nudges=[
        ("You're trying all subsets in Part 1", "That's fine for 20. Say the cost, then: what's the state if you go day by day?",
         "(day, scrolls in hand) is enough. Scrolls in hand are at most 10 × n, so a DP is O(n² × 10)."),
        ("Part 3: your solution is still a DP over scrolls", "With 200,000 days, how big is that table?",
         "Too big. Sweep days in order; tentatively take every monster; when you're over budget, drop the most expensive one taken so far. A max-heap makes it O(n log n)."),
        ("You claim the greedy is optimal without saying why", "Convince me.",
         "Exchange argument: any feasible set can be transformed into the greedy's set without losing count or adding cost. Dropping the most expensive monster frees the most budget for the future and lowers spend the most."),
    ],
    solution_notes="""
<div class="say"><span class="lbl">Part 1–2</span><p>"n is 20, so 2^20 subsets with an O(n) feasibility check works, about 20 million steps. A cleaner way: DP over (day, scrolls in hand). For the tie-break, I'll compare (count, −spend, days) carefully, because 'lexicographically smallest' needs the day lists compared in the right direction."</p></div>
<div class="say"><span class="lbl">Part 3</span><p>"Sweep forward. Take every monster; if spend exceeds 10 × (d + 1), give back the most expensive one taken so far, with a max-heap. Each monster is pushed and popped at most once: O(n log n). Why it's right: giving back the priciest one keeps the count, and it frees the most budget for later, and it minimizes spend among sets of that size."</p></div>""",
    discussion_answers="""
<ol>
<li>Invariant: after day d, the heap holds a maximum-size feasible set for days 0…d with minimum spend. When adding today's monster breaks the budget, exactly one must go, and removing the most expensive one keeps the size and leaves the cheapest possible spend (and prefix constraints only get easier).</li>
<li>Not necessarily: among equal-cost sets it doesn't control which days are used. Fix: break heap ties by preferring to drop the later day, or run the exact DP on the instances where ties matter.</li>
<li>Online, irrevocable: a threshold policy (accept if cost ≤ some multiple of the daily income and you keep a reserve), evaluated by competitive ratio against the offline optimum, or by simulation over a cost distribution.</li>
<li>Expiry turns budget into per-day buckets with deadlines; a heap of costs isn't enough. It becomes a flow or matching problem: scrolls from day j can pay for monsters on days j…j+2.</li>
</ol>""",
)
WIZARD["tests"] = fill([
    T(1, "example: two of three", "max", [5, 25, 5]),
    T(1, "example: only one", "max", [10, 20, 30]),
    T(1, "all cheap", "max", [1, 1, 1, 1]),
    T(1, "saving up pays off", "max", [11, 11, 11, 1]),
    T(1, "single day too expensive", "max", [11]),
    *_wiz_random(1, "max", 6, 5, 6, 16),
    T(2, "example: skip the big one", "days", [5, 25, 5]),
    T(2, "example: tie on count, least spend", "days", [10, 20, 30]),
    T(2, "tie on count and spend: smallest days", "days", [10, 10, 10, 30]),
    T(2, "nothing affordable", "days", [11]),
    T(2, "save for a late monster", "days", [10, 30, 1, 1]),
    *_wiz_random(2, "days", 8, 17, 8, 16),
    T(3, "example", "big", [5, 25, 5]),
    T(3, "small random", "big", [7, 19, 3, 25, 9, 14, 30, 2, 11, 6]),
    T(3, "200,000 days, cheap monsters", "big", ints(200000, 12345, 1, 20)),
    T(3, "200,000 days, mixed costs", "big", ints(200000, 777, 1, 10000)),
    T(3, "100,000 days, all exactly 10", "big", ints(100000, 1, 10, 10)),
], {"max": refs.max_monsters, "days": refs.choose_monster_days, "big": refs.max_monsters_and_cost})


# =====================================================================
# 6. Spaceship Loadout
# =====================================================================
_HZ = ["pirates", "debris", "asteroids", "radiation", "ion storm", "solar flare", "mines", "boarding", "cold", "heat", "dust", "gravity"]


def _load_random(part, fn, count, seed, n_lo, n_hi):
    r = random.Random(seed)
    out = []
    for i in range(count):
        n = r.randint(n_lo, n_hi)
        hz = _HZ[:r.randint(3, 6)]
        prot = [r.sample(hz, r.randint(1, 3)) for _ in range(n)]
        w = [r.randint(1, 9) for _ in range(n)]
        runs = [r.sample(hz, r.randint(1, 3)) for _ in range(5)]
        cap = r.randint(5, 25)
        if fn == "opt":
            names = [f"item{j:02d}" for j in range(n)]
            r.shuffle(names)
            out.append(T(part, f"random, {n} items #{i + 1}", fn, cap, names, w, prot, runs))
        else:
            out.append(T(part, f"random, {n} items #{i + 1}", fn, cap, w, prot, runs))
    return out


LOADOUT = dict(
    id="loadout",
    title="Spaceship Loadout",
    tagline="Score a loadout → best loadout by brute force → 60 items with hazard masks",
    source="Reported Jane Street question (capacity-limited equipment, hazards, five test runs). Rewritten for practice; weights, scoring, tie-breaks and Part 3 are authored.",
    functions=[
        dict(key="score", py="mitigated_runs", js="mitigatedRuns", params=[("protections", "String[][]"), ("runs", "String[][]"), ("selected", "int[]")], ret="int"),
        dict(key="opt", py="optimize_loadout", js="optimizeLoadout", params=[("capacity", "int"), ("names", "String[]"), ("weights", "int[]"), ("protections", "String[][]"), ("runs", "String[][]")], ret="String[]"),
        dict(key="big", py="best_loadout_score", js="bestLoadoutScore", params=[("capacity", "int"), ("weights", "int[]"), ("protections", "String[][]"), ("runs", "String[][]")], ret="int[]"),
    ],
    intro=q("Interviewer", "A spaceship can carry equipment up to a weight capacity. Each item protects against some hazards. We've recorded five test runs, each a list of hazards hit."),
    parts=[
        dict(title="Score a loadout", fns=["score"], body="""
<p>Item <code>i</code> protects against the hazards in <code>protections[i]</code>. A run is <em>fully mitigated</em> if every hazard in it is covered by at least one selected item. Given the selected item indices, return how many runs are fully mitigated.</p>
<p>Example: protections <code>[["debris"], ["pirates"], ["asteroids"], ["debris", "pirates"]]</code>, selecting <code>[3]</code>: runs <code>[["pirates"], ["debris"], ["asteroids"], ["debris", "pirates"], ["pirates"]]</code> → 4.</p>"""),
        dict(title="Best loadout", fns=["opt"], body=q("Interviewer", "Now pick the loadout.") + """
<p>Choose items with total weight ≤ <code>capacity</code>. Maximize fully mitigated runs, then minimize total weight, then pick the lexicographically smallest <em>sorted</em> list of names (compare names one by one as strings; a shorter list that's a prefix of a longer one is smaller). Return that sorted list. <code>n ≤ 18</code>, exactly 5 runs.</p>
<p>Example: capacity 7, names <code>["Armor", "Laser", "Shield", "Net"]</code>, weights <code>[4, 3, 4, 2]</code>, protections and runs as above → <code>["Net", "Shield"]</code> (weight 6, all five runs).</p>"""),
        dict(title="Sixty items", fns=["big"], tag="extension", body=q("Interviewer", "The catalogue grew to 60 items. 2^60 is out. Just give me the best score and its weight.") + """
<p>Return <code>[max fully mitigated runs, minimum weight achieving it]</code> (weight 0 if the best is zero runs). <code>n ≤ 60</code>, still 5 runs, and the runs mention at most 12 distinct hazards. Items may protect against hazards no run has.</p>
<p class="meta">What's small in this problem now?</p>"""),
        dict(title="Discussion", discussion=True, body="""
<ol>
<li>Why do bitmasks help in Part 2, concretely? What's the cost per subset with and without them?</li>
<li>In Part 3 you search over hazard sets instead of item sets. When does that stop being a good idea?</li>
<li>The five runs are a <em>sample</em> of future hazards, not the future itself. How would you choose a loadout for the next 100 trips? What would you want more data on?</li>
<li>Weights become real numbers and capacity is huge. Which of your approaches still work?</li>
</ol>"""),
    ],
    clarify=[
        ("Can a run list the same hazard twice? Can an item?", "Treat them as sets. Duplicates don't matter."),
        ("Is selecting nothing allowed?", "Yes. If nothing fits or helps, the answer to Part 2 is <code>[]</code>."),
        ("For the name tie-break, sorted by what?", "Plain string order (ASCII). Sort the chosen names, then compare the lists element by element."),
        ("How many distinct hazards are there?", "Few in the runs: at most 12 in Part 3. That's the hint for the extension."),
    ],
    nudges=[
        ("Part 2: you rebuild sets for every subset", "How long does one subset check take?",
         "Turn each item and each run into a bitmask over hazards. Covering a run is <code>(run &amp; cover) == run</code>. Everything per subset becomes integer ops."),
        ("Part 3: you're trying to prune 2^60", "How many different <em>hazard coverages</em> can a loadout have?",
         "At most 2^12 = 4096. Compute the cheapest way to reach each coverage (a knapsack over masks), then check which runs each coverage satisfies."),
        ("Part 3: the cheapest exact coverage misses supersets", "Is covering exactly the hazards you need the only way?",
         "No: an item can cover extra hazards. Take the minimum over all supersets of a mask (a sum-over-subsets pass), or iterate over which runs you want covered."),
    ],
    solution_notes="""
<div class="say"><span class="lbl">Part 1–2</span><p>"Map every hazard in the runs to a bit. Each item is a mask; each run is a mask. A loadout's cover is the OR of its items, and a run is covered when run &amp; cover == run. Then n ≤ 18 is 262k subsets with cheap checks, and I keep the best by (−runs, weight, sorted names)."</p></div>
<div class="say"><span class="lbl">Part 3</span><p>"The item count grew, but the hazard count stayed small. So I flip the search: for each hazard mask, the cheapest set of items covering it. That's a 0/1 knapsack over 2^12 masks, 60 × 4096 steps. Then the min over supersets, and for each of the 32 subsets of runs, the cheapest cover of their union. Pick the best score, then the lowest weight."</p></div>""",
    discussion_answers="""
<ol>
<li>A subset check becomes a few ORs and ANDs on machine words instead of hashing strings: O(n + runs) word ops versus O(total hazards) set operations.</li>
<li>When distinct hazards grow (2^h states). With h ≈ 30 you'd use ILP or branch-and-bound set cover instead.</li>
<li>Estimate hazard frequencies (with uncertainty, since 5 runs is tiny), then maximize the expected number of mitigated trips. Ask about correlations between hazards and the cost of failure per hazard.</li>
<li>The mask DP stores min weight per mask, so real weights are fine. Weight-indexed knapsack tables (dp over capacity) would not be.</li>
</ol>""",
)
_P = [["debris"], ["pirates"], ["asteroids"], ["debris", "pirates"]]
_R = [["pirates"], ["debris"], ["asteroids"], ["debris", "pirates"], ["pirates"]]
LOADOUT["tests"] = fill([
    T(1, "example: Net alone", "score", _P, _R, [3]),
    T(1, "nothing selected", "score", _P, _R, []),
    T(1, "everything selected", "score", _P, _R, [0, 1, 2, 3]),
    T(1, "duplicate hazards in a run", "score", [["a"], ["b"]], [["a", "a"], ["a", "b"], ["b"], ["c"], ["a", "b", "a"]], [0, 1]),
    T(1, "item protects extra hazards", "score", [["a", "x", "y"]], [["a"], ["x"], ["z"], ["a", "y"], ["q"]], [0]),
    T(2, "example: Net + Shield", "opt", 7, ["Armor", "Laser", "Shield", "Net"], [4, 3, 4, 2], _P, _R),
    T(2, "example: C alone", "opt", 3, ["A", "B", "C"], [2, 2, 3], [["pirates"], ["debris"], ["pirates", "debris"]], [["pirates"], ["debris"], ["pirates", "debris"], ["asteroids"], ["pirates"]]),
    T(2, "nothing fits", "opt", 1, ["Big"], [5], [["a"]], [["a"], ["a"], ["a"], ["a"], ["a"]]),
    T(2, "tie on weight: smaller names win", "opt", 4, ["Zed", "Amp", "Kit"], [2, 2, 2], [["a"], ["a"], ["b"]], [["a"], ["b"], ["a", "b"], ["c"], ["a"]]),
    *_load_random(2, "opt", 6, 3, 8, 15),
    T(3, "example as a score", "big", 7, [4, 3, 4, 2], _P, _R),
    T(3, "zero runs possible", "big", 1, [5], [["a"]], [["a"], ["a"], ["a"], ["a"], ["a"]]),
    *_load_random(3, "big", 4, 8, 8, 14),
    T(3, "60 items, 12 hazards", "big", 40, ints(60, 4242, 1, 20), hazard_sets(60, 99, _HZ, 4),
      [["pirates", "debris", "mines"], ["asteroids", "cold"], ["radiation", "heat", "dust"], ["ion storm", "solar flare", "boarding", "gravity"], ["pirates", "cold", "heat"]]),
    T(3, "60 items, tight capacity", "big", 15, ints(60, 31337, 1, 12), hazard_sets(60, 7, _HZ, 3),
      [["pirates", "gravity"], ["asteroids", "dust", "mines"], ["radiation"], ["ion storm", "heat", "debris", "cold"], ["solar flare", "boarding"]]),
], {"score": refs.mitigated_runs, "opt": refs.optimize_loadout, "big": refs.best_loadout_score})


# =====================================================================
# 7. Modified Dice
# =====================================================================
_STD = [[1, 2, 3, 4, 5, 6]] * 10
_MOD = [[1, 1, 3, 4, 5, 6], [1, 2, 2, 4, 5, 6], [1, 2, 3, 3, 5, 6], [1, 2, 3, 4, 4, 6], [1, 2, 3, 4, 5, 5],
        [2, 2, 3, 4, 5, 6], [1, 3, 3, 4, 5, 6], [1, 2, 4, 4, 5, 6], [1, 2, 3, 5, 5, 6], [1, 2, 3, 4, 6, 6]]
_BIG = [[10 ** 6, -10 ** 6, 999999, -999999, 123456, -7], [10 ** 6] * 6, [-10 ** 6, 10 ** 6, 0, 0, 0, 1], [1, 2, 3, 4, 5, 6],
        [500000, 500001, -3, 8, 0, 999998], [7] * 6, [-1, -2, -3, -4, -5, -6], [0, 0, 0, 0, 0, 10 ** 6], [2, 4, 8, 16, 32, 64], [999999] * 5 + [-10 ** 6]]
_SMALL = [[-20, 20, 0, 5, 5, 6], [1, 2, 3, 4, 5, 6], [3, 3, 4, 4, 5, 5], [-5, 0, 0, 10, 10, 10], [6, 6, 6, 1, 1, 1],
          [2, 3, 5, 7, 11, 13], [0, 0, 0, 0, 0, 20], [-1, 1, -1, 1, -1, 8], [4, 4, 4, 4, 4, 4], [1, 1, 1, 1, 1, 20]]
DICE = dict(
    id="dice",
    title="Modified Dice",
    tagline="Exact expectations → variance → exact probability of profit",
    source="Reported Jane Street question (ten modified dice, 100 rolls, an entry fee of 350, exact expected value). Rewritten for practice; Parts 2–3 are extensions.",
    functions=[
        dict(key="ev", py="modified_dice_expectations", js="modifiedDiceExpectations", params=[("dice", "int[][]"), ("roll_counts", "int[]")], ret="String[]"),
        dict(key="var", py="net_payout_variance", js="netPayoutVariance", params=[("dice", "int[][]"), ("roll_counts", "int[]")], ret="String"),
        dict(key="prob", py="probability_net_positive", js="probabilityNetPositive", params=[("dice", "int[][]"), ("roll_counts", "int[]")], ret="String"),
    ],
    intro=q("Interviewer", "Ten fair six-sided dice, each with its own face values. You roll die <code>i</code> exactly <code>roll_counts[i]</code> times, 100 rolls in total. You're paid the sum of all rolls and you pay a 350 entry fee."),
    parts=[
        dict(title="Expected values", fns=["ev"], body="""
<p>Return 11 reduced fractions as <code>"num/den"</code> strings: the expected face value of each die, in order, then the expected net payout (total minus 350). Denominators are positive; zero is <code>"0/1"</code>. Faces are integers in [−10⁶, 10⁶].</p>
<p>Example: ten standard dice, 10 rolls each → ten <code>"7/2"</code> and <code>"0/1"</code>.</p>"""),
        dict(title="How risky is it?", fns=["var"], tag="extension", body=q("Interviewer", "Expected value isn't the whole story. How spread out is the payout?") + """
<p>Return the variance of the net payout as a reduced fraction string. Same input limits: faces up to 10⁶ in absolute value.</p>
<p class="meta">Check your integer types against the largest values these inputs can produce.</p>"""),
        dict(title="Will you make money?", fns=["prob"], tag="extension", body=q("Interviewer", "Forget averages. What's the exact probability that I walk away with a profit?") + """
<p>Return the probability that the net payout is strictly positive (total &gt; 350), as an exact reduced fraction. For this part every face is in [−20, 20]. The denominator can be as large as 6¹⁰⁰.</p>
<p class="meta">What's the distribution of a sum of independent rolls, and how big does its support get?</p>"""),
        dict(title="Discussion", discussion=True, body="""
<ol>
<li>You can play once for 350. Would you? What if it cost your entire savings? What if you could play 1,000 times?</li>
<li>You get to choose the roll counts (still summing to 100). How do you maximize expected profit? Is that the same choice that maximizes the probability of profit?</li>
<li>Estimate Part 3's answer in your head with the central limit theorem. When is that estimate bad?</li>
<li>Someone offers to sell you this game for 340. How do you decide how much to buy, if you can buy fractions of it?</li>
</ol>"""),
    ],
    clarify=[
        ("Can faces be negative?", "Yes, in [−10⁶, 10⁶] for Parts 1–2, and [−20, 20] for Part 3."),
        ("Do dice with a roll count of 0 still need an expected value?", "Yes, all ten dice, in order."),
        ("Do you want decimals?", "No, exact reduced fractions. Floating point rounding is not acceptable."),
        ("Are the rolls independent?", "Yes. Worth saying why that matters for Part 2."),
    ],
    nudges=[
        ("You're about to enumerate outcomes for Part 1", "How many outcomes are there for 100 rolls?",
         "6^100. You don't need them: expectation is linear, so E[total] = Σ count_i × mean_i, whatever the dependence."),
        ("Part 2: you're using doubles", "What's the largest number your variance formula touches?",
         "Sums of squares of 10⁶ times 6 times 100 reach ~10¹⁵. Use exact integers: Java long, JS BigInt or careful Number, Python int."),
        ("Part 3: you're summing probabilities as floats", "The answer has a denominator of 6^100. Can a double represent that?",
         "No. Count ways with big integers: a DP over possible sums, adding one roll at a time. The sum range is only about −2000…2000, so it's 100 × 4000 × 6 big-integer additions."),
    ],
    solution_notes="""
<div class="say"><span class="lbl">Part 1</span><p>"Mean of a die is the sum of faces over 6. By linearity, the expected total is Σ count × mean; subtract 350. I'll do it with exact fractions: Python's Fraction, or numerator/denominator with gcd."</p></div>
<div class="say"><span class="lbl">Part 2</span><p>"Rolls are independent, so variances add: Var = Σ count × (E[X²] − E[X]²). The fee is a constant shift, so it doesn't change variance. The numbers get big, so I'll keep exact integers."</p></div>
<div class="say"><span class="lbl">Part 3</span><p>"The total is a sum of independent rolls, so its distribution is the convolution of each roll's distribution. I'll keep a map from sum to number of ways, apply one roll at a time (100 times), and count ways with total above 350. The answer is ways / 6^100, reduced. Big integers are required: 6^100 has 78 digits."</p></div>""",
    discussion_answers="""
<ol>
<li>One play: positive EV is necessary but not sufficient. Look at variance and the downside relative to your wealth (utility). With your whole savings, no unless the edge is enormous. With 1,000 plays, the law of large numbers makes a positive edge close to a sure profit.</li>
<li>Expected profit: put all 100 rolls on the die with the highest mean. Probability of profit can prefer a lower-variance die when the mean is barely above 3.5, or a higher-variance one when the mean is below the break-even. They're different objectives.</li>
<li>Total ≈ Normal(mean, variance). Bad in the tails, and with skewed faces, few rolls, or lattice effects at the boundary.</li>
<li>Kelly: with edge e and variance σ² per unit, bet a fraction ≈ e / σ² of your bankroll, less if you're unsure of your estimates.</li>
</ol>""",
)
DICE["tests"] = fill([
    T(1, "example: standard dice", "ev", _STD, [10] * 10),
    T(1, "example: only the first die", "ev", _MOD, [100] + [0] * 9),
    T(1, "spread across dice", "ev", _MOD, [5, 15, 10, 10, 10, 10, 10, 10, 10, 10]),
    T(1, "huge faces", "ev", _BIG, [10] * 10),
    T(1, "negative expectation", "ev", [[-6, -5, -4, -3, -2, -1]] * 10, [10] * 10),
    T(2, "standard dice", "var", _STD, [10] * 10),
    T(2, "constant dice have no variance", "var", [[4] * 6] * 10, [10] * 10),
    T(2, "modified dice", "var", _MOD, [5, 15, 10, 10, 10, 10, 10, 10, 10, 10]),
    T(2, "huge faces stress integer width", "var", _BIG, [10] * 10),
    T(2, "all rolls on the widest die", "var", _BIG, [100] + [0] * 9),
    T(3, "standard dice", "prob", _STD, [10] * 10),
    T(3, "constant dice: certain loss", "prob", [[3] * 6] * 10, [10] * 10),
    T(3, "constant dice: certain win", "prob", [[4] * 6] * 10, [10] * 10),
    T(3, "small faces, mixed counts", "prob", _SMALL, [20, 0, 10, 10, 10, 10, 10, 10, 10, 10]),
    T(3, "all rolls on one swingy die", "prob", _SMALL, [100] + [0] * 9),
], {"ev": refs.modified_dice_expectations, "var": refs.net_payout_variance, "prob": refs.probability_net_positive})


ALL = [STACK, ACCUM, FOLD, TOWERS, WIZARD, LOADOUT, DICE]
