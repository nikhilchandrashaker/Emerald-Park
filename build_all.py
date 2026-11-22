import sys, json, pickle, bisect, time, numpy as np, pandas as pd
sys.path.insert(0, "src")
from evalpark import *
P = st["P"]; t0 = time.time()
EM = emerald(310, 350, 430, 2.2, 0.86)
rv = stats(league_vec(ref))
# ---------- 1. league factors: all 30 real parks, reference, Emerald ----------
rows = []
tm = pd.read_csv("data/raw/Teams.csv"); tm = tm[tm.yearID == 2019].set_index("teamID")
for code, pk in list(parks.items()) + [("REF", ref), ("EMERALD", EM)]:
    s, f = factors(pk, rv=rv)
    r = dict(park_code=code, park=(tm.park.get(code, pk.name)), lf_line=pk.dims[0], lf_alley=pk.dims[1], cf=pk.dims[2], rf_alley=pk.dims[3], rf_line=pk.dims[4],
             elevation_ft=round(pk.elev), foul_territory_x=pk.foul, infield_speed_x=pk.infield,
             lahman_BPF_2019=tm.BPF.get(code, np.nan), lahman_PPF_2019=tm.PPF.get(code, np.nan))
    r.update({"model_" + k + "_factor": round(float(v), 1) for k, v in f.items() if k in ("HR_PA","AVG","BABIP","ISO","XBH_PA","RAO","FOUL_OUT_PA")})
    rows.append(r)
pf = pd.DataFrame(rows).rename(columns={"model_RAO_factor": "model_runs_factor"})
real = pf[pf.park_code.isin(parks)]
corr = float(np.corrcoef(real.model_runs_factor, real.lahman_BPF_2019)[0, 1])
corr_hr = float(np.corrcoef(real.model_HR_PA_factor, real.lahman_BPF_2019)[0, 1])
print("validation corr(model runs factor, Lahman BPF) =", round(corr, 3), " HR factor vs BPF =", round(corr_hr, 3))
pf.to_csv("data/parks_mlb_2019_and_emerald.csv", index=False)
# ---------- 2. design-space grids ----------
g1 = []
for A in range(330, 391, 10):
    for CF in range(400, 451, 10):
        s, f = factors(emerald(310, A, CF, 2.2, 0.86), rv=rv)
        g1.append(dict(alley=A, cf=CF, HR=f["HR_PA"], BABIP=f["BABIP"], runs=f["RAO"], AVG=f["AVG"]))
g2 = []
for fo in (1.0, 1.4, 1.8, 2.2, 2.6):
    for inf in (1.0, 0.94, 0.90, 0.86, 0.82):
        s, f = factors(emerald(310, 350, 430, fo, inf), rv=rv)
        g2.append(dict(foul=fo, infield=inf, HR=f["HR_PA"], BABIP=f["BABIP"], runs=f["RAO"], AVG=f["AVG"]))
pd.DataFrame(g1).to_csv("data/design_space_alley_cf.csv", index=False); pd.DataFrame(g2).to_csv("data/design_space_foul_infield.csv", index=False)
print("grids done", round(time.time() - t0))
# ---------- 3. player-level results ----------
out, bbs = [], []
for i, p in enumerate(players):
    for tag, pk in (("REF", ref), ("EMERALD", EM)):
        v = pa_probs(p, draws[i], pk, ref, K, 40000); s_ = stats(v)
        out.append(dict(player=p["player"], team=p["team"], bats=p["bats"], park=tag, PA_2019=p["PA"], **{k: round(float(x), 5) for k, x in s_.items() if k != "RAO"},
                        HR_per_600PA=round(float(v[6] * 600), 2), H_per_600PA=round(float(s_["H_PA"] * 600), 1)))
        if tag == "EMERALD" or True:
            b = batted(draws[i], p["s"], p["bats"], pk, ref, dict(K, c=K["c"] * p["m"]), 100)
            for j in range(100):
                bbs.append((p["player"], tag, round(float(b["ev"][j]), 1), round(float(b["la"][j]), 1), round(float(b["phi"][j]), 1), round(float(b["d"][j]), 0), int(b["hr"][j])))
res = pd.DataFrame(out); res.to_csv("data/sim_player_park_results.csv", index=False)
pd.DataFrame(bbs, columns=["player","park","exit_velo_mph","launch_angle_deg","spray_angle_deg","carry_ft","is_HR"]).to_csv("data/sim_batted_balls_sample.csv", index=False)
wide = res.pivot(index="player", columns="park", values="HR_per_600PA"); wide["dHR_600"] = wide.EMERALD - wide.REF
print(wide.sort_values("dHR_600").head(3).round(1).to_string()); print(wide.sort_values("dHR_600").tail(3).round(1).to_string())
# player-level validation vs real 2019 (reference park)
rr = res[res.park == "REF"].set_index("player"); pr = pl.set_index("player")
real_avg = pr.H / (pr.AB); real_slg = (pr.H + pr.B2 + 2 * pr.B3 + 3 * pr.HR) / pr.AB
v_avg = float(np.corrcoef(rr.AVG.reindex(pr.index), real_avg)[0, 1]); v_slg = float(np.corrcoef(rr.SLG.reindex(pr.index), real_slg)[0, 1])
v_hr = float(np.corrcoef(rr.HR_PA.reindex(pr.index), pr.HR / pr.PA)[0, 1])
print("player validation r: HR", round(v_hr, 3), "AVG", round(v_avg, 3), "SLG", round(v_slg, 3))
print("players done", round(time.time() - t0))
# ---------- 4. game simulator ----------
def vecs(pk):
    return [pa_probs(p, draws[i], pk, ref, K, 20000) for i, p in enumerate(players)]
