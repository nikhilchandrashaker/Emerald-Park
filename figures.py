import sys, pickle, json, numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
sys.path.insert(0, "src")
from evalpark import *
s2 = pickle.load(open("data/_state2.pkl", "rb")); EM = s2["EM"]
G = dict(d1="#052e16", d2="#14532d", d3="#15803d", m="#22c55e", l1="#4ade80", l2="#86efac", l3="#dcfce7", bg="#f4fbf5", ink="#052e16", lime="#bef264")
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": G["d2"], "axes.labelcolor": G["ink"], "xtick.color": G["ink"], "ytick.color": G["ink"], "axes.titleweight": "bold", "axes.titlecolor": G["d2"], "figure.facecolor": "white", "axes.facecolor": G["bg"], "savefig.dpi": 200, "savefig.bbox": "tight"})
cm = matplotlib.colors.LinearSegmentedColormap.from_list("g", ["#f0fdf4", "#86efac", "#22c55e", "#14532d"])
FIG = "figures/"
def xy(d, phi): r = np.radians(phi); return d * np.sin(r), d * np.cos(r)
def fence_xy(pk, n=181):
    a = np.linspace(-45, 45, n); D, _ = pk.fence(a); return xy(D, a)
def draw_field(ax, pk, ref_pk=None, grass="#16803d"):
    x, y = fence_xy(pk); ax.fill(np.r_[0, x, 0], np.r_[0, y, 0], color=grass, zorder=1)
    for k in range(0, 460, 40): ax.fill_between(*[np.linspace(-330, 330, 2)], k, k + 20, color="white", alpha=.04, zorder=2) if False else None
    ax.fill([0, -63.6, 0, 63.6], [0, 63.6, 127.3, 63.6], color="#1fa34a", zorder=2)
    for s_ in (-1, 1): ax.plot([0, s_ * pk.dims[0 if s_ < 0 else 4] * np.sin(np.pi / 4)], [0, pk.dims[0 if s_ < 0 else 4] * np.cos(np.pi / 4)], color="white", lw=1, alpha=.8, zorder=3)
    if ref_pk is not None: rx, ry = fence_xy(ref_pk); ax.plot(rx, ry, ls="--", color="#052e16", lw=2, zorder=6)
    ax.plot(x, y, color=G["lime"], lw=3, zorder=5); ax.set_aspect("equal"); ax.set_axis_off()
# ---- Fig 1 field
fig, ax = plt.subplots(figsize=(7, 5.4)); draw_field(ax, EM, ref)
for code, pk in parks.items(): px, py = fence_xy(pk); ax.plot(px, py, color="white", alpha=.13, lw=.8, zorder=3)
for a, lab in ((-45, "LF line"), (-22.5, "LF alley"), (0, "CF"), (22.5, "RF alley"), (45, "RF line")):
    D = float(EM.fence(a)[0]); x, y = xy(D * .86, a); ax.text(x, y, f"{lab}\n{D:.0f} ft", color="white", ha="center", va="center", fontsize=9, fontweight="bold", zorder=7)
ax.set_title("Emerald Park fence (lime) vs. league-average park (dark dashed); 30 real parks faint", fontsize=10, pad=14); ax.set_ylim(-15, 450); ax.set_xlim(-330, 330); fig.savefig(FIG + "fig1_field_dimensions.png"); plt.close()
# ---- Fig 2 design-space
g1 = pd.read_csv("data/design_space_alley_cf.csv"); g2 = pd.read_csv("data/design_space_foul_infield.csv")
fig, axs = plt.subplots(1, 3, figsize=(13, 4))
for ax, col, ttl in zip(axs, ("HR", "runs", "BABIP"), ("Home-run factor", "Run-scoring factor", "BABIP factor")):
    pv = g1.pivot(index="alley", columns="cf", values=col); im = ax.imshow(pv.values, origin="lower", cmap=cm, aspect="auto")
    ax.set_xticks(range(len(pv.columns))); ax.set_xticklabels(pv.columns); ax.set_yticks(range(len(pv.index))); ax.set_yticklabels(pv.index)
    for i in range(pv.shape[0]):
        for j in range(pv.shape[1]): ax.text(j, i, f"{pv.values[i,j]:.0f}", ha="center", va="center", fontsize=8, color="white" if pv.values[i, j] > pv.values.mean() else G["ink"])
    ok = (g1.pivot(index="alley", columns="cf", values="HR") >= 108) & ((g1.pivot(index="alley", columns="cf", values="runs") >= 98) & (g1.pivot(index="alley", columns="cf", values="runs") <= 102))
    for i in range(pv.shape[0]):
        for j in range(pv.shape[1]):
            if ok.values[i, j]: ax.add_patch(Rectangle((j - .5, i - .5), 1, 1, fill=False, ec=G["lime"], lw=2.5))
    si, sj = list(pv.index).index(350), list(pv.columns).index(430); ax.plot(sj, si, marker="*", ms=13, color=G["lime"], mec=G["d1"]); ax.set_title(ttl); ax.set_xlabel("Center-field distance (ft)"); ax.set_ylabel("Alley distance (ft)")
