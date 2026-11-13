"""Question bank, part A: the most-reported problems and the reported onsite problems.

Each entry: id, title, tagline, source, intro, parts [(title, html[, "talk"])],
clarify [(question, answer)], nudges [(if, interviewer says, what it means)],
solution (html). Statements are paraphrased from interview reports.
"""


def P(id, title, tagline, source, intro, parts, clarify=(), nudges=(), solution=""):
    return dict(id=id, title=title, tagline=tagline, source=source, intro=intro,
                parts=[dict(title=p[0], body=p[1], discussion=len(p) > 2 and p[2] == "talk") for p in parts],
                clarify=[list(c) for c in clarify], nudges=[list(n) for n in nudges], solution=solution)


def q(text):
    return f'<div class="quote"><span class="who">Interviewer</span>{text}</div>'


# =====================================================================
# Tier 1: most reported
# =====================================================================
STACK_INTERP = P(
    "stack-interpreter", "Stack-Based Interpreter",
    "Run instructions → conditional jumps → log every taken jump",
    "Reported 9 times in round one; also used onsite when it wasn't asked earlier.",
    q("Design an interpreter for a small stack language. A program is a list of instruction strings and the machine has one stack."),
    [
        ("Run it", """
<ul>
<li><code>PUSH x</code>: push <code>x</code>, an integer or a string.</li>
<li><code>POP</code>: remove the top value.</li>
<li><code>POP_AND_PRINT</code>: remove the top value and print it.</li>
<li><code>ADD</code>: pop two values and push their sum. Two integers add; if either is a string, convert both to strings and concatenate. The top of the stack is the <b>right</b> operand.</li>
<li><code>JUMP i</code>: continue at instruction <code>i</code>.</li>
</ul>
<p>Execution starts at index 0 and ends when the program counter runs past the last instruction.</p>
<p>Example: <code>PUSH 2, PUSH 3, ADD, POP_AND_PRINT</code> prints <code>5</code>. <code>PUSH "answer=", PUSH 42, ADD, POP_AND_PRINT</code> prints <code>answer=42</code>.</p>"""),
        ("Conditional jumps and errors", """
<p>Add <code>JNZ i</code>: look at the top value <b>without popping it</b>; if it is a nonzero integer, jump to <code>i</code>, otherwise continue.</p>
<p>Handle: popping an empty stack, an invalid jump target, a string where <code>JNZ</code> needs an integer, an unknown instruction, and programs that never halt.</p>"""),
        ("Debug every jump", q("We want to debug programs. Print <code>Jumping from X to Y</code> every time a jump is <b>taken</b>, using the original instruction numbers.") + """
<p>Some interviewers then add: do it by <b>rewriting the program</b> (inserting instructions) instead of changing the interpreter loop.</p>"""),
        ("Discussion", """
<ol><li>How do you detect an infinite loop? Is "I visited this index before" correct?</li>
<li>If you rewrite the program, why can't you print <i>before</i> a <code>JNZ</code>?</li>
<li>What changes if <code>JUMP</code> pops its target from the stack instead?</li></ol>""", "talk"),
    ],
    clarify=[
        ("Does JNZ pop the value it tests?", "No, it only peeks. (Some versions pop; always ask.)"),
        ("For ADD with a string, which operand comes first?", "The value below the top is the left operand: <code>PUSH \"a\", PUSH \"b\", ADD</code> gives <code>\"ab\"</code>."),
        ("Are jump indices 0-based? What happens on a bad target?", "0-based. A bad target is an error; raise or report it, your choice, but say which."),
        ("Do I return the printed output or print it?", "Either; returning a list of printed lines makes testing easier."),
    ],
    nudges=[
        ("You use a for loop over the instructions", "How does your loop handle a jump backwards?", "Jumps need full control of the program counter. Use <code>while pc &lt; len(program)</code> and let each instruction set the next pc."),
        ("Pop logic is repeated in POP, POP_AND_PRINT and ADD", "What happens on an empty stack in each of those?", "Centralize it: one <code>pop()</code> helper that validates. The postmortems call this out."),
        ("You detect loops with a visited set of indices", "Does this program loop forever? It revisits line 1 three times.", "Revisiting an index is normal in a loop. Use a step limit, or track the full state (pc plus whole stack)."),
        ("Your rewrite prints before JNZ", "What does JNZ see on top of the stack now?", "Pushing the message changes what JNZ tests. Let JNZ decide first and print only on the taken branch."),
    ],
    solution="""
<h3>Part 1</h3>
<p>Parse each line once into (opcode, argument). State is <code>pc</code> and a stack. Loop <code>while pc &lt; len(program)</code>; each handler sets the next pc (normally <code>pc + 1</code>). One <code>pop()</code> helper raises a clear error on an empty stack. For ADD, pop <code>right</code> then <code>left</code>; two ints add, otherwise <code>str(left) + str(right)</code>.</p>
<h3>Part 2</h3>
<p><code>JNZ</code> peeks: if the top is a nonzero int, jump; if it is a string, that's a type error. Guard infinite loops with a step limit (say 10,000). A visited-index set is wrong because loops legitimately revisit lines with a different stack; exact detection needs (pc, whole stack) and still misses loops whose stack grows.</p>
<h3>Part 3, the hard part</h3>
<p>Simple version: route every jump through one <code>jump(from, to)</code> helper that validates the target and prints the message. Then the follow-up is one line.</p>
<p>Rewrite version, two traps:</p>
<ul>
<li><b>Inserted lines shift every index.</b> First pass: compute <code>newStart[i]</code> for each old line (a JUMP becomes 3 lines: PUSH msg, POP_AND_PRINT, JUMP; a JNZ becomes 5). Second pass: emit, rewriting every target through <code>newStart</code>. Jumping to old line t lands at the start of t's block, so its print still runs.</li>
<li><b>JNZ must decide first.</b> Emit <code>JNZ s+2 / JUMP s+5 / PUSH msg / POP_AND_PRINT / JUMP newStart[t]</code>. JNZ peeks the real value; only the taken branch prints; the stack is unchanged afterwards.</li>
</ul>
<p>If JUMP pops its target at runtime, you can't know the target while rewriting; say so.</p>""",
)

CONNECT_K = P(
    "connect-k", "Infinite Connect-K",
    "Place pieces on an infinite board → K in a row → diagonals, or bottom insertion",
    "Reported 6 times in round one; graded on clean code, bugs and out-of-bounds awareness.",
    q("Two players drop pieces into columns of a board that extends infinitely left, right and up. Columns are any integer, including negative ones."),
    [
        ("Place a piece", "<p>Implement <code>move(player, column)</code>. Pieces fall to the lowest free row in that column. Players are <code>R</code> and <code>B</code>.</p>"),
        ("K in a row", "<p>The game is created with <code>k</code>. After a move, return the winning player if they now have <code>k</code> pieces in a row <b>horizontally or vertically</b>. If one move creates wins for both, the player who moved wins.</p>"),
        ("Diagonals", "<p>Also count diagonal lines of <code>k</code>.</p>"),
        ("Variant: bottom insertion (push-up)", """
<p>Reported variant: <code>place(column, player)</code> inserts at the <b>bottom</b> of the column and every existing piece in that column shifts up one row. Return <code>none</code>, either player, or <code>both</code>.</p>
<p>Example: before, row 1 is <code>R R . R</code> and row 0 is <code>. . R .</code>. Blue inserts at the bottom of column 2, so the R moves up and row 1 becomes <code>R R R R</code>: <b>Red wins although Blue moved.</b></p>"""),
    ],
    clarify=[
        ("How do I store an infinite board?", "Your choice. A map from column to a list of pieces is typical."),
        ("Is it at least k, or exactly k?", "At least k."),
        ("Who enforces turn order?", "The caller."),
    ],
    nudges=[
        ("You allocate a big 2D array", "What if someone plays column -1,000,000?", "The board is sparse and unbounded. Store <code>Map&lt;column, list&gt;</code>."),
        ("You scan the whole board after each move", "What could have changed after this move?", "Only lines through the new piece. Check 4 directions, counting both ways, capped at k-1 steps."),
        ("Bottom insertion: you only check the new piece", "Look at my example: who wins?", "Every piece in that column moved, so check runs through every cell of the modified column, for both players."),
    ],
    solution="""
<p><b>State:</b> <code>Map&lt;Integer, List&lt;Character&gt;&gt; columns</code>. Read with <code>getOrDefault</code> so probing an empty column doesn't create it.</p>
<p><b>Gravity move:</b> row = size of the column; append. Then for each direction (1,0), (0,1), (1,1), (1,-1): count matching pieces stepping forward and backward from (row, col); win if 1 + forward + backward ≥ k. Each move is O(k).</p>
<p><b>Cell lookup helper:</b> <code>get(row, col)</code> returns empty if the column is missing or the row is past its height. That single helper is your out-of-bounds safety.</p>
<p><b>Bottom insertion, the hard part:</b> inserting at index 0 shifts every piece in the column, so the "only check the new piece" invariant breaks. Any new run must pass through the modified column, so for each row of that column, check horizontal (and diagonal if needed) runs through that cell, plus the column's vertical runs, for both players. Return both if both win. Cost is O(height × k) per move. Use a deque per column for O(1) front insertion.</p>
<p><b>Test aloud:</b> negative columns, gaps between columns, k = 1, a run longer than k, and a push-up that hands the opponent a win.</p>""",
)

