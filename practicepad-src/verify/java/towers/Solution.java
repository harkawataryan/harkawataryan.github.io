import java.util.*;

public class Solution {
    record Team(int near, int far, int dollies, int bricks, int transit, boolean locked) {
        static Team fresh() { return new Team(5, 0, 0, 0, 0, false); }
        Team turn(String a) {
            if (locked) return new Team(near, far + transit, dollies, bricks, 0, false);
            return switch (a) {
                case "BUY" -> new Team(near, far, dollies + 1, bricks, transit, false);
                case "LOAD" -> new Team(near, far, dollies, bricks + dollies, transit, false);
                case "MOVE_NEAR" -> new Team(near + bricks, far, dollies, 0, transit, false);
                case "MOVE_FAR" -> new Team(near, far, dollies, 0, bricks, true);
                default -> this;
            };
        }
    }
    static final String[] ACTIONS = {"BUY", "LOAD", "MOVE_FAR", "MOVE_NEAR", "OBSERVE"};
    static boolean beats(Team a, Team b) { return a.near() > b.far() && a.far() > b.near(); }
    static int simulateTowers(String[] west, String[] east) {
        Team w = Team.fresh(), e = Team.fresh();
        for (int d = 0; d < west.length; d++) {
            w = w.turn(west[d]); if (beats(w, e)) return d;
            e = e.turn(east[d]); if (beats(w, e)) return d;
        }
        return -1;
    }
    record Node(Team w, Team e, List<String> path) {}
    static String[] findWinningTowerStrategy(String[] east, int limit) {
        List<Node> layer = List.of(new Node(Team.fresh(), Team.fresh(), List.of()));
        for (int d = 0; d < limit; d++) {
            List<Node> nxt = new ArrayList<>(); Set<List<Team>> seen = new HashSet<>();
            for (Node n : layer) for (String a : n.w().locked() ? new String[]{"WAIT"} : ACTIONS) {
                Team w2 = n.w().turn(a); List<String> p = new ArrayList<>(n.path()); p.add(a);
                if (beats(w2, n.e())) return p.toArray(new String[0]);
                Team e2 = n.e().turn(east[d]);
                if (beats(w2, e2)) return p.toArray(new String[0]);
                if (seen.add(List.of(w2, e2))) nxt.add(new Node(w2, e2, p));
            }
            layer = nxt;
        }
        return new String[0];
    }
    static int countFastestWins(String[] east, int limit) {
        Map<List<Team>, Integer> layer = new LinkedHashMap<>(); layer.put(List.of(Team.fresh(), Team.fresh()), 1);
        for (int d = 0; d < limit; d++) {
            Map<List<Team>, Integer> nxt = new LinkedHashMap<>(); int wins = 0;
            for (var en : layer.entrySet()) {
                Team w = en.getKey().get(0), e = en.getKey().get(1);
                for (String a : w.locked() ? new String[]{"WAIT"} : ACTIONS) {
                    Team w2 = w.turn(a), e2 = e.turn(east[d]);
                    if (beats(w2, e) || beats(w2, e2)) wins += en.getValue();
                    else nxt.merge(List.of(w2, e2), en.getValue(), Integer::sum);
                }
            }
            if (wins > 0) return wins;
            layer = nxt;
        }
        return 0;
    }
}