fig.suptitle("Design space: alleys x center field (lime outline = HR >= 108 and runs 98 to 102; star = Emerald Park)", color=G["d2"], fontweight="bold", y=1.03); fig.savefig(FIG + "fig2_design_space.png"); plt.close()
fig, axs = plt.subplots(1, 2, figsize=(9.5, 4))
for ax, col, ttl in zip(axs, ("BABIP", "runs"), ("BABIP factor", "Run-scoring factor")):
    pv = g2.pivot(index="infield", columns="foul", values=col); ax.imshow(pv.values, origin="lower", cmap=cm.reversed() if col == "BABIP" else cm, aspect="auto")
    ax.set_xticks(range(len(pv.columns))); ax.set_xticklabels([f"{c}x" for c in pv.columns]); ax.set_yticks(range(len(pv.index))); ax.set_yticklabels([f"{c}x" for c in pv.index])
    for i in range(pv.shape[0]):
        for j in range(pv.shape[1]): ax.text(j, i, f"{pv.values[i,j]:.1f}", ha="center", va="center", fontsize=8, color=G["ink"])
    ax.set_title(ttl); ax.set_xlabel("Foul territory (x league average)"); ax.set_ylabel("Infield speed (x)")
fig.suptitle("Pitcher-side levers (alleys 350, center 430)", color=G["d2"], fontweight="bold"); fig.savefig(FIG + "fig3_pitcher_levers.png"); plt.close()
# ---- Fig 4 park scatter, Fig 5 validation
pf = pd.read_csv("data/parks_mlb_2019_and_emerald.csv"); real = pf[pf.park_code.isin(parks)]; emr = pf[pf.park_code == "EMERALD"].iloc[0]
fig, ax = plt.subplots(figsize=(6.6, 5)); ax.axvspan(100, 120, ymin=0, ymax=(100 - 94) / (104 - 94), color=G["l2"], alpha=.35)
ax.scatter(real.model_HR_PA_factor, real.model_BABIP_factor, color=G["d3"], s=40, label="30 MLB parks (model)")
for r in real.itertuples(): ax.annotate(r.park_code, (r.model_HR_PA_factor, r.model_BABIP_factor), fontsize=6.5, xytext=(3, 3), textcoords="offset points")
ax.scatter([emr.model_HR_PA_factor], [emr.model_BABIP_factor], marker="*", s=300, color=G["lime"], ec=G["d1"], zorder=5, label="Emerald Park")
ax.axhline(100, color=G["d2"], lw=.8); ax.axvline(100, color=G["d2"], lw=.8); ax.set_xlim(84, 118); ax.set_ylim(94, 104); ax.set_xlabel("Home-run factor (higher = batter-friendly)"); ax.set_ylabel("BABIP factor (lower = pitcher-friendly)"); ax.legend(loc="upper left", fontsize=8)
ax.set_title("Shaded = batter- and pitcher-friendly at once"); fig.savefig(FIG + "fig4_park_quadrant.png"); plt.close()
fig, axs = plt.subplots(1, 2, figsize=(10, 4.2)); ax = axs[0]; ax.scatter(real.lahman_BPF_2019, real.model_runs_factor, color=G["d3"], s=36)
for r in real.itertuples(): ax.annotate(r.park_code, (r.lahman_BPF_2019, r.model_runs_factor), fontsize=6.5, xytext=(3, 3), textcoords="offset points")
b = np.polyfit(real.lahman_BPF_2019, real.model_runs_factor, 1); xs = np.linspace(real.lahman_BPF_2019.min(), real.lahman_BPF_2019.max(), 10); ax.plot(xs, np.polyval(b, xs), color=G["m"])
ax.set_xlabel("Lahman 2019 park factor (BPF)"); ax.set_ylabel("Model run factor"); ax.set_title(f"Out-of-sample park check, r = {s2['corr']:.2f}")
ss = pd.read_csv("data/sim_league_seasons.csv"); m = ss.groupby("park").runs_per_game.mean(); ax = axs[1]
ax.bar(["Real 2019\nMLB", "Simulated\nleague park", "Simulated\nEmerald"], [9.66, m["REF"], m["EMERALD"]], color=[G["l3"], G["l1"], G["d3"]], ec=G["d2"])
for i, v in enumerate([9.66, m["REF"], m["EMERALD"]]): ax.text(i, v + .05, f"{v:.2f}", ha="center", fontweight="bold")
ax.set_ylim(8.5, 10.5); ax.set_ylabel("Runs per game (both teams)"); ax.set_title("Simulator vs. real 2019 scoring"); fig.savefig(FIG + "fig5_validation.png"); plt.close()
# ---- Fig 6 league impact
pv = ss.pivot(index="season", columns="park")
mets = [("HR_per_game", "HR"), ("H_per_game", "Hits"), ("doubles_per_game", "2B"), ("triples_per_game", "3B"), ("K_per_game", "K"), ("runs_per_game", "Runs"), ("foul_outs_per_game", "Foul outs")]
fig, ax = plt.subplots(figsize=(8, 4.2)); vals = []
for i, (c, n) in enumerate(mets):
    d = 100 * (pv[c]["EMERALD"] / pv[c]["REF"] - 1); vals.append((n, d.mean(), d.std()))
    ax.bar(i, d.mean(), yerr=d.std(), color=G["l1"] if d.mean() > 0 and n in ("HR", "2B", "Runs") else G["l3"], ec=G["d2"], capsize=4)
    ax.text(i, d.mean() + (3 if d.mean() >= 0 else -9), f"{d.mean():+.1f}%", ha="center", fontsize=8, fontweight="bold")