TETRIS = P(
    "tetris", "Tetris Engine",
    "Pieces, gravity, rotation, line clears → score and preview → pause, speed, undo",
    "Reported in round one and as a recurring onsite / final-round problem.",
    q("Build Tetris. The hardest decision is how to represent pieces so moving, rotating, locking and clearing lines stay simple."),
    [
        ("Core game", """
<ul><li>Pieces arrive one at a time and fall one row per timestep (say every second).</li>
<li>Support left, right and down moves, and clockwise / counterclockwise rotation. Reject moves that leave the board or overlap settled cells.</li>
<li>A piece that can't move down locks. Then remove every full row and shift every row above it down.</li>
<li>The game ends when a new piece can't spawn.</li></ul>"""),
        ("Score and display", "<p>Add 10 points per cleared line. One report adds a multiplier that grows when a placement clears a line and resets when it doesn't. Display the board and score after each input, and show the next piece.</p>"),
        ("Pause, speed, undo", "<ul><li>Pause and resume. Hide the board while paused. Only three pauses are allowed.</li><li>Increase the drop speed as the score increases.</li><li>Undo the last X locked pieces.</li></ul>"),
        ("Variant", "<p>One report: given a board and a piece, how far can the piece drop at a given horizontal offset? Then simulate the drop, then implement line clearing.</p>"),
    ],
    clarify=[
        ("Are there wall kicks on a blocked rotation?", "No. A blocked rotation is rejected."),
        ("Do several full rows clear at once?", "Yes."),
        ("Exactly how does the multiplier work?", "Your call; state it. A common reading: +1 per clearing placement, reset to 1 otherwise."),
        ("Where do pieces spawn?", "Top center."),
    ],
    nudges=[
        ("Your piece mutates, then you check validity and roll back", "What happens if the rotation is invalid halfway through?", "Build a candidate piece, check <code>board.fits(candidate)</code>, assign only if valid."),
        ("Pause/speed logic is inside Board", "Does the board need to know about time?", "Board = geometry. Game owns time, score, pause, undo and preview."),
        ("Undo replays from the start", "How expensive is undo after 500 pieces?", "Store a snapshot (or an inverse delta) per lock and pop X of them."),
    ],
    solution="""
<p><b>Three classes, strict ownership:</b> <code>Piece</code> = cell offsets inside an n×n box plus an origin, immutable (moved/rotated return new pieces). <code>Board</code> = settled cells; <code>fits</code>, <code>lock</code>, <code>clearFullRows</code>. <code>Game</code> = active piece, next piece, score, multiplier, pause state, history, tick.</p>
<p><b>Moves:</b> candidate = piece.moved(dr, dc) or piece.rotated(cw); if <code>board.fits</code>, assign. Rotation inside the box: clockwise (r, c) → (c, n−1−r); counterclockwise (r, c) → (n−1−c, r).</p>
<p><b>Down / tick:</b> if the piece can't move down: push a snapshot to history, lock, clear rows, score, spawn; if the spawn doesn't fit, game over.</p>
<p><b>Clearing:</b> keep rows that aren't full, prepend that many empty rows.</p>
<p><b>Part 3:</b> pause is a flag (render hides the board, tick and input are no-ops) plus a counter refusing the 4th pause. Speed: <code>interval = max(0.1, 1.0 − 0.1·(score / 100))</code>, read by <code>tick(now)</code>, with an injected clock. Undo X: pop X snapshots of (grid, score, multiplier, lines, active, next). The alternative to mention is an inverse delta per lock (cells written plus cleared rows), cheaper but harder to get right.</p>
<p><b>Drop distance variant:</b> step the piece down until it no longer fits, or per piece column compute the gap to the highest filled cell below it and take the minimum.</p>""",
)

VIRTUAL_DRIVE = P(
    "virtual-drive", "Virtual Drive with Parity",
    "Virtual → physical addresses → XOR parity recovery → async drives",
    "Reported as common onsite and in final-round lists; a firsthand onsite report.",
    q("Four physical drives A, B, C and P each hold 100 bytes. The virtual drive has capacity 300: virtual address 0 is A0, address 100 is B0, address 200 is C0. Drive P stores parity: <code>P[i] = A[i] ^ B[i] ^ C[i]</code>."),
    [
        ("Address mapping", "<p>Implement <code>read(virtualAddress)</code> and <code>write(virtualAddress, value)</code> on top of the physical drives. No error recovery yet.</p>"),
        ("Recover a failed drive", "<p>If one drive fails, reads must still work. Example: if B3 is lost, <code>B3 = A3 ^ C3 ^ P3</code>. Keep parity correct on every write.</p>"),
        ("Async physical drives", "<p>The physical drive API becomes asynchronous: <code>read(index, callback)</code> and <code>write(index, value, callback)</code>. Adapt Part 2.</p>"),
    ],
    clarify=[
        ("How do I know a drive failed?", "Assume each drive exposes <code>isFailed()</code>."),
        ("How many failures must we survive?", "One at a time."),
        ("What if the parity drive fails?", "Normal reads still work; you just lose the ability to recover."),
    ],
    nudges=[
        ("Your write updates data but not parity", "Read the parity after that write. Is it still correct?", "Parity must change with every data write: <code>newP = oldP ^ oldV ^ newV</code>."),
        ("Async: you call the client callback inside each sub-read", "How many times does the client hear back?", "Keep a per-request context with a remaining count; fire the callback exactly once when it hits zero."),
    ],
    solution="""
<p><b>Mapping:</b> <code>drive = addr / 100</code>, <code>local = addr % 100</code>. Validate 0 ≤ addr &lt; 300. The parity drive is never exposed as a virtual address.</p>
<p><b>Write:</b> read old value and old parity at <code>local</code>; write the new value; write <code>oldP ^ oldV ^ newV</code> to P. (Alternative: recompute parity from all three drives.)</p>
<p><b>Read:</b> if the target drive is healthy, read it. Otherwise XOR the parity with every surviving data drive at the same local index. Rebuilding a failed drive in place is a separate method.</p>
<p><b>Async, the hard part:</b> the synchronous return becomes a small state machine. For a recovered read, fan out reads to P and the surviving data drives into a context object <code>{values, remaining, done}</code>; each callback stores its value and decrements; at zero, XOR and call the client once. For a write: read old data and old parity (in parallel), then write both, then call <code>done()</code> after both writes finish. A sequential callback chain is fine as a first version; say that parallel fan-out is the optimization.</p>
<p><b>Discuss:</b> parity can recover a <i>known</i> missing value but can't tell you which drive is silently wrong (that needs checksums); concurrent writes to the same stripe need a lock per index.</p>""",
)

