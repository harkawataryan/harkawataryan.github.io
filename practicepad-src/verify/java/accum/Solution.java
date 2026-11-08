import java.util.*;

public class Solution {
    static int[] runProgram(int[] memory, String[] instructions) {
        int[] mem = memory.clone(); int n = instructions.length;
        String[] ops = new String[n]; int[] xs = new int[n];
        for (int i = 0; i < n; i++) { String[] p = instructions[i].split(" "); ops[i] = p[0]; xs[i] = Integer.parseInt(p[1]); }
        int acc = 0, pc = 0;
        while (pc < n) {
            String op = ops[pc]; int x = xs[pc]; pc++;
            switch (op) {
                case "LOAD" -> acc = mem[x];
                case "STORE" -> mem[x] = acc;
                case "ADD" -> acc += x;
                case "SUB" -> acc -= x;
                case "MUL" -> acc *= x;
                case "LOADI" -> acc = mem[mem[x]];
                case "STOREI" -> mem[mem[x]] = acc;
                case "JMP" -> pc = x;
                case "JZ" -> { if (acc == 0) pc = x; }
                case "JNEG" -> { if (acc < 0) pc = x; }
            }
        }
        return mem;
    }
    static String[] optimize(String[] instructions) {
        List<String> prog = new ArrayList<>(Arrays.asList(instructions));
        while (true) { List<String> nw = dead(fold(prog)); if (nw.equals(prog)) return nw.toArray(new String[0]); prog = nw; }
    }
    static List<String> out; static Long known; static Set<Integer> same; static Integer load; static long a, b;
    static void emit(String op, long x) { out.add(op + " " + x); if (!op.equals("STORE")) same = new HashSet<>(); }
    static void affine(long a, long b) {
        if (a == 1 && b == 0) return;
        if (known != null) { long t = a * known + b; if (t != known) emit("ADD", t - known); known = t; }
        else if (a == 0) { emit("MUL", 0); if (b != 0) emit("ADD", b); known = b; }
        else { if (a != 1) emit("MUL", a); if (b != 0) emit("ADD", b); }
    }
    static void flush() {
        if (load != null && a != 0) { if (!same.contains(load)) { emit("LOAD", load); same = new HashSet<>(Set.of(load)); known = null; } affine(a, b); }
        else if (load != null) affine(0, b);
        else affine(a, b);
        load = null; a = 1; b = 0;
    }
    static List<String> fold(List<String> prog) {
        out = new ArrayList<>(); known = 0L; same = new HashSet<>(); load = null; a = 1; b = 0;
        for (String s : prog) {
            String[] p = s.split(" "); int x = Integer.parseInt(p[1]);
            switch (p[0]) {
                case "LOAD" -> { load = x; a = 1; b = 0; }
                case "ADD" -> b += x;
                case "SUB" -> b -= x;
                case "MUL" -> { a *= x; b *= x; }
                case "STORE" -> { flush(); if (!same.contains(x)) { out.add("STORE " + x); same.add(x); } }
            }
        }
        return out;
    }
    static List<String> dead(List<String> prog) {
        LinkedList<String> keep = new LinkedList<>(); Set<Integer> over = new HashSet<>();
        for (int i = prog.size() - 1; i >= 0; i--) {
            String[] p = prog.get(i).split(" "); int x = Integer.parseInt(p[1]);
            if (p[0].equals("STORE")) { if (over.contains(x)) continue; over.add(x); }
            else if (p[0].equals("LOAD")) over.remove(x);
            keep.addFirst(prog.get(i));
        }
        while (!keep.isEmpty() && !keep.getLast().startsWith("STORE ")) keep.removeLast();
        return new ArrayList<>(keep);
    }
}
