"""Question bank: Databricks SWE intern practice problems.

Same entry format as bank_a (see P there). These show under the Databricks
problem set in the pad's top bar, not in the Jane Street bank.
"""
from bank_a import P, q

MODES = P(
    "modes-of-transport", "Modes of Transport",
    "Fastest mode from S to D on a grid, then three follow-ups",
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
    "First-match ALLOW/DENY for an IP → check a whole CIDR block",
    "Reported Databricks intern question; also reported in a new grad phone screen.",
    q("Write a firewall. It's built from an ordered list of rules, and answers whether an IPv4 address is allowed."),
    [
        ("Check an address", """
<p>Implement <code>IpFirewall(rules)</code> and <code>query(ip)</code>. Each rule is <code>(action, ip_or_cidr)</code> with action <code>"ALLOW"</code> or <code>"DENY"</code>. A bare IP means <code>/32</code>. The first rule that matches decides; if none matches, return <code>"DENY"</code>.</p>
<pre class="treebox">rules = [("ALLOW", "192.168.100.5/30"),
         ("DENY",  "10.0.0.0/8"),
         ("ALLOW", "10.1.2.3")]

query("192.168.100.4") → "ALLOW"
query("192.168.100.8") → "DENY"
query("10.1.2.3")      → "DENY"
query("8.8.8.8")       → "DENY"</pre>"""),
        ("Check a whole block", q("Now the target can be a whole CIDR block, not just one address.") + """
<p>Write <code>access_ok(rules, target_cidr)</code>: return true if and only if every address in <code>target_cidr</code> is allowed. For <code>"123.45.67.89/20"</code>, every address in that block must be allowed.</p>
<pre class="treebox">access_ok(rules, "192.168.100.4/30") → true
access_ok(rules, "192.168.100.0/29") → false</pre>"""),
    ],
    clarify=[
        ("Are the addresses always valid IPv4?", "Yes. Four octets, 0 to 255."),
        ("Can a rule's base address have bits set below its prefix, like 192.168.100.5/30?", "Yes. Only the first k bits of the base matter."),
        ("How many rules and queries?", "Thousands of rules, many more queries. Ask whether to optimize query time."),
        ("What's the default if no rule matches?", "DENY."),
    ],
    nudges=[
        ("You're comparing addresses as strings", "How would you check whether two addresses share their first 27 bits?",
         "Parse to a 32-bit integer; compare (ip & mask) with (base & mask), where mask = ~0 << (32 − prefix)."),
        ("Part 2: you're enumerating every address in the block", "How many addresses are in a /8?",
         "16 million. Walk the rules in order instead, tracking which part of the block is still undecided. A rule either covers that part, sits inside it, or misses it."),
    ],
    solution="""
<div class="say"><span class="lbl">Part 1</span><p>"I'll parse each rule once into (action, base & mask, mask). A query parses the IP to an int and returns the first rule where ip & mask equals the stored base. O(R) per query, O(1) extra memory. If queries dominate, a binary trie on the bits gives O(32), keeping the smallest rule index at each node."</p></div>
<div class="say"><span class="lbl">Part 2</span><p>"Treat every CIDR as an integer range [low, high]. Keep the target's still-unresolved ranges, starting with the whole target. Walk the rules in order: intersect the rule's range with what's unresolved. A DENY rule that hits anything means some address is denied first, so return false. An ALLOW rule that hits removes those parts from the unresolved list. If nothing is left unresolved, return true. If rules run out with addresses still unresolved, they fall to the default DENY: return false."</p></div>""",
)

TIC_TAC_TOE = P(
    "tic-tac-toe", "Tic-Tac-Toe (k in a row)",
    "m × n board, k in a row wins → play against a bot",
    "Reported Databricks intern question.",
    q("Write the game logic for tic-tac-toe on an m × n board between two players."),
    [
        ("Play", """
<ul>
<li>A player who places k of their marks in a horizontal, vertical or diagonal row wins.</li>
<li>Every move is valid and goes on an empty cell. Players alternate. Once someone wins, no more moves are made.</li>
</ul>
<p>Implement <code>TicTacToe(m, n, k)</code> and <code>move(row, col, player)</code>, which returns 0 if there's no winner after the move, or 1 or 2 if that player has won. After each move, print the board with X for player 1 and O for player 2, one row per line, like <code>|X| |O|</code>.</p>
<p>Example on 3 × 3 with k = 3: moves (0,0,1), (0,2,2), (2,2,1), (1,1,2), (2,0,1), (1,0,2), (2,1,1) return 0, 0, 0, 0, 0, 0, 1.</p>"""),
        ("Add a bot", q("Now let me play against the computer. Add a bot that chooses its own move.") + """
<p>Start with a bot that plays a random empty cell. Then make it smarter.</p>"""),
    ],
    clarify=[
        ("What if the board fills up with no winner?", "That's a draw. Return -1."),
        ("Can k be bigger than the board?", "No, k ≤ max(m, n), and a line has to fit on the board."),
        ("Do I need to validate moves?", "No, moves are guaranteed valid."),
    ],
    nudges=[
        ("Each move rescans the whole board", "What does a move cost on a 1,000 × 1,000 board?",
         "Only lines through the new piece can have become a win. Count matching marks outward from it in each direction."),
        ("Part 2: the bot is random and you're done", "Would you lose to this bot?",
         "Never. A simple heuristic beats it: win if you can this move, otherwise block the opponent's winning move, otherwise random."),
    ],
    solution="""
<div class="say"><span class="lbl">Part 1</span><p>"Store the board and a count of placed marks. After placing, for each of the four directions (0,1), (1,0), (1,1), (1,−1), count matching marks outward from the new cell both ways, stopping at the edge or a different mark. If 1 + both counts ≥ k, this player wins. If the board is full and nobody won, it's a draw."</p></div>
<p><b>Cost:</b> a move is O(k) (eight walks of at most k − 1 cells), printing is O(m × n), and the board is O(m × n) space.</p>
<p><b>Bot:</b> a method that picks the bot's move. Random: list the empty cells and pick one. Heuristic: for each empty cell, check if placing the bot's mark wins (play it); then check if the opponent placing there would win (block it); otherwise play randomly. Reuse the same direction-count helper for both checks.</p>""",
)