DISK_FS = P(
    "disk-filesystem", "Spinning-Disk File System",
    "Async reads and writes on a disk you can't seek → bucket requests by position",
    "Reported as common onsite.",
    q("You get a spinning disk: <code>Disk(size)</code>, <code>size()</code>, <code>position()</code>, and <code>read()</code> / <code>write(c)</code>, which act on the single byte under the head. You can't move the head; the disk rotates by itself and calls your <code>onSpin()</code> each time the head advances."),
    [
        ("Basic file system", "<p>Implement <code>write(filename, data)</code> and <code>read(filename)</code>. Both return immediately; the real work happens on later <code>onSpin()</code> calls. When a read finishes, call <code>reportReadComplete(filename, data)</code>. Files are stored contiguously, the first at position 0 and each next one right after the previous. Assume enough space.</p>"),
        ("Process spins", "<p>On each <code>onSpin()</code>, perform any pending write or read whose next needed byte is under the head.</p>"),
        ("Make onSpin fast", "<p>Scanning every pending request on every spin is O(requests). Make each spin cheap. Follow-ups: wraparound, deletion, overwrite, many readers of the same file.</p>"),
    ],
    clarify=[
        ("Can a read and a write need the same position on the same spin?", "Yes. Decide the order; processing writes first means the read sees the new data."),
        ("Can a read start before its file is fully written?", "Ask; a reasonable answer is that the read waits for the data it needs."),
        ("Duplicate filenames?", "Treat a second write as an overwrite, or reject it; say which."),
    ],
    nudges=[
        ("onSpin loops over every pending request", "With 10,000 pending reads, what does one spin cost?", "Index requests by the disk position they need next."),
        ("You busy-wait in read()", "What happens to the caller?", "read() must return immediately; completion is reported later from onSpin."),
    ],
    solution="""
<p><b>Metadata:</b> <code>directory: filename → (start, length)</code>, plus <code>nextFree</code> for contiguous allocation.</p>
<p><b>Requests:</b> a write request is (data, start, written); a read request is (filename, start, length, read, buffer). Invariant: next needed position = start + progress.</p>
<p><b>onSpin:</b> p = disk.position(). Handle the write waiting on p (write one byte, advance), then the reads waiting on p (read one byte, append, advance). A finished read calls <code>reportReadComplete</code>.</p>
<p><b>The optimization (the hard part):</b> bucket requests by the position they need next: <code>writesAt[pos]</code> (at most one, because allocations don't overlap) and <code>readsAt[pos]</code> (a list; many readers can wait on the same byte). After handling a request, move it to bucket pos + 1. Now a spin costs O(requests at this position).</p>
<p><b>Follow-ups:</b> wraparound uses <code>(start + offset) % size</code> but needs real free-space management; deletion needs a free list or interval set; fragmentation means a file might need to be split or space compacted.</p>""",
)

ARITH = P(
    "arithmetic-encoding", "Arithmetic Encoding",
    "Narrow an interval per symbol → decode → adaptive frequencies and precision",
    "Reported as common onsite and in final-round lists.",
    q("Compress a message into one number in [0, 1) using symbol frequencies, then decode it."),
    [
        ("Encode and decode", """
<p>Split [0, 1) into ranges proportional to each symbol's frequency, in a fixed symbol order. For each message symbol, narrow the current interval to that symbol's share of it. Output any number inside the final interval. To decode, you get the number, the frequency table and the message length.</p>
<p>Example with A:3, B:1: A owns [0, 0.75), B owns [0.75, 1). Encoding <code>AB</code> gives [0.5625, 0.75), so 0.625 is valid; decoding 0.625 with length 2 gives <code>AB</code>.</p>"""),
        ("Adaptive frequencies", "<p>Frequencies are not given up front; they update after every symbol. Support resetting them when they grow too large.</p>"),
        ("Discussion", "<ol><li>Why do doubles break on long messages?</li><li>How would a real encoder output bits as it goes?</li><li>How does the decoder know the frequencies in the adaptive version?</li></ol>", "talk"),
    ],
    clarify=[
        ("Is the message length given to the decoder?", "Yes, no end-of-message symbol needed."),
        ("Can I use exact fractions instead of doubles?", "Yes, and explain why."),
        ("Is every frequency positive?", "Yes in Part 1. In Part 2, start counts at 1."),
    ],
    nudges=[
        ("You build ranges by iterating a HashMap", "Will the decoder build the same ranges?", "Fix one symbol order (sorted keys) on both sides."),
        ("Encoder updates counts before coding the symbol", "When can the decoder update?", "Only after decoding the symbol. Code with the old counts, then update, on both sides."),
    ],
    solution="""
<p><b>Encode:</b> lo = 0, hi = 1. For each symbol: w = hi − lo; hi = lo + w·high(s); lo = lo + w·low(s) (both from the old lo). Output the midpoint. Invariant: after k symbols, [lo, hi) is exactly the interval of those k symbols.</p>
<p><b>Decode:</b> repeat <code>length</code> times: position = (value − lo) / (hi − lo); find the symbol whose [low, high) contains it; narrow exactly like the encoder. Half-open intervals mean a value on a boundary belongs to the upper symbol.</p>
<p><b>Why one number is enough:</b> every message of a given length gets a disjoint slice, and the slice's width is the message's probability, so the number needs about log₂(1/width) bits. Frequent symbols cost few bits.</p>
<p><b>Precision:</b> the width shrinks exponentially; doubles fail after about 50 symbols. Use exact fractions in the interview. Mention renormalization: keep integer lo/hi and emit settled top bits, shifting to regain precision (plus "pending bits" for the straddling case).</p>
<p><b>Adaptive, the hard part:</b> all counts start at 1. Code each symbol with the current counts, then increment. The decoder rebuilds the same model because it updates at the same moments with the same symbol order. Reset by halving all counts (keeping ≥ 1) when the total passes a threshold; both sides trigger it identically.</p>""",
)

SWIPE = P(
    "swipe-keyboard", "Swipe Keyboard",
    "Pick letters at key samples → top-k word probabilities → streaming samples",
    "Reported as common onsite and in a superday (round 3).",
    q("A swipe produces samples over time. Each sample maps letters to the area touched, for example <code>{a: 0.8, s: 0.2}</code>. A helper <code>is_vertex(prev, cur, next)</code> tells you whether the middle sample is a change of direction."),
    [
        ("Best guess", "<p>The important samples are the first, every direction change and the last. For each important sample pick the letter with the largest area; the letters in order form the word. A sample that is both first and last counts once.</p>"),
        ("Top guesses", """<p>Implement <code>SwipeKeyboard(maxGuesses)</code>, <code>addSample(sample)</code> and <code>wordGuesses()</code>. Normalize each important sample into probabilities; a word's probability is the product of its letters' probabilities. Return at most <code>maxGuesses</code> words, highest first, ties broken alphabetically. No dictionary.</p>
<p>Example: samples <code>{a: 0.8, b: 0.2}</code> and <code>{x: 0.6, y: 0.4}</code> give ax 0.48, ay 0.32, bx 0.12, by 0.08. With maxGuesses = 2: <code>ax, ay</code>.</p>"""),
        ("Streaming", "<p>More samples may arrive after <code>wordGuesses()</code> is called. A sample treated as the final endpoint for one query may stop being important once more samples arrive.</p>"),
    ],
    clarify=[
        ("Are areas already probabilities?", "No; normalize each sample by its total area."),
        ("Is there a dictionary?", "No."),
        ("Empty stream?", "Return no guesses."),
    ],
    nudges=[
        ("You enumerate every possible word", "How many words for 10 samples and 26 letters?", "Beam search: keep only the best k prefixes after each sample."),
        ("You append the last sample to your saved state on each query", "What if another sample arrives and the last one isn't a vertex?", "The endpoint is provisional. Extend a copy, never the committed state."),
    ],
    solution="""
<p><b>Part 1:</b> selected = first + vertices + last (once if n = 1); argmax per sample.</p>
<p><b>Top k:</b> beam = [("", 1)]. For each selected sample, extend every prefix by every letter, multiply probabilities, keep the top k (ties alphabetical). This is exact: if a top-k word's prefix fell out of the beam, k better prefixes extended with the same letter would give k better words.</p>
<p><b>Streaming, the hard part:</b> split committed and provisional state. A middle sample's status is only known when the next sample arrives, so on <code>addSample(s)</code>, check <code>is_vertex(prev2, prev1, s)</code> and, if true, extend the committed beam with prev1. The first sample is committed immediately. On <code>wordGuesses()</code>, take a copy of the committed beam, extend it with the current last sample (unless it is also the first), and return its top k. Never write that extension back.</p>
<p><b>Why:</b> samples a, b, then query → "ab". Then c arrives in a straight line, so b isn't a vertex; the answer must become "ac", not "abc".</p>""",
)