ax.set_xticks(range(len(mets))); ax.set_xticklabels([n for _, n in mets]); ax.axhline(0, color=G["d2"], lw=1); ax.set_ylabel("% change per game vs. league-average park"); ax.set_title("League impact (5 simulated seasons, error bar = 1 s.d.)"); fig.savefig(FIG + "fig6_league_impact.png"); plt.close()
json.dump({n: [round(a, 2), round(b, 2)] for n, a, b in vals}, open("data/league_impact_pct.json", "w"))
# ---- Fig 7 spray chart (HR hitter)
fig, axs = plt.subplots(1, 2, figsize=(11, 5)); i = int(pl.HR.idxmax()); p = players[i]; Ki = dict(K, c=K["c"] * p["m"])
for ax, pk, ttl in ((axs[0], ref, "League-average park"), (axs[1], EM, "Emerald Park")):
    draw_field(ax, pk, None); b = batted(draws[i], p["s"], p["bats"], pk, ref, Ki, 700); Dn, _ = pk.fence(b["phi"]); dd = np.where(b["d"] < 60, 85 + (b["ev"] - 60) * .9, np.where(b["hr"], b["d"], np.minimum(b["d"], Dn - 3))); x, y = xy(dd, b["phi"]); hit = b["p_hit"] > .5
    ax.scatter(x[~b["hr"]], y[~b["hr"]], s=7, color="#052e16", alpha=.45, label="in play"); ax.scatter(x[b["hr"]], y[b["hr"]], s=16, color=G["lime"], ec=G["d1"], lw=.4, label=f"HR ({int(b['hr'].sum())} of 700)")
    ax.legend(loc="lower center", fontsize=8, framealpha=.9); ax.set_title(f"{p['player']}: {ttl}")
