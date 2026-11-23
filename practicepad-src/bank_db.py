"""Question bank: Databricks SWE intern practice problems.

Same entry format as bank_a (see P there). These show under the Databricks
problem set in the pad's top bar, not in the Jane Street bank.
"""
from bank_a import P, q

MODES = P(
    "modes-of-transport", "Modes of Transport",
    "Fastest single-mode path on a grid → one BFS instead of one per mode",
    "Databricks SWE intern practice. One problem, plus a follow-up the interviewer reveals once you're done.",
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
    ],
    clarify=[
        ("Which cells can a mode use?", "Only cells marked with that mode's digit, plus <code>S</code> and <code>D</code>. Every mode can stand on <code>S</code> and <code>D</code>."),
        ("How is the time of a path computed?", "Number of moves × <code>time</code> for that mode. Every move of one mode takes the same time."),
        ("How do the arrays line up with the digits?", "Your call, just state it. A common choice: 0-indexed arrays, so mode m uses <code>time[m − 1]</code> and <code>cost[m − 1]</code>."),
        ("What if no mode can reach D?", "Return -1."),
        ("What if two modes tie on both time and cost?", "Return the lower mode number."),
        ("How big is the grid?", "Assume up to about a million cells, and a handful of modes."),
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
<p><b>Edge cases worth naming:</b> S next to D (one move for every mode), D unreachable (-1), ties on time broken by cost, and modes whose digit never appears on the grid.</p>""",
)

DATABRICKS = [MODES]
