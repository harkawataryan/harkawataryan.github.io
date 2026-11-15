"""Java starters for the bank problems: the API you're handed (Part 1 and the intro only), as stubs.

Each entry is (public class name, body). Provided helpers are interfaces you can fake in main().
Only Part 1 and intro APIs appear, so a starter never previews a later part.
"""

HEADER = ("// {title}\n// Runs in your browser on a real Java 21 JDK. The first Run downloads the JDK,\n"
          "// so give it 20-40 seconds; later runs are quick.\nimport java.util.*;\n\n")

MAIN = "    public static void main(String[] args) {\n        // Try the example from the question here.\n    }\n"

S = {}

S["stack-interpreter"] = ("Interpreter", """public class Interpreter {
    /** Runs the program (one instruction string per entry, e.g. "PUSH 2") and returns the printed lines. */
    public List<String> run(List<String> program) {
        return new ArrayList<>();
    }

MAIN}
""")

S["connect-k"] = ("ConnectK", """public class ConnectK {
    public ConnectK(int k) {
    }

    /** Drops player's piece ("R" or "B") into column (any integer). Returns the winner, or "" if none. */
    public String move(String player, int column) {
        return "";
    }

MAIN}
""")

S["tetris"] = ("Tetris", """public class Tetris {
    // How you represent pieces and the board is up to you.

    public Tetris(int rows, int cols) {
    }

    /** One timestep: the active piece falls one row (and locks if it can't). */
    public void tick() {
    }

    public boolean moveLeft() { return false; }
    public boolean moveRight() { return false; }
    public boolean moveDown() { return false; }
    public boolean rotateClockwise() { return false; }
    public boolean rotateCounterclockwise() { return false; }

    public boolean isGameOver() { return false; }

MAIN}
""")

S["virtual-drive"] = ("VirtualDrive", """/** Provided: one physical drive of 100 bytes (values 0-255). */
interface PhysicalDrive {
    int read(int index);
    void write(int index, int value);
}

public class VirtualDrive {
    public VirtualDrive(PhysicalDrive a, PhysicalDrive b, PhysicalDrive c, PhysicalDrive p) {
    }

    public int read(int virtualAddress) {
        return 0;
    }

    public void write(int virtualAddress, int value) {
    }

MAIN}
""")

S["disk-filesystem"] = ("DiskFileSystem", """/** Provided: the spinning disk. read/write act on the byte under the head. */
interface Disk {
    int size();
    int position();
    char read();
    void write(char c);
}

public class DiskFileSystem {
    public DiskFileSystem(Disk disk) {
    }

    /** Returns immediately; the bytes are written on later onSpin() calls. */
    public void write(String filename, String data) {
    }

    /** Returns immediately; call reportReadComplete when the whole file has been read. */
    public void read(String filename) {
    }

    /** Called by the disk each time the head advances one position. */
    public void onSpin() {
    }

    /** Provided callback. */
    void reportReadComplete(String filename, String data) {
        System.out.println("read " + filename + ": " + data);
    }

MAIN}
""")

S["arithmetic-encoding"] = ("ArithmeticEncoding", """public class ArithmeticEncoding {
    /** freq is in the fixed symbol order (use a LinkedHashMap). Returns a number in the final interval. */
    public static double encode(String message, LinkedHashMap<Character, Integer> freq) {
        return 0;
    }

    public static String decode(double code, LinkedHashMap<Character, Integer> freq, int length) {
        return "";
    }

MAIN}
""")

S["swipe-keyboard"] = ("SwipeKeyboard", """public class SwipeKeyboard {
    /** Provided: is the middle sample a change of direction? (Stubbed here; fake it while testing.) */
    static boolean isVertex(Map<Character, Double> prev, Map<Character, Double> cur, Map<Character, Double> next) {
        return false;
    }

    /** Each sample maps a letter to the area touched, e.g. {a=0.8, s=0.2}. */
    public static String bestGuess(List<Map<Character, Double>> samples) {
        return "";
    }

MAIN}
""")

S["tree-browser"] = ("TreeBrowser", """/** Provided tree helpers. Nodes are ints; the root has level 0 and parent -1. */
interface Tree {
    int getParent(int node);
    List<Integer> getChildren(int node);
    List<Integer> getAncestors(int node);
    int getLevel(int node);
}

public class TreeBrowser {
    public TreeBrowser(Tree tree) {
    }

    public void select(int node) {
    }

    public void deselect(int node) {
    }

    /** Called very often. Selected nodes, their ancestors and their siblings, each once. */
    public Collection<Integer> display() {
        return new ArrayList<>();
    }

MAIN}
""")

