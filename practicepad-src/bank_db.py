"""Question bank: Databricks SWE intern practice problems.

Same entry format as bank_a (see P there). These show under the Databricks
problem set in the pad's top bar, not in the Jane Street bank.
"""
from bank_a import P, q

MODES = P(
    "modes-of-transport", "Modes of Transport",
    "Fastest single-mode path on a grid → one BFS instead of one per mode → switching modes",
    "The most-reported Databricks intern question (phone screen and onsite). Parts 3–4 are reported follow-ups.",
    """<p>You're given a 2D grid of a city with a source <code>S</code>, a destination <code>D</code>, and roadblocks <code>X</code>:</p>
<pre class="treebox">1 2 3 S 1 2 4
X 2 3 2 1 X 2
2 1 1 D 2 X 4</pre>
<p>The digits <code>1</code> to <code>4</code> are different modes of transport. You're also given two arrays:</p>
<ul>
<li><code>time[]</code>, where <code>time[i]</code> is the travel time per move for transport mode <code>i</code></li>
<li><code>cost[]</code>, where <code>cost[i]</code> is the total cost of using transport mode <code>i</code></li>
</ul>""",
    [
        ("Fastest mode", """
<p><b>Movement rules</b></p>
<ul>
<li>You can move up, down, left or right.</li>
<li>You can't switch modes once you pick one.</li>
<li>You can't move through roadblocks (<code>X</code>).</li>
</ul>
<p><b>Goal:</b> return the mode of transport that gives the fastest path from <code>S</code> to <code>D</code>. If several modes have the same minimum time, return the one with the lowest cost.</p>"""),
        ("Single BFS", q("Right now you run a separate BFS for each mode of transport. Can you solve it with a single BFS instead?")),
        ("Switching modes", q("New rule: you may switch modes partway. Each switch adds <code>switch_time</code> and <code>switch_cost</code>. The mode you start with from <code>S</code> isn't a switch.") + """
<p>Minimize total time, then total cost. Return the route (the list of cells from <code>S</code> to <code>D</code>) with its time and cost, or nothing if <code>D</code> is unreachable.</p>"""),
        ("At most k switches", q("Same as before, but you can switch at most <code>max_switches</code> times.")),
    ],
    clarify=[
        ("Which cells can a mode use?", "Only cells marked with that mode's digit, plus <code>S</code> and <code>D</code>. Every mode can stand on <code>S</code> and <code>D</code>."),
        ("How is the time of a path computed?", "Number of moves × <code>time</code> for that mode. Every move of one mode takes the same time."),
        ("How do the arrays line up with the digits?", "Your call, just state it. A common choice: 0-indexed arrays, so mode m uses <code>time[m − 1]</code> and <code>cost[m − 1]</code>."),
        ("What if no mode can reach D?", "Return -1."),
        ("What if two modes tie on both time and cost?", "Return the lower mode number."),
        ("How big is the grid?", "Assume up to about a million cells, and a handful of modes."),
        ("With switching, what does a path cost?", "Your call, just state it. A clean choice: each move costs its mode's per-move time, each mode used adds its cost once, and each switch adds switch_time and switch_cost."),
    ],
    nudges=[
        ("You're exploring every path with DFS or backtracking",
         "How do you find the fewest moves on a grid where every move costs the same?",
         "Use BFS. Within one mode every move costs the same, so fewest moves gives the least time: moves × time[mode]."),
        ("You reached for Dijkstra in Part 1",
         "For a fixed mode, is any move more expensive than another?",
         "No, so plain BFS is enough. Dijkstra only earns its keep once modes with different step times share one search."),
        ("Your single BFS lets a path change modes partway",
         "Once I've picked a mode, can I change it?",
         "The mode is part of the state. Visit (row, col, mode), not (row, col), or one mode will block cells another mode needs."),
        ("You claim the single BFS is asymptotically faster",
         "What's the cost of each version, in rows, columns and modes?",
         "Both touch each (cell, mode) state at most once: O(M × R × C). The gain is one pass, shared code, and the chance to stop early."),
    ],
    solution="""
<div class="say"><span class="lbl">Part 1</span><p>"For each mode m, BFS from S over cells marked m, plus D. The BFS depth at D is the fewest moves for that mode, so its time is moves × time[m]. Keep the best (time, cost, mode); return -1 if no mode reaches D. That's O(M × R × C) time and O(R × C) memory, reused per mode."</p></div>
<p>In the example grid, mode 2 is the only one that reaches <code>D</code> (S → the 2 below it → D, 2 moves), so the answer is 2 whatever <code>time</code> and <code>cost</code> are.</p>
<div class="say"><span class="lbl">Follow-up</span><p>"Make the mode part of the state: (row, col, mode). Seed the search with (S, m) for every mode. A plain FIFO BFS then gives moves per mode, and I'd still compare moves × time at the end. To stop early, order the frontier by (elapsed time, cost, mode) with a heap: the first time D comes off it is the answer, ties included."</p></div>
<p><b>Cost, said out loud:</b> both versions visit each (cell, mode) state at most once, so O(M × R × C) either way. A single search doesn't change the big-O. It gives one pass over the grid, one copy of the neighbour code, and an early exit when a fast mode reaches D quickly. With a heap that's O(M × R × C × log(M × R × C)).</p>
<div class="say"><span class="lbl">Switching modes</span><p>"Now the step costs differ and I can change mode, so BFS isn't enough. Dijkstra over (row, col, mode), keyed by (time, cost). From a state I can move to a neighbour of my mode, or switch to another mode in place and pay the switch. Keep a parent pointer per state to rebuild the route."</p></div>
<div class="say"><span class="lbl">At most k switches</span><p>"Add the switch count to the state: (row, col, mode, switches used), and never go past max_switches. States grow by a factor of k + 1, so it's O(M × (k + 1) × R × C × log) with the heap."</p></div>
<p><b>Edge cases worth naming:</b> S next to D (one move for every mode), D unreachable (-1), ties on time broken by cost, and modes whose digit never appears on the grid.</p>""",
)