def teams_lineups(V):
    avg = (np.array(V) * W[:, None]).sum(0); L = {}
    for t, g in pl.groupby("team"):
        idx = list(g.sort_values("PA", ascending=False).index[:9]); vv = [V[i] for i in idx]
        while len(vv) < 9: vv.append(avg)
        L[t] = [list(np.cumsum(v / v.sum())) for v in vv]
    return L
class Sim:
    def __init__(s, seed): s.r = np.random.default_rng(seed); s.U = s.r.random(2_000_000); s.i = 0
    def nxt(s):
        if s.i >= len(s.U): s.U = s.r.random(2_000_000); s.i = 0
        s.i += 1; return s.U[s.i - 1]
def half(S, cums, idx, st_, target=99):
    outs = 0; b1 = b2 = b3 = 0; runs = 0; nxt = S.nxt
    while outs < 3 and runs < target:
        cum = cums[idx]; idx = (idx + 1) % 9; o = bisect.bisect_left(cum, nxt()); o = min(o, 9); st_[o] += 1
        if o == 0 or o == 9: outs += 1
        elif o <= 2:
            if b1:
                if b2:
                    runs += b3; b3 = 1
                b2 = 1
            b1 = 1
        elif o == 3:
            runs += b3; b3 = 0
            if b2:
                if nxt() < .60: runs += 1
                else: b3 = 1
                b2 = 0
            if b1:
                if b3 == 0 and nxt() < .28: b3 = 1
                else: b2 = 1
            b1 = 1
        elif o == 4:
            runs += b3 + b2; b3 = b2 = 0
            if b1:
                if nxt() < .42: runs += 1
                else: b3 = 1
            b1 = 0; b2 = 1
        elif o == 5: runs += b1 + b2 + b3; b1 = b2 = 0; b3 = 1
        elif o == 6: runs += 1 + b1 + b2 + b3; b1 = b2 = b3 = 0
        elif o == 7:
            outs += 1
            if b3 and outs < 3 and nxt() < .35: runs += 1; b3 = 0
        else:
            if b1 and outs < 2 and nxt() < .45:
                outs += 2; b1 = 0
                if outs < 3: runs += b3; b3 = b2; b2 = 0
            else:
                outs += 1
                if outs < 3:
                    if b3 and nxt() < .55: runs += 1; b3 = 0
                    if b2 and not b3 and nxt() < .6: b3 = 1; b2 = 0
                    if b1 and not b2 and nxt() < .6: b2 = 1; b1 = 0
    return runs, idx
def game(S, home, away):
    sh, sa = np.zeros(10, int), np.zeros(10, int); rh = ra = 0; ih = ia = 0; inn = 1
    while True:
        r, ia = half(S, away, ia, sa); ra += r
        if inn >= 9 and rh > ra: break
        r, ih = half(S, home, ih, sh, target=(ra - rh + 1) if inn >= 9 else 99); rh += r
        if inn >= 9 and rh != ra: break
        inn += 1
    return rh, ra, sh, sa, inn
def season(S, L, tag, yr):
    codes = list(L); log = []
    for h in codes:
        for _ in range(81):
            a = codes[S.r.integers(len(codes))]
            while a == h: a = codes[S.r.integers(len(codes))]
            rh, ra, sh, sa, inn = game(S, L[h], L[a]); s = sh + sa
            log.append(dict(season=yr, park=tag, home=h, away=a, home_runs=rh, away_runs=ra, innings=inn, PA=int(s.sum()), HR=int(s[6]), H=int(s[3:7].sum()), K=int(s[0]), BB=int(s[1] + s[2]),
                            doubles=int(s[4]), triples=int(s[5]), foul_outs=int(s[9])))
    return log
Lref, Lem = teams_lineups(vecs(ref)), teams_lineups(vecs(EM))
logs = []
for yr in range(1, 6):
    for tag, L in (("REF", Lref), ("EMERALD", Lem)):
        logs += season(Sim(yr * 7 + (tag == "EMERALD")), L, tag, yr)
    print("season", yr, round(time.time() - t0))
gl = pd.DataFrame(logs); gl["total_runs"] = gl.home_runs + gl.away_runs
gl[gl.season == 1].to_csv("data/sim_game_log_season1.csv", index=False)
ss = gl.groupby(["park", "season"]).agg(games=("PA", "size"), runs_per_game=("total_runs", "mean"), HR_per_game=("HR", "mean"), H_per_game=("H", "mean"), K_per_game=("K", "mean"),
        BB_per_game=("BB", "mean"), doubles_per_game=("doubles", "mean"), triples_per_game=("triples", "mean"), foul_outs_per_game=("foul_outs", "mean"),
        PA_per_game=("PA", "mean"), extra_inning_pct=("innings", lambda x: (x > 9).mean() * 100), one_run_game_pct=("total_runs", lambda x: 0)).reset_index()
ss["one_run_game_pct"] = gl.assign(d=(gl.home_runs - gl.away_runs).abs() == 1).groupby(["park", "season"]).d.mean().values * 100
ss.round(3).to_csv("data/sim_league_seasons.csv", index=False)
print(ss.groupby("park").mean(numeric_only=True).round(3).T.to_string())
print("real 2019 R/G per team", round(st["lg"]["R_G"], 3), "-> per game (both teams)", round(2 * st["lg"]["R_G"], 2))
pickle.dump(dict(EM=EM, rv=rv, corr=corr, corr_hr=corr_hr, val=(v_hr, v_avg, v_slg)), open("data/_state2.pkl", "wb"))
print("total", round(time.time() - t0))
