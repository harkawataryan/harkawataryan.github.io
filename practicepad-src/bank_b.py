"""Question bank, part B: other reported questions."""
from bank_a import P, q

SNAKE = P(
    "snake", "Snake",
    "Move and grow → self-collision and walls → timing and input",
    "Reported in round one.",
    q("Run Snake on an M × N grid. The snake moves one cell per step, grows by one when it eats an apple, and the score is the number of apples eaten."),
    [
        ("Move", "<p><code>Snake(rows, cols, initialBody, direction, apples)</code>, <code>step(direction)</code>, <code>getState()</code>. Crossing a wall loses. A direct reversal is invalid when the snake is longer than 1. Steps after game over change nothing. Apples don't respawn.</p>"),
        ("Grow and collide", "<p>Eating an apple grows the snake. Hitting its own body loses, but on a non-eating move the tail leaves its cell, so moving into it is legal.</p>"),
        ("Timing", "<p>The snake moves every second while input is read every 0.1 seconds. Keep input and timing out of the core logic.</p>"),
        ("Pathfinding follow-up", "<p>Find the best path to an apple. Ask whether that means the fewest moves to one apple or the most apples overall.</p>", "talk"),
    ],
    clarify=[("Walls or wrap-around?", "Walls in this version; another report wraps. Ask."), ("Reversal: ignore or reject?", "Ask; ignoring it (keep the current direction) is common.")],
    nudges=[("You check collision before removing the tail", "The snake moves into the cell its tail is leaving. Dead?", "On a non-eating move, remove the tail first, then check.")],
    solution="""
<p><b>State:</b> a deque of body cells (head first) plus a set of occupied cells, kept in sync on every path; direction, apples, score, gameOver.</p>
<p><b>step:</b> ignore a reversal if length &gt; 1; compute the new head; off the grid → game over; eating = head in apples; if not eating, pop the tail and remove it from the set <i>before</i> the collision check; if the head is in the set → game over; push the head; if eating, remove the apple and score.</p>
<p><b>Design (from mock feedback):</b> Snake is data; Board owns snake and apples and applies moves; Game owns timing, input and score. Mention an alternative you rejected.</p>
<p><b>Pathfinding:</b> plain BFS with the body as walls is wrong because the body moves. A body segment j cells from the tail clears after j + 1 moves, so a time-aware BFS treats a cell as blocked only if you'd arrive before it clears. Maximizing apples is a much harder search.</p>""",
)

MAKE24 = P(
    "make-24", "Make 24",
    "Evaluate valid expressions → build an expression that reaches a target",
    "Reported in round one (Arithmetic Expressions / the 24 Game).",
    q("Expressions are fully parenthesized over + − × ÷. A provided <code>split(expr)</code> returns the left operand, the operator and the right operand."),
    [
        ("Evaluate", "<p>Evaluate an expression. Every intermediate result must be a non-negative integer; otherwise return −1 (negative subtraction, non-integer division, malformed input).</p>"),
        ("Make the target", "<p>Given a small list of numbers and a target, use every number exactly once to build a valid expression that reaches the target, or return −1. Example: [1, 2, 3, 4] and 24 → <code>(4*3)*(2*1)</code>.</p>"),
    ],
    clarify=[("May I reorder the numbers?", "Yes, any order and any grouping."), ("Do Part 1's rules (non-negative integers) apply in Part 2?", "Ask; usually yes.")],
    nudges=[("You only try contiguous splits of the list", "What about (1+4)×(2+3)?", "Split the <i>set</i> of numbers, not the sequence: try every subset partition.")],
    solution="""
<p><b>Part 1:</b> recursive evaluate: split, evaluate both sides, short-circuit on −1, reject division by zero, non-divisible division and negative subtraction.</p>
<p><b>Part 2:</b> memoize on the subset of numbers used (a bitmask): <code>reach(mask)</code> = map value → expression. Base case: a single number. Otherwise split the mask into two non-empty submasks (each split once), combine every pair of values with each operator and both orders for − and ÷, keeping only valid results. Answer: <code>reach(full).get(target)</code>. Submask loop: <code>for (sub = (mask-1) &amp; mask; sub &gt; 0; sub = (sub-1) &amp; mask)</code>.</p>
<p><b>Say:</b> the input is small, so correctness beats cleverness; the cost is roughly 3ⁿ times the values per subset.</p>""",
)