TREE_BROWSER = P(
    "tree-browser", "Tree Browser",
    "Select and deselect nodes → fast display → most valuable levels",
    "Reported 3 times in round one (also called Tree Backend).",
    q("You're given a tree with helpers <code>getParent</code>, <code>getChildren</code>, <code>getAncestors</code> and <code>getLevel</code>. The root is level 0."),
    [
        ("Display", "<p>Implement <code>select(node)</code>, <code>deselect(node)</code> and <code>display()</code>. Display returns every selected node, all of its ancestors, and all of its siblings, each once. Selecting a selected node or deselecting an unselected node does nothing. <code>display()</code> is called very often.</p>"),
        ("Deselect correctly", "<p>Removing one selection must not hide a node another selection still needs. Example: select two sibling leaves, then deselect one; it stays visible as the other's sibling.</p>"),
        ("Scores", "<p>Score each node: 3 if selected, plus 2 for each selected node it is an ancestor of, plus 1 for each selected node it is a sibling of. Implement <code>findMaxScoreRange(maxLevels)</code>: the block of <code>maxLevels</code> consecutive levels with the highest total score, as (startLevel, endLevel), earliest on ties.</p>"),
    ],
    clarify=[
        ("Does a node count as its own sibling?", "No. The root has no siblings."),
        ("Are scores summed, or does each node take its best rule?", "This version sums. Another reported version takes the max rule only; always ask."),
        ("Can maxLevels exceed the tree height?", "No."),
    ],
    nudges=[
        ("display() recomputes from all selected nodes", "display is called a thousand times per select. What does it cost?", "Move work to the updates: keep the visible set maintained."),
        ("You keep a visible boolean per node", "Select two siblings, deselect one. Is it still visible?", "Overlapping reasons. Use a reference count per node."),
    ],
    solution="""
<p><b>State:</b> <code>selected</code> set, <code>refCount: node → int</code>, <code>levelScore[]</code>.</p>
<p><b>select(n):</b> if already selected, return. Add it; increment refCount for n, each ancestor, and each sibling (parent's children minus n); add 3 to levelScore[level(n)], 2 at each ancestor's level, 1 at each sibling's level.</p>
<p><b>deselect(n):</b> the exact mirror; remove nodes whose count reaches 0.</p>
<p><b>display():</b> return the keys of refCount, so it's O(1) to hand back (or O(visible) to copy). Updates cost O(depth + siblings).</p>
<p><b>Best levels:</b> sliding window of width maxLevels over levelScore; take the earliest maximum. If it's queried after every update on a deep tree, a prefix-sum or segment tree makes it O(log H).</p>
<p><b>The point:</b> overlapping dependency closures. A boolean loses why a node is visible; counts keep it, and the same per-relationship counts power the scoring follow-up.</p>""",
)

MULTICACHE = P(
    "multicache", "Cache Proxy / MultiCache",
    "Hit or fetch → async out-of-order responses → keep put order",
    "Reported 3 times in round one; a firsthand onsite report (cache producer/consumer).",
    q("A cache already exists with <code>get(key)</code> and <code>put(key, value)</code>. You also get <code>requestFromRemote(key)</code> and <code>publish(key, value)</code>. Build the proxy clients talk to."),
    [
        ("Hit or fetch", "<p>Implement <code>get(key)</code> and <code>receiveFromRemote(key, value)</code>. On a hit, publish immediately. On a miss, request from the remote; when the response arrives, put it in the cache and publish.</p>"),
        ("Async responses", "<p>Responses arrive later and possibly out of order. Several clients may ask for the same missing key while it is in flight; send only one remote request and answer all of them.</p>"),
        ("Order matters", "<p>The cache's eviction policy depends on put order (for example FIFO). Requests for foo then bar may come back as bar then foo, but the cache must receive puts in request order: foo, then bar.</p>"),
        ("MultiCache variant", "<p>Put a coordinator in front of <b>two</b> black-box caches with different eviction policies. A query that hits either is served; a double miss fetches remotely. Follow-ups: register demand for slow keys before the value arrives; the two caches share a fixed total capacity with <code>resize(c1, c2)</code>, so tune the split to maximize hit rate.</p>"),
    ],
    clarify=[
        ("Must publish order follow request order, or arrival order?", "Ask. In Part 3 the cache's put order must follow request order."),
        ("Can the remote fail or time out?", "Discuss it; the basic version assumes it always answers."),
        ("Is anything multithreaded?", "Callbacks may come from another thread; say what you'd lock."),
    ],
    nudges=[
        ("Two misses for the same key send two requests", "100 clients ask for the same cold key at once. What does the remote see?", "Coalesce: <code>inflight: key → list of waiters</code>; only the first miss sends a request."),
        ("Part 3: you put into the cache as responses arrive", "Requests foo, bar; responses bar, foo. What's the put order?", "Number each miss and drain completed responses in sequence order (a reorder buffer)."),
    ],
    solution="""
<p><b>Part 1:</b> hit → publish; miss → requestFromRemote. receiveFromRemote → put, publish.</p>
<p><b>Part 2:</b> <code>inflight: key → waiters</code>. The first miss creates the entry and sends the request; later misses append. On the response: put, publish to each waiter, then remove the entry. Remove it at a point that can't race with a new miss (under the same lock), or a waiter gets lost.</p>
<p><b>Part 3, the hard part:</b> assign each miss a monotonically increasing sequence number and keep <code>nextToApply</code>. On a response, store it in <code>completed[seq]</code>; then <code>while completed has nextToApply</code>: put, publish, increment. Out-of-order arrivals wait in the buffer, so the cache always sees request order. This is the same reorder buffer TCP and video players use.</p>
<p><b>MultiCache notes:</b> you can't see inside the black boxes, so say what's impossible (for example "touching" a key in a cache that has no such API). Resizing is a feedback controller: track per-cache hits and unique wins over a window and shift capacity with hysteresis, not on every miss.</p>""",
)

