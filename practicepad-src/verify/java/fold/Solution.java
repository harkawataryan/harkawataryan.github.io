import java.util.*;

public class Solution {
    static String[][] codeEditorOperations(String[] lines, String[] operations) {
        Map<Integer, Integer> match = new TreeMap<>(); Deque<Integer> st = new ArrayDeque<>();
        for (int i = 0; i < lines.length; i++) {
            String t = lines[i].replaceAll("[ \t]+$", "");
            if (t.endsWith("{")) st.push(i); else if (t.endsWith("}")) match.put(st.pop(), i);
        }
        Set<Integer> folded = new HashSet<>();
        List<String[]> out = new ArrayList<>();
        for (String op : operations) {
            String[] p = op.split(" ");
            switch (p[0]) {
                case "MATCH" -> out.add(match.entrySet().stream().map(e -> e.getKey() + ":" + e.getValue()).toArray(String[]::new));
                case "TOGGLE" -> { toggle(folded, Integer.parseInt(p[1])); out.add(new String[0]); }
                case "GET" -> out.add(view(lines, match, folded).stream().map(r -> r[1]).toArray(String[]::new));
                case "TOGGLE_LINE" -> { toggle(folded, Integer.parseInt(view(lines, match, folded).get(Integer.parseInt(p[1]))[0])); out.add(new String[0]); }
                case "GET_RANGE" -> {
                    List<String[]> v = view(lines, match, folded);
                    int lo = Math.min(Integer.parseInt(p[1]), v.size()), hi = Math.max(lo, Math.min(Integer.parseInt(p[2]), v.size()));
                    out.add(v.subList(lo, hi).stream().map(r -> r[1]).toArray(String[]::new));
                }
            }
        }
        return out.toArray(new String[0][]);
    }
    static void toggle(Set<Integer> f, int i) { if (!f.remove(i)) f.add(i); }
    static List<String[]> view(String[] lines, Map<Integer, Integer> match, Set<Integer> folded) {
        List<String[]> rows = new ArrayList<>(); int i = 0;
        while (i < lines.length) {
            if (folded.contains(i)) { String l = lines[i]; rows.add(new String[]{"" + i, l.substring(0, l.lastIndexOf('{') + 1) + " ... }"}); i = match.get(i) + 1; }
            else { rows.add(new String[]{"" + i, lines[i]}); i++; }
        }
        return rows;
    }
}