S["multicache"] = ("CacheProxy", """/** Provided: the existing cache. get returns null on a miss. */
interface Cache {
    String get(String key);
    void put(String key, String value);
}

/** Provided: the remote store and the channel back to clients. */
interface Remote {
    void requestFromRemote(String key);
    void publish(String key, String value);
}

public class CacheProxy {
    public CacheProxy(Cache cache, Remote remote) {
    }

    /** A client asks for key. */
    public void get(String key) {
    }

    /** The remote's response to an earlier requestFromRemote. */
    public void receiveFromRemote(String key, String value) {
    }

MAIN}
""")

S["layered-interpolation"] = ("LayeredInterpolation", """public class LayeredInterpolation {
    /** layers.get(0) is the highest priority; each maps position to value. */
    public LayeredInterpolation(List<TreeMap<Double, Double>> layers) {
    }

    /** Nearest-neighbor value for x, or null if every layer is empty. */
    public Double get(double x) {
        return null;
    }

MAIN}
""")

S["lease-manager"] = ("LeaseManager", """/** Provided. Only one alarm is active; setting a new one replaces the old. */
interface Clock {
    long now();
    void setAlarm(long time, Runnable callback);
}

public class LeaseManager {
    public LeaseManager(Clock clock) {
    }

    public void requestLease(String machineId, String machineName, long expiresAt) {
    }

    /** Names of machines whose lease is still valid (expiresAt > now). */
    public List<String> allValidMachines() {
        return new ArrayList<>();
    }

MAIN}
""")

S["image-encoder"] = ("ImageEncoder", """public class ImageEncoder {
    /** pixels are colors like "R", "B"; returns records like "RAW(R)" or "REPEAT". */
    public static List<String> encode(List<String> pixels) {
        return new ArrayList<>();
    }

MAIN}
""")

S["etf-exposure"] = ("EtfExposure", """public class EtfExposure {
    /**
     * etfs: ETF -> (stock -> shares per ETF share), e.g. SPY -> {AAPL=3, MSFT=5}
     * prices: stock -> price; positions: symbol (stock or ETF) -> shares held
     */
    public EtfExposure(Map<String, Map<String, Double>> etfs, Map<String, Double> prices, Map<String, Double> positions) {
    }

    /** stock -> total shares of exposure. */
    public Map<String, Double> shareExposure() {
        return new HashMap<>();
    }

    /** stock -> total dollar exposure. */
    public Map<String, Double> dollarExposure() {
        return new HashMap<>();
    }

MAIN}
""")

S["exchange-arbitrage"] = ("Arbitrage", """/** Provided. side is "BUY" or "SELL". */
interface OrderGateway {
    void sendOrder(String exchange, String side, double price);
}

public class Arbitrage {
    public Arbitrage(OrderGateway gateway) {
    }

    public void onTopOfBook(String exchange, double bid, double ask) {
    }

    public void onBookEmpty(String exchange) {
    }

MAIN}
""")

S["schema-versioning"] = ("Schema", """public class Schema {
    public record Field(String name, int length) {}

    public Schema(List<Field> fields) {
    }

    public int getOffset(String name) {
        return 0;
    }

    public void insert(String name, int length, int index) {
    }

    public void remove(String name) {
    }

MAIN}
""")

S["marketplace"] = ("Marketplace", """public class Marketplace {
    public record Fill(String seller, int price) {}

    /** Lists one unit of item. */
    public void sell(String item, String sellerId, int price) {
    }

    /** For each item, buys the cheapest unit at or under maxPrice. Returns item -> fill (skipped items absent). */
    public Map<String, Fill> buy(String buyerId, List<String> items, int maxPrice) {
        return new HashMap<>();
    }

MAIN}
""")

S["fuzzy-find"] = ("FuzzyFinder", """/** Provided screen. draw writes one character and moves the cursor right. */
interface Screen {
    int getWidth();
    int getHeight();
    void moveCursorToPosition(int x, int y);
    void draw(char c);
}

public class FuzzyFinder {
    public FuzzyFinder(Screen screen, List<String> choices) {
    }

    /** Filters the choices by q and redraws the screen. */
    public void query(String q) {
    }

MAIN}
""")

S["task-allocator"] = ("TaskAllocator", """record Task(String id) {}

record Job(String id, List<Task> tasks) {}

/** Provided: a machine that runs one task at a time. */
interface Node {
    String id();
    void allocateTask(Task task);
}

public class TaskAllocator {
    public TaskAllocator(List<Node> nodes) {
    }

    public void scheduleJob(Job job) {
    }

MAIN}
""")