HIT_COUNTER = P(
    "qps-kv-store", "Queries Per Second (Key-Value Store)",
    "A key-value store that reports its own get and put load → a month → an interval",
    "Reported Databricks intern question.",
    q("Implement a key-value store that also reports how busy it is."),
    [
        ("Store and load", """
<pre class="treebox">class KeyValueStore:
    def __init__(self): ...
    def put(self, key, value): ...   # add or overwrite
    def get(self, key): ...          # the value, or None if the key doesn't exist
    def avg_get_load(self): ...      # average gets per second over the past 5 minutes
    def avg_put_load(self): ...      # average puts per second over the past 5 minutes</pre>
<p>Use whole seconds: <code>int(time.time())</code>.</p>"""),
        ("The last month", q("Now product wants the QPS over the last month instead of the last 5 minutes.")),
        ("Any interval", q("Now give me the QPS for any interval inside the last 2 hours.")),
        ("Testing", q("How would you test this?"), "talk"),
    ],
    clarify=[
        ("Does a get for a missing key count toward the load?", "Yes, every call to get counts."),
        ("What if the store is less than 5 minutes old?", "Average over the time it has existed, not over 300 seconds."),
        ("How many calls per second?", "Could be thousands. Ask what that does to your memory."),
    ],
    nudges=[
        ("You store one timestamp per call", "What happens to memory at 10,000 gets a second?",
         "Store (second, count) pairs instead. There are at most 300 distinct seconds in the window, so memory and work are bounded by the window, not by traffic."),
        ("You divide by 300 from the first second", "The store was created 10 seconds ago and got 10 gets. What's the load?",
         "1 per second, not 10/300. Remember the creation time and divide by min(300, now − created)."),
        ("Part 2: you kept per-second entries for a month", "How many entries is that?",
         "About 2.6 million. Bucket coarser (say 5-minute buckets) and accept a little imprecision at the edges."),
    ],
    solution="""
<div class="say"><span class="lbl">Part 1</span><p>"A dict for the data, and one deque per operation holding [second, count]. Every method first evicts entries older than now − 300 from the front. A call increments the last entry if it's this second, else appends [now, 1]. The load is the sum of counts divided by min(300, seconds since creation). Each deque has at most 300 entries, so every method is O(300) = O(1), and memory is O(1) beyond the data itself."</p></div>
<p><b>Naive version to mention:</b> one timestamp per call. Time and memory then grow with traffic, not with the window.</p>
<p><b>The last month:</b> per-second entries are too many. Keep counts in coarser buckets (5 minutes, or an hour) with a small wrapper; you lose at most one bucket of precision at each end, which doesn't matter over a month.</p>
<p><b>Any interval in the last 2 hours:</b> keep the per-second entries for 2 hours, sorted by time, with prefix sums. Binary-search the first entry ≥ the interval's start and the last ≤ its end; the count is a prefix-sum difference. O(log n) per query.</p>
<p><b>Testing:</b> don't sleep for 5 minutes. Inject a clock (a function or object returning "now") and mock it in tests to jump time forward, cross the 300-second boundary, and check the under-5-minutes case.</p>""",
)