GITDIFF = P(
    "git-diff", "Git-Like Array Diff",
    "Find a unique common word → shared prefix and suffix → recursive diff",
    "Reported in round one (String Diff).",
    q("You get two arrays of strings (lines or words)."),
    [
        ("Anchor", "<p>Find a word that occurs exactly once in each array and return its index in each.</p>"),
        ("Prefix and suffix", "<p>Find the shared prefix, the shared suffix and the differing middle slices.</p>"),
        ("Diff", "<p>Print a diff: recursively anchor on a unique common word (diff before it, print it unchanged, diff after it). With no anchor, print the left lines with <code>-</code> and the right lines with <code>+</code>.</p>"),
    ],
    clarify=[("Is this meant to be a minimal diff?", "No; it's the patience-diff heuristic. Mention LCS for minimal diffs.")],
    nudges=[("You pick any unique word as the anchor", "What if anchors cross each other?", "Anchors must keep increasing indices on both sides, or the output degrades.")],
    solution="""
<p><b>Anchor:</b> one pass per array counting occurrences and recording first indices; pick a word with count 1 in both. O(n + m).</p>
<p><b>Prefix/suffix:</b> advance from the front while equal, then from the back (not past the prefix).</p>
<p><b>Diff:</b> strip prefix and suffix (unchanged), then within the middle choose unique common words as anchors in increasing order on both sides (patience diff picks the longest increasing sequence of them), recurse between anchors, and fall back to −/+ when none exist.</p>
<p><b>Mention:</b> repeated lines make poor anchors; for a minimal diff use LCS (O(nm) table) or Myers' algorithm.</p>""",
)

TEXT_EDITOR = P(
    "text-editor", "Text Editor Backend",
    "Insert, delete, cursor → selection, copy, paste → large documents",
    "Reported in round one and as a phone question.",
    q("Maintain document text, a cursor, an optional selection and a clipboard."),
    [
        ("Edit", "<p>Insert text at the cursor, backspace, delete forward, and move the cursor.</p>"),
        ("Selection", "<p>Select a range, copy, and paste. Insert or paste replaces the selection.</p>"),
        ("Scale", "<p>The document is huge and edits are frequent. Avoid copying the rest of a long line on every keystroke. Discuss memory and speed tradeoffs.</p>"),
    ],
    clarify=[("Does copy clear the selection?", "Ask."), ("Where does the cursor go after paste?", "To the end of the pasted text."), ("Can paste contain newlines?", "Yes.")],
    solution="""
<p><b>Start simple:</b> a string (or StringBuilder), cursor index, selection as a normalized [lo, hi). Insert/paste: delete the selection if present, insert, move the cursor to the end of the insertion.</p>
<p><b>Scale:</b> a gap buffer gives amortized O(1) edits near the cursor (moving the gap costs the distance). A piece table keeps the original text immutable and makes undo cheap. A rope gives O(log n) split and concatenate for huge documents. Name the workload you optimize for, and count the gap move or rebalancing in your Big-O, not just the final insert.</p>""",
)

SUPERMARKET = P(
    "supermarket-queue", "Supermarket Queue",
    "Lines of customers → process items → customers who move between lines",
    "Reported in round one.",
    q("Design supermarket checkout lines."),
    [
        ("Operations", "<p>Add a customer to a line; change a customer's remaining item count; process x items in one line; process one item in every line; output customers in the order they leave.</p>"),
        ("Moving customers", "<p>Customers may now move between lines or be inserted among other customers.</p>"),
    ],
    clarify=[("Does x spill over to the next customer?", "Ask; usually yes."), ("Does setting items to 0 make a customer leave immediately?", "Ask."), ("Order when several lines finish in one global step?", "Line order.")],
    solution="""
<p><b>Part 1:</b> a deque per line plus <code>customerId → (line, customer)</code>. Processing x items consumes from the front customer and pops completed customers while budget remains, appending them to the departure log. "One item in each line" iterates lines in order.</p>
<p><b>Part 2:</b> deques can't remove from the middle efficiently. Use an order-statistic tree (balanced BST with subtree sizes) or an implicit treap per line for O(log n) insert/remove by position. Name exactly which operation forced the change.</p>""",
)