fig.savefig(FIG + "fig7_spray_chart.png"); plt.close()
# ---- Fig 8 player impact
res = pd.read_csv("data/sim_player_park_results.csv"); w = res.pivot(index="player", columns="park", values="HR_per_600PA"); w["d"] = w.EMERALD - w.REF
pj = pl.set_index("player").join(w); fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
axs[0].scatter(pj.REF, pj.d, c=[G["d3"] if b == "R" else G["l1"] if b == "L" else G["lime"] for b in pj.bats], s=22, ec=G["d2"], lw=.3); axs[0].set_xlabel("HR per 600 PA in league-average park"); axs[0].set_ylabel("Extra HR per 600 PA in Emerald Park"); axs[0].set_title("Power hitters gain the most"); 
for b, c in (("R", G["d3"]), ("L", G["l1"]), ("B", G["lime"])): axs[0].scatter([], [], color=c, label=f"bats {b}")
axs[0].legend(fontsize=8)
sd = pj.groupby("bats").d.mean(); axs[1].hist([pj[pj.bats == b].d for b in ("R", "L", "B")], bins=14, stacked=True, color=[G["d3"], G["l1"], G["lime"]], ec="white"); axs[1].set_xlabel("Extra HR per 600 PA"); axs[1].set_ylabel("Hitters"); axs[1].set_title("Distribution of the effect (207 hitters)"); fig.savefig(FIG + "fig8_player_effects.png"); plt.close()
bt = pj.groupby("bats").d.mean().round(2).to_dict(); corr_pow = float(np.corrcoef(pj.REF, pj.d)[0, 1])
# ---- Fig 9 model schematic
fig, ax = plt.subplots(figsize=(11, 4.6)); ax.set_xlim(0, 11); ax.set_ylim(0, 4.6); ax.axis("off")
def box(x, y, w, h, t, fc=G["l3"], fs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04", fc=fc, ec=G["d2"], lw=1.4)); ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, color=G["ink"])
def arr(x1, y1, x2, y2): ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color=G["d3"], lw=1.6))
box(.1, 3.3, 2.3, 1, "Real 2019 data\nK, BB, HBP rates\nHR per ball in play\nBABIP (207 hitters)", G["l2"]); box(3.1, 3.3, 2.1, 1, "Plate appearance\nK / BB / HBP / foul out\nor ball in play"); box(5.9, 3.3, 2.6, 1, "Batted ball\nEV ~ N(88+s, 14) mph\nLA ~ N(12, 25) deg\nspray ~ N(-side*pull, 23) deg"); box(9, 3.3, 1.9, 1, "Flight\nd = 0.68 v^2 sin(2LA) / g\nx air-density carry")
arr(2.4, 3.8, 3.1, 3.8); arr(5.2, 3.8, 5.9, 3.8); arr(8.5, 3.8, 9, 3.8)
box(.1, 1.7, 2.6, 1, "Fence test\nHR if LA in [17,52] and\nd >= D(spray) + 1.4 x wall", G["l1"]); box(3.3, 1.7, 2.6, 1, "Hit probability\nground / line drive / fly ball\nnear-wall and outfield-depth terms"); box(6.5, 1.7, 2.1, 1, "Hit type\n1B / 2B / 3B by\nwall distance"); box(9.1, 1.7, 1.8, 1, "Outcome\nOut / hit / HR")
arr(9.9, 3.3, 1.4, 2.7); arr(2.7, 2.2, 3.3, 2.2); arr(5.9, 2.2, 6.5, 2.2); arr(8.6, 2.2, 9.1, 2.2)
box(.1, .1, 3.2, 1, "Calibrate (reference park)\ns: match each HR rate\nc, a2, a3: league BABIP, 2B, 3B\nm: each hitter's BABIP", G["l2"]); box(3.9, .1, 3.2, 1, "Game simulator\n9 innings, base-state logic,\nlineups of real 2019 teams"); box(7.7, .1, 3.2, 1, "Outputs: park factors,\nleague seasons, game logs,\nswing simulator", G["l2"]); arr(3.3, .6, 3.9, .6); arr(7.1, .6, 7.7, .6)
fig.savefig(FIG + "fig9_model_schematic.png"); plt.close()
# ---- pitcher projection
rvec, evec = league_vec(ref), league_vec(EM); hits = lambda v: v[3:6].sum(); wts = np.array([.74, 1.04, 1.31]); w_h = float((rvec[3:6] * wts).sum() / rvec[3:6].sum())
f_hr, f_h = evec[6] / rvec[6], hits(evec) / hits(rvec); f_bip = 1.0
pt = pd.read_csv("data/raw/Pitching.csv"); pt = pt[(pt.yearID == 2019)].groupby("playerID").agg(IPouts=("IPouts", "sum"), H=("H", "sum"), HR=("HR", "sum"), BB=("BB", "sum"), SO=("SO", "sum"), ER=("ER", "sum"), BFP=("BFP", "sum"), GS=("GS", "sum")).reset_index()
pp = pd.read_csv("data/raw/People.csv", encoding="latin1")[["playerID", "nameFirst", "nameLast"]]; pt = pt.merge(pp, on="playerID"); pt["pitcher"] = pt.nameFirst + " " + pt.nameLast; pt = pt[pt.IPouts >= 300].copy()
pt["IP"] = pt.IPouts / 3; pt["ERA_2019"] = 9 * pt.ER / pt.IP; pt["H_nonHR"] = pt.H - pt.HR
base = .74 * 0 + w_h * pt.H_nonHR + 1.67 * pt.HR + .6 * pt.BB; new = w_h * pt.H_nonHR * f_h + 1.67 * pt.HR * f_hr + .6 * pt.BB
pt["ERA_emerald_proj"] = pt.ERA_2019 * (new / base); pt["dERA"] = pt.ERA_emerald_proj - pt.ERA_2019; pt["HR9_2019"] = 9 * pt.HR / pt.IP; pt["HR9_emerald"] = pt.HR9_2019 * f_hr
pt["H9_2019"] = 9 * pt.H / pt.IP; pt["H9_emerald"] = 9 * (pt.HR * f_hr + pt.H_nonHR * f_h) / pt.IP; pt["SO9"] = 9 * pt.SO / pt.IP
pt[["pitcher","IP","ERA_2019","ERA_emerald_proj","dERA","HR9_2019","HR9_emerald","H9_2019","H9_emerald","SO9"]].round(3).sort_values("dERA").to_csv("data/pitchers_2019_emerald_projection.csv", index=False)
fig, ax = plt.subplots(figsize=(7, 4)); ax.hist(pt.dERA, bins=24, color=G["m"], ec="white"); ax.axvline(0, color=G["d1"], lw=1.2); ax.axvline(pt.dERA.mean(), color=G["lime"], lw=2.5, label=f"mean {pt.dERA.mean():+.2f} ERA")
ax.set_xlabel("Projected ERA change in Emerald Park"); ax.set_ylabel("Pitchers (>= 100 IP, 2019)"); ax.legend(); ax.set_title("Pitcher view: who gains and who loses"); fig.savefig(FIG + "fig10_pitcher_effects.png"); plt.close()
corr_h = float(np.corrcoef(pt.HR9_2019, pt.dERA)[0, 1])
summ = dict(f_hr=float(f_hr), f_h=float(f_h), w_h=w_h, mean_dERA=float(pt.dERA.mean()), n_pitch=int(len(pt)), pct_better=float((pt.dERA < 0).mean()), corr_hr9_dERA=corr_h, bats_mean=bt, corr_power=corr_pow,
            hr_extra_max=float(pj.d.max()), hr_extra_mean=float(pj.d.mean()), best=pt.sort_values("dERA").head(3)[["pitcher","dERA"]].values.tolist(), worst=pt.sort_values("dERA").tail(3)[["pitcher","dERA"]].values.tolist())
json.dump(summ, open("data/_summ.json", "w"), default=float); print(json.dumps(summ, default=float, indent=1))
