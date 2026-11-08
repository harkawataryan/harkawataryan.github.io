"""Reference solutions for every practice-pad problem (Python).

These produce the expected outputs baked into the generated tests, and the
Python shown in each problem's Solution tab is taken from the SOLUTION
blocks below.
"""
from __future__ import annotations

import heapq
from fractions import Fraction
from math import gcd

# =====================================================================
# Stack Machine
# =====================================================================
# SOLUTION stack
def parse(instruction):
    """Split 'OP arg' on the first space only, so PUSH keeps its spaces."""
    op, _, arg = instruction.partition(" ")
    return op, arg


def step(stack, op, arg):
    """Apply one non-jump instruction. Returns the printed string or None."""
    if op == "PUSH":
        stack.append(arg)
    elif op == "POP":
        if stack:
            stack.pop()
    elif op == "PRINT":
        return stack[-1] if stack else ""
    elif op == "TRUNCATE":
        if stack:
            top = stack[-1]
            stack[-1] = top[:max(0, len(top) - int(arg))]
    return None


def next_pc(stack, pc, op, arg):
    if op == "JUMP":
        return int(arg)
    if op == "JUMP_IF_EMPTY" and (not stack or stack[-1] == ""):
        return int(arg)
    return pc + 1


def run_interpreter(instructions):
    stack, out, pc = [], [], 0
    while pc < len(instructions):
        op, arg = parse(instructions[pc])
        printed = step(stack, op, arg)
        if printed is not None:
            out.append(printed)
        pc = next_pc(stack, pc, op, arg)
    return out


def instrument_jumps(instructions):
    # new_start[i] = where original instruction i begins after rewriting.
    new_start, pos = [], 0
    for ins in instructions:
        new_start.append(pos)
        pos += 4 if parse(ins)[0] == "JUMP" else 1
    new_start.append(pos)                      # the end target

    out = []
    for i, ins in enumerate(instructions):
        op, arg = parse(ins)
        if op == "JUMP":
            out += [f"PUSH jump@{i}", "PRINT", "POP", f"JUMP {new_start[int(arg)]}"]
        elif op == "JUMP_IF_EMPTY":
            out.append(f"JUMP_IF_EMPTY {new_start[int(arg)]}")
        else:
            out.append(ins)
    return out


def trace_jumps(instructions, limit):
    # Record jumps from inside the interpreter instead of grepping printed
    # output: a program can print "jump@3" itself (in-band signalling).
    stack, pc, steps, trace = [], 0, 0, []
    seen = set()
    while pc < len(instructions):
        state = (pc, tuple(stack))
        if state in seen:
            return trace + ["LOOP"]
        seen.add(state)
        if steps == limit:
            return trace + ["LIMIT"]
        op, arg = parse(instructions[pc])
        if op == "JUMP":
            trace.append(str(pc))
        step(stack, op, arg)
        pc = next_pc(stack, pc, op, arg)
        steps += 1
    return trace
# END SOLUTION


# =====================================================================
# Accumulator VM
# =====================================================================
# SOLUTION accum
def run_program(memory, instructions):
    mem = list(memory)                     # never mutate the caller's list
    program = [(op, int(arg)) for op, arg in (s.split(" ") for s in instructions)]
    acc, pc = 0, 0
    while pc < len(program):
        op, x = program[pc]
        pc += 1
        if op == "LOAD":     acc = mem[x]
        elif op == "STORE":  mem[x] = acc
        elif op == "ADD":    acc += x
        elif op == "SUB":    acc -= x
        elif op == "MUL":    acc *= x
        elif op == "LOADI":  acc = mem[mem[x]]
        elif op == "STOREI": mem[mem[x]] = acc
        elif op == "JMP":    pc = x
        elif op == "JZ":     pc = x if acc == 0 else pc
        elif op == "JNEG":   pc = x if acc < 0 else pc
    return mem


def optimize(instructions):
    """Straight-line programs only. Fold arithmetic into affine form, drop
    dead loads/stores, repeat until nothing changes."""
    prog = list(instructions)
    while True:
        new = _dead_stores(_fold(prog))
        if new == prog:
            return new
        prog = new