RING_BUFFER = P(
    "ring-buffer", "Ring Buffer / Circular Disk",
    "Queue contiguous writes on a ticking ring → complete-only reads → free space and threads",
    "Reported (Ring Buffer Design / Circular Disk).",
    q("A circular disk has N one-byte slots. Each <code>tick()</code> writes at most one byte at the head and advances it, wrapping after the last slot."),
    [
        ("Write and read", "<p><code>write(payload)</code> queues a multi-byte payload, written to a contiguous run of free slots one byte per tick, in arrival order. A payload starts only when its whole segment is free, and can't cross the physical end. <code>read(index, length)</code> succeeds only once that payload is fully written. Reject payloads longer than N; never overwrite live data.</p><p>Example: N = 10, head at 0: <code>hello</code> fills slots 0–4 after five ticks, then <code>abc</code> fills 5–7. A four-byte payload can't start at slot 8.</p>"),
        ("Follow-ups", "<p>Payload boundaries, deletion, fragmentation, and a separate reader and writer thread, then multiple readers or writers.</p>"),
    ],
    clarify=[("Can a payload wrap around the end?", "Not in this version; ask."), ("What does a queued write return?", "Define a handle that completes later.")],
    solution="""
<p><b>Slot state:</b> free, reserved, writing, complete, each tagged with an allocation id so a read can't stitch two payloads together.</p>
<p><b>tick:</b> if there's an active payload and the head is at its next slot, write a byte. If nothing is active, the FIFO's first payload starts when the head sits at a slot where [head, head + len) is free and doesn't cross N. Advance the head.</p>
<p><b>read:</b> look up the allocation covering index; succeed only if it's complete and (index, length) matches it.</p>
<p><b>Follow-ups:</b> length-prefix or per-allocation metadata for boundaries; a free-interval set for deletion; fragmentation means space exists but not contiguously (compaction or best-fit); with threads, protect slot metadata with a lock, define when a write becomes visible, and notify waiting readers.</p>""",
)

MATCHING = P(
    "order-matching", "Continuous Order-Matching Engine",
    "Price-time priority → partial fills → cancel and de-duplicate buy/sell code",
    "Reported (other questions list).",
    q("Process <code>BUY id price qty</code> and <code>SELL id price qty</code>. A buy crosses sells priced at or below its limit; a sell crosses buys at or above its limit."),
    [
        ("Match", "<p>Match best price first, FIFO within a price. Each trade takes the smaller remaining quantity; filled orders leave the book; partial orders rest.</p>"),
        ("Clean up", "<p>Remove the duplicated buy/sell matching logic and support cancel by id.</p>"),
    ],
    clarify=[("Trade price?", "Conventionally the resting order's price."), ("Does a partially filled resting order keep its place?", "Yes.")],
    solution="""
<p><b>Book:</b> bids as a sorted map price → FIFO queue (highest first), asks lowest first, plus <code>id → order</code> for cancels.</p>
<p><b>match(order, oppositeBook, crosses):</b> while the order has quantity and the best opposite level crosses, trade min(qty) against the front order, pop it if filled, drop empty levels. Rest the remainder. One function serves both sides with a comparator, which answers the duplication follow-up.</p>
<p><b>Cancel:</b> lazy (mark dead, skip at the front) or O(1) eager removal with linked-list nodes.</p>""",
)

AUCTION = P(
    "batch-auction", "Single-Price Batch Auction",
    "Choose the price that trades the most volume → allocate fills",
    "Reported (other questions list; also in the master doc).",
    q("Clients submit buy and sell orders (side, size, price), then <code>matchOrders()</code> is called once. A buy at P accepts any price ≤ P; a sell at Q accepts any price ≥ Q."),
    [
        ("Match", "<p>Choose a single price maximizing the shares traded. Return one consolidated fill per order id, with size 0 for unfilled orders.</p><p>Example: buy 100 @ 10, sell 150 @ 8, buy 200 @ 8 → price 8; fills: order 1 100, order 2 150, order 3 50.</p>"),
        ("Ties and allocation", "<p>Several prices may maximize volume; decide how to break ties and how to allocate among orders on the same side.</p>", "talk"),
    ],
    clarify=[("Price tie-break?", "Ask."), ("Allocation priority?", "Better price first, then arrival order, unless told pro-rata.")],
    solution="""
<p><b>Curves:</b> candidate prices = all order prices. Supply S(p) = total sell size with price ≤ p; demand D(p) = total buy size with price ≥ p. Sort prices and build both with prefix sums.</p>
<p><b>Price:</b> pick p maximizing min(S(p), D(p)) under an explicit tie rule. The maximum need not be where S equals D.</p>
<p><b>Allocate:</b> volume V. Fill eligible sells (cheapest first) and eligible buys (highest first) up to V each; every order gets a fill, 0 if unfilled. Both sides total V.</p>""",
)

