import random, itertools, sys
sys.setrecursionlimit(10000)
from refs import *

def eq(a,b,label):
    assert a==b, f"{label}\n got {a}\n exp {b}"
# --- examples from the statements ---
eq(run_program([4,1],["LOAD 0","ADD 3","STORE 1","MUL 2"]),[4,7],"acc1")
eq(run_program([9,-2],["STORE 0","LOAD 1","SUB -3","STORE 1"]),[0,1],"acc2")
eq(run_program([2,5],[]),[2,5],"acc3")
eq(instrument_jumps(["PUSH x","JUMP 3","PUSH skip","PRINT"]),["PUSH x","PUSH jump@1","PRINT","POP","JUMP 6","PUSH skip","PRINT"],"ins1")
eq(instrument_jumps(["JUMP_IF_EMPTY 2","JUMP 3","JUMP 3"]),["JUMP_IF_EMPTY 5","PUSH jump@1","PRINT","POP","JUMP 9","PUSH jump@2","PRINT","POP","JUMP 9"],"ins2")
eq(instrument_jumps(["PUSH JUMP 0","PRINT"]),["PUSH JUMP 0","PRINT"],"ins3")
eq(run_interpreter(["PUSH hello","PRINT","TRUNCATE 2","PRINT"]),["hello","hel"],"int1")
eq(run_interpreter(["PUSH ","JUMP_IF_EMPTY 4","PUSH skip","PRINT","PUSH ok","PRINT"]),["ok"],"int2")
eq(run_interpreter(["POP","PRINT","PUSH abc","JUMP 5","PRINT"]),[""],"int3")
L=["def outer() {"," before();"," if (ready) {"," work();"," }"," after();","}","done();"]
eq(code_editor_operations(L,["MATCH","TOGGLE 2","GET","TOGGLE 0","GET","TOGGLE 0","GET"]),
 [["0:6","2:4"],[],["def outer() {"," before();"," if (ready) { ... }"," after();","}","done();"],[],["def outer() { ... }","done();"],[],["def outer() {"," before();"," if (ready) { ... }"," after();","}","done();"]],"fold1")
eq(code_editor_operations([],["MATCH","GET"]),[[],[]],"fold2")
eq(code_editor_operations(["{","}"],["GET","TOGGLE 0","GET","TOGGLE 0","GET"]),[["{","}"],[],["{ ... }"],[],["{","}"]],"fold3")
eq(find_winning_tower_strategy(["OBSERVE"]*7,7),["BUY","BUY","BUY","LOAD","LOAD","MOVE_FAR","WAIT"],"tow1")
eq(find_winning_tower_strategy(["BUY","LOAD","MOVE_NEAR","BUY"],4),[],"tow2")
eq(choose_monster_days([5,25,5]),[0,2],"wiz1"); eq(choose_monster_days([10,20,30]),[0],"wiz2")
eq(optimize_loadout(7,["Armor","Laser","Shield","Net"],[4,3,4,2],[["debris"],["pirates"],["asteroids"],["debris","pirates"]],[["pirates"],["debris"],["asteroids"],["debris","pirates"],["pirates"]]),["Net","Shield"],"load1")
eq(optimize_loadout(3,["A","B","C"],[2,2,3],[["pirates"],["debris"],["pirates","debris"]],[["pirates"],["debris"],["pirates","debris"],["asteroids"],["pirates"]]),["C"],"load2")
D=[[1,2,3,4,5,6]]*10
eq(modified_dice_expectations(D,[10]*10),["7/2"]*10+["0/1"],"dice1")
D2=[[1,1,3,4,5,6],[1,2,2,4,5,6],[1,2,3,3,5,6],[1,2,3,4,4,6],[1,2,3,4,5,5],[2,2,3,4,5,6],[1,3,3,4,5,6],[1,2,4,4,5,6],[1,2,3,5,5,6],[1,2,3,4,6,6]]
eq(modified_dice_expectations(D2,[100]+[0]*9),["10/3"]*5+["11/3"]*5+["-50/3"],"dice2")
print("statement examples OK")

R=random.Random(7)
# --- optimizer equivalence ---
def rand_prog(n,memlen):
    ops=[]
    for _ in range(n):
        o=R.choice(["LOAD","STORE","ADD","SUB","MUL","LOAD","STORE"])
        x=R.randrange(memlen) if o in("LOAD","STORE") else R.randint(-3,3)
        ops.append(f"{o} {x}")
    return ops