FIB_TREE = P(
    "fibonacci-tree-path", "Fibonacci Tree Path",
    "Directions between two nodes of a numbered Fibonacci tree → post-order numbering",
    "Reported Databricks intern question.",
    """<p>A Fibonacci tree T<sub>n</sub> is defined recursively:</p>
<ul>
<li>T<sub>0</sub> is an empty tree.</li>
<li>T<sub>1</sub> is a single root.</li>
<li>For n ≥ 2, T<sub>n</sub> is a root with T<sub>n−2</sub> as its <b>left</b> subtree and T<sub>n−1</sub> as its <b>right</b> subtree.</li>
</ul>
<p>Number the nodes 0 to N − 1 in pre-order (root, left, right). Here is T<sub>4</sub>:</p>
<pre class="treebox">        0
      /   \\
     1     3
      \\   / \\
       2 4   5
              \\
               6</pre>""",
    [
        ("Find the path", """
<p>Implement <code>fibPath(n, start, end)</code>: the moves from <code>start</code> to <code>end</code> in T<sub>n</sub>, where <code>U</code> goes to the parent, <code>L</code> to the left child and <code>R</code> to the right child.</p>
<pre class="treebox">fibPath(4, 2, 4) → "UURL"    # 2 → 1 → 0 → 3 → 4
fibPath(4, 0, 6) → "RRR"</pre>"""),
        ("Post-order", q("Now the tree is numbered in post-order (left, right, root) instead. What changes?") + """
<p>In post-order, T<sub>4</sub>'s root is 6 and <code>fibPath(4, 0, 3)</code> is <code>"UURRR"</code>.</p>"""),
        ("Worst case and testing", q("What's the worst case for your solution, and how would you test it?"), "talk"),
    ],
    clarify=[
        ("Is the tree given to me?", "No, only n. You work out its shape."),
        ("Can start equal end?", "Yes; return an empty path."),
        ("How big can n get?", "Assume large enough that you shouldn't build the tree."),
    ],
    nudges=[
        ("You build the tree as nodes", "How many nodes does T<sub>40</sub> have?",
         "Hundreds of millions. size(n) = size(n − 2) + size(n − 1) + 1 tells you, from a label, whether a node is the root, in the left subtree or in the right one."),
        ("You're searching the whole tree for each node", "In pre-order, what's the label of the left child? Of the right child?",
         "Left child = v + 1; right child = v + 1 + size of the left subtree. Walk down from the root comparing against those boundaries."),
    ],
    solution="""
<div class="say"><span class="lbl">Approach</span><p>"First a size array: size[0] = 0, size[1] = 1, size[k] = size[k − 2] + size[k − 1] + 1. T4 has 7 nodes, T5 has 12. To get the root-to-x path in T_k: if x is the root, stop; if x ≤ size[k − 2], go L with x − 1 in T_{k−2}; else go R with x − 1 − size[k − 2] in T_{k−1}. Do that for start and end, drop their common prefix (that's the lowest common ancestor), then the answer is one U per remaining step of start's path, followed by the rest of end's path."</p></div>
<p><b>Cost:</b> the size array is O(n). The depth of T<sub>n</sub> is n (always going right), so each path is O(n): O(n) time and space overall.</p>
<p><b>Post-order:</b> same idea, only the boundaries change. The root of T<sub>k</sub> at v has its right child at v − 1 and its left child at v − 1 − size[k − 1].</p>
<p><b>Worst case:</b> both nodes are deep leaves on different sides, so both paths are about n long. <b>Testing:</b> hand-check every pair in T<sub>2</sub>…T<sub>4</sub>, then compare against a brute force that builds small trees explicitly and finds the path with parent pointers.</p>""",
)

REVENUE = P(
    "referral-tracking", "Referral Tracking",
    "Users with tokens and referrers → top k by tokens → bonus from a whole referral network",
    "Reported Databricks intern question.",
    q("Build a class that manages users and a multi-level referral program."),
    [
        ("Users and tokens", """
<ul>
<li><code>App(bonus)</code>: <code>bonus</code> is the tokens a user gets for each referral.</li>
<li><code>addUser(tokens, referrer=None)</code>: creates a user with <code>tokens</code> and returns its id (sequential, starting at 0). If <code>referrer</code> is given, the referrer gains <code>bonus</code> tokens.</li>
<li><code>getTokens(user_id)</code>: the user's current tokens.</li>
<li><code>addTokens(user_id, amount)</code>: adds <code>amount</code> tokens to the user.</li>
</ul>
<pre class="treebox">app = App(10)
app.addUser(100)      → 0
app.addUser(50, 0)    → 1     # user 0 now has 110
app.addUser(30, 1)    → 2     # user 1 now has 60
app.getTokens(0)      → 110</pre>"""),
        ("Top k", """<p><code>getTopK(k, threshold)</code>: the ids of up to k users with the most tokens, among users with at least <code>threshold</code> tokens, highest first.</p>
<pre class="treebox">app.getTopK(2, 50)    → [0, 1]
app.addTokens(2, 100)
app.getTopK(2, 50)    → [2, 0]</pre>"""),
        ("Bonus from the network", """<p><code>getBonusTokens(user_id)</code>: the total bonus the user has earned from their whole downstream referral network: everyone they referred directly or indirectly. Each user in that network contributes one bonus.</p>
<pre class="treebox">app.getBonusTokens(0) → 20    # users 1 and 2
app.getBonusTokens(1) → 10</pre>"""),
        ("Which operation is hot?", q("Suppose getTopK is called far more often than users are added or tokens change. Is your design right for that? What if it's the other way round?"), "talk"),
    ],
    clarify=[
        ("How are ties in getTopK ordered?", "Lower id first."),
        ("Does a referrer's bonus also flow up to their own referrer?", "No. In Parts 1–2 only the direct referrer gains tokens. Part 3 asks about the whole network."),
        ("Can a user refer themselves?", "No; referrers are always existing users."),
    ],
    nudges=[
        ("getTopK sorts every user on every call", "What if getTopK is called thousands of times between writes?",
         "Keep a list sorted by (−tokens, id) and update it on every write. A query then just walks the front of the list."),
        ("Part 3: you counted only direct referrals", "User 0 referred user 1, who referred user 2. Does 2 count for 0?",
         "Yes, the network is everything downstream. Keep each user's referrals as an adjacency list and walk it with a BFS."),
    ],
    solution="""
<div class="say"><span class="lbl">Parts 1–2</span><p>"A list of tokens indexed by id, an adjacency list of referrals, and a list of (−tokens, id) kept sorted. addUser appends and inserts into the sorted list with bisect. Any change to a user's tokens (a referral bonus or addTokens) goes through one helper: find and delete the old (−old, id) entry with bisect_left, insert (−new, id) with bisect_right. getTopK walks the sorted list until it has k ids or tokens drop below the threshold."</p></div>
<div class="say"><span class="lbl">Part 3</span><p>"BFS from the user's referrals over the adjacency list, adding one bonus per user visited. O(size of that user's network)."</p></div>
<p><b>Costs:</b> getTokens O(1); addUser and addTokens O(n), from inserting into the middle of a Python list (the binary searches are O(log n)); getTopK O(k). A balanced tree or sorted container makes writes O(log n).</p>
<p><b>Part 4:</b> this trades slow writes for very cheap reads, which is right when getTopK is frequent and k is small. If writes dominate and top-k queries are rare, keep the data unsorted and sort (or use a size-k heap) only when getTopK is called.</p>""",
)