IP_FIREWALL = P(
    "ip-firewall", "IP Firewall (CIDR Rules)",
    "First-match ALLOW/DENY for an IP → the status of a whole CIDR block",
    "Reported Databricks phone screen (new grad), and on several question lists. A variant of LeetCode 751.",
    q("Write a firewall. It's built from an ordered list of rules, and answers whether an IPv4 address is allowed."),
    [
        ("Check an address", """
<p>Implement <code>IpFirewall(rules)</code> and <code>query(ip)</code>. Each rule is <code>(action, ip_or_cidr)</code> with action <code>"ALLOW"</code> or <code>"DENY"</code>. A bare IP means <code>/32</code>. The first rule that matches decides; if none matches, return <code>"DENY"</code>.</p>
<pre class="treebox">rules = [("ALLOW", "192.168.100.5/30"),
         ("DENY",  "10.0.0.0/8"),
         ("ALLOW", "10.1.2.3")]

query("192.168.100.4") → "ALLOW"   # /30 covers .4 to .7
query("192.168.100.8") → "DENY"    # no rule matches
query("10.1.2.3")      → "DENY"    # the /8 rule comes first
query("8.8.8.8")       → "DENY"</pre>"""),
        ("Check a whole block", q("Now the query can be a CIDR block, not just one address. What's the status of the whole block?") + """
<p>Return <code>"ALLOW"</code> if every address in the block is allowed, <code>"DENY"</code> if every one is denied, and <code>"MIXED"</code> otherwise.</p>
<p class="meta">Reported as a follow-up; the exact return values here are ours.</p>"""),
    ],
    clarify=[
        ("Are the addresses always valid IPv4?", "Yes. Four octets, 0 to 255."),
        ("Can a rule's base address have bits set below its prefix, like 192.168.100.5/30?", "Yes. Mask it: /30 means only the top 30 bits matter."),
        ("How many rules and queries?", "Thousands of rules, many more queries. Ask whether to optimize query time."),
    ],
    nudges=[
        ("You're comparing addresses as strings", "How would you check whether two addresses share their first 27 bits?",
         "Parse to a 32-bit integer; compare (ip & mask) with (base & mask), where mask = ~0 << (32 − prefix)."),
        ("Part 2: you're enumerating every address in the block", "How many addresses are in a /8?",
         "16 million. Walk the rules in order instead, tracking which part of the block is still undecided. A rule either covers that part, sits inside it, or misses it."),
    ],
    solution="""
<div class="say"><span class="lbl">Part 1</span><p>"I'll parse each rule once into (action, base & mask, mask). A query parses the IP to an int and returns the first rule where ip & mask equals the stored base. O(R) per query, O(1) extra memory. If queries dominate, a binary trie on the bits gives O(32), keeping the smallest rule index at each node."</p></div>
<div class="say"><span class="lbl">Part 2</span><p>"A query block and a rule's block are either nested or disjoint, because CIDR blocks are aligned. Walk the rules in order with a list of still-undecided sub-blocks, starting with the query block. A rule that contains an undecided piece decides all of it. A rule inside a piece splits the piece into the rule's block and the rest. The rest of a block minus a sub-block is at most 32 CIDR blocks, so this stays small. At the end the leftovers are DENY. If every decision is the same action, return it; otherwise MIXED."</p></div>""",
)