def _fold(prog):
    out = []
    known = 0            # acc value if it's a known constant, else None
    same_as = set()      # cells whose value equals the emitted acc right now
    load = None          # pending LOAD not yet emitted
    a, b = 1, 0          # pending acc -> a*acc + b

    def emit(op, x):
        nonlocal known, same_as
        out.append(f"{op} {x}")
        if op != "STORE":
            same_as = set()

    def emit_affine(a, b):
        nonlocal known
        if (a, b) == (1, 0):
            return
        if known is not None:
            target = a * known + b
            if target != known:
                emit("ADD", target - known)
            known = target
        elif a == 0:
            emit("MUL", 0)
            if b:
                emit("ADD", b)
            known = b
        else:
            if a != 1:
                emit("MUL", a)
            if b:
                emit("ADD", b)

    def flush():
        nonlocal load, a, b, known, same_as
        if load is not None and a != 0:
            if load not in same_as:
                emit("LOAD", load)
                same_as = {load}
                known = None
            emit_affine(a, b)
        elif load is not None:             # MUL 0 made the load irrelevant
            emit_affine(0, b)
        else:
            emit_affine(a, b)
        load, a, b = None, 1, 0

    for s in prog:
        op, x = s.split(" ")
        x = int(x)
        if op == "LOAD":
            load, a, b = x, 1, 0
        elif op == "ADD":
            b += x
        elif op == "SUB":
            b -= x
        elif op == "MUL":
            a, b = a * x, b * x
        elif op == "STORE":
            flush()
            if x not in same_as:               # else the cell already holds acc
                out.append(f"STORE {x}")
                same_as.add(x)
    return out


def _dead_stores(prog):
    keep, overwritten = [], set()
    for s in reversed(prog):
        op, x = s.split(" ")
        x = int(x)
        if op == "STORE":
            if x in overwritten:
                continue
            overwritten.add(x)
        elif op == "LOAD":
            overwritten.discard(x)
        keep.append(s)
    keep.reverse()
    # arithmetic after the last STORE can't be observed
    while keep and keep[-1].split(" ")[0] != "STORE":
        keep.pop()
    return keep
# END SOLUTION


# =====================================================================
# Code Folding
# =====================================================================
# SOLUTION fold
class Editor:
    def __init__(self, lines):
        self.lines = lines
        self.match = {}                    # opening line -> closing line
        stack = []
        for i, line in enumerate(lines):
            text = line.rstrip(" \t")
            if text.endswith("{"):
                stack.append(i)
            elif text.endswith("}"):
                self.match[stack.pop()] = i
        self.folded = set()

    def toggle(self, i):
        self.folded ^= {i}

    def view(self):
        """[(original index, text)] of what's on screen."""
        rows, i = [], 0
        while i < len(self.lines):
            if i in self.folded:
                line = self.lines[i]
                rows.append((i, line[:line.rindex("{") + 1] + " ... }"))
                i = self.match[i] + 1      # skip everything inside, even if
            else:                          # inner blocks are expanded
                rows.append((i, self.lines[i]))
                i += 1
        return rows


def code_editor_operations(lines, operations):
    ed, out = Editor(lines), []
    for op in operations:
        name, *args = op.split(" ")
        if name == "MATCH":
            out.append([f"{o}:{c}" for o, c in sorted(ed.match.items())])
        elif name == "TOGGLE":
            ed.toggle(int(args[0]))
            out.append([])
        elif name == "GET":
            out.append([text for _, text in ed.view()])
        elif name == "TOGGLE_LINE":         # display index -> original index
            ed.toggle(ed.view()[int(args[0])][0])
            out.append([])
        elif name == "GET_RANGE":
            lo, hi = int(args[0]), int(args[1])
            out.append([text for _, text in ed.view()[lo:hi]])
    return out
# END SOLUTION


# =====================================================================
# Brick Towers
# =====================================================================
# SOLUTION towers
from dataclasses import dataclass, replace

ACTIONS = ["BUY", "LOAD", "MOVE_FAR", "MOVE_NEAR", "OBSERVE"]   # already sorted


@dataclass(frozen=True)
class Team:
    near: int = 5
    far: int = 0
    dollies: int = 0
    bricks: int = 0
    in_transit: int = 0      # committed by MOVE_FAR, lands next turn
    locked: bool = False

    def take_turn(self, action):
        if self.locked:                                  # action is ignored
            return replace(self, far=self.far + self.in_transit, in_transit=0, locked=False)
        if action == "BUY":
            return replace(self, dollies=self.dollies + 1)
        if action == "LOAD":
            return replace(self, bricks=self.bricks + self.dollies)
        if action == "MOVE_NEAR":
            return replace(self, near=self.near + self.bricks, bricks=0)
        if action == "MOVE_FAR":
            return replace(self, in_transit=self.bricks, bricks=0, locked=True)
        return self                                      # OBSERVE / WAIT


