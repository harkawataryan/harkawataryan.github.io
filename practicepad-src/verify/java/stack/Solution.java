import java.util.*;

public class Solution {
    static String[] parse(String s) { int i = s.indexOf(' '); return i < 0 ? new String[]{s, ""} : new String[]{s.substring(0, i), s.substring(i + 1)}; }
    static String step(Deque<String> st, String op, String arg) {
        switch (op) {
            case "PUSH": st.push(arg); break;
            case "POP": if (!st.isEmpty()) st.pop(); break;
            case "PRINT": return st.isEmpty() ? "" : st.peek();
            case "TRUNCATE": if (!st.isEmpty()) { String t = st.pop(); st.push(t.substring(0, Math.max(0, t.length() - Integer.parseInt(arg)))); } break;
        }
        return null;
    }
    static int next(Deque<String> st, int pc, String op, String arg) {
        if (op.equals("JUMP")) return Integer.parseInt(arg);
        if (op.equals("JUMP_IF_EMPTY") && (st.isEmpty() || st.peek().isEmpty())) return Integer.parseInt(arg);
        return pc + 1;
    }
    static String[] runInterpreter(String[] ins) {
        Deque<String> st = new ArrayDeque<>(); List<String> out = new ArrayList<>(); int pc = 0;
        while (pc < ins.length) { String[] p = parse(ins[pc]); String r = step(st, p[0], p[1]); if (r != null) out.add(r); pc = next(st, pc, p[0], p[1]); }
        return out.toArray(new String[0]);
    }
    static String[] instrumentJumps(String[] ins) {
        int[] start = new int[ins.length + 1]; int pos = 0;
        for (int i = 0; i < ins.length; i++) { start[i] = pos; pos += parse(ins[i])[0].equals("JUMP") ? 4 : 1; }
        start[ins.length] = pos;
        List<String> out = new ArrayList<>();
        for (int i = 0; i < ins.length; i++) {
            String[] p = parse(ins[i]);
            if (p[0].equals("JUMP")) { out.add("PUSH jump@" + i); out.add("PRINT"); out.add("POP"); out.add("JUMP " + start[Integer.parseInt(p[1])]); }
            else if (p[0].equals("JUMP_IF_EMPTY")) out.add("JUMP_IF_EMPTY " + start[Integer.parseInt(p[1])]);
            else out.add(ins[i]);
        }
        return out.toArray(new String[0]);
    }
    static String[] traceJumps(String[] ins, int limit) {
        Deque<String> st = new ArrayDeque<>(); List<String> trace = new ArrayList<>(); Set<List<Object>> seen = new HashSet<>();
        int pc = 0, steps = 0;
        while (pc < ins.length) {
            if (!seen.add(List.of(pc, new ArrayList<>(st)))) { trace.add("LOOP"); break; }
            if (steps == limit) { trace.add("LIMIT"); break; }
            String[] p = parse(ins[pc]);
            if (p[0].equals("JUMP")) trace.add(String.valueOf(pc));
            step(st, p[0], p[1]); pc = next(st, pc, p[0], p[1]); steps++;
        }
        return trace.toArray(new String[0]);
    }
}