TIC_TAC_TOE = P(
    "tic-tac-toe", "N × N Tic-Tac-Toe",
    "Winner after each move in O(1) → m × n board with k in a row",
    "Reported for Databricks interns and on several question lists (LeetCode 348 and variants).",
    q("Build the game logic for tic-tac-toe on any board size. No UI."),
    [
        ("Who won?", """
<p>Implement <code>TicTacToe(n)</code> and <code>move(row, col, player)</code> for players 1 and 2. Return the winner if this move completes a full row, column or diagonal, else 0. Ignore invalid moves (off the board or on a taken cell) and return 0.</p>
<p>Example on 3 × 3: moves (0,0,1), (0,2,2), (2,2,1), (1,1,2), (2,0,1), (1,0,2), (2,1,1) return 0, 0, 0, 0, 0, 0, 1. Player 1 completes the bottom row.</p>"""),
        ("Faster", q("Your move checks the whole row, column and diagonals. Can a move be O(1)?")),
        ("k in a row", q("Now the board is m × n and you win with k in a row, not a full line.") + """
<p>Rows, columns and both diagonal directions all count. <code>k ≤ min(m, n)</code>.</p>"""),
    ],
    clarify=[
        ("Do players have to alternate?", "Assume the caller passes valid turns. Just validate the cell."),
        ("What happens after someone wins?", "Your call. Returning the same winner for later moves is fine."),
    ],
    nudges=[
        ("Each move rescans its row, column and diagonals", "This board could be 10,000 × 10,000. What does a move cost?",
         "Keep a counter per row, per column and for the two diagonals, per player. A move bumps at most four counters; a counter reaching n is a win."),
        ("Part 3: you kept the full-line counters", "Does three in a row on a 10-wide board fill a counter?",
         "Counters no longer work. From the new piece, count matching pieces outward in each of the four directions: O(k) per move."),
    ],
    solution="""
<p><b>Part 1–2:</b> grid for validation, plus counters <code>rows[p][r]</code>, <code>cols[p][c]</code>, <code>diag[p]</code> (r == c) and <code>anti[p]</code> (r + c == n − 1). A move updates the ones it touches and wins when one reaches n. O(1) per move, O(n²) for the grid (or a set of taken cells).</p>
<p><b>Part 3:</b> for each direction pair, (0,1)/(0,−1), (1,0)/(−1,0), (1,1)/(−1,−1), (1,−1)/(−1,1), count the player's pieces outward from the new cell until a gap. Win if 1 + both sides ≥ k. O(k) per move.</p>
<p><b>Follow-ups reported elsewhere:</b> a computer player that moves randomly, or one that plays perfectly with minimax and deterministic tie-breaks.</p>""",
)