def beats(a, b):
    return a.near > b.far and a.far > b.near


def simulate_towers(west_actions, east_actions):
    w, e = Team(), Team()
    for day, (wa, ea) in enumerate(zip(west_actions, east_actions)):
        w = w.take_turn(wa)
        if beats(w, e):
            return day
        e = e.take_turn(ea)
        if beats(w, e):
            return day
    return -1


def _search(east_actions, day_limit):
    # BFS by day. Within a day, expand in lexicographic order; the first
    # schedule to reach a state is the lexicographically smallest one of
    # that length, so keeping only it is safe.
    layer = [(Team(), Team(), [])]
    for day in range(day_limit):
        nxt, seen = [], set()
        for w, e, path in layer:
            for action in (["WAIT"] if w.locked else ACTIONS):
                w2 = w.take_turn(action)
                if beats(w2, e):
                    return path + [action]
                e2 = e.take_turn(east_actions[day])
                if beats(w2, e2):
                    return path + [action]
                if (w2, e2) not in seen:
                    seen.add((w2, e2))
                    nxt.append((w2, e2, path + [action]))
        layer = nxt
    return []


def find_winning_tower_strategy(east_actions, day_limit):
    return _search(east_actions, day_limit)


def count_fastest_wins(east_actions, day_limit):
    # Same BFS, but instead of throwing duplicates away, merge them and add
    # up how many schedules reached each state.
    layer = {(Team(), Team()): 1}
    for day in range(day_limit):
        nxt, wins = {}, 0
        for (w, e), ways in layer.items():
            for action in (["WAIT"] if w.locked else ACTIONS):
                w2 = w.take_turn(action)
                e2 = e.take_turn(east_actions[day])
                if beats(w2, e) or beats(w2, e2):
                    wins += ways
                else:
                    nxt[(w2, e2)] = nxt.get((w2, e2), 0) + ways
        if wins:
            return wins
        layer = nxt
    return 0
# END SOLUTION


# =====================================================================
# Wizard Scrolls
# =====================================================================
# SOLUTION wizard
def max_monsters(costs):
    return max_monsters_and_cost(costs)[0]


def max_monsters_and_cost(costs):
    # Take every monster; whenever we're over budget, give back the most
    # expensive one taken so far. Exchange argument: dropping the priciest
    # keeps the count as high as possible and the spend as low as possible.
    taken, spent = [], 0                    # max-heap via negated costs
    for day, cost in enumerate(costs):
        heapq.heappush(taken, -cost)
        spent += cost
        if spent > 10 * (day + 1):
            spent += heapq.heappop(taken)
    return [len(taken), spent]


def choose_monster_days(costs):
    # best[d][r]: best (count, -spend, days) using days d.. with r scrolls in
    # hand at the start of day d (before that day's ten arrive).
    n = len(costs)
    cap = 10 * n
    best = [[None] * (cap + 1) for _ in range(n + 1)]
    for r in range(cap + 1):
        best[n][r] = (0, 0, ())
    for d in range(n - 1, -1, -1):
        for r in range(cap + 1):
            have = min(cap, r + 10)
            skip = best[d + 1][have]
            opts = [skip]
            if costs[d] <= have:
                c, neg, days = best[d + 1][have - costs[d]]
                opts.append((c + 1, neg - costs[d], (d,) + days))
            # more monsters, then less spend, then lexicographically smaller
            best[d][r] = max(opts, key=lambda t: (t[0], t[1], [-x for x in t[2]] + [float("inf")]))
    return list(best[0][0][2])
# END SOLUTION


def choose_monster_days_brute(costs):
    n = len(costs)
    best = None
    for mask in range(1 << n):
        days = [d for d in range(n) if mask >> d & 1]
        spent, ok = 0, True
        for d in range(n):
            if mask >> d & 1:
                spent += costs[d]
            if spent > 10 * (d + 1):
                ok = False
                break
        if not ok:
            continue
        key = (-len(days), spent, days)
        if best is None or key < best:
            best = key
    return best[2]