S["potion-brewing"] = ("PotionBrewing", """public class PotionBrewing {
    /** A spell consumes some counts of ingredients and produces others (index 0 = 'a'). */
    public record Spell(int[] consumes, int[] produces) {}

    /** counts has 26 entries, one per letter. Returns the letters that can be increased. */
    public static Set<Character> canIncrease(int[] counts, List<Spell> spells) {
        return new TreeSet<>();
    }

MAIN}
""")

S["secret-filesystem"] = ("SecretFileSystem", """/** Provided (and expensive): does file belong to the secret system? */
interface Oracle {
    boolean isValid(String file);
}

public class SecretFileSystem {
    /** Returns the index of the secret system in systems. */
    public static int findSecret(List<Set<String>> systems, Oracle oracle) {
        return -1;
    }

MAIN}
""")

S["merkle-tree"] = ("MerkleTree", """public class MerkleTree {
    public static class Node {
        final String value;
        final Node left, right;
        public Node(String value, Node left, Node right) { this.value = value; this.left = left; this.right = right; }
    }

    /** Provided: hex SHA-256 of s. */
    static String sha256(String s) {
        try {
            byte[] d = java.security.MessageDigest.getInstance("SHA-256").digest(s.getBytes(java.nio.charset.StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : d) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (java.security.NoSuchAlgorithmException e) {
            throw new RuntimeException(e);
        }
    }

    /** hash(node) = sha256(value + hash(left) + hash(right)), "" for a missing child. */
    public static String hash(Node node) {
        return "";
    }

    /** Does the client's subtree appear in the server's tree? */
    public static boolean containsSubtree(Node server, Node client) {
        return false;
    }

MAIN}
""")

S["copying-gc"] = ("CopyingGC", """/** Provided by the runtime. */
interface GcRuntime {
    /** Heap indices of the root pointers. */
    List<Integer> getPointers();
    /** Is the word at this heap index a reference? */
    boolean isPointer(int heapIndex);
}

public class CopyingGC {
    int[] heap, backup;
    int nextFree = 0;

    public CopyingGC(int heapSize, GcRuntime runtime) {
        heap = new int[heapSize];
        backup = new int[heapSize];
    }

    /** Writes the size header and returns the payload's start index, or -1 if there's no room. */
    public int allocate(int numWords) {
        return -1;
    }

MAIN}
""")

S["snake"] = ("Snake", """public class Snake {
    /** body cells are {row, col}, head first; direction is 'U', 'D', 'L' or 'R'. */
    public Snake(int rows, int cols, List<int[]> initialBody, char direction, List<int[]> apples) {
    }

    public void step(char direction) {
    }

    /** Your choice of format: e.g. body, score and whether the game is over. */
    public String getState() {
        return "";
    }

MAIN}
""")

S["make-24"] = ("Make24", """public class Make24 {
    /** Provided: splits a fully parenthesized expression into {left, operator, right}, or null for a plain number. */
    static String[] split(String expr) {
        expr = expr.trim();
        while (expr.startsWith("(") && matchingParen(expr, 0) == expr.length() - 1) expr = expr.substring(1, expr.length() - 1).trim();
        int depth = 0;
        for (int i = 0; i < expr.length(); i++) {
            char c = expr.charAt(i);
            if (c == '(') depth++;
            else if (c == ')') depth--;
            else if (depth == 0 && "+-*/".indexOf(c) >= 0 && i > 0)
                return new String[]{expr.substring(0, i).trim(), String.valueOf(c), expr.substring(i + 1).trim()};
        }
        return null;
    }

    private static int matchingParen(String s, int open) {
        int depth = 0;
        for (int i = open; i < s.length(); i++) {
            if (s.charAt(i) == '(') depth++;
            else if (s.charAt(i) == ')' && --depth == 0) return i;
        }
        return -1;
    }

    /** Value of expr, or -1 if any intermediate result isn't a non-negative integer. */
    public static long evaluate(String expr) {
        return -1;
    }

MAIN}
""")

S["git-diff"] = ("GitDiff", """public class GitDiff {
    /** Returns {i, j} where a[i] equals b[j] and that word occurs exactly once in each, or null. */
    public static int[] anchor(List<String> a, List<String> b) {
        return null;
    }

MAIN}
""")