STREAM_CMP = P(
    "stream-comparison", "Real-Time Data Stream Comparison",
    "Two streams of (type, value) → consistent per type → report the first mismatch fast",
    "Reported (other questions list; a phone question).",
    q("Two streams of <code>(type, value)</code> pairs are consistent if, for every type, the sequence of values is the same in both. Interleaving across types may differ."),
    [
        ("Check", "<p>Return false as soon as an inconsistency is known; return true only when both streams end consistently.</p>"),
        ("Memory", "<p>One stream may run far ahead of the other. Discuss memory bounds.</p>", "talk"),
    ],
    clarify=[("Are types known in advance?", "No."), ("Can a stream end early?", "Yes; unmatched leftovers mean inconsistent.")],
    solution="""
<p><b>State:</b> per type, a queue of unmatched values and which side they came from.</p>
<p><b>On a record:</b> if the type's queue holds values from the other side, compare with the oldest: mismatch → return false; match → pop. Otherwise enqueue.</p>
<p><b>End:</b> true only if both streams ended and every queue is empty. Lockstep comparison fails because interleavings differ; hashing whole streams delays detection.</p>
<p><b>Memory:</b> bounded by how far one side runs ahead per type; add backpressure or read the lagging stream preferentially.</p>""",
)

VIDEO = P(
    "video-player", "Video Player",
    "Download chunks in order → pick the highest quality that won't stall",
    "Reported (Live Video Streaming Client).",
    q("Video is split into chunks, each available at several qualities. A periodic <code>tick(timestamp)</code> drives the player; only one download runs at a time."),
    [
        ("Play", "<p>Download chunks in order at the highest quality and play each once downloaded.</p>"),
        ("Adapt", "<p>Choose the highest quality whose download will finish before the buffered video runs out, using the provided download-time estimates.</p>"),
        ("Live variant", "<p>Refresh a manifest to discover new segments; downloads may finish out of order; play in order without duplicates and stay near the live edge.</p>"),
    ],
    clarify=[("Can a download be cancelled?", "Ask."), ("What if no quality can finish in time?", "Pick the fastest or keep the current one; say the tradeoff.")],
    solution="""
<p><b>State machine:</b> idle, downloading, ready, playing, ended.</p>
<p><b>Each tick:</b> finish the active download if done and queue its video; start the next chunk: for each quality (best first) estimate finish time; pick the best one within the remaining buffer. Use the active download's own remaining-time estimate for it and URL estimates for alternatives.</p>
<p><b>Live:</b> <code>requested</code> set, <code>downloaded</code> map, <code>nextToPlay</code>; play only when downloaded[nextToPlay] exists, then drain contiguous segments. Download order and playback order are different things.</p>""",
)

FAILURE = P(
    "failure-pattern", "Failure Pattern",
    "Consecutive failures per name → within a time window",
    "Reported (Failure Manager).",
    q("You get interleaved <code>(name, outcome)</code> events."),
    [
        ("Streaks", "<p>Return every name that reaches <code>threshold</code> consecutive failures. A pass resets only that person's streak.</p>"),
        ("Timed", "<p>Events now carry timestamps; the qualifying streak's first-to-last time must be at most <code>window</code>.</p>"),
    ],
    clarify=[("Is consecutive per person or global?", "Per person."), ("Does a name stay reported after a later pass?", "Ask.")],
    solution="""
<p><b>Part 1:</b> <code>count[name]</code>; failure increments, pass resets that name only; report when it reaches the threshold.</p>
<p><b>Part 2:</b> also keep the timestamp where each name's current streak began; on reaching the threshold, check last − first ≤ window. If "any threshold consecutive failures within the window" is meant, keep a deque of the streak's last threshold timestamps instead.</p>""",
)