HIT_COUNTER = P(
    "hit-counter", "Rolling Hit Counter",
    "Count hits in a sliding time window → bounded memory → out-of-order timestamps",
    "Reported Databricks onsite question; also listed as \"hash map with QPS\" (LeetCode 362 family).",
    q("Count requests over a sliding time window."),
    [
        ("Count hits", """
<p>Implement <code>simulate_hit_counter(window, operations)</code>. An operation <code>[0, t]</code> records a hit at time t. An operation <code>[1, t]</code> returns the number of hits in <code>(t − window, t]</code>, so a hit exactly <code>window</code> old has expired. Duplicate timestamps count separately. Timestamps never decrease. Return the answers to the <code>[1, t]</code> operations, in order.</p>
<pre class="treebox">window 5, [[0,1],[0,1],[1,1],[0,3],[1,5],[1,6],[1,8]]  →  [2, 3, 1, 0]
window 3, [[1,10],[0,10],[1,10],[0,10],[1,10],[1,12],[1,13]]  →  [0, 1, 2, 2, 0]</pre>"""),
        ("Millions of hits a second", q("Now traffic is huge, and one timestamp can have millions of hits. Keep memory bounded.")),
        ("Out of order", q("Timestamps can now arrive slightly out of order. What changes?"), "talk"),
    ],
    clarify=[
        ("Is the window inclusive at both ends?", "No: (t − window, t]. A hit at exactly t − window has expired."),
        ("Can a query come before any hits?", "Yes; return 0."),
    ],
    nudges=[
        ("You store every hit in a list and filter on each query", "What's a query cost after a million hits?",
         "Expire from the front of a queue as time moves forward; keep a running total so a query is amortized O(1)."),
        ("Part 2: one queue entry per hit", "How much memory at a million hits per second?",
         "Store (timestamp, count) groups, or a ring of per-second buckets of size window. Memory is O(window), not O(hits)."),
    ],
    solution="""
<div class="say"><span class="lbl">Part 1–2</span><p>"A deque of (timestamp, count) plus a running total. A hit merges into the last group if the timestamp matches. A query pops groups with timestamp ≤ t − window and subtracts them, then returns the total. Each group is pushed and popped once, so it's amortized O(1), and memory is the number of distinct timestamps in the window."</p></div>
<p><b>Out of order:</b> the deque's order breaks. Options: a ring of <code>window</code> buckets indexed by t mod window, each tagged with the timestamp it holds, so a late hit lands in the right bucket if it's still inside the window. Or accept lateness up to a bound and buffer. Hits older than the window are dropped; say so.</p>""",
)

FIB_TREE = P(
    "fibonacci-tree-path", "Fibonacci Tree Path",
    "Directions between two preorder-numbered nodes of a huge implicit tree",
    "Reported Databricks onsite question; also on the new grad question lists.",
    q("A Fibonacci tree of order n has a left subtree of order n − 1 and a right subtree of order n − 2. Orders 0 and 1 are a single node. Nodes are numbered in preorder starting at 0."),
    [
        ("Find the path", """
<p>Implement <code>fibonacci_tree_path(order, source, target)</code>. Return the moves from source to target: <code>U</code> to the parent, <code>L</code> and <code>R</code> to a child. The path goes up some number of times, then down. Return <code>""</code> if source equals target.</p>
<pre class="treebox">fibonacci_tree_path(4, 4, 7)   → "UUURL"
fibonacci_tree_path(4, 1, 4)   → "LR"
fibonacci_tree_path(5, 12, 6)  → "UUULLR"</pre>
<p>An order-4 tree has 9 nodes and an order-5 tree has 15. Draw the order-4 one first.</p>"""),
        ("Order 70", q("Now the order goes up to 70. That's about 6 × 10<sup>14</sup> nodes.") + "<p>Don't build the tree. Labels need 64-bit integers.</p>"),
    ],
    clarify=[
        ("Is the tree given to me?", "No, only the order. You work out its shape."),
        ("Are labels always valid?", "Yes, both are in range."),
    ],
    nudges=[
        ("You build the tree as nodes", "How many nodes at order 70?",
         "Too many. size(n) = 1 + size(n − 1) + size(n − 2) tells you, from a label, whether it's the root, in the left subtree or in the right one."),
        ("You're searching from the root for each node", "What does the path from the root to a label look like?",
         "Walk down from the root using subtree sizes to get each node's L/R string. The answer is one U per step of the source's string after the common prefix, then the rest of the target's string."),
    ],
    solution="""
<div class="say"><span class="lbl">Approach</span><p>"Precompute size(k) for k ≤ order. To get the root-to-x path: at a node of order k with x &gt; 0, if x ≤ size(k − 1) go L with x − 1 and order k − 1, else go R with x − 1 − size(k − 1) and order k − 2. That's O(order) per node, about 70 steps. Take the common prefix of the two paths; the answer is 'U' × (len(source path) − prefix) + target path after the prefix."</p></div>
<p>Edge cases: one node is an ancestor of the other (all U's or no U's), source equals target, order 0 or 1.</p>""",
)