LOGGER = P(
    "thread-safe-logger", "Thread-Safe Logger",
    "Many writers, no interleaving → a slow disk → bursts and shutdown",
    "Reported in the Databricks concurrency round. Durable-writer versions are also on the question lists.",
    q("Many threads call <code>log(message)</code>. Lines must never interleave, and logging shouldn't slow the callers down much."),
    [
        ("Make it safe", "<p>Write a <code>Logger</code> with <code>log(message)</code> that's safe to call from many threads. Each message comes out as one whole line.</p><p class=\"meta\">Java is the natural language here. Python's <code>threading</code> works too; JavaScript has no shared-memory threads.</p>"),
        ("Slow disk", q("Writing to disk is slow. log() should return quickly even while the disk is busy.")),
        ("Bursts and shutdown", q("For a while, messages arrive faster than the disk can take them. What happens in your design? Then: how does the program shut down without losing messages?")),
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
    "Chained map() that runs only when indexOf() needs it → memoization",
    "Reported Databricks intern question.",
    q("Build an array whose transformations are lazy: a chain of <code>map</code> calls is recorded, and only applied when a search needs it."),
    [
        ("map and indexOf", """
<ul>
<li><code>LazyArray(data)</code>: wraps an initial array of values.</li>
<li><code>map(fn)</code>: returns a new LazyArray with <code>fn</code> added to its pipeline. It doesn't apply <code>fn</code>, and calls can be chained.</li>
<li><code>indexOf(x)</code>: the first index whose transformed value equals <code>x</code>, or -1.</li>
</ul>
<pre class="treebox">LazyArray([10, 20, 30, 40, 50]).map(x → x * 2).indexOf(40)                → 1
LazyArray([10, 20, 30, 40, 50]).map(x → x * 2).map(x → x * 3).indexOf(240) → 3</pre>"""),
        ("Memoization", q("Now the functions are expensive and indexOf gets called a lot.") + """
<p>Change the constructor to <code>LazyArray(data, function_memory=None)</code>, where <code>function_memory</code> is an optional dictionary used to cache function results, and use it to avoid recomputing.</p>"""),
    ],
    clarify=[
        ("Does map change the original array?", "No. Each LazyArray keeps its own pipeline; earlier ones are unaffected."),
        ("Are the functions pure?", "Yes, same input, same output."),
    ],
    nudges=[
        ("map applies fn right away", "What if nobody ever calls indexOf?",
         "Then the work was wasted. map should only record fn: a new object with the same data and the old pipeline plus fn."),
        ("Part 2: your cache returns the wrong kind of value", "What does a cache hit give you, and what does indexOf return?",
         "Cache the transformed value for a (value, pipeline) key, then compare it with x as usual. Don't return the cached value as an index."),
    ],
    solution="""
<div class="say"><span class="lbl">Part 1</span><p>"Store the data and a list of functions. map returns LazyArray(same data, fns + [fn]), so each chain keeps its own history and nothing is computed. indexOf loops over the data, runs each value through every function, and returns the first index that matches."</p></div>
<p><b>Cost:</b> constructor O(n) (one copy of the data), map O(1) plus copying the pipeline, indexOf O(n × k) for k functions. Space O(n + k).</p>
<p><b>Memoization:</b> share one dictionary across the chain. Key it by (original value, the pipeline as a tuple) and store the transformed value; on a hit, skip the functions and compare. Trade-off: fewer repeated calls in exchange for memory to hold the results.</p>""",
)

SNAPSHOT_SET = P(
    "snapshot-set", "Snapshot Set",
    "A set you can keep changing while you iterate over a snapshot of it",
    "Reported Databricks intern question.",
    q("Build a set you can iterate over as a snapshot, while still adding and removing elements."),
    [
        ("Snapshot iteration", """
<p>Implement <code>add(x)</code>, <code>remove(x)</code>, <code>contains(x)</code> and an iterator.</p>
<ul>
<li><b>Snapshot:</b> an iterator returns exactly the elements present when it was created, whatever happens afterwards.</li>
<li><b>Live operations:</b> add, remove and contains keep working while an iterator is active.</li>
<li><b>Single iterator:</b> only one iterator may be active at a time.</li>
<li><b>Space:</b> don't copy the entire set when creating an iterator.</li>
</ul>
<pre class="treebox">add(1); add(2); add(3)
it = iterator()
remove(2); add(4)
list(it)    → [1, 2, 3]
contains(2) → false</pre>"""),
    ],
    clarify=[
        ("What happens if someone asks for a second iterator while one is active?", "Raise an error. The first must finish first."),
        ("Can an element be removed and added back?", "Yes, any number of times."),
        ("Does iteration order matter?", "No."),
    ],
    nudges=[
        ("iterator() copies the set", "The spec says not to copy the set. What could you record instead?",
         "Versions. Keep a counter that goes up on every change, and record for each element when it was added and when it was removed."),
        ("An element removed and re-added shows up wrong", "Add 5, take an iterator, remove 5, add 5 again. What should the iterator see?",
         "5, once. Re-adding has to update the element's added version, and the iterator checks added ≤ its version < removed."),
    ],
    solution="""
<div class="say"><span class="lbl">Approach</span><p>"A dict from element to (added_version, removed_version), with removed = infinity while it's present, plus a version counter bumped on every real change. add on a new or removed element sets (version, inf); remove on a present element sets its removed version. contains checks removed == inf. The iterator records the version when it's created and yields elements with added ≤ version < removed. A flag on the set enforces one active iterator, cleared when the iterator finishes."</p></div>
<p><b>Cost:</b> add, remove and contains are O(1). Creating the iterator is O(1) if it filters lazily as it walks; precomputing the snapshot list at creation is simpler but O(n). <b>Trade-off:</b> removed elements stay in the dict, so you'd clean them up once no iterator can still see them.</p>""",
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
    "Largest connected group of 1s in a grid → a grid too big for memory",
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
        ("Push filters down", q("Now move each Filter as close to the Scans as it can go.") + "<p>A filter can move below a Project if it only uses columns the Project keeps, and below a Join onto the side that has all its columns.</p>"),
    ],
    nudges=[
        ("You prune top-down and forget the join keys", "Does a Join need its key column even if nobody above uses it?",
         "Yes. Pass a set of required columns down the tree; each node adds what it needs itself (predicate columns, join keys) before passing it on."),
    ],
    solution="""<p><b>Pruning:</b> recursive rewrite with the set of columns required from above. Project: required = its columns ∩ required from above, plus nothing more. Filter: required ∪ predicate columns. Join: split required by side, plus the key on each side. Scan: keep columns ∩ required. <b>Pushdown:</b> another recursive pass that carries a list of conjuncts; at each node, push a conjunct to the child that has all its columns, and leave it where it is otherwise. Mention why it matters: less I/O, and filters that reach the Scan can use file statistics to skip data.</p>""",
)