# =====================================================================
# Tier 2: reported onsite
# =====================================================================
LAYERED = P(
    "layered-interpolation", "Layered Interpolation",
    "Priority layers → nearest-neighbor lookup → merged interpolation with updates",
    "Reported onsite; four variants share the same core. Also listed as Layered Nearest Neighbor in a final round.",
    q("You have layers ordered from highest to lowest priority. Each layer is a sparse map from position to value, like readings from sensors trusted to different degrees."),
    [
        ("Nearest neighbor", "<p>For a query <code>x</code>, scan layers from the top. In the first layer that has any points: an exact point at x wins; otherwise use the nearest key on either side; if only one side exists use it; on equal distance pick the left. Empty layers fall through to the next. If every layer is empty, return none.</p>"),
        ("Merge and interpolate", "<p>Variant: at each position the highest-priority layer with a value wins. Between winning points, interpolate linearly. Preprocess so <code>get(x)</code> is O(1).</p>"),
        ("Updates", "<p>Support <code>set(layer, x, value)</code> (and removing a point) without rebuilding everything.</p>"),
    ],
    clarify=[
        ("Can a lower layer's exact hit beat a higher layer's nearby point?", "In the base version, no: the first non-empty layer answers. Confirm it; it's the main trap."),
        ("Outside every point's range?", "Ask: return none, or clamp to the end value."),
        ("Are positions integers in a fixed range?", "Ask; if yes, an array of answers gives O(1) get."),
    ],
    nudges=[
        ("You store each layer in a HashMap and scan it", "How do you find the nearest key quickly?", "A sorted map: floorKey and ceilingKey in O(log n)."),
        ("You store only the winning value per position", "Remove the top layer's point. What should show through?", "Keep every layer's value per position so removals reveal the layer below."),
        ("set() rebuilds the whole answer array", "Which answers can change after one point changes?", "Only the gap between the changed point's two neighbors."),
    ],
    solution="""
<p><b>Part 1:</b> each layer is a <code>TreeMap</code>. For each layer top-down: if empty, continue; left = floorKey(x), right = ceilingKey(x); exact hit wins; one side missing → the other; otherwise the closer, left on ties. O(L log K).</p>
<p><b>Part 2 state:</b> <code>byDay: position → TreeMap(layer → value)</code> (the winner is firstEntry), <code>effective: TreeMap(position → winning value)</code>, and optionally <code>answer[]</code>.</p>
<p><b>Why updates are local:</b> the answer at d depends only on the two effective points bracketing d. If the effective point at x changes, only days between <code>effective.lowerKey(x)</code> and <code>effective.higherKey(x)</code> change.</p>
<p><b>set:</b> update byDay[x]; new winner = firstEntry; if it equals effective[x], stop; otherwise set effective[x] and refill [lower, higher]. <b>remove:</b> delete from byDay[x]; if empty remove x from effective (two gaps merge), else the next layer's value is revealed; refill the bracketing gap.</p>
<p><b>Tradeoff to say:</b> a precomputed array gives O(1) get but updates cost the gap size; interpolating at query time from floorEntry/ceilingEntry gives O(log n) get and O(log n) updates. Pick by the read/write ratio.</p>""",
)

LEASE = P(
    "lease-manager", "Lease Manager",
    "Track leases with a single alarm → renewals → alive/stale callbacks",
    "Reported onsite (distributed-systems flavored round).",
    q("You get a <code>Clock</code> with <code>now()</code> and <code>setAlarm(time, callback)</code>. Only one alarm can be active; setting a new one replaces the old."),
    [
        ("Valid machines", """<p>Implement <code>requestLease(machineId, machineName, expiresAt)</code> and <code>allValidMachines()</code>. For a given machine id, the most recent request wins. A lease is valid while <code>expiresAt &gt; now</code>.</p>
<p>Timeline: at t=0 lease m1 (alpha, 10), m2 (beta, 20), m3 (gamma, 30): the alarm is at 10. At t=10 alpha expires, alarm moves to 20. At t=15 m1 renews as alpha2 until 25: the alarm stays at 20. At t=20 beta expires: valid = alpha2, gamma, alarm at 25. Then 25, 30, and no alarm.</p>"""),
        ("Membership callbacks", "<p>Call <code>onMemberAlive</code> and <code>onMemberStale</code> on every transition. Renewing into the past makes a member stale immediately. Lookup by id must be O(1).</p>"),
    ],
    clarify=[
        ("Can a renewal shorten a lease?", "Yes, the most recent request wins."),
        ("Is a lease expiring exactly at now valid?", "No; valid means expiresAt &gt; now."),
        ("Key by id or name?", "By id. The name can change (alpha → alpha2)."),
    ],
    nudges=[
        ("A renewal leaves the old heap entry", "The old entry fires at 10 but the lease now ends at 25. What happens?", "Lazy deletion: a heap entry is live only if it still matches the map."),
        ("You call the global clock directly", "How would you test this?", "Inject the Clock (dependency injection) so tests can fake time."),
    ],
    solution="""
<p><b>State:</b> <code>leases: id → (name, expiresAt)</code> (source of truth), a min-heap of <code>(expiresAt, id)</code> that may hold stale entries, and <code>alarmAt</code>.</p>
<p><b>request:</b> if expiresAt ≤ now, drop the lease (most recent wins). Otherwise store it, push to the heap, and if alarmAt is unset or later than expiresAt, re-arm.</p>
<p><b>onAlarm:</b> pop every entry with time ≤ now; delete the lease only if the entry still matches the map. Then discard stale tops and arm for the earliest live entry, or none.</p>
<p><b>Invariant:</b> the alarm is always at the earliest live expiry. Extensions leave stale early entries, which fire harmlessly and re-arm; shortenings re-arm sooner.</p>
<p><b>Callbacks:</b> route every transition through <code>makeAlive</code> / <code>makeStale</code> helpers so a renewal of an alive member doesn't fire alive twice, and an old expiry never stales a renewed member. Keep an alive set for O(1) membership. The archived postmortem's mistakes: keying by name, no injected clock, stale heap entries, and mixing up creation with becoming alive.</p>""",
)

IMAGE_ENC = P(
    "image-encoder", "Image Encoder (Smart Pixels)",
    "RAW and REPEAT → RECENT references → decode one pixel without decoding everything",
    "Reported onsite and in a superday (round 1: encode, decode, random-access decode).",
    q("Compress an image given as a list of RGB values into one record per pixel."),
    [
        ("RAW and REPEAT", "<p><code>RAW(rgb)</code> stores a color; <code>REPEAT</code> means the same as the previous pixel. Use REPEAT for consecutive identical pixels.</p>"),
        ("RECENT", "<p>Add <code>RECENT(code)</code> with code 0 to 3: RECENT(0) refers to the pixel two back, RECENT(3) to five back. REPEAT and RECENT don't overlap. Prefer REPEAT, then any matching RECENT, otherwise RAW. Never reference before the start.</p><p>Example: <code>[R, B, G, B, R]</code> → <code>[RAW(R), RAW(B), RAW(G), RECENT(0), RECENT(2)]</code>.</p>"),
        ("Random access", "<p><code>decodePixel(encoded, index)</code> returns one pixel's color without decoding the whole image, following chains of REPEAT and RECENT.</p>"),
        ("Variant: move-to-front cache", "<p>Another version keeps a cache of the 5 most recently used <b>distinct</b> colors. A hit emits <code>(1, cacheIndex)</code>, a miss emits <code>(0, value)</code>; either way the color moves to the front and the oldest is evicted. Decode must keep the identical cache.</p>"),
    ],
    clarify=[
        ("Are RECENT offsets positions in the image or slots in a cache of distinct colors?", "Sources differ. Ask; it changes everything."),
        ("Does RGB equality need defining?", "Yes. Use a record or tuple with real equality."),
    ],
    nudges=[
        ("decodePixel decodes the prefix into a full image", "Can you avoid materializing every pixel?", "Each record points back by a fixed offset. Follow the pointers until you reach a RAW."),
        ("You special-case index 0", "Do you need to?", "A general 'never reference before the start' check covers it."),
    ],
    solution="""
<p><b>Encode (positional version):</b> for i, if i ≥ 1 and image[i−1] == image[i] emit REPEAT; else for k in 0..3, if i−2−k ≥ 0 and image[i−2−k] == image[i], emit RECENT(k); else RAW.</p>
<p><b>Random access:</b> j = index; while record j isn't RAW: j −= 1 for REPEAT, j −= 2 + k for RECENT(k). Return the RAW's color. Worst case O(index) for long chains; mention checkpoints (a RAW copy or a cached decode every K records) or memoization for repeated queries.</p>
<p><b>Move-to-front version:</b> the cache state is part of decoding, so random access is harder: replay from the start (or the nearest checkpoint storing the 5-entry cache). The clever approach from the reports walks backward tracking which cache slot holds the target color and how each earlier record permutes the slots, until a raw value resolves it.</p>
<p><b>Pitfalls from the postmortem:</b> mutating a list while iterating it, assuming color equality is defined, special-casing index 0, and not finishing random access.</p>""",
)