REVENUE = P(
    "revenue-system", "Referral Revenue System",
    "Customers with referrers → top k by revenue including referrals → indirect referrals, threads",
    "Reported Databricks coding round (concurrency-focused). A version with indirect referrals is also on the question lists.",
    q("Track customer revenue, where a customer gets credit for revenue from the customers they referred."),
    [
        ("Insert and rank", """
<ul>
<li><code>insert(revenue)</code> adds a customer and returns its id. Ids start at 0 and go up by 1.</li>
<li><code>insert(revenue, referrer)</code> adds a customer referred by <code>referrer</code>.</li>
<li><code>get_top_k(k, min_revenue)</code> returns the ids of the k customers with the highest total revenue. Total = own revenue + the revenue of customers they referred directly. Only customers with total ≥ <code>min_revenue</code> count.</li>
</ul>
<pre class="treebox">insert(10)      → 0
insert(20, 0)   → 1
insert(5, 0)    → 2
insert(15)      → 3
get_top_k(2, 10) → {0, 1}
# totals: 0 → 35, 1 → 20, 2 → 5, 3 → 15</pre>"""),
        ("Indirect referrals", q("Now a customer also gets credit from customers their referrals referred, all the way down.")),
        ("Many threads", q("insert and get_top_k are now called from many threads at once. What do you lock?"), "talk"),
    ],
    clarify=[
        ("Does a referral count only the referred customer's own revenue?", "In Part 1, yes: own revenue plus direct referrals' own revenue."),
        ("How are ties ordered?", "By lower id first."),
        ("Which call is hot?", "Ask. If get_top_k is frequent, keep totals sorted."),
    ],
    nudges=[
        ("get_top_k sorts every customer each call", "What if this is called a lot more than insert?",
         "Maintain totals incrementally: an insert changes at most two totals. Keep a sorted structure keyed by (−total, id) and walk it."),
        ("Part 2: you recompute every total by walking the referral tree", "When a new customer joins, whose totals change?",
         "Exactly their chain of referrers. Walk up the parent pointers and add the revenue to each: O(depth) per insert."),
    ],
    solution="""
<div class="say"><span class="lbl">Part 1</span><p>"Store own revenue, referrer and total per id. insert adds the new total and bumps the referrer's total. For get_top_k, either a heap over all totals (O(N log k)) or, if queries dominate, a sorted set of (−total, id) updated on each insert (remove and re-add the referrer: O(log N))."</p></div>
<div class="say"><span class="lbl">Part 2</span><p>"Walk the referrer chain on insert and add the revenue to every ancestor, updating the sorted set for each. O(depth × log N) per insert. If chains are deep, that's the cost to talk about."</p></div>
<p><b>Threads:</b> the simplest correct answer is one lock around both operations. Then discuss: a read-write lock if queries dominate; that ids need an atomic counter; that per-customer locks need a fixed lock order (walk up the chain) to avoid deadlock.</p>""",
)

LOGGER = P(
    "thread-safe-logger", "Thread-Safe Logger",
    "Many writers, no interleaving → a queue and one writer thread → what to do when it's full",
    "Reported in the Databricks concurrency round (\"an efficient logger that processes messages in a queue\"). Durable-writer versions are also on the question lists.",
    q("Many threads call <code>log(message)</code>. Lines must never interleave, and logging shouldn't slow the callers down much."),
    [
        ("Make it safe", "<p>Write a <code>Logger</code> with <code>log(message)</code> that's safe to call from many threads. Each message comes out as one whole line.</p><p class=\"meta\">Java is the natural language here. Python's <code>threading</code> works too; JavaScript has no shared-memory threads.</p>"),
        ("Don't block the callers", q("Writing to disk is slow, and holding a lock during the write makes every caller wait. Move the writing off the callers' threads.")),
        ("Queue is full", q("The writer can't keep up and the queue fills. What do you do? Then: how does the program shut down without losing messages?")),
    ],
    nudges=[
        ("You hold the lock while writing to the file", "What are the other 100 threads doing during that write?",
         "Waiting. Callers only enqueue under a short lock; one background thread dequeues and writes, ideally in batches."),
        ("Your queue is unbounded", "What happens if the disk stalls for a minute?",
         "Memory grows without limit. Bound the queue and pick a policy: block the producer, drop with a counter, or flush on the caller's thread."),
    ],
    solution="""
<div class="say"><span class="lbl">Design</span><p>"A bounded blocking queue. log() enqueues. One writer thread takes everything available, writes it as a batch and flushes. One writer means no interleaving without a file lock. When full, I'd block the caller by default, since silently losing logs is worse; dropping with a counter is the other reasonable choice for hot paths."</p></div>
<p><b>Shutdown:</b> stop accepting new messages, put a sentinel on the queue, let the writer drain up to it, flush and close, then join the writer thread. <b>Durability:</b> if a caller must know its message is on disk, return a future completed after the batch's fsync (group commit).</p>""",
)