SMALLEST_RANGE = P(
    "smallest-range-k-lists", "Smallest Range Covering K Lists",
    "Smallest range with at least one number from each sorted list",
    "Reported Databricks intern question (LeetCode 632).",
    q("You have k lists of integers, each sorted in non-decreasing order."),
    [
        ("Find the range", """
<p>Find the smallest range <code>[a, b]</code> that includes at least one number from each of the k lists. Range [a, b] is smaller than [c, d] if b − a &lt; d − c, or if b − a == d − c and a &lt; c.</p>
<pre class="treebox">[[4,10,15,24,26], [0,9,12,20], [5,18,22,30]]  → [20, 24]
[[1,2,3], [1,2,3], [1,2,3]]                    → [1, 1]</pre>
<p class="meta">In the first example, 24 is from list 1, 20 from list 2 and 22 from list 3.</p>"""),
    ],
    clarify=[
        ("Can a list be empty?", "No, every list has at least one number."),
        ("How big is it?", "Up to a few thousand lists, and tens of thousands of numbers in total."),
    ],
    nudges=[
        ("You're checking every pair of candidate endpoints", "How many candidates is that with 50,000 numbers?",
         "Too many. Keep exactly one current number from each list. The range is [smallest current, largest current]. Which one should move forward?"),
        ("You advance the largest pointer", "Can moving the largest number up ever make the range smaller?",
         "No. Only advancing the smallest can shrink it, so pop the minimum from a heap and push the next number from that same list."),
    ],
    solution="""
<div class="say"><span class="lbl">Approach</span><p>"A min-heap with one (value, list index, position) per list, and the largest value seen so far. The current range is [heap minimum, largest]. Repeatedly pop the minimum, record the range if it's smaller than the best, and push the next number from the same list, updating the largest. Stop as soon as a popped list has no next number, because no range can include that list any more without its current number."</p></div>
<p><b>Why it works:</b> the heap always holds one number per list, and the only move that can shrink the range is advancing the smallest number. <b>Cost:</b> O(k log k) to build the heap, then O(N log k) for N numbers in total; O(k) space.</p>""",
)