ETF = P(
    "etf-exposure", "ETF Exposure Calculator",
    "Total exposure through ETFs → sell to hit a target while disturbing others least",
    "Reported in round one and onsite (another report: first round of a superday).",
    q("You get ETF compositions (underlying shares per ETF share; SPY might hold 3 AAPL and 5 MSFT), stock prices, and your positions in stocks and ETFs."),
    [
        ("Exposure", "<p>Compute each underlying stock's total exposure from direct holdings plus ETF holdings, in shares and in dollars.</p><p>Example: positions 2 AAPL, 1 QQQ, 2 SPY, 3 MSFT; QQQ = 10 AAPL + 10 MSFT + 10 SNAP; SPY = 5 AAPL + 5 MSFT. Share exposure: AAPL 22, MSFT 23, SNAP 10.</p>"),
        ("Reduce exposure", "<p><code>minimizeExposure(symbol, targetExposure)</code>: return sales as (asset, negative quantity) pairs. Fractional shares allowed; only sales. Reach the target stock's dollar exposure while minimizing the total absolute change in dollar exposure to every <b>other</b> stock. Never sell more than you hold.</p>"),
    ],
    clarify=[
        ("Shares or dollars?", "Ask first. The reporter wasn't sure; the js version uses dollars."),
        ("Can ETFs contain ETFs?", "No, only stocks."),
        ("What if the target is unreachable?", "Targets lie between 0 and current exposure, but say what you'd return."),
    ],
    nudges=[
        ("You sell the ETF with the most of the target first", "What does selling QQQ do to SNAP?", "Collateral damage: selling the stock directly has zero side effects."),
        ("Greedy for a multi-asset objective", "Is greedy optimal here?", "With one target constraint and fractional assets, ratio greedy works; in general it's a linear program."),
    ],
    solution="""
<p><b>Exposure:</b> flatten every asset into an underlying vector (a stock is its own unit vector), multiply by the position and sum. Multiply by price for dollars.</p>
<p><b>Reduction:</b> let x_j be the shares of asset j sold, 0 ≤ x_j ≤ position_j. Each unit sold reduces the target by t_j dollars and other stocks by c_j collateral dollars.</p>
<ul><li>Sell the stock directly first: its collateral is zero.</li>
<li>Then sell ETFs in increasing order of collateral per dollar of target removed (c_j / t_j), fractionally, until the target is reached. With one constraint and an L1 objective that's linear in x, this ratio greedy is optimal (it's a fractional knapsack).</li></ul>
<p><b>Say out loud:</b> if the objective were total dollars sold instead, the ranking changes; in general (several targets, shorting, costs) formulate it as a linear program with auxiliary variables for absolute values.</p>""",
)

ARBITRAGE = P(
    "exchange-arbitrage", "Exchange Arbitrage",
    "Crossed markets between two exchanges → many exchanges at high update rates → fills and stale quotes",
    "Reported onsite (active exchange arbitrage) and in a superday (round 2).",
    q("Several exchanges trade one stock. Callbacks: <code>onTopOfBook(exchange, bid, ask)</code> and <code>onBookEmpty(exchange)</code>. You can call <code>sendOrder(exchange, side, price)</code>."),
    [
        ("Two exchanges", "<p>When you can buy on one exchange for less than you can sell on the other, do both. Example: exchange 1 bid 7 / ask 10, exchange 2 bid 11 / ask 13 → buy on 1 at 10, sell on 2 at 11.</p>"),
        ("Many exchanges", "<p>Support many exchanges (and instruments) at around a million updates per second.</p>"),
        ("Real trading", "<p>Handle fills, partial fills, fees, stale quotes and your own orders. Variant: quote passively on one exchange based on another's prices and cancel when the source moves.</p>"),
    ],
    clarify=[
        ("Are sizes given or only prices?", "Ask. If sizes exist, trade the smaller of the two."),
        ("Fees or minimum profit?", "Discuss; only trade if the spread beats them."),
        ("After onBookEmpty, which side is invalid?", "Both bid and ask."),
    ],
    nudges=[
        ("You rescan all exchanges on each update", "A million updates a second across 50 exchanges?", "Maintain indexed best bid and best ask (sorted structure or lazy heap)."),
        ("You fire again on the next update", "The quotes are still crossed. Do you send the same trade twice?", "Track outstanding orders; don't re-trade an opportunity you're acting on."),
    ],
    solution="""
<p><b>Two exchanges:</b> store (bid, ask, valid) per exchange; after each update check both directions.</p>
<p><b>Many exchanges:</b> keep a structure of bids (max first) and asks (min first) tagged by exchange. On an update, remove that exchange's old entries and insert the new ones, O(log E); or a heap with lazy deletion using a version number per exchange (discard tops whose version is stale). Check: best bid &gt; best ask (from different exchanges) and the gap beats fees. One structure per instrument.</p>
<p><b>Judgment calls:</b> quotes aren't fills, so leg risk (one side fills, the other doesn't) needs fill callbacks, cancels and a plan for leftover inventory. Don't double-fire; size to the smaller quote; filter your own orders out of market data in the quoting variant; cancel stale quotes when the source moves.</p>""",
)

SCHEMA = P(
    "schema-versioning", "Schema with Versioning",
    "Field offsets → insert and remove fields → objects keep their original schema",
    "Reported twice in round one (Memory Schema Allocator).",
    q("An object layout is an ordered list of fields, each with a byte length, packed contiguously from offset 0 with no padding."),
    [
        ("Offsets", "<p>Implement <code>Schema(fields)</code>, <code>getOffset(name)</code>, <code>insert(name, length, index)</code> and <code>remove(name)</code>. Example: foo 3, bar 6, baz 2 → offsets 0, 3, 9. Insert qux (2 bytes) at index 1 → foo 0, qux 3, bar 5, baz 11. Invalid operations report an error.</p>"),
        ("Versioned objects", "<p><code>createObject()</code> ties a new object id to the current schema. Later schema changes must not change existing objects: <code>getOffset(objectId, name)</code> uses that object's original layout, and fields added later don't exist on it.</p>"),
        ("Nested layouts", "<p>Propose an API for nested layouts and explain how changes propagate.</p>", "talk"),
    ],
    clarify=[
        ("Are names unique? Sizes positive?", "Yes and yes."),
        ("Which is more frequent, lookups or updates?", "Ask; it decides the data structure."),
    ],
    nudges=[
        ("You copy the whole schema on every change", "A million objects and a thousand schema versions?", "Version the schema, not the objects: each object stores a version id."),
    ],
    solution="""
<p><b>Part 1:</b> store the ordered field list plus a name → index map; offsets are prefix sums. Recompute the suffix after an insert or remove in O(n − index), or cache the name → offset map and rebuild it lazily. If updates dominate, a Fenwick tree over sizes gives O(log n) offset queries and updates.</p>
<p><b>Part 2:</b> every insert/remove creates a new immutable schema version (copy-on-write; persistent structures can share unchanged parts). <code>createObject()</code> stores <code>objectId → versionId</code>. <code>getOffset(objectId, name)</code> looks up that version's offset map; a field missing in that version is an error. Cache each version's offset map since versions never change.</p>
<p><b>Follow-ups:</b> lazy migration (move an old object to the current layout when it's touched, then bump its version); nested layouts as a field whose type is another schema, so a nested change creates a new parent version too.</p>""",
)