ANAGRAM_INDEX = P(
    "anagram-index-of", "Anagram indexOf",
    "First substring that's a rearrangement of a pattern → all of them",
    "Reported Databricks onsite question (LeetCode 438 family).",
    q("Like <code>indexOf</code>, but the match can be any rearrangement of the pattern."),
    [
        ("First match", """
<p>Return the start index of the first substring of <code>text</code> that is a permutation of <code>pattern</code>, or -1.</p>
<pre class="treebox">("cbaebabacd", "abc") → 0      # "cba"
("eidboaoo", "ab")    → -1</pre>"""),
        ("All matches", q("Now return every start index.") + "<pre class=\"treebox\">(\"cbaebabacd\", \"abc\") → [0, 6]</pre>"),
    ],
    nudges=[
        ("You sort or count every window from scratch", "What changes between one window and the next?",
         "One character leaves and one enters. Keep a count array for the window and the number of characters whose count matches the pattern's: O(1) per step, O(n) total."),
    ],
    solution="""<p>Fixed window of length m = len(pattern). Count the pattern; slide over the text adjusting counts for the char entering and the one leaving, and track how many of the 26 (or alphabet-size) counts currently match. A match count equal to the alphabet size means a hit. O(n + m) time, O(alphabet) memory. Part 1 exits at the first hit.</p>""",
)

DELTA = P(
    "delta-encoding", "In-Place Delta Encoding",
    "Delta-encode an array in place → decode it → do it on a cluster",
    "Reported Databricks new grad onsite coding round.",
    q("Columnar formats store sorted numbers as differences, because small numbers compress well."),
    [
        ("Encode", "<p>Modify the array in place: keep the first element, and replace each later element with its difference from the original previous element. <code>[5, 7, 4, 4, 10]</code> → <code>[5, 2, -3, 0, 6]</code>.</p>"),
        ("Decode", q("Now undo it, in place.")),
        ("Too big for one machine", q("The array is split across many machines. How do you encode it with Spark, or any cluster?"), "talk"),
    ],
    nudges=[
        ("You loop forward and overwrite", "When you compute element 2, what's in element 1?",
         "Already a difference, not the original. Loop from the back, or keep the previous original in a variable."),
    ],
    solution="""<p><b>Encode:</b> for i from n − 1 down to 1, a[i] −= a[i − 1]. <b>Decode:</b> for i from 1 up, a[i] += a[i − 1] (a prefix sum). Both O(n), O(1) extra.</p>
<p><b>Cluster:</b> each partition encodes locally, except its first element needs the previous partition's last original value. Collect each partition's last value (one small pass), broadcast them, then encode. Decoding is a distributed prefix sum: sum per partition, prefix-sum those sums on the driver, then each partition adds its offset.</p>""",
)

LAZY_ARRAY = P(
    "lazy-array", "Lazy Array",
    "Defer map() until indexOf() needs it → prove it's lazy",
    "Reported Databricks coding question.",
    q("Build an array whose <code>map</code> is lazy: functions run only when a result is needed."),
    [
        ("map and indexOf", """
<p><code>LazyArray(values)</code>. <code>map(f)</code> returns a new LazyArray without calling f. <code>indexOf(v)</code> applies the pending functions and returns the first index whose result equals v, or -1.</p>
<pre class="treebox">LazyArray([10, 20, 30, 40, 50]).map(x → x * 2).indexOf(40)                → 1
LazyArray([10, 20, 30, 40, 50]).map(x → x * 2).map(x → x * 3).indexOf(240) → 3</pre>"""),
        ("Prove it", q("How would you test that it's actually lazy, and that the original array is unchanged after a map?")),
    ],
    nudges=[
        ("map applies f right away", "What if nobody ever calls indexOf?",
         "Store the source values and a list of pending functions. map copies that list and appends f; nothing runs."),
        ("indexOf maps the whole array first", "If the match is at index 0, how many calls do you make?",
         "Apply the chain element by element and stop at the first match."),
    ],
    solution="""<p>Each LazyArray holds a reference to the shared source values and its own tuple of functions. <code>map</code> returns a new object with the tuple plus f: O(1), and earlier arrays are unaffected. <code>indexOf</code> runs the composed functions per element and stops at the first match. Test laziness with a function that counts its calls: zero after map, and exactly i + 1 calls per function when the match is at index i.</p>""",
)