TETRIS = P(
    "tetris-drop", "Tetris Drop",
    "Find where a falling piece comes to rest",
    "Reported Databricks intern question.",
    "",
    [
        ("Drop the piece", """
<p>You're given:</p>
<ul>
<li>A grid (N × M) of 0s (empty) and 1s (settled blocks).</li>
<li>A piece (P × Q): a 2D matrix where the 1s form the shape.</li>
<li><code>start_col</code>: the leftmost column of the piece, which starts held above the grid.</li>
</ul>
<p>The piece falls straight down one row at a time, without rotating. It comes to rest when moving it down one more row would put any of its blocks below the grid's bottom (row ≥ N) or on top of a settled block. Return the grid row index of the bottom edge of the piece's bounding box when it comes to rest.</p>
<pre class="treebox">grid = [[0,0,0,0],
        [0,0,0,0],
        [0,1,0,0],
        [1,1,0,1]]

piece [[1,1],
       [0,1]]  at start_col 0  → 1
piece [[1,1],
       [1,0]]  at start_col 2  → 3</pre>"""),
    ],
    clarify=[
        ("What if the piece doesn't fit horizontally at start_col?", "Raise an error."),
        ("Can the piece have empty rows or columns in its matrix?", "Yes. Only the 1s collide."),
        ("Do full rows clear?", "No, just where it lands."),
    ],
    nudges=[
        ("You simulate one row at a time and check every cell", "How much work for a tall grid?",
         "O(N × P × Q). Instead, for each column you only need the highest settled block in the grid and the lowest block of the piece."),
    ],
    solution="""
<div class="say"><span class="lbl">Approach</span><p>"Check start_col + Q ≤ M. For each grid column, find the surface: the first row with a 1, or N if empty. For each piece column, find its lowest 1. Each piece column limits how far the piece can drop: its lowest block must end at surface − 1 in that grid column. The piece drops by the smallest of those limits, and the answer is that drop plus the row of the piece's lowest block."</p></div>
<p><b>Cost:</b> O(N × Q) to find the surfaces under the piece (or O(N × M) for the whole grid) and O(P × Q) for the piece. Space O(Q).</p>
<p><b>Edge cases:</b> empty piece columns don't constrain anything; a piece with no 1s at all; a piece that rests partly above the grid's top.</p>""",
)

RLE = P(
    "rle-bit-packing", "Run-Length and Bit-Packing Encoder",
    "Encode values into RLE and bit-packed runs → decode them back",
    "Reported Databricks intern question.",
    """<p><b>Run-length encoding (RLE)</b> writes repeated values as a value and a count: 1, 1, 1, 1, 1 becomes 1 (5).</p>
<p><b>Bit-packing (BP)</b> stores small integers in fewer than 4 bytes each: 2, 3, 4 and 5 all fit in 3 bits, so the four of them take 12 bits instead of 16 bytes.</p>
<p>A <b>run</b> is a sequence of values that all use the same encoding. Runs can interleave: [RLE, BP, RLE, RLE, BP, …].</p>""",
    [
        ("Encode", """
<p>The rules:</p>
<ul>
<li>Every value goes into a run, and the order of values doesn't change.</li>
<li>An RLE run has at least 8 values, except the last run, which can have fewer.</li>
<li>Once started, an RLE run extends as far as possible: it continues as long as the value repeats.</li>
<li>A BP run has exactly 8 values, except the last run, which can have fewer.</li>
<li>RLE is the default. BP is used only when RLE can't apply, because there aren't enough repeated values.</li>
</ul>
<p>Write an <code>Encoder</code> with <code>encode(value)</code>, called once per value, and <code>finalize()</code>, which returns the list of runs.</p>
<pre class="treebox">[1, 1, 1]                             → RLE(1, 3)
[1, 1, 1, 1, 2, 3, 4, 5]              → BP([1, 1, 1, 1, 2, 3, 4, 5])
[1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 4, 5]  → RLE(1, 8), BP([2, 3, 4, 5])
[1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 4, 5]  → RLE(1, 9), BP([2, 3, 4, 5])</pre>"""),
        ("Decode", q("Now read it back, one value at a time.") + """
<p>Write a <code>Decoder(encoded)</code> with <code>has_next()</code> and <code>decode()</code>, which returns the next original value.</p>"""),
    ],
    clarify=[
        ("Do I actually pack bits?", "No. Represent runs as tuples like ('RLE', value, count) and ('BP', [values])."),
        ("Can encode be called after finalize?", "No."),
    ],
    nudges=[
        ("You collect all the values first and encode at the end", "encode is called once per value from a stream. What do you need to remember between calls?",
         "Only the run in progress and its type. Decide when a value arrives whether it extends that run, closes it, or switches it."),
        ("A short repeat at the start ends up as its own RLE run", "Is an RLE run of 4 allowed in the middle?",
         "No, only at the very end. Fewer than 8 repeats followed by a different value means those values belong in a BP run."),
    ],
    solution="""
<div class="say"><span class="lbl">Encoder</span><p>"Keep the current run and its type. A new run starts as RLE. While RLE: a repeat extends it; a different value either closes it (if it already has 8 or more) and starts a new RLE run, or turns it into BP (fewer than 8). While BP: append until it has 8, then close it and start a new RLE run with the next value. finalize closes the last run, which may be short of either rule."</p></div>
<div class="say"><span class="lbl">Decoder</span><p>"An index into the runs and an index within the current run. decode loads the next run when the current one is used up, then returns the RLE value (count times) or the next BP value. has_next is true while there's a value left in the current run or another run after it."</p></div>
<p><b>Cost:</b> O(1) amortized per value both ways; memory is one run (at most 8 values for BP) plus the output. <b>Watch for:</b> an RLE run that switches to BP and then sees 8+ repeats, and the rule for the last run.</p>""",
)

