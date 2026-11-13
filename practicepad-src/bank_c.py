"""Question bank, part C: experimental onsite formats and unverified reports."""
from bank_a import P, q

SOLE_MATE = P(
    "sole-mate-review", "Sole Mate Code Review",
    "Review a diff for membership tiers → judge a purchase-ordering algorithm",
    "Experimental onsite round: code review. The original diff wasn't retained, so write the code yourself and review it.",
    q("Review two Python files from an online shoe store. Bugs are the priority."),
    [
        ("Membership tiers diff", """<p>The diff adds tiers from the member's current point balance; each tier discounts the final price:</p>
<ul><li>Bronze 0–99 points: 0%</li><li>Silver 100–199: 5%</li><li>Gold 200–499: 10%</li><li>Platinum 500+: 15%</li></ul>
<p>Review for bugs, readability, confusing naming and style. The diff contains exactly two bugs. Practice: write your own version of this code with plausible bugs, then review it out loud.</p>"""),
        ("Purchase ordering", """<p>The store wants to order purchases to minimize the customer's total. Mandatory purchases must all be bought; optional ones may be bought if that lowers the total. One dollar earns one point, points arrive after a purchase completes, a new tier applies only to later purchases, and several items may be grouped into one purchase.</p>
<p>The supplied algorithm, one tier at a time: enumerate subsets of remaining items; keep those reaching the next tier; estimate the loss of buying them before the discount and the gain of the discount on the remaining mandatory items; pick the qualifying subset with the smallest loss; stop when the loss exceeds the gain; buy the rest. Explain it, decide whether it's correct, and give a counterexample if not.</p>"""),
    ],
    clarify=[("Do I fix the bugs or just report them?", "Report them clearly, with the fix; prioritize."), ("Can one purchase skip several tiers?", "Yes. That's the key.")],
    solution="""
<h3>Part 1: the two bugs</h3>
<ol><li>Points-until-next-tier is reversed: 80 points should need 100 − 80 = 20, not 80 − 100 = −20.</li>
<li>Existing add-points and remove-points functions change the balance without updating the tier. Every mutation must keep the tier consistent, including downgrades.</li></ol>
<p>Other comments: centralize the tier thresholds instead of repeated range checks; <code>apply_discount</code> only computes a price, so the name misleads; floating-point prices converted to integer points need explicit rounding rules.</p>
<h3>Part 2: the algorithm is wrong</h3>
<p>It only looks one tier ahead, but one purchase can jump several tiers. Counterexample: tiers Bronze 0 (0%), Silver 100 (1%), Gold 101 (2%), Platinum 102 (99%). Mandatory [90, 100], optional [12]. Greedy: buying 100 first loses 1.00 and gains only 0.90 on the 90, so it stops: total 100 + 89.10 = 189.10. Better: buy 90 + 12 together (102 points, Platinum), then 100 at 99% off = 1: total 103.</p>
<p><b>How to run the round:</b> read everything first, rank findings (bugs, then correctness risks, then readability, then style), say which are blocking, and propose tests that would have caught each bug.</p>""",
)

CLUSTER = P(
    "cluster-scaling", "Cluster Endpoint Scaling",
    "Start and stop VMs from an endpoint list → apply a new endpoint list",
    "Experimental onsite round: AI-assisted coding in an existing codebase. Practice the workflow; the codebase isn't available.",
    q("A cluster of n virtual machines; each endpoint maps one-to-one to a VM, and the cluster is a list of endpoints. Supplied low-level APIs inspect and operate the VMs. There's no single start call: starting a VM composes several operations (reported as GET → SSH → RUN)."),
    [
        ("Start and stop", "<p>Understand the codebase and use the APIs to start or stop the VMs for the cluster's endpoints.</p>"),
        ("Scale", "<p>Given the old and new endpoint lists: a new endpoint on an existing path → restart both VMs for that path so each knows its sibling; a new path → start its VM; a removed path → stop its VM. Then review and explain the resulting code.</p>"),
    ],
    clarify=[("What if a start fails halfway?", "Discuss retries and leaving the cluster consistent."), ("Should new VMs start before old ones stop?", "Ask; usually yes, to avoid downtime.")],
    solution="""
<p><b>Diff by path:</b> group old and new endpoints by path. Paths only in new → start. Paths only in old → stop. Paths in both with more endpoints → start the new VM and restart all of that path's VMs.</p>
<p><b>Start helper:</b> wrap GET → SSH → RUN in one <code>startVm</code> with error handling, so the logic reads at the level of start/stop/restart.</p>
<p><b>AI-assisted rounds:</b> read the code yourself before prompting, give the AI precise small tasks, review every line it writes, run it, and explain your judgment calls (idempotency, partial failure, ordering). They grade your review, not the AI's typing.</p>""",
)

