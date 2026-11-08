import java.util.*;

public class Solution {
    static int maxMonsters(int[] costs) { return maxMonstersAndCost(costs)[0]; }
    static int[] maxMonstersAndCost(int[] costs) {
        PriorityQueue<Integer> taken = new PriorityQueue<>(Comparator.reverseOrder()); long spent = 0;
        for (int d = 0; d < costs.length; d++) { taken.add(costs[d]); spent += costs[d]; if (spent > 10L * (d + 1)) spent -= taken.poll(); }
        return new int[]{taken.size(), (int) spent};
    }
    static int[] chooseMonsterDays(int[] costs) {
        int n = costs.length; int[] best = null; long bestSpent = 0;
        for (int mask = 0; mask < (1 << n); mask++) {
            long spent = 0; boolean ok = true; List<Integer> days = new ArrayList<>();
            for (int d = 0; d < n; d++) { if ((mask >> d & 1) == 1) { spent += costs[d]; days.add(d); } if (spent > 10L * (d + 1)) { ok = false; break; } }
            if (!ok) continue;
            int[] cand = days.stream().mapToInt(Integer::intValue).toArray();
            if (best == null || cand.length > best.length || (cand.length == best.length && (spent < bestSpent || (spent == bestSpent && Arrays.compare(cand, best) < 0)))) { best = cand; bestSpent = spent; }
        }
        return best;
    }
}