IP_TO_CIDR = P(
    "ip-to-cidr", "IP Range to CIDR Blocks",
    "Cover a range of IP addresses with as few CIDR blocks as possible",
    "Reported Databricks intern question (LeetCode 751).",
    """<p>An IPv4 address is a 32-bit unsigned integer, printed as four 8-bit groups in decimal, separated by dots: <code>00001111 10001000 11111111 01101011</code> is <code>15.136.255.107</code>.</p>
<p>A CIDR block is a base address, a slash, and a prefix length k. It covers every address whose first k bits match the base: <code>123.45.67.89/20</code> covers <code>01111011 00101101 0100xxxx xxxxxxxx</code>.</p>""",
    [
        ("Cover the range", """
<p>Given a start address <code>ip</code> and a count <code>n</code>, return the shortest list of CIDR blocks that covers exactly the addresses <code>[ip, ip + n − 1]</code>: nothing outside the range. Any shortest answer is fine.</p>
<pre class="treebox">ipToCIDR("255.0.0.7", 10) → ["255.0.0.7/32", "255.0.0.8/29", "255.0.0.16/32"]</pre>"""),
    ],
    clarify=[
        ("Can the range wrap past 255.255.255.255?", "No."),
        ("How big can n be?", "Up to 1,000."),
    ],
    nudges=[
        ("You emit one /32 per address", "That covers the range. Is it the shortest list?",
         "No. A block of size 2^j can start at an address only if that address is a multiple of 2^j. Take the biggest block that's aligned and doesn't overshoot."),
    ],
    solution="""
<div class="say"><span class="lbl">Approach</span><p>"Convert the IP to an int. While n &gt; 0: the largest aligned block at cur is cur &amp; −cur (the lowest set bit; 2^32 if cur is 0). Shrink it to the largest power of two ≤ n. Emit cur/(32 − log2(size)), then advance cur by size and reduce n by size. Convert back with shifts and masks."</p></div>
<p><b>Why greedy is optimal:</b> at each step the biggest legal block covers the most addresses without leaving the range, and taking less would only leave more to cover from a worse-aligned start. <b>Cost:</b> O(log n) blocks, about 2 × 32 at most.</p>""",
)

STRING_INTERVALS = P(
    "string-intervals", "String Intervals (Covers)",
    "Delete a character from a cover → keep the cover maximal",
    "Reported Databricks intern question.",
    """<p>A string can be compressed as a list of intervals of a reference string:</p>
<pre class="treebox">reference: "ABC123ASDF1678ABC"
target:    "ABCDF678"
cover:     [(0, 3), (8, 10), (11, 14)]</pre>
<p>Each interval is [start, end) in the reference. Concatenating those slices in order gives the target.</p>""",
    [
        ("Delete", """
<p>Write <code>delete(cover, index)</code>: return the cover of the target with the character at <code>index</code> of the target deleted. You aren't given the reference string; you don't need it.</p>
<pre class="treebox">delete([(0, 3), (8, 10), (11, 14)], 3) → [(0, 3), (9, 10), (11, 14)]    # "ABCF678"</pre>"""),
        ("Maximum covers", """
<p>A <b>maximum cover</b> uses as few intervals as possible to represent the target. With reference <code>"abc123abc"</code>, <code>[(6, 9), (3, 6)]</code> and <code>[(0, 3), (3, 6)]</code> are not maximum covers of <code>"abc123"</code>, but <code>[(0, 6)]</code> is.</p>
<p>Write <code>delete(max_cover, ref_str, index)</code>: given a maximum cover and the reference string, return a maximum cover of the target with the character at <code>index</code> deleted.</p>
<pre class="treebox">delete([(0, 4)], "abcdacd", 1) → [(4, 7)]    # "acd"</pre>"""),
    ],
    clarify=[
        ("Is index always valid?", "Yes, 0 ≤ index &lt; target length."),
        ("Can intervals overlap in the reference?", "Yes, they're independent slices."),
    ],
    nudges=[
        ("Part 1: you rebuild the target string", "Do you need the characters at all?",
         "No. Walk the intervals keeping a running target position; split only the one interval that contains index."),
        ("Part 2: you split the interval and stop", "Is the result still as short as possible?",
         "Not always. After the deletion, neighbouring pieces may now match one longer slice of the reference. You have the reference: re-cover the new target."),
    ],
    solution="""
<div class="say"><span class="lbl">Part 1</span><p>"Walk the intervals with a running position in the target. The interval containing index splits into [start, start + offset) and [start + offset + 1, end), dropping empty pieces. Everything else is copied. O(number of intervals)."</p></div>
<div class="say"><span class="lbl">Part 2</span><p>"Rebuild the new target from the cover and the reference, delete the character, then cover it greedily from the left: at each position take the longest slice of the reference that matches. Greedy is optimal here, because any prefix of a matching slice also matches, so taking the longest never hurts."</p></div>
<p><b>Cost:</b> naive longest-match is O(|ref| × |target|) per rebuild; a suffix automaton on the reference makes each step linear in the match. <b>Faster idea to discuss:</b> only re-cover around the deletion. If you propose it, argue why the rest of the cover stays optimal, or find a case where it doesn't.</p>""",
)