S["text-editor"] = ("TextEditor", """public class TextEditor {
    public void insert(String text) {
    }

    /** Deletes the character before the cursor. */
    public void backspace() {
    }

    /** Deletes the character after the cursor. */
    public void delete() {
    }

    /** Moves the cursor by delta characters (negative = left), clamped to the document. */
    public void moveCursor(int delta) {
    }

    public String getText() {
        return "";
    }

    public int getCursor() {
        return 0;
    }

MAIN}
""")

S["supermarket-queue"] = ("Supermarket", """public class Supermarket {
    public Supermarket(int numLines) {
    }

    public void addCustomer(int line, String customerId, int items) {
    }

    public void updateItems(String customerId, int items) {
    }

    /** Processes x items in one line. */
    public void processItems(int line, int x) {
    }

    /** Processes one item in every line. */
    public void processOneItemEachLine() {
    }

    /** Customers in the order they left. */
    public List<String> departed() {
        return new ArrayList<>();
    }

MAIN}
""")

S["ring-buffer"] = ("RingBuffer", """public class RingBuffer {
    public RingBuffer(int n) {
    }

    /** Queues a payload to be written one byte per tick. */
    public void write(String payload) {
    }

    /** Writes at most one byte at the head and advances it. */
    public void tick() {
    }

    /** The payload at [index, index + length) once it's fully written, otherwise null. */
    public String read(int index, int length) {
        return null;
    }

MAIN}
""")

S["order-matching"] = ("MatchingEngine", """public class MatchingEngine {
    /** order is "BUY id price qty" or "SELL id price qty". Returns the trades it caused, in order. */
    public List<String> process(String order) {
        return new ArrayList<>();
    }

MAIN}
""")

S["batch-auction"] = ("BatchAuction", """public class BatchAuction {
    /** side is "BUY" or "SELL". Returns the new order's id (1, 2, 3, ...). */
    public int submit(String side, int size, int price) {
        return 0;
    }

    /** Called once. Returns order id -> filled size (0 if unfilled). */
    public Map<Integer, Integer> matchOrders() {
        return new HashMap<>();
    }

MAIN}
""")

S["stream-comparison"] = ("StreamComparison", """public class StreamComparison {
    /** Next (type, value) from stream 0 or 1. Returns false as soon as the streams are known to be inconsistent. */
    public boolean push(int stream, String type, String value) {
        return true;
    }

    /** Both streams have ended. True only if they're consistent. */
    public boolean finish() {
        return true;
    }

MAIN}
""")

S["video-player"] = ("VideoPlayer", """/** Provided. Only one download may run at a time. */
interface Network {
    void download(int chunk, int quality, Runnable onDone);
}

/** Provided. */
interface Screen {
    void play(int chunk, int quality);
}

public class VideoPlayer {
    /** qualities lists the available qualities for every chunk. */
    public VideoPlayer(int numChunks, List<Integer> qualities, Network network, Screen screen) {
    }

    /** Called periodically. */
    public void tick(long timestamp) {
    }

MAIN}
""")

S["failure-pattern"] = ("FailurePattern", """public class FailurePattern {
    /** events are {name, outcome} with outcome "PASS" or "FAIL". Names reaching threshold consecutive failures. */
    public static List<String> streaks(List<String[]> events, int threshold) {
        return new ArrayList<>();
    }

MAIN}
""")

S["gamepad"] = ("Gamepad", """public class Gamepad {
    public void keyValue(String pattern, int value) {
    }

    /** Records a press; prints the value when the presses complete a registered pattern. */
    public void keyIn(char button) {
    }

MAIN}
""")

S["candy-crush"] = ("CandyCrush", """public class CandyCrush {
    /** One round: crush every run of 3+ equal nonzero values at once, then apply gravity. */
    public static int[][] crushOnce(int[][] grid) {
        return grid;
    }

MAIN}
""")

S["merge-diff"] = ("MergeDiff", """public class MergeDiff {
    /** Positions refer to the result. Returns one diff equal to applying diff1, then diff2. */
    public static TreeMap<Integer, String> merge(SortedMap<Integer, String> diff1, SortedMap<Integer, String> diff2) {
        return new TreeMap<>();
    }

MAIN}
""")

S["match-strings"] = ("MatchStrings", """public class MatchStrings {
    /** Returns {same-position matches, different-position matches}. */
    public static int[] score(String guess, String target) {
        return new int[]{0, 0};
    }

MAIN}
""")

S["string-compression"] = ("StringCompression", """public class StringCompression {
    public static String compress(String s) {
        return "";
    }

MAIN}
""")