SNAPSHOT_SET = P(
    "snapshot-set", "Snapshot Set Iterator",
    "A set whose iterators see the set as it was when they were created",
    "Reported Databricks coding question (related to LeetCode 1146).",
    q("Build a set whose iterators don't change when the set does."),
    [
        ("Snapshot iterators", """
<p>Implement <code>add(x)</code>, <code>remove(x)</code>, <code>contains(x)</code> and <code>iterator()</code>. An iterator yields the elements present when it was created, whatever add or remove calls happen afterwards.</p>
<pre class="treebox">add(1); add(2); add(3)
it = iterator()
remove(2); add(4)
list(it)   → [1, 2, 3]
contains(2) → false</pre>"""),
        ("Cheap snapshots", q("Copying the whole set per iterator is too slow when the set is big and iterators are common. Make iterator() O(1).")),
    ],
    nudges=[
        ("iterator() copies the set", "What does that cost with a million elements and an iterator per request?",
         "Version the data: a global version counter, and per element the versions it was added and removed at. An iterator remembers its version and skips elements not alive at it."),
    ],
    solution="""<p>Keep a version counter. Each add/remove bumps it. Store per element a list of (added_at, removed_at) intervals. <code>iterator()</code> records the current version: O(1). Iterating yields elements alive at that version. Old entries can be cleaned up once no live iterator has a version that old (track open iterators). Trade-off: iteration walks removed elements too, so compaction matters.</p>""",
)

TIME_KV = P(
    "time-based-kv", "Time-Based Key-Value Store",
    "set with a timestamp → get the latest value at or before a time",
    "Reported Databricks coding question (LeetCode 981).",
    q("A key-value store that remembers every version of every key."),
    [
        ("set and get", """
<p><code>set(key, value, timestamp)</code> and <code>get(key, timestamp)</code>, which returns the value with the largest timestamp ≤ the given one, or <code>""</code>. Timestamps for one key arrive increasing.</p>
<pre class="treebox">set("foo", "bar", 1)
get("foo", 1) → "bar";  get("foo", 3) → "bar"
set("foo", "bar2", 4)
get("foo", 4) → "bar2"; get("foo", 5) → "bar2"; get("foo", 0) → ""</pre>"""),
        ("Out of order", q("Now sets for one key can arrive with timestamps out of order.")),
    ],
    nudges=[
        ("get scans every version", "How many versions might a key have?",
         "Since timestamps arrive increasing, each key's list is sorted: binary search for the last timestamp ≤ t. O(log v)."),
    ],
    solution="""<p>Map key → list of (timestamp, value), appended in order. get binary-searches for the rightmost timestamp ≤ t. set O(1), get O(log v). Out of order: a sorted map per key (TreeMap floorEntry in Java, a sorted list with bisect.insort in Python) makes set O(log v), or O(v) with a plain list insert.</p>""",
)

HOUSE_ROBBER = P(
    "house-robber", "House Robber",
    "Max non-adjacent sum → houses in a circle → skip k houses",
    "Reported Databricks phone screen question (LeetCode 198, 213).",
    q("Houses in a row each hold some money. You can't take from two adjacent houses."),
    [
        ("In a row", "<p>Return the most money you can take. <code>[2, 7, 9, 3, 1]</code> → 12 (2 + 9 + 1).</p>"),
        ("In a circle", q("The houses are in a circle, so the first and last are adjacent.") + "<p><code>[2, 3, 2]</code> → 3.</p>"),
        ("Skip k", q("Now any two houses you take must have at least k houses between them.") + "<p>With k = 2, <code>[2, 7, 9, 3, 1]</code> → 9.</p>"),
    ],
    nudges=[
        ("You're trying every subset", "What's the best you can do using only the first i houses?",
         "best[i] = max(best[i − 1], best[i − 2] + a[i]). Two variables are enough."),
        ("Part 2: you're special-casing the first house", "Can the answer use both the first and the last house?",
         "No. So the answer is the better of the row without the first house and the row without the last."),
    ],
    solution="""<p><b>Row:</b> best[i] = max(best[i − 1], a[i] + best[i − 2]); O(n) time, O(1) space. <b>Circle:</b> max(row(a[1:]), row(a[:−1])). <b>Skip k:</b> best[i] = max(best[i − 1], a[i] + best[i − k − 1]); keep the last k + 1 values.</p>""",
)