WEB_CRAWLER = P(
    "web-crawler", "Multithreaded Web Crawler",
    "Crawl every page on one host → do it with many threads",
    "Reported Databricks question (LeetCode 1242).",
    q("You're given a start URL and an <code>HtmlParser</code> whose <code>getUrls(url)</code> returns the links on that page. It's a slow, blocking network call."),
    [
        ("Crawl", """
<p>Return every URL reachable from <code>startUrl</code> that has the same hostname as <code>startUrl</code>, each once, in any order. The hostname of <code>http://news.example.org/a/b</code> is <code>news.example.org</code>.</p>"""),
        ("Many threads", q("Each getUrls call takes about a second. Crawl with many threads at once.")),
    ],
    clarify=[
        ("Do http and https count as the same URL?", "Assume every URL uses http, and no URL has a port or a fragment."),
        ("Can pages link in cycles?", "Yes."),
        ("How many pages?", "Up to about 1,000."),
    ],
    nudges=[
        ("Your crawl loops forever", "What happens when two pages link to each other?",
         "Keep a seen set and add a URL to it when you schedule it, not when you finish it."),
        ("Part 2: threads share the seen set without a lock", "Two threads find the same new URL at once. What happens?",
         "Both may crawl it. Either guard the check-and-add with a lock, or keep all set updates on one coordinating thread and only run getUrls on the pool."),
    ],
    solution="""
<div class="say"><span class="lbl">Part 1</span><p>"BFS from startUrl with a seen set, enqueueing each new same-host URL once. O(pages + links) calls."</p></div>
<div class="say"><span class="lbl">Part 2</span><p>"A thread pool (say 16 workers). The main thread submits getUrls(startUrl) as a future and keeps a queue of futures. It pops a future, waits for its result, and for each new same-host URL adds it to seen and submits another getUrls. Only the main thread touches seen, so there's no lock, and the pool runs the slow calls in parallel. Stop when no futures are left."</p></div>
<p><b>Discussion:</b> pool size versus politeness to the host, timeouts and retries on getUrls, and how you'd distribute it across machines (partition URLs by hash, with a shared seen store).</p>""",
)

REDUNDANT = P(
    "redundant-connection", "Redundant Connection",
    "Find the edge that turns a tree into a graph with a cycle",
    "Reported Databricks question (LeetCode 684).",
    q("A tree of n nodes labeled 1 to n had one extra edge added between two different nodes that weren't already connected."),
    [
        ("Find the edge", """
<p>Given the edges, return an edge that can be removed so the graph becomes a tree of n nodes again. If there are several answers, return the one that appears last in the input.</p>
<pre class="treebox">[[1,2], [1,3], [2,3]]                → [2, 3]
[[1,2], [2,3], [3,4], [1,4], [1,5]]  → [1, 4]</pre>"""),
    ],
    clarify=[
        ("Is the graph directed?", "No."),
        ("How many nodes?", "Up to 1,000."),
    ],
    nudges=[
        ("You run a DFS from scratch for every edge", "That's O(n²). Can you process the edges once, in order?",
         "Union-find: an edge whose two ends already have the same root closes a cycle. The first such edge in order is the last one on that cycle in the input."),
    ],
    solution="""
<div class="say"><span class="lbl">Approach</span><p>"Union-find over n nodes. For each edge in order, find both roots; if they're equal, this edge closes a cycle, so return it. Otherwise union them by rank. With path compression and union by rank that's about O(n α(n))."</p></div>
<p><b>Why it returns the last such edge:</b> the cycle is complete only when its last edge in input order arrives, so that's the first edge union-find rejects.</p>""",
)

DATABRICKS = [MODES, HIT_COUNTER, FIB_TREE, SMALLEST_RANGE, TIC_TAC_TOE, REVENUE, TETRIS, RLE, LAZY_ARRAY,
              SNAPSHOT_SET, IP_FIREWALL, IP_TO_CIDR, STRING_INTERVALS, WEB_CRAWLER, REDUNDANT]
DATABRICKS_MORE = [LOGGER, ANAGRAM_INDEX, DELTA, TIME_KV, HOUSE_ROBBER, ISLAND, FLIGHTS, QUERY_PLAN]