# =====================================================================
# Spaceship Loadout
# =====================================================================
# SOLUTION loadout
def mitigated_runs(protections, runs, selected):
    covered = set()
    for i in selected:
        covered |= set(protections[i])
    return sum(1 for run in runs if set(run) <= covered)


def optimize_loadout(capacity, names, weights, protections, runs):
    # Bitmask every hazard that appears in a run; ignore the rest.
    hazards = sorted({h for run in runs for h in run})
    bit = {h: 1 << i for i, h in enumerate(hazards)}
    item_mask = [sum(bit.get(h, 0) for h in set(p)) for p in protections]
    run_mask = [sum(bit[h] for h in set(run)) for run in runs]

    best = None
    n = len(names)
    for subset in range(1 << n):
        weight = cover = 0
        for i in range(n):
            if subset >> i & 1:
                weight += weights[i]
                cover |= item_mask[i]
        if weight > capacity:
            continue
        score = sum(1 for m in run_mask if m & cover == m)
        chosen = sorted(names[i] for i in range(n) if subset >> i & 1)
        key = (-score, weight, chosen)
        if best is None or key < best:
            best = key
    return best[2]


def best_loadout_score(capacity, weights, protections, runs):
    # Only 5 runs and few distinct hazards: search over hazard sets, not
    # item sets. cheapest[m] = min weight of items covering at least mask m.
    hazards = sorted({h for run in runs for h in run})
    bit = {h: 1 << i for i, h in enumerate(hazards)}
    full = 1 << len(hazards)
    INF = float("inf")
    exact = [INF] * full                     # cheapest with cover exactly m
    exact[0] = 0
    for w, p in zip(weights, protections):
        m_item = sum(bit.get(h, 0) for h in set(p))
        for m in range(full - 1, -1, -1):     # 0/1 knapsack order
            if exact[m] + w < exact[m | m_item]:
                exact[m | m_item] = exact[m] + w
    cheapest = exact[:]
    for b in range(len(hazards)):             # min over supersets
        for m in range(full):
            if not m >> b & 1 and cheapest[m | 1 << b] < cheapest[m]:
                cheapest[m] = cheapest[m | 1 << b]

    run_mask = [sum(bit[h] for h in set(run)) for run in runs]
    best = (0, 0)
    for chosen in range(1 << len(runs)):
        need = 0
        for r in range(len(runs)):
            if chosen >> r & 1:
                need |= run_mask[r]
        w = cheapest[need]
        if w > capacity:
            continue
        # every run covered by `need` counts, not only the chosen ones
        score = sum(1 for m in run_mask if m & need == m)
        if (score, -w) > (best[0], -best[1]):
            best = (score, w)
    return [best[0], best[1]]
# END SOLUTION


# =====================================================================
# Modified Dice
# =====================================================================
# SOLUTION dice
def frac(f: Fraction) -> str:
    return f"{f.numerator}/{f.denominator}"     # Fraction is always reduced


def modified_dice_expectations(dice, roll_counts):
    means = [Fraction(sum(faces), 6) for faces in dice]
    total = sum(c * m for c, m in zip(roll_counts, means))   # linearity
    return [frac(m) for m in means] + [frac(total - 350)]


def net_payout_variance(dice, roll_counts):
    # Rolls are independent, so variances add. The fee shifts, never spreads.
    var = Fraction(0)
    for faces, c in zip(dice, roll_counts):
        mean = Fraction(sum(faces), 6)
        var += c * (Fraction(sum(x * x for x in faces), 6) - mean * mean)
    return frac(var)


def probability_net_positive(dice, roll_counts):
    # ways[s] = number of the 6^k equally likely roll sequences so far
    # whose total is s. Exact integers, so the answer is exact.
    ways = {0: 1}
    for faces, c in zip(dice, roll_counts):
        face_count = {}
        for f in faces:
            face_count[f] = face_count.get(f, 0) + 1
        for _ in range(c):
            nxt = {}
            for s, w in ways.items():
                for f, k in face_count.items():
                    nxt[s + f] = nxt.get(s + f, 0) + w * k
            ways = nxt
    winning = sum(w for s, w in ways.items() if s > 350)
    return frac(Fraction(winning, 6 ** sum(roll_counts)))
# END SOLUTION