S["message-queue"] = ("MessageRouter", """class Worker {
    final String id;
    final int capacity;
    int load;
    final Set<String> types;
    Worker(String id, int capacity, Set<String> types) { this.id = id; this.capacity = capacity; this.types = types; }
}

record Message(String id, String type, int size, long timestamp) {}

public class MessageRouter {
    public void init(List<Worker> workers) {
    }

    /** Routes m to a worker (returns its id) or queues it (returns null). */
    public String sendMessage(Message m) {
        return null;
    }

    public void completeMessage(String messageId) {
    }

    /** worker id -> current load. */
    public Map<String, Integer> getWorkerStatus() {
        return new HashMap<>();
    }

    public List<Message> getMessageQueue() {
        return new ArrayList<>();
    }

MAIN}
""")

S["weighted-graph"] = ("UnitConverter", """public class UnitConverter {
    /** ("m", 3.28, "ft") means 1 m = 3.28 ft. */
    public record Fact(String from, double factor, String to) {}

    public UnitConverter(List<Fact> facts) {
    }

    /** How many `to` units are in amount `from` units, or null if they aren't connected. */
    public Double convert(double amount, String from, String to) {
        return null;
    }

MAIN}
""")

S["wordle"] = ("Wordle", """public class Wordle {
    /** Returns {same-position matches, different-position matches}. */
    public static int[] compare(String a, String b) {
        return new int[]{0, 0};
    }

MAIN}
""")

S["square-up"] = ("SquareUp", """public class SquareUp {
    /** player is '-' (Player 1) or '+' (Player 2). Returns "Player 1 wins", "Player 2 wins" or "No winner". */
    public String drop(char player, int column) {
        return "No winner";
    }

MAIN}
""")

S["falling-path-sum"] = ("FallingPathSum", """public class FallingPathSum {
    public static int minFallingPathSum(int[][] grid) {
        return 0;
    }

MAIN}
""")

S["sole-mate-review"] = ("SoleMateReview", """public class SoleMateReview {
    // This is a code-review question: the interviewer shares two Python files.
    // Use this pad for notes, or write your own buggy version of the tier logic and review it out loud.

MAIN}
""")

S["cluster-scaling"] = ("ClusterManager", """/** Provided low-level VM APIs (reported as GET -> SSH -> RUN). */
interface VmApi {
    /** Looks up the VM behind an endpoint; returns its host. */
    String get(String endpoint);
    void ssh(String host);
    void run(String host, String command);
}

public class ClusterManager {
    public ClusterManager(VmApi api) {
    }

    public void start(List<String> endpoints) {
    }

    public void stop(List<String> endpoints) {
    }

MAIN}
""")

S["filtered-pnl"] = ("PnlTable", """record Trade(String id, Map<String, String> attributes) {}

/** Provided: PnL of a trade at a time. */
interface PnlSource {
    double getPnl(Trade trade, long time);
}

public class PnlTable {
    public PnlTable(List<java.util.function.Predicate<Trade>> filters, List<Long> times, PnlSource pnl) {
    }

    public void addTrade(Trade trade) {
    }

    /** Rows are filters, columns are times. Must be O(1). */
    public double[][] viewResult() {
        return new double[0][0];
    }

    /** null clears the global filter. */
    public void setGlobalFilter(java.util.function.Predicate<Trade> filter) {
    }

MAIN}
""")

S["generic-filesystem"] = ("FileSystem", """public class FileSystem {
    /** Like mkdir -p. */
    public void mkdir(String path) {
    }

    public void writeFile(String path, String content) {
    }

    public String readFile(String path) {
        return null;
    }

    public void delete(String path) {
    }

    public List<String> list(String path) {
        return new ArrayList<>();
    }

MAIN}
""")

S["sparse-stream"] = ("SparseStream", """public class SparseStream {
    public record Row(long timestamp, double[] values) {}

    /** All M possible codes. */
    public SparseStream(List<String> codes) {
    }

    /** Consumes one record; returns any rows that are now complete. */
    public List<Row> accept(long timestamp, String code, double value) {
        return new ArrayList<>();
    }

    /** End of stream: returns the last row, if any. */
    public List<Row> finish() {
        return new ArrayList<>();
    }

MAIN}
""")


def java_starter(pid, title):
    """(class name, source) for a bank problem, or None to keep the generic starter."""
    if pid not in S:
        return None
    cls, body = S[pid]
    return cls, HEADER.format(title=title) + body.replace("MAIN", MAIN)