GAMEPAD = P(
    "gamepad", "Gamepad Pattern Matcher",
    "Register button patterns → match as buttons arrive → overlapping patterns",
    "Reported (other questions list).",
    q("<code>keyValue(pattern, value)</code> registers a button sequence. <code>keyIn(button)</code> records a press and prints the value when the presses so far complete a registered pattern."),
    [
        ("Match", "<p>Register <code>abc → 1</code>; pressing a, b, c prints 1.</p>"),
        ("Follow-ups (practice)", "<p>Not reported, but good practice: <code>keyOut()</code> undoes the last press; <code>possibleButtons()</code>; <code>possibleValues()</code>.</p>"),
    ],
    clarify=[("What happens on a press that matches nothing?", "Ask; reset, or keep matching overlapping patterns."), ("Can one pattern be a prefix of another?", "Yes.")],
    nudges=[("You reset to the root on a mismatch", "Pattern AAB, input AAAB?", "Reset loses overlapping matches. Check suffixes of recent presses, or use failure links (KMP / Aho-Corasick).")],
    solution="""
<p><b>Trie:</b> insert patterns; values at terminal nodes. Keep a current-node pointer and a history stack (for undo). Possible buttons = current node's children; possible values = terminals in its subtree.</p>
<p><b>Overlaps:</b> keep the last L presses (L = longest pattern) and check every suffix against the trie on each press, or build Aho-Corasick failure links so a mismatch falls back to the longest suffix that is still a prefix.</p>""",
)

CANDY = P(
    "candy-crush", "Candy Crush Stabilization",
    "Mark runs simultaneously → crush and drop",
    "Reported (other questions list).",
    q("Given a grid of integers (0 means empty), crush every horizontal or vertical run of at least three equal nonzero values."),
    [("One round", "<p>Remove all marked cells at the same time, then let each column fall, filling the top with zeros.</p>"),
     ("Until stable", "<p>Practice extension: repeat until nothing crushes.</p>")],
    solution="""
<p><b>Mark first:</b> scan rows and columns without changing values, marking cells in a boolean grid (or by negating values). Deleting during the scan breaks overlapping and longer runs.</p>
<p><b>Drop:</b> per column, write unmarked values from the bottom up, then fill the rest with 0. O(RC) per round.</p>""",
)

MERGE_DIFF = P(
    "merge-diff", "Merge Diff",
    "Compose two insertion diffs in linear time",
    "Reported (other questions list).",
    q("An insertion diff maps positions to inserted items. Applying <code>{0: A, 3: B}</code> to <code>z z z</code> gives <code>A z z B z</code>: positions refer to the result. A second diff is applied to the result of the first."),
    [("Merge", "<p>Merge two diffs into one that has the same effect as applying the first, then the second. Do it in linear time.</p><p>Example: diff1 <code>{0: A, 3: B}</code>, diff2 <code>{0: C, 4: D}</code> → merged <code>{0: C, 1: A, 4: D, 5: B}</code>. Applied to <code>z z z</code>: <code>C A z z D B z</code>.</p>")],
    clarify=[("Are keys in increasing order?", "Assume yes (or sort them)."), ("Same position in both?", "diff2's item goes first, as in the example.")],
    solution="""
<p><b>Brute force:</b> apply both to a dummy list and read off non-dummy positions: O(n²) because of list inserts.</p>
<p><b>Linear:</b> diff2's positions are final positions. Walk both diffs in order with two pointers, tracking how many diff2 items are placed before the current diff1 item: a diff1 item at intermediate position p ends at p + (number of diff2 items placed before it). Emit whichever comes first in the final order (diff2 wins ties). Check with the example: A (p 0) sits after C, so 1; B (p 3) sits after C and D, so 5.</p>""",
)

