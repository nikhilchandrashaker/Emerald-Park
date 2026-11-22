import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "src")
from model import *
YEAR = 2019
raw = "data/raw/"
# ---------- real data: Lahman 2019 ----------
b = pd.read_csv(raw + "Batting.csv"); b = b[b.yearID == YEAR]
agg = b.groupby("playerID").agg(G=("G","sum"), AB=("AB","sum"), H=("H","sum"), B2=("2B","sum"), B3=("3B","sum"), HR=("HR","sum"),
        BB=("BB","sum"), IBB=("IBB","sum"), SO=("SO","sum"), HBP=("HBP","sum"), SF=("SF","sum"), SH=("SH","sum"), R=("R","sum")).reset_index()
agg["team"] = b.sort_values("stint").groupby("playerID").teamID.last().values
agg["PA"] = agg.AB + agg.BB + agg.HBP + agg.SF + agg.SH
p = pd.read_csv(raw + "People.csv", encoding="latin1")[["playerID","nameFirst","nameLast","bats"]]
pl = agg.merge(p, on="playerID"); pl["player"] = pl.nameFirst + " " + pl.nameLast
pl = pl[pl.PA >= 400].copy(); pl["bats"] = pl.bats.fillna("R").replace({"R":"R","L":"L","B":"B"})
pl["k_rate"] = pl.SO / pl.PA; pl["bb_rate"] = pl.BB / pl.PA; pl["hbp_rate"] = pl.HBP / pl.PA
pl["bip"] = pl.PA - pl.SO - pl.BB - pl.HBP - pl.SH
pl["hr_bip"] = pl.HR / pl.bip
pl = pl.reset_index(drop=True)
tm = pd.read_csv(raw + "Teams.csv"); tm = tm[tm.yearID == YEAR]
lg = dict(PA=int(agg.PA.sum()), R_G=float(tm.R.sum() / (tm.G.sum() / 1)), HR=int(tm.HR.sum()))
print("players", len(pl), "league 2019 R/G per team-game", round(tm.R.sum()/tm.G.sum(),3))

# ---------- parks (approximate public specs; LF line, LCF, CF, RCF, RF line) ----------
P = {"ARI":(330,374,407,374,334,1100),"ATL":(335,385,400,375,325,1050),"BAL":(333,364,410,373,318,20),"BOS":(310,379,390,380,302,20),
"CHA":(330,377,400,372,335,600),"CHN":(355,368,400,368,353,600),"CIN":(328,379,404,370,325,490),"CLE":(325,370,405,375,325,650),
"COL":(347,390,415,375,350,5200),"DET":(345,370,420,365,330,600),"HOU":(315,362,409,373,326,40),"KCA":(330,387,410,387,330,750),
"LAA":(330,389,400,365,330,150),"LAN":(330,375,395,375,330,340),"MIA":(344,386,407,392,335,10),"MIL":(344,371,400,374,345,635),
"MIN":(339,377,404,367,328,840),"NYA":(318,399,408,385,314,55),"NYN":(335,358,408,375,330,10),"OAK":(330,388,400,388,330,10),
"PHI":(329,374,401,369,330,20),"PIT":(325,389,399,375,320,730),"SDN":(336,390,396,391,322,15),"SEA":(331,378,401,381,326,20),
"SFN":(339,364,399,421,309,10),"SLN":(336,375,400,375,335,465),"TBA":(315,370,404,370,322,40),"TEX":(329,372,407,374,326,550),
"TOR":(328,375,400,375,328,250),"WAS":(336,377,402,370,335,10)}
parks = {k: Park(k, v[:5], v[5], heights=([37,37,17,5,3] if k=="BOS" else None)) for k, v in P.items()}
ref = Park("REFERENCE (league-average park)", np.mean([v[:5] for v in P.values()], 0), np.mean([v[5] for v in P.values()]))
print("ref dims", ref.dims.round(1), "elev", round(ref.elev))

# ---------- calibration (reference park, common random numbers) ----------
N = 40000
draws = [make_draws(N, 1000 + i) for i in range(len(pl))]
K = dict(c=1.0, a2=1.0, a3=1.0)
def hr_rate(s, i): return batted(draws[i], s, pl.bats[i], ref, ref, K)["hr"].mean()
S = np.zeros(len(pl))
for i in range(len(pl)):
    lo, hi = -25.0, 25.0
    tgt = pl.hr_bip[i]
    for _ in range(14):
        mid = (lo + hi) / 2
        if hr_rate(mid, i) < tgt: lo = mid
        else: hi = mid
    S[i] = (lo + hi) / 2
pl["s"] = S
print("EV shift mean/min/max", S.mean().round(2), S.min().round(1), S.max().round(1))
# real league shares (our player set)
tot = pl[["AB","H","B2","B3","HR","SO","SF","BB","HBP","SH","PA"]].sum()
nonhr_h = tot.H - tot.HR
real_babip = nonhr_h / (tot.AB - tot.SO - tot.HR + tot.SF)
real_2b, real_3b = tot.B2 / nonhr_h, tot.B3 / nonhr_h
w = pl.bip.values / pl.bip.sum()
def league_bip(K):
    return sum(wi * bip_probs(batted(draws[i], pl.s[i], pl.bats[i], ref, ref, K, 15000)) for i, wi in enumerate(w))
for it in range(4):
    lo, hi = 0.3, 2.5
    for _ in range(16):
        K["c"] = (lo + hi) / 2; x = league_bip(K); nh = x[:3].sum() / (1 - x[3])
        if nh < real_babip * 0.985 / 0.985: lo = K["c"]
        else: hi = K["c"]
    K["c"] = (lo + hi) / 2; x = league_bip(K); nh = x[:3].sum()
    K["a2"] *= real_2b / (x[1] / nh); K["a3"] *= real_3b / (x[2] / nh)
x = league_bip(K); nh = x[:3].sum()
print("K", K, "| model BABIP-like", round(nh/(1-x[3]),3), "real", round(real_babip,3), "| 2B share", round(x[1]/nh,3), round(real_2b,3), "3B", round(x[2]/nh,3), round(real_3b,3))
# per-player contact-quality multiplier m: matches each hitter's real non-HR hit rate (BABIP) in the reference park
real_b = ((pl.H - pl.HR) / (pl.AB - pl.SO - pl.HR + pl.SF)).values
M = np.ones(len(pl))
for i in range(len(pl)):
    lo, hi = 0.2, 2.6
    for _ in range(14):
        mid = (lo + hi) / 2; Ki = dict(K, c=K["c"] * mid); x = bip_probs(batted(draws[i], pl.s[i], pl.bats[i], ref, ref, Ki, 20000))
        if x[:3].sum() / (1 - x[3]) < real_b[i]: lo = mid
        else: hi = mid
    M[i] = (lo + hi) / 2
pl["m"] = M; print("contact multiplier m mean/min/max", M.mean().round(3), M.min().round(2), M.max().round(2))
json.dump(K, open("data/calibration_constants.json", "w"))
pl.drop(columns=["nameFirst","nameLast"]).to_csv("data/players_2019_calibrated.csv", index=False)
import pickle; pickle.dump(dict(K=K, ref=ref, parks=parks, lg=lg, P=P), open("data/_state.pkl", "wb"))