PNL_TABLE = P(
    "filtered-pnl", "Filtered PnL Table",
    "Sum PnL by filter and time → O(1) view → global filter changes → async PnL",
    "Unverified onsite report; cycle unclear.",
    q("<code>Table(filters, times)</code>, <code>addTrade(trade)</code>, <code>viewResult()</code> and <code>setGlobalFilter(f)</code>. Rows are filters (they may overlap), columns are times. Each cell is the sum of PnL for trades matching the row filter, at that column's time, and matching the current global filter (initially none)."),
    [
        ("Table", "<p>Keep results correct as trades arrive and the global filter changes. <code>viewResult()</code> must be O(1), independent of the number of trades.</p>"),
        ("Async PnL", "<p>PnL now comes from an async <code>getPnl(trade, time)</code>. Cache repeated calls, and keep the cache useful when the global filter changes.</p>"),
    ],
    clarify=[("How often does the global filter change compared with addTrade?", "Rarely; ask."), ("Is a filter a predicate on the trade?", "Yes.")],
    solution="""
<p><b>State:</b> a cached result matrix R × T, the list of all trades, and a cache of PnL per (trade, time).</p>
<p><b>addTrade:</b> if it passes the global filter, add its PnL to every matching row for every time: O(R·T). <b>viewResult:</b> return the cached matrix.</p>
<p><b>setGlobalFilter:</b> rebuild the matrix from stored trades using cached PnL values (no new getPnl calls): O(trades × R × T), acceptable because it's rare. If the global filter comes from a small known set, keep one matrix per filter.</p>
<p><b>Async:</b> cache promises keyed by (trade, time) so concurrent requests coalesce; when one resolves, add it to the cells only if the trade still matches the current global filter (tag work with a filter version and drop stale updates).</p>""",
)

GENERIC_FS = P(
    "generic-filesystem", "Generic File System Design",
    "In-memory file system → concurrency, auth, persistence, distribution",
    "Unverified onsite report; cycle unclear.",
    q("Design an in-memory file system."),
    [
        ("Core", "<p>Support <code>mkdir -p</code>, creating and writing files, reading files, deleting files and directories (define what happens to non-empty ones), and listing a directory in a defined order. Clarify Unix-style paths, the root, invalid or missing paths, and file-vs-directory name conflicts.</p>"),
        ("Follow-ups", "<ul><li>Concurrent operations and consistency.</li><li>Authentication and authorization.</li><li>Persistence and recovery.</li><li>Distributing metadata and data across machines.</li></ul>", "talk"),
    ],
    solution="""
<p><b>Core:</b> a tree of nodes: a directory has a sorted map name → child; a file has content. Parse paths by splitting on <code>/</code>, ignoring empty parts. mkdir -p walks and creates; writing to a path whose parent is missing or is a file is an error; delete of a non-empty directory requires a recursive flag.</p>
<p><b>Concurrency:</b> a read-write lock per node (lock parent then child, in path order to avoid deadlock) or one global lock to start. <b>Auth:</b> owner and permission bits or ACLs checked during path walks. <b>Persistence:</b> a write-ahead log plus periodic snapshots; replay on start. <b>Distribution:</b> a metadata service (sharded by path) plus chunk servers holding replicated file data, as in GFS/HDFS.</p>""",
)

SPARSE_STREAM = P(
    "sparse-stream", "Sparse Stream to Matrix Rows",
    "Turn (timestamp, code, value) records into dense rows → late arrivals",
    "Unverified phone report; cycle unclear.",
    q("There are M possible string codes. A stream of <code>(timestamp, code, value)</code> is ordered by timestamp, then code."),
    [
        ("Rows", "<p>Emit <code>(timestamp, vector)</code> rows of length M, positions in lexicographic code order, with −1 for codes missing at that timestamp. Emit each row as soon as its timestamp's records are all consumed.</p>"),
        ("Out of order", "<p>What changes if a small portion of codes arrive out of order? A small portion of whole records?</p>", "talk"),
    ],
    solution="""
<p><b>Core:</b> precompute code → index from the sorted codes. Keep the current timestamp and a vector filled with −1. On a record with the same timestamp, set the slot; with a new timestamp, emit the current row and start a new one. Flush at end of stream.</p>
<p><b>Late data:</b> you can no longer emit as soon as the timestamp changes. Keep open rows in a sorted map by timestamp and emit a row once a watermark (latest timestamp minus an allowed lateness) passes it; records later than that go to a correction path. The tradeoff is latency against completeness.</p>""",
)

TIER4 = [SOLE_MATE, CLUSTER]
TIER5 = [PNL_TABLE, GENERIC_FS, SPARSE_STREAM]
