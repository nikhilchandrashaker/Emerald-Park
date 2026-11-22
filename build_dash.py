import json, pickle, sys, numpy as np, pandas as pd
sys.path.insert(0, "src")
st = pickle.load(open("data/_state.pkl","rb")); s2 = pickle.load(open("data/_state2.pkl","rb"))
K, ref, EM = st["K"], st["ref"], s2["EM"]
pl = pd.read_csv("data/players_2019_calibrated.csv").sort_values("HR", ascending=False)
pj = [dict(n=r.player, t=r.team, b=r.bats, s=round(r.s,2), m=round(r.m,3), k=round(r.k_rate,4), bb=round(r.bb_rate,4), hb=round(r.hbp_rate,4), pa=int(r.PA), ab=int(r.AB), h=int(r.H), d2=int(r.B2), d3=int(r.B3), hr=int(r.HR)) for r in pl.itertuples()]
pf = pd.read_csv("data/parks_mlb_2019_and_emerald.csv")
parks = [dict(c=r.park_code, hr=r.model_HR_PA_factor, babip=r.model_BABIP_factor, runs=r.model_runs_factor) for r in pf.itertuples()]
ss = pd.read_csv("data/sim_league_seasons.csv"); m = ss.groupby("park").mean(numeric_only=True)
lo, hi = ss.groupby("park").min(numeric_only=True), ss.groupby("park").max(numeric_only=True)
league = {p: {c: round(float(m.loc[p, c]), 3) for c in m.columns if c != "season"} for p in m.index}
res = pd.read_csv("data/sim_player_park_results.csv"); w = res.pivot(index="player", columns="park", values="HR_per_600PA"); w["d"] = w.EMERALD - w.REF
g = w.sort_values("d", ascending=False)
gain = [dict(n=i, d=round(float(r.d),2), ref=round(float(r.REF),1), em=round(float(r.EMERALD),1)) for i, r in g.head(10).iterrows()]
eff = pf[pf.park_code == "EMERALD"].iloc[0]
data = dict(players=pj, parks=parks, K=dict(c=K["c"], a2=float(K["a2"]), a3=float(K["a3"])),
            ref=dict(dims=[round(float(x),1) for x in ref.dims], carry=ref.carry, foul=1, infield=1),
            em=dict(dims=[float(x) for x in EM.dims], carry=EM.carry, foul=EM.foul, infield=EM.infield),
            league=league, gain=gain, fx={k: float(eff["model_"+k+"_factor"]) for k in ("HR_PA","AVG","BABIP","ISO","XBH_PA","FOUL_OUT_PA")}|{"runs": float(eff.model_runs_factor)},
            val=dict(corr=round(s2["corr"],2), hr=round(s2["val"][0],2), slg=round(s2["val"][2],2)))
json.dump(data, open("data/dashboard_data.json","w"), separators=(",",":"))
tpl = open("src/dashboard_template.html").read()
html = tpl.replace("/*__CHARTJS__*/", open("/tmp/node_modules/chart.js/dist/chart.umd.js").read()).replace("/*__DATA__*/", "const DATA=" + json.dumps(data, separators=(",",":")) + ";")
open("emerald_park_dashboard.html","w").write(html); print("dashboard bytes", len(html))