MARKETPLACE = P(
    "marketplace", "Buyer Marketplace and Rollback",
    "Match buyers to the cheapest offer → cancel a buyer and re-match as if they never existed",
    "Reported in round one; a personal report of the same question.",
    q("Each listing is one unit of an item at a price."),
    [
        ("Buy and sell", "<p><code>sell(item, sellerId, price)</code> lists a unit. <code>buy(buyerId, items, maxPrice)</code>: for each item, buy the cheapest listing at or under maxPrice and skip items with none. Equal prices fill in listing order. Return item → (seller, price).</p>"),
        ("Rollback", "<p><code>cancelUserPurchases(buyer)</code>: undo that buyer's purchases and re-match everything as if their buy requests never happened. Other buyers may get cheaper offers; buyers who failed may now succeed. Keep the cancelled buyer's sell offers. Return each buyer's refund = old total paid − new total paid (a new payment is negative).</p><p>Example: monitors at 80 then 100. A (max 90) gets 80; B (max 120) gets 100; C (max 110) gets nothing. Cancel A: B gets 80, C gets 100. Refunds A +80, B +20, C −100.</p>"),
    ],
    clarify=[
        ("Buyer priority during re-matching?", "Original request order."),
        ("Are items in one request independent?", "Yes; some may succeed while others fail."),
        ("Heaps allowed?", "One report banned them; then keep listings sorted per item."),
    ],
    nudges=[
        ("Rollback puts A's items back and stops", "Who should own the $80 monitor now?", "Changes cascade. Replay history without the cancelled buyer."),
        ("Your log only has successful purchases", "How does C succeed on replay?", "Log every request, including failures."),
    ],
    solution="""
<p><b>Part 1:</b> per item, a heap of (price, seq, seller). buy: peek; if within maxPrice, poll.</p>
<p><b>What Part 2 needs from Part 1:</b> an ordered log of every sell and buy (failed buys included), and <code>paid[item][buyer]</code>.</p>
<p><b>Cancel:</b> (1) affected items = items the cancelled buyer bought; (2) remove their buy events from the log; (3) for each affected item, rebuild a fresh heap by replaying the log in order (sells add listings, buys run the same <code>tryBuy</code> rule); (4) refund = old paid − new paid per buyer; (5) swap in the rebuilt state. Replaying sells and buys together matters: a buyer can only get listings that existed when they arrived.</p>
<p><b>Why it's correct:</b> it reuses the exact matching rule, so cascades are handled automatically, and unaffected items are never touched.</p>""",
)

FUZZY = P(
    "fuzzy-find", "Fuzzy Find UI",
    "Filter and render → selection and scrolling → minimal redraws",
    "Reported onsite; also seen as Command Line Parser / URL bar.",
    q("You get a fixed-size screen with <code>getWidth()</code>, <code>getHeight()</code>, <code>moveCursorToPosition(x, y)</code> and <code>draw(char)</code> (which draws and moves right), plus a list of choices."),
    [
        ("Filter and render", "<p><code>query(q)</code> filters the choices and redraws. Matching is case-insensitive subsequence: <code>abc</code> matches <code>AxxByyC</code>. (The js version uses substring matching: <code>app</code> matches pineapple, happy, application, apple.) Keep the original order; the first match becomes selected; an empty query matches everything.</p>"),
        ("Select and scroll", "<p><code>moveSelection(up/down)</code> stops at the ends; highlight the selected row with a leading <code>&gt;</code>; <code>select()</code> returns the highlighted choice or none. Scroll when results don't fit; truncate long lines; never write outside the screen.</p>"),
        ("Fewer writes", "<p>Reduce the number of character writes when the query, selection or visible results change.</p>"),
    ],
    clarify=[
        ("Does selection wrap?", "No, it stops at the ends (some versions wrap; ask)."),
        ("Does the query use a screen row? Is the result count shown?", "Ask; a typical layout is results, then the query line and count."),
    ],
    nudges=[
        ("Selection moves off screen", "Press down 30 times on a 10-row screen.", "Keep the invariant scroll ≤ selected &lt; scroll + rows."),
        ("You clear and redraw everything on each key", "How many draw calls does moving the selection by one cost?", "Diff against the previous frame and write only changed cells (and blanks over stale text)."),
    ],
    solution="""
<p><b>State:</b> all choices, filtered list, selected index, scroll offset, current query, and the previous frame (a char grid).</p>
<p><b>Subsequence match:</b> one pointer through the choice, advancing the query pointer on a case-insensitive match.</p>
<p><b>query:</b> refilter, selected = 0, scroll = 0, render. <b>move:</b> clamp, then adjust scroll so the selection stays visible.</p>
<p><b>Render:</b> build the new frame in memory (rows clipped to width, marker on the selected row, padding with spaces so stale characters get overwritten), then compare to the previous frame and only move the cursor and draw where cells differ, coalescing runs so cursor moves are minimized. Moving the selection then costs about two rows of writes.</p>""",
)

TASK_ALLOC = P(
    "task-allocator", "Task Allocator",
    "Schedule a job's tasks onto nodes → completion callbacks → onJobFinish exactly once",
    "Reported once in round one / phone screen this cycle. The original API wasn't fully retained.",
    q("There are jobs made of tasks, and nodes that run tasks. A node calls you back when a task finishes."),
    [
        ("Schedule", "<p>Implement <code>TaskAllocator(nodes)</code> and <code>scheduleJob(job)</code>, which assigns the job's tasks to free nodes with <code>node.allocateTask(task)</code>. Tasks that can't be placed wait.</p>"),
        ("Complete", "<p>Implement <code>onTaskComplete(taskId)</code>: record the completion, give the freed node a waiting task, and call <code>onJobFinish(jobId)</code> when every task of a job is done. It must be safe to call twice.</p>"),
        ("Follow-ups", "<ul><li>A task can belong to several jobs.</li><li>Long-running tasks: run a task on several nodes and abort the others when one finishes (<code>abortTask</code>).</li><li>What if some tasks can never be allocated?</li></ul>"),
    ],
    clarify=[
        ("If a task belongs to two jobs, does it run once?", "Ask. The reported code runs it once and counts it for both."),
        ("Can onTaskComplete arrive twice, or for an unknown task?", "Yes; it must be idempotent."),
        ("Job with zero tasks?", "It finishes immediately."),
    ],
    nudges=[
        ("A shared task decrements a job twice", "Two jobs share task t. What does each job's counter do when t completes?", "Decrement each job once per distinct task, and finish each job exactly once (the reported bug: several jobs marked complete wrongly)."),
        ("A completed task is scheduled again by a new job", "Job 2 arrives after t already finished. What happens?", "Decide: re-run it, or count it as already done. Track completed tasks."),
    ],
    solution="""
<p><b>State:</b> free nodes (set), a FIFO of waiting task ids, <code>taskToJobs: task → set of jobs</code>, <code>remaining: job → count</code>, <code>running: task → node(s)</code>, <code>finished</code> jobs set.</p>
<p><b>scheduleJob:</b> remaining[job] = number of distinct tasks. For each task: add the job to taskToJobs; if the task is already running or waiting, don't start it twice; otherwise place it on a free node or enqueue it. A zero-task job finishes immediately.</p>
<p><b>onTaskComplete:</b> if the task isn't running, return (idempotent). Remove it from running; for each job in taskToJobs[task], decrement; at 0, if not already finished, mark finished and call onJobFinish once. Then hand the freed node the next waiting task, or mark it free.</p>
<p><b>Bugs in the reported code to spot:</b> an undefined variable in the decrement loop, a typo in the allocate call, and mixing Task objects with task ids as keys. Redundant execution: map task → every node running it; on the first completion, abort the rest and free those nodes.</p>""",
)