ISLAND = P(
    "max-area-island", "Max Area of Island",
    "Largest connected group of 1s in a grid",
    "Reported Databricks coding question (LeetCode 695).",
    q("A grid of 0s (water) and 1s (land). Land connects up, down, left and right."),
    [
        ("Largest island", """
<p>Return the area of the largest island, or 0 if there's no land.</p>
<pre class="treebox">1 1 0 0
0 1 0 1
1 0 1 1
0 0 0 1      → 4</pre>"""),
        ("Huge grid", q("The grid has a billion cells and is read one row at a time. What now?"), "talk"),
    ],
    nudges=[
        ("You recurse with DFS", "How deep can that recursion get on a 2,000 × 2,000 grid of all land?",
         "Four million frames. Use an explicit stack or a BFS queue."),
        ("Part 2", "Do you need the whole grid in memory at once?",
         "Union-find row by row: only the previous row's labels are live, with sizes kept on the roots."),
    ],
    solution="""<p>For each unvisited land cell, flood fill with an explicit stack, counting cells and marking them visited (or overwriting with 0). O(R × C) time. Streaming version: union-find over the current and previous row, carrying component sizes; when a component doesn't touch the new row, it's finished and can update the max.</p>""",
)

FLIGHTS = P(
    "cheapest-flights-k-stops", "Cheapest Flights Within K Stops",
    "Cheapest route with a limit on stops",
    "Reported as \"path finding under constraints\" for Databricks (LeetCode 787).",
    q("Flights are <code>[from, to, price]</code> between n cities."),
    [
        ("Cheapest with at most k stops", """
<p>Return the cheapest price from <code>src</code> to <code>dst</code> using at most k stops (k + 1 flights), or -1.</p>
<pre class="treebox">n = 4, flights = [[0,1,100],[1,2,100],[2,0,100],[1,3,600],[2,3,200]]
src 0, dst 3, k = 1 → 700     # 0 → 1 → 3
src 0, dst 3, k = 2 → 400     # 0 → 1 → 2 → 3</pre>"""),
    ],
    nudges=[
        ("You run plain Dijkstra on price", "Can the cheapest path to a city use too many stops to continue?",
         "Yes. Plain Dijkstra keeps one best price per city and loses the cheaper-but-shorter path. Put the stop count in the state, or use Bellman-Ford for k + 1 rounds."),
    ],
    solution="""<p>Bellman-Ford limited to k + 1 rounds: each round relaxes every flight using a copy of the previous round's prices, so a path never uses more flights than rounds. O(k × E). Or Dijkstra over (city, stops), skipping states past k stops.</p>""",
)

QUERY_PLAN = P(
    "query-plan-pruning", "Column Pruning and Filter Pushdown",
    "Rewrite a query plan tree: drop unused columns, move filters down",
    "On the Databricks new grad question lists. Details here are ours; the reported statement is longer.",
    q("A query plan is a tree of <code>Scan(table, columns)</code>, <code>Filter(predicate, child)</code>, <code>Project(columns, child)</code> and <code>Join(left, right, key)</code> nodes. Each predicate knows which columns it uses."),
    [
        ("Prune columns", "<p>Rewrite the plan so every Scan reads only the columns something above it actually uses: the final output, a filter, or a join key.</p>"),
        ("Push filters down", q("Now move each Filter as close to the Scans as it can go.") + "<p>A filter can move below a Project if it only uses columns the Project keeps, and below a Join onto the side that has all its columns. Split <code>A AND B</code> predicates so each part can move separately.</p>"),
    ],
    nudges=[
        ("You prune top-down and forget the join keys", "Does a Join need its key column even if nobody above uses it?",
         "Yes. Pass a set of required columns down the tree; each node adds what it needs itself (predicate columns, join keys) before passing it on."),
    ],
    solution="""<p><b>Pruning:</b> recursive rewrite with the set of columns required from above. Project: required = its columns ∩ required from above, plus nothing more. Filter: required ∪ predicate columns. Join: split required by side, plus the key on each side. Scan: keep columns ∩ required. <b>Pushdown:</b> another recursive pass that carries a list of conjuncts; at each node, push a conjunct to the child that has all its columns, and leave it where it is otherwise. Mention why it matters: less I/O, and filters that reach the Scan can use file statistics to skip data.</p>""",
)

DATABRICKS = [MODES, IP_FIREWALL, TIC_TAC_TOE, HIT_COUNTER, FIB_TREE, REVENUE, LOGGER, ANAGRAM_INDEX]
DATABRICKS_MORE = [DELTA, LAZY_ARRAY, SNAPSHOT_SET, TIME_KV, HOUSE_ROBBER, ISLAND, FLIGHTS, QUERY_PLAN]