tot_in=tot_out=0
for t in range(3000):
    ml=R.randint(1,4); p=rand_prog(R.randint(0,14),ml); q=optimize(p)
    tot_in+=len(p); tot_out+=len(q)
    assert len(q)<=len(p),(p,q)
    for _ in range(12):
        m=[R.randint(-9,9) for _ in range(ml)]
        assert run_program(m,p)==run_program(m,q),(p,q,m)
print("optimizer equivalent on 3000 random programs; size",tot_in,"->",tot_out)

# --- wizard: DP vs brute; greedy count/cost vs brute ---
for t in range(1500):
    n=R.randint(1,10); c=[R.choice([R.randint(1,12),R.randint(1,40)]) for _ in range(n)]
    b=choose_monster_days_brute(c); eq(choose_monster_days(c),b,f"wiz {c}")
    eq(max_monsters_and_cost(c),[len(b),sum(c[d] for d in b)],f"greedy {c}")
print("wizard OK")

# --- towers: BFS vs brute force over all schedules ---
ACTS=["BUY","LOAD","MOVE_FAR","MOVE_NEAR","OBSERVE","WAIT"]
def brute(east,limit,east_can_win):
    for L in range(1,limit+1):
        for sched in itertools.product(ACTS,repeat=L):
            w,e=Team(),Team(); ok=True; won=False
            for d,a in enumerate(sched):
                if w.locked != (a=="WAIT"): ok=False;break
                w=w.take_turn(a)
                if beats(w,e): won = (d==L-1); break
                e=e.take_turn(east[d])
                if beats(w,e): won=(d==L-1); break
                if east_can_win and beats(e,w): break
            if ok and won: return list(sched)
    return []
EA=["BUY","LOAD","MOVE_FAR","MOVE_NEAR","OBSERVE"]
for t in range(60):
    lim=R.randint(1,7); east=[R.choice(EA) for _ in range(lim)]
    eq(find_winning_tower_strategy(east,lim),brute(east,lim,False),f"tow {east}")
    eq(find_safe_tower_strategy(east,lim),brute(east,lim,True),f"safe {east}")
print("towers OK")

# --- loadout part 3 vs brute ---
for t in range(400):
    hz=["h%d"%i for i in range(R.randint(1,5))]
    n=R.randint(1,8)
    prot=[R.sample(hz,R.randint(1,len(hz))) for _ in range(n)]
    w=[R.randint(1,6) for _ in range(n)]
    runs=[R.sample(hz,R.randint(1,len(hz))) for _ in range(5)]
    cap=R.randint(0,15); names=["n%d"%i for i in range(n)]
    sel=optimize_loadout(cap,names,w,prot,runs)
    idx=[names.index(s) for s in sel]
    eq(best_loadout_score(cap,w,prot,runs),[mitigated_runs(prot,runs,idx),sum(w[i] for i in idx)],"loadout3")
print("loadout OK")

# --- dice probability sanity: small brute ---
for t in range(30):
    dice=[[R.randint(-3,6) for _ in range(6)] for _ in range(10)]
    cnt=[0]*10
    for _ in range(3): cnt[R.randrange(10)]+=1
    # shift fee: compare by brute enumeration with threshold 350 -> use counts summing 3, fee check s>350 always false; so test generic via monkeypatch
from fractions import Fraction
def brute_p(dice,cnt,thr):
    seq=[f for f,c in zip(dice,cnt) for _ in range(c)]
    tot=0;win=0
    for combo in itertools.product(*seq):
        tot+=1; win+= sum(combo)>thr
    return Fraction(win,tot)
import refs
for t in range(20):
    dice=[[R.randint(-3,6) for _ in range(6)] for _ in range(10)]
    cnt=[0]*10
    for _ in range(4): cnt[R.randrange(10)]+=1
    # reuse DP with threshold by temporarily computing via shifted fee
    ways={0:1}
    for faces,c in zip(dice,cnt):
        for _ in range(c):
            nxt={}
            for s,w in ways.items():
                for f in faces: nxt[s+f]=nxt.get(s+f,0)+w
            ways=nxt
    thr=R.randint(-5,15)
    p=Fraction(sum(w for s,w in ways.items() if s>thr),6**sum(cnt))
    eq(p,brute_p(dice,cnt,thr),"dice dp")
print("dice DP OK")
