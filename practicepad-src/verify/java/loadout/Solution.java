import java.util.*;

public class Solution {
    static int mitigatedRuns(String[][] protections, String[][] runs, int[] selected) {
        Set<String> cov = new HashSet<>(); for (int i : selected) cov.addAll(Arrays.asList(protections[i]));
        int c = 0; for (String[] r : runs) if (cov.containsAll(Arrays.asList(r))) c++;
        return c;
    }
    static Map<String, Integer> bits(String[][] runs) {
        TreeSet<String> hz = new TreeSet<>(); for (String[] r : runs) hz.addAll(Arrays.asList(r));
        Map<String, Integer> bit = new HashMap<>(); int i = 0; for (String h : hz) bit.put(h, 1 << i++);
        return bit;
    }
    static int mask(String[] hs, Map<String, Integer> bit) { int m = 0; for (String h : hs) m |= bit.getOrDefault(h, 0); return m; }
    static String[] optimizeLoadout(int capacity, String[] names, int[] weights, String[][] protections, String[][] runs) {
        Map<String, Integer> bit = bits(runs); int n = names.length;
        int[] item = new int[n]; for (int i = 0; i < n; i++) item[i] = mask(protections[i], bit);
        int[] run = new int[runs.length]; for (int r = 0; r < runs.length; r++) run[r] = mask(runs[r], bit);
        int bestScore = -1, bestW = 0; List<String> best = null;
        for (int s = 0; s < (1 << n); s++) {
            int w = 0, cov = 0;
            for (int i = 0; i < n; i++) if ((s >> i & 1) == 1) { w += weights[i]; cov |= item[i]; }
            if (w > capacity) continue;
            int score = 0; for (int m : run) if ((m & cov) == m) score++;
            if (score < bestScore || (score == bestScore && w > bestW)) continue;
            List<String> chosen = new ArrayList<>(); for (int i = 0; i < n; i++) if ((s >> i & 1) == 1) chosen.add(names[i]);
            Collections.sort(chosen);
            if (score > bestScore || w < bestW || compare(chosen, best) < 0) { bestScore = score; bestW = w; best = chosen; }
        }
        return best.toArray(new String[0]);
    }
    static int compare(List<String> a, List<String> b) {
        for (int i = 0; i < Math.min(a.size(), b.size()); i++) { int c = a.get(i).compareTo(b.get(i)); if (c != 0) return c; }
        return a.size() - b.size();
    }
    static int[] bestLoadoutScore(int capacity, int[] weights, String[][] protections, String[][] runs) {
        Map<String, Integer> bit = bits(runs); int h = bit.size(), full = 1 << h;
        long INF = Long.MAX_VALUE / 4; long[] exact = new long[full]; Arrays.fill(exact, INF); exact[0] = 0;
        for (int i = 0; i < weights.length; i++) { int m = mask(protections[i], bit); for (int s = full - 1; s >= 0; s--) if (exact[s] + weights[i] < exact[s | m]) exact[s | m] = exact[s] + weights[i]; }
        long[] cheap = exact.clone();
        for (int b = 0; b < h; b++) for (int s = 0; s < full; s++) if ((s >> b & 1) == 0 && cheap[s | 1 << b] < cheap[s]) cheap[s] = cheap[s | 1 << b];
        int[] run = new int[runs.length]; for (int r = 0; r < runs.length; r++) run[r] = mask(runs[r], bit);
        int bs = 0; long bw = 0;
        for (int c = 0; c < (1 << runs.length); c++) {
            int need = 0; for (int r = 0; r < runs.length; r++) if ((c >> r & 1) == 1) need |= run[r];
            long w = cheap[need]; if (w > capacity) continue;
            int score = 0; for (int m : run) if ((m & need) == m) score++;
            if (score > bs || (score == bs && w < bw)) { bs = score; bw = w; }
        }
        return new int[]{bs, (int) bw};
    }
}