MATCH_STRINGS = P(
    "match-strings", "Match Strings",
    "Score a guess → compare two guessing strategies",
    "Reported (other questions list).",
    q("Strings have length 3 over the letters A to E."),
    [
        ("Score", "<p>Return (matches in the same position, matches in different positions), without double-counting duplicates. <code>(ABC, ACB) → (1, 2)</code>, <code>(ABB, BAA) → (0, 2)</code>, <code>(ABC, AEE) → (1, 0)</code>.</p>"),
        ("Compare strategies", "<p>An adversary picks a string; after each guess you get Part 1's score. A helper lists all possible strings; the target must be found within 20 guesses. Given two black-box strategies (history → next guess), determine which is better.</p>"),
    ],
    clarify=[("Better on average, or worst case?", "Ask; report both, plus failures."), ("Are strategies deterministic?", "Ask; if random, run many trials.")],
    solution="""
<p><b>Score:</b> exact = positions equal; total = sum over letters of min(count in a, count in b); misplaced = total − exact.</p>
<p><b>Compare:</b> for each of the 125 possible secrets, simulate: history = []; up to 20 times ask the strategy, score, append, stop on success. Record guesses used or failure. Compare average, worst case and failure count; if strategies are random, repeat per secret. Watch for a strategy that never guesses the same string twice versus one that loops.</p>""",
)

STRING_COMP = P(
    "string-compression", "String Compression System",
    "Run-length encoding → streaming chunks → out-of-order chunks",
    "Reported (other questions list).",
    q("Run-length encode consecutive groups: a group of length 1 is just the character, otherwise the character then the count."),
    [
        ("Compress", "<p><code>compress(\"aabbcc\") → \"a2b2c2\"</code>, <code>compress(\"a\") → \"a\"</code>.</p>"),
        ("Streaming", "<p>Repeated calls continue one stream. Keep the unfinished last group and return only groups known to be complete. <code>compress(\"aabb\") → \"a2\"</code>, then <code>compress(\"bccdddd\") → \"b3c2\"</code>. A <code>flush()</code> emits what's buffered.</p>"),
        ("Out of order", "<p>Chunks arrive with their starting index, possibly out of order. Buffer them and process in order, still returning only completed groups. (The reported examples' counts are inconsistent; clarify them.)</p>"),
    ],
    clarify=[("Single letters: 'a' or 'a1'?", "Part 1 says 'a'; the out-of-order example shows 'a1'. Ask."), ("Can chunks overlap?", "Assume not.")],
    solution="""
<p><b>Part 1:</b> walk once, counting runs; append char and count (if &gt; 1).</p>
<p><b>Part 2:</b> keep (currentChar, count) across calls. For each character: same → count++; different → emit the finished group and start a new one. Never emit the last group until a different character or flush arrives.</p>
<p><b>Part 3:</b> <code>pending: startIndex → chunk</code> and <code>nextIndex</code>. On arrival, store it; then while pending has nextIndex, feed that chunk to the Part 2 compressor and advance nextIndex by its length. Same reorder-buffer idea as TCP.</p>""",
)

MSG_QUEUE = P(
    "message-queue", "Message Queue Router",
    "Route messages to workers by type and load → queue when full → drain on completion",
    "Reported (other questions list).",
    q("Workers have an id, capacity, current load and supported message types. Messages have an id, type, size and timestamp."),
    [("Route", """<p><code>init(workers)</code>, <code>sendMessage(m)</code>, <code>completeMessage(id)</code>, <code>getWorkerStatus()</code>, <code>getMessageQueue()</code>. A worker must support the type and have room (load + size ≤ capacity). Among those, prefer the lowest load percentage, then the highest capacity. If none fits, queue the message.</p>
<p>Workers: W1 cap 100 (email, sms), W2 cap 150 (email, push), W3 cap 80 (sms, push). M1 email 30 → W1 and W2 both at 0%, W2 wins on capacity.</p>"""),
     ("Completion", "<p>Completing a message frees capacity; try to route queued messages.</p>")],
    clarify=[("Queue order: strict FIFO, or may a later message skip a blocked one?", "Ask; it's the main design decision."), ("Can a message be larger than every worker's capacity?", "Then it can never run; reject it.")],
    solution="""
<p><b>State:</b> workers, <code>msgId → (message, worker)</code>, a FIFO queue.</p>
<p><b>Route:</b> filter by type and room, sort (or scan) by (load / capacity, −capacity), assign, add the size to the worker's load.</p>
<p><b>Complete:</b> subtract the size, then scan the queue and route anything that now fits (or only the head if strict FIFO). With many workers, index them per type in a heap by load percentage, with lazy updates.</p>""",
)