POTION = P(
    "potion-brewing", "Potion Brewing",
    "Which ingredients can increase → which can become infinite",
    "Reported onsite; rare but recurring. Only a short prompt was retained, so clarifying is part of the problem.",
    q("Starting ingredients are 26 counts, one per letter a to z. Spells convert some ingredients into other ingredients."),
    [
        ("Can increase", "<p>Given the starting counts and a list of spells, return which ingredients can be increased.</p>"),
        ("Can become infinite", "<p>Return which ingredients can become unbounded by applying spells repeatedly.</p>"),
    ],
    clarify=[
        ("What does a spell look like? Does it consume its inputs?", "Assume a spell consumes a multiset of inputs and produces a multiset of outputs, and can be cast any number of times while you have the inputs."),
        ("Can a spell take several different ingredients?", "Yes in the general version; that's what makes Part 2 hard."),
    ],
    nudges=[
        ("You mark every ingredient on a graph cycle as infinite", "a → b and b → a. Does anything grow?", "A cycle only grows if it nets a gain. Track quantities, not just reachability."),
    ],
    solution="""
<p><b>Model it first:</b> a spell is a vector of net changes (outputs − inputs) plus its input requirements.</p>
<p><b>Part 1:</b> compute which spells are castable: start with the ingredients you have; repeatedly mark a spell castable if all its inputs are available, which makes its outputs available (a fixed-point closure). An ingredient can increase if some castable spell has a positive net effect on it. State the simplification: this ignores exact quantities (you might be able to cast a spell only once).</p>
<p><b>Part 2:</b> an ingredient becomes infinite if some combination of castable spells, repeated, has a net change that is ≥ 0 for everything it consumes and &gt; 0 for that ingredient. Single-input spells form a graph with multipliers: a cycle whose product of yields exceeds 1 is a pump, and everything reachable from a pumped ingredient through castable spells is infinite too. With multi-input spells it becomes an integer linear program; say so.</p>
<p><b>Graded on:</b> turning the story into a precise model before choosing an algorithm, and not claiming every cycle is unbounded.</p>""",
)

SECRET_FS = P(
    "secret-filesystem", "Secret File System Finder",
    "Identify a hidden system with membership queries → minimize queries",
    "Reported onsite.",
    q("Each candidate file system is a set of files; a file can be in several systems. One system is secretly chosen. <code>isValid(file)</code> tells you whether a file belongs to the secret system."),
    [
        ("Identify it", "<p>Find the secret system. Handle edge cases.</p>"),
        ("Fewer queries", "<p>Queries are expensive. Minimize how many you make.</p>"),
    ],
    clarify=[
        ("Can two systems have identical file sets?", "Yes. Then no query can tell them apart; return the group or say it's impossible."),
        ("Is the file universe known up front?", "Yes."),
    ],
    nudges=[
        ("You test systems one by one", "With 1,000 systems, how many queries?", "Each query should split the remaining candidates as evenly as possible."),
    ],
    solution="""
<p><b>Part 1:</b> keep the set of still-possible systems. Pick a file that some but not all candidates contain, query it, and keep only the consistent candidates. Stop at one candidate, or when the remaining candidates are identical.</p>
<p><b>Part 2:</b> choose the file whose split is closest to half (maximum information), like binary search: about log₂(n) queries when good splits exist. Precompute file → candidates to evaluate splits quickly.</p>
<p><b>Say:</b> greedy balanced splitting isn't guaranteed optimal for arbitrary set systems; the exact minimum is a decision-tree optimization (exponential). Identical systems are observationally indistinguishable.</p>""",
)

MERKLE = P(
    "merkle-tree", "Merkle Tree",
    "Hash a tree → find a subtree → find what's missing on the server",
    "Reported onsite and as a phone question (node presence verification).",
    q("Each node's hash is <code>SHA256(value ‖ hash(left) ‖ hash(right))</code>, with empty strings for missing children."),
    [
        ("Build and verify", "<p>Represent an immutable tree with cached hashes. Given a client subtree, decide whether it appears in the server's canonical tree.</p>"),
        ("Find missing nodes", "<p>The client has node hashes; the server exposes <code>hasNode(hash)</code>. Return the client nodes missing on the server, with as few calls as possible.</p>"),
        ("Follow-ups", "<ul><li>Locate a single changed node.</li><li>Stream verification when the whole subtree can't be sent.</li><li>Hash collisions and malicious clients.</li></ul>", "talk"),
    ],
    clarify=[
        ("How are values and hashes combined?", "Ask; use an unambiguous encoding (length prefixes)."),
        ("Odd leaves (leaf-list version)?", "Duplicate the last leaf or promote it; ask."),
    ],
    nudges=[
        ("You check every client node", "If the server has the root hash, what do you know?", "A matching hash covers the whole subtree. Prune."),
    ],
    solution="""
<p><b>Hashing:</b> compute bottom-up and cache in each immutable node. Use length-prefixed fields so "ab"+"c" and "a"+"bc" don't collide.</p>
<p><b>Subtree lookup:</b> index server nodes by hash for expected O(1); optionally compare structure to guard against collisions.</p>
<p><b>Missing nodes:</b> top-down: if the server has a node's hash, the entire subtree is present, so stop; otherwise record it missing and recurse into the children. Calls are proportional to the changed region, about O(changes × depth).</p>
<p><b>Single change:</b> a change propagates to every ancestor, so compare corresponding hashes and descend only into the mismatching child: O(depth). Versions can share unchanged immutable subtrees.</p>""",
)

COPY_GC = P(
    "copying-gc", "Copying Garbage Collector",
    "Allocate on a heap → copy reachable objects to the other heap → fix every pointer",
    "Reported onsite.",
    q("You have two fixed-size heaps (arrays of words). An allocation is a size word followed by that many payload words. <code>getPointers()</code> returns the roots and <code>isPointer(...)</code> says whether a word is a reference."),
    [
        ("Allocate", "<p><code>allocate(numWords)</code>: if there's room, write the size header at nextFree, return the payload's start index, and advance nextFree.</p>"),
        ("Collect", "<p>Copy every reachable allocation to the backup heap, rewrite every pointer to the new addresses, discard unreachable data, swap the heaps and reset nextFree.</p>"),
    ],
    clarify=[
        ("Does a pointer address the header or the payload?", "Ask; be precise either way."),
        ("Can objects form cycles or be shared?", "Yes."),
    ],
    nudges=[
        ("You copy an object every time you see a pointer to it", "Two pointers to the same object, or a cycle?", "A forwarding map old → new: copy once, reuse after."),
        ("You forget the roots", "After the swap, what do the roots point to?", "Update the roots too."),
    ],
    solution="""
<p><b>Allocate:</b> check nextFree + 1 + n ≤ heapSize; write n at nextFree; return nextFree + 1; advance.</p>
<p><b>Collect (Cheney):</b> forwarding map old → new. Copy each root's object to to-space (once) and update the root. Then scan to-space with a scan pointer: for each word of each copied object that is a pointer, copy its target if not yet copied (append at the free pointer) and rewrite the word to the new address. The to-space itself is the BFS queue, so no recursion. When scan meets free, everything reachable is copied; swap heaps; nextFree = free.</p>
<p><b>Why the forwarding map matters:</b> it prevents duplicate copies, handles cycles, and is the address translation table.</p>""",
)

TIER1 = [STACK_INTERP, CONNECT_K, TETRIS, VIRTUAL_DRIVE, DISK_FS, ARITH, SWIPE, TREE_BROWSER, MULTICACHE]
TIER2 = [LAYERED, LEASE, IMAGE_ENC, ETF, ARBITRAGE, SCHEMA, MARKETPLACE, FUZZY, TASK_ALLOC, POTION, SECRET_FS, MERKLE, COPY_GC]
