import java.math.BigInteger;
import java.util.*;

public class Solution {
    static String frac(BigInteger n, BigInteger d) {
        if (d.signum() < 0) { n = n.negate(); d = d.negate(); }
        BigInteger g = n.gcd(d); if (g.signum() == 0) g = BigInteger.ONE;
        return n.divide(g) + "/" + d.divide(g);
    }
    static String[] modifiedDiceExpectations(int[][] dice, int[] counts) {
        String[] out = new String[11]; long total = 0;
        for (int i = 0; i < 10; i++) { long s = 0; for (int f : dice[i]) s += f; out[i] = frac(BigInteger.valueOf(s), BigInteger.valueOf(6)); total += counts[i] * s; }
        out[10] = frac(BigInteger.valueOf(total - 2100), BigInteger.valueOf(6));
        return out;
    }
    static String netPayoutVariance(int[][] dice, int[] counts) {
        BigInteger num = BigInteger.ZERO;
        for (int i = 0; i < 10; i++) {
            long s = 0, q = 0; for (int f : dice[i]) { s += f; q += (long) f * f; }
            num = num.add(BigInteger.valueOf(counts[i]).multiply(BigInteger.valueOf(6).multiply(BigInteger.valueOf(q)).subtract(BigInteger.valueOf(s).multiply(BigInteger.valueOf(s)))));
        }
        return frac(num, BigInteger.valueOf(36));
    }
    static String probabilityNetPositive(int[][] dice, int[] counts) {
        Map<Integer, BigInteger> ways = new HashMap<>(); ways.put(0, BigInteger.ONE); int rolls = 0;
        for (int i = 0; i < 10; i++) for (int k = 0; k < counts[i]; k++) {
            Map<Integer, BigInteger> nxt = new HashMap<>(); rolls++;
            for (var e : ways.entrySet()) for (int f : dice[i]) nxt.merge(e.getKey() + f, e.getValue(), BigInteger::add);
            ways = nxt;
        }
        BigInteger win = BigInteger.ZERO; for (var e : ways.entrySet()) if (e.getKey() > 350) win = win.add(e.getValue());
        return frac(win, BigInteger.valueOf(6).pow(rolls));
    }
}