WEIGHTED_GRAPH = P(
    "weighted-graph", "Weighted Graph (Unit Conversion)",
    "Build a graph of conversion facts → answer queries → shortest weighted paths",
    "Reported (other questions list; a sample video question).",
    q("Facts like <code>(\"m\", 3.28, \"ft\")</code> mean 1 m = 3.28 ft. Queries like <code>(2, \"m\", \"in\")</code> ask how many inches are in 2 meters."),
    [("Convert", "<p>With facts m→ft 3.28, ft→in 12, hr→min 60, min→sec 60: (2, m, in) → 78.72; (13, in, m) → about 0.396; (2, m, hr) → none.</p>"),
     ("Flights variant", "<p>Directed routes with durations; find the fastest route between two cities (NYC→SEA = 8.0 via LAX). Why is BFS wrong here?</p>")],
    clarify=[("Do facts imply the reverse conversion?", "Yes: add the reciprocal edge."), ("Unknown unit?", "Return none.")],
    solution="""
<p><b>Conversion:</b> build a graph with an edge u→v of weight k and v→u of weight 1/k. Answer a query with BFS/DFS from the source, multiplying weights along the path; none if unreachable. Any path works because consistent facts give the same product. Precompute connected components with a multiplier to a root for O(1) queries.</p>
<p><b>Flights:</b> BFS finds the fewest hops, not the least time. Use Dijkstra with a min-heap on total duration.</p>""",
)

WORDLE = P(
    "wordle", "Wordle-Style Game",
    "Count exact and misplaced matches between two strings",
    "Reported (other questions list).",
    q("Given two strings of equal length, return (same-position matches, different-position matches). Each character counts once; use the minimum frequency."),
    [("Compare", "<p><code>(abc, axc) → (2, 0)</code>, <code>(abc, bca) → (0, 3)</code>, <code>(aab, bba) → (0, 2)</code>, <code>(CRANE, ALERT) → (1, 2)</code>.</p>")],
    solution="""
<p>exact = count of i with a[i] == b[i]. Count characters at non-exact positions in each string; misplaced = sum over characters of min(countA, countB). Equivalently total overlap (min frequencies over the whole strings) minus exact. O(n).</p>""",
)

SQUARE_UP = P(
    "square-up", "Square Up",
    "Gravity drops on an infinite board → first 2×2 square wins → O(1) per move",
    "Reported (other questions list).",
    q("Two players drop pieces into columns of a board infinite horizontally with no height limit. Player 1 is <code>-</code>, player 2 is <code>+</code>; they alternate and <code>-</code> moves first. The first to fill a 2×2 square with their own pieces wins."),
    [("Drop", "<p><code>drop(player, column)</code> returns exactly one of <code>Player 1 wins</code>, <code>Player 2 wins</code>, <code>No winner</code>. Follow-up: make it O(1).</p>")],
    solution="""
<p>Store <code>(row, col) → player</code> and <code>height[col]</code>. The new piece is the highest in its column, so it can only be in the top row of a new square: check the two squares below-left and below-right of it, (r−1..r, c−1..c) and (r−1..r, c..c+1). That's O(1) per drop.</p>""",
)

FALLING_PATH = P(
    "falling-path-sum", "Falling Path Sum",
    "Minimum path from top row to bottom row (LeetCode 931)",
    "Reported (other questions list).",
    q("Given an n × n grid, a falling path starts in any cell of the first row and moves to the cell directly below or diagonally left or right in the next row."),
    [("Minimum sum", "<p>Return the minimum sum of a falling path.</p>")],
    solution="""
<p>2D DP: <code>dp[r][c] = grid[r][c] + min(dp[r−1][c−1], dp[r−1][c], dp[r−1][c+1])</code> (skipping out-of-range columns). Answer: min of the last row. O(n²) time; keep only the previous row for O(n) space.</p>""",
)

TIER3 = [SNAKE, MAKE24, GITDIFF, TEXT_EDITOR, SUPERMARKET, RING_BUFFER, MATCHING, AUCTION, STREAM_CMP, VIDEO,
         FAILURE, GAMEPAD, CANDY, MERGE_DIFF, MATCH_STRINGS, STRING_COMP, MSG_QUEUE, WEIGHTED_GRAPH, WORDLE,
         SQUARE_UP, FALLING_PATH]
