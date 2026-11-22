import json, pickle, sys, numpy as np, pandas as pd
sys.path.insert(0, "src")
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
st = pickle.load(open("data/_state.pkl", "rb")); s2 = pickle.load(open("data/_state2.pkl", "rb")); K = st["K"]
S = json.load(open("data/_summ.json")); IMP = json.load(open("data/league_impact_pct.json"))
pf = pd.read_csv("data/parks_mlb_2019_and_emerald.csv"); em = pf[pf.park_code == "EMERALD"].iloc[0]
ss = pd.read_csv("data/sim_league_seasons.csv"); m = ss.groupby("park").mean(numeric_only=True); R, E = m.loc["REF"], m.loc["EMERALD"]
pl = pd.read_csv("data/players_2019_calibrated.csv"); res = pd.read_csv("data/sim_player_park_results.csv")
w = res.pivot(index="player", columns="park", values="HR_per_600PA"); w["d"] = w.EMERALD - w.REF; w = w.sort_values("d", ascending=False)
GD, GM, GL, GP = colors.HexColor("#14532d"), colors.HexColor("#15803d"), colors.HexColor("#dcfce7"), colors.HexColor("#f0fdf4")
H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=14, textColor=GD, spaceBefore=14, spaceAfter=6)
H2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11, textColor=GM, spaceBefore=8, spaceAfter=3)
B = ParagraphStyle("b", fontName="Times-Roman", fontSize=10.5, leading=14.2, alignment=TA_JUSTIFY, spaceAfter=6)
EQ = ParagraphStyle("eq", parent=B, alignment=TA_CENTER, fontName="Times-Italic", backColor=GP, borderPadding=4, spaceBefore=3, spaceAfter=8)
CAP = ParagraphStyle("cap", fontName="Helvetica-Oblique", fontSize=8.5, leading=11, textColor=GD, alignment=TA_CENTER, spaceAfter=10)
T = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=20, leading=24, textColor=GD, alignment=TA_CENTER, spaceAfter=4)
SUB = ParagraphStyle("s", fontName="Helvetica", fontSize=10.5, leading=14, textColor=GM, alignment=TA_CENTER, spaceAfter=3)
AB = ParagraphStyle("ab", parent=B, leftIndent=24, rightIndent=24, fontSize=10, leading=13.4, backColor=GP, borderPadding=7, borderColor=GM, borderWidth=.6, spaceBefore=8, spaceAfter=10)
def P(t, s=B): return Paragraph(t, s)
def fig(name, cap, wd=6.4):
    from PIL import Image as PI
    w_, h_ = PI.open("figures/" + name).size; return KeepTogether([Image("figures/" + name, wd * inch, wd * inch * h_ / w_), P(cap, CAP)])
def tab(rows, cw=None, fs=8.5):
    cs = ParagraphStyle("c", fontName="Helvetica", fontSize=fs, leading=fs + 2)
    rows = [[Paragraph(c, cs) if (i > 0 and isinstance(c, str) and len(c) > 34) else c for c in r] for i, r in enumerate(rows)]
    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), GD), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), fs),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GP]), ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#86efac")), ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return [t, Spacer(1, 8)]
pct = lambda a, b: f"{100 * (a / b - 1):+.1f}%"
ab = lambda a, b: f"{100 * abs(a / b - 1):.1f}%"
def foot(c, d):
    c.saveState(); c.setFont("Helvetica", 8); c.setFillColor(GM); c.drawCentredString(letter[0] / 2, .5 * inch, f"Emerald Park | page {d.page}"); c.restoreState()
doc = SimpleDocTemplate("emerald_park_research_paper.pdf", pagesize=letter, leftMargin=.95 * inch, rightMargin=.95 * inch, topMargin=.85 * inch, bottomMargin=.8 * inch, title="Emerald Park: a ballpark for both pitchers and batters", author="Nikhil Chandrashaker")
s = []
s += [P("Emerald Park", T), P("Can a Ballpark Help Hitters and Pitchers at the Same Time?", ParagraphStyle("t2", parent=T, fontSize=13, leading=16, textColor=GM)),
      P("A batted-ball and game simulation built on real 2019 MLB data", SUB), P("Nikhil Chandrashaker | California Lutheran University | November 2026", SUB)]
s.append(P(f"<b>Abstract.</b> Ballparks are usually described as pitcher-friendly or batter-friendly, as if one must choose. This paper asks whether a single field can be both. "
 f"I build a physics-based batted-ball model calibrated to the real 2019 batting lines of {len(pl)} MLB hitters (strikeout, walk and home-run rates matched exactly, plus each hitter's non-HR hit rate), "
 f"design a hypothetical park (Emerald Park: short 310 ft lines, 350 ft alleys, 430 ft center field, 2.2x foul territory, slow grass infield), and simulate 5 seasons of {int(R.games):,} games in it and in a league-average park. "
 f"Emerald Park raises home runs by {ab(E.HR_per_game, R.HR_per_game)} per game, cuts hits by {ab(E.H_per_game, R.H_per_game)}, more than doubles foul-ball outs ({pct(E.foul_outs_per_game, R.foul_outs_per_game)}), and leaves scoring essentially unchanged "
 f"({R.runs_per_game:.2f} to {E.runs_per_game:.2f} runs per game, {pct(E.runs_per_game, R.runs_per_game)}). The park therefore does not make scoring easier or harder; it changes <i>how</i> runs are scored, rewarding power hitters and pitchers who keep the ball in the park. "
 f"The model reproduces real 2019 scoring within {abs(100 * (R.runs_per_game / 9.66 - 1)):.0f}% and ranks real parks' run environments with r = {s2['corr']:.2f} against Lahman park factors.", AB))
s.append(P("1. Introduction", H1))
s.append(P("Park factors summarize how a ballpark changes run scoring, but they hide structure. Coors Field raises almost everything. Petco Park and Oracle Park suppress most things. Rarely do we see a park that pushes home runs up while pushing balls in play down. "
 "That combination is not a contradiction: home runs depend on how far a ball carries to a fence, while singles and doubles depend on where fielders can reach and how much foul territory exists to catch mistakes. These are different physical mechanisms, so they can be tuned in different directions."))
s.append(P("I define a park as <b>both-friendly</b> when three conditions hold at once. (1) Batter-friendly: the home-run factor is at least 108 (8% above a league-average park). (2) Pitcher-friendly: the factor for BABIP (batting average on balls in play, home runs excluded) is at most 97 and caught-foul-ball outs rise. "
 "(3) Run-neutral: total run scoring is within 2% of a league-average park, so the park is not simply a hitter's or pitcher's park in disguise. The research questions are: Can such a park exist inside the model? What dimensions produce it? And what does it do to hitters, pitchers and the league?"))
s.append(P("2. Data", H1))
s.append(P(f"<b>Real data.</b> Batting and pitching lines for 2019 come from the Lahman Baseball Databank (2021.2 release), the last full 162-game season it contains. I use the {len(pl)} hitters with at least 400 plate appearances and {S['n_pitch']} pitchers with at least 100 innings. "
 "Team run totals and the real 2019 park factors (BPF) from the same source are used for validation. 2019 is also the peak home-run season in MLB history (6,776 league home runs), which makes it a demanding test for a power-oriented park."))
s.append(P("<b>Approximate or modeled inputs.</b> Statcast batted-ball data was not available in the build environment, so exit velocity, launch angle and spray angle are modeled, not observed (Section 3). The 30 real parks' fence distances (left line, left alley, center, right alley, right line) are approximate public figures and should be re-checked before publication. "
 "Outfield walls are 8 ft everywhere except Fenway Park (a 37 ft left-field wall). Elevation drives an air-density carry term. All other park features (wind, humidity, roof, dirt and turf types) are omitted."))
s.append(fig("fig9_model_schematic.png", "Figure 1. Model pipeline: real rates feed a plate-appearance model, batted balls are simulated and tested against each park's fence, and the results drive a game simulator."))
s.append(P("3. Model", H1))
s.append(P("3.1 Plate appearances", H2))
s.append(P("Each hitter's strikeout, walk (including intentional) and hit-by-pitch rates per plate appearance are taken directly from 2019. These outcomes do not depend on the park. Of the remaining plate appearances, a share q = 0.008 x (foul-territory multiplier) ends with a caught foul ball. The rest become balls in play."))
s.append(P("3.2 Batted balls", H2))
s.append(P("A ball in play has exit velocity EV, launch angle LA and spray angle phi (-45 = left-field line, +45 = right-field line):", B))
s.append(P("EV = N(88 + s<sub>i</sub>, 14) - 0.012 (LA - 17)<super>2</super> mph;  LA ~ N(12, 25) deg;  phi ~ N(-side x pull<sub>i</sub>, 23) deg, reflected at the foul lines", EQ))
s.append(P("The power parameter s<sub>i</sub> is fitted for every hitter by bisection so that his simulated home runs per ball in play in the league-average park equal his real 2019 rate. Pull tendency rises with power, pull<sub>i</sub> = clip(10 + 0.35 s<sub>i</sub>, 4, 18) degrees, and switch hitters bat left-handed 65% of the time. "
 f"Fitted s<sub>i</sub> ranges from {pl.s.min():.1f} to {pl.s.max():.1f} mph around the 88 mph base."))
s.append(P("3.3 Flight and the fence", H2))
s.append(P("Carry distance uses a drag-adjusted projectile approximation with an air-density term for elevation (h feet):", B))
s.append(P("d = 0.68 x v<super>2</super> sin(2 LA) / g x (1 + 0.000012 h),   v = 1.4667 x EV ft/s,  g = 32.174 ft/s<super>2</super>", EQ))
s.append(P("A ball is a home run when 17 <= LA <= 52 degrees and d >= D(phi) + 1.4 x W(phi), where D is the fence distance at spray angle phi (linear interpolation between the five anchor distances) and W is the wall height in feet. The 0.68 drag factor reproduces familiar Statcast pairings (roughly 375 ft at 100 mph and 28 degrees)."))
s.append(P("3.4 Hits, outs and foul territory", H2))
s.append(P("Balls in play that are not home runs become hits with probability c x m<sub>i</sub> x p. Here p depends on batted-ball type. Ground balls (LA below 10): p = 0.17 + 0.005 (EV - 80), multiplied by the park's infield-speed factor. Line drives (10 to 25 degrees): 0.62 + 0.008 (EV - 90). Fly balls: a base of 0.09 x (D / D<sub>ref</sub>)<super>1.5</super>, so a larger outfield exposes more gaps. "
 "Any non-ground ball landing within 45 ft of the fence has a much higher hit probability (up to 0.9), which is how wall ball doubles and triples arise. Hit type (single, double, triple) depends on whether the ball reached the wall and on the wall distance, with deeper fences producing more triples."))
s.append(P(f"<b>Calibration.</b> The global constants c = {K['c']:.3f}, a<sub>2</sub> = {float(K['a2']):.3f} and a<sub>3</sub> = {float(K['a3']):.3f} are fitted so that league BABIP, the doubles share and the triples share of non-HR hits match 2019 exactly in the reference park (a 30-park average, with fences {st['ref'].dims.round(0).astype(int).tolist()} ft and 509 ft elevation). "
 f"A per-hitter contact multiplier m<sub>i</sub> ({pl.m.min():.2f} to {pl.m.max():.2f}) then matches each hitter's own BABIP. Because s<sub>i</sub> and m<sub>i</sub> are fitted to 2019 outcomes, the hitter-level agreement in Section 6 is a fit, not a test."))
s.append(P("3.5 Game simulator", H2))
s.append(P("Each club's lineup is its nine hitters with the most 2019 plate appearances (a league-average hitter fills any gap), batting against league-average pitching, with the home team in Emerald Park or the reference park. The simulator plays full games with base-state logic: walks force runners, singles score runners from third and usually from second, doubles score runners from second and third, "
 "ground balls can become double plays (45% with a runner on first and fewer than two outs), and fly outs score runners from third 35% of the time. A season is 81 home games per club, 2,430 games, against random opponents; I simulate 5 seasons per park. Pitchers are summarized separately in Section 5.5."))
s.append(P("4. Emerald Park", H1))
rows = [["Feature", "Emerald Park", "League-average park", "Mechanism"], ["Left and right lines", "310 ft", f"{st['ref'].dims[0]:.0f} / {st['ref'].dims[4]:.0f} ft", "Batter: pulled power becomes home runs"],
 ["Alleys", "350 ft", f"{st['ref'].dims[1]:.0f} ft", "Batter: the pull-side alleys are where most home runs land"], ["Center field", "430 ft", f"{st['ref'].dims[2]:.0f} ft", "Pitcher: takes away center and opposite-field power"],
 ["Foul territory", "2.2x", "1.0x", "Pitcher: caught foul pop-ups end plate appearances"], ["Infield", "0.86x speed", "1.0x", "Pitcher: slow, lush grass turns grounders into outs"], ["Elevation", "509 ft", "509 ft", "Held equal so geometry is isolated"]]
s += tab(rows, [1.2 * inch, .95 * inch, 1.3 * inch, 2.9 * inch], 8)
s.append(fig("fig1_field_dimensions.png", "Figure 2. Emerald Park (lime) against the league-average park (dark dashed) and the 30 real parks (faint).", 4.9))
s.append(P("5. Results", H1))
s.append(P("5.1 The design space", H2))
s.append(P("Figure 3 sweeps alley and center-field distance with the pitcher-side levers fixed. Home runs respond strongly to alley distance (each 10 ft shorter adds roughly 6 to 8 points of home-run factor) and moderately to center-field depth. BABIP barely moves with geometry; it is the foul-territory and infield levers that set it (Figure 4). "
 "Run scoring stays inside 98 to 102 across a band of designs, outlined in lime, which is what allows the park to be run-neutral. Emerald Park (star) sits in that band with a home-run factor of 114."))
s.append(fig("fig2_design_space.png", "Figure 3. Home-run, run-scoring and BABIP factors across alley and center-field distances. Lime outlines meet HR >= 108 and run factor 98 to 102.", 6.6))
s.append(fig("fig3_pitcher_levers.png", "Figure 4. BABIP and run factors across foul-territory and infield-speed settings.", 5.2))
s.append(P("5.2 League-level park factors", H2))
rows = [["Metric (per PA, index 100 = league park)", "Emerald Park", "Reading"], ["Home runs", f"{em.model_HR_PA_factor:.0f}", "batter-friendly"], ["Isolated power", f"{em.model_ISO_factor:.0f}", "batter-friendly"], ["Extra-base hits", f"{em.model_XBH_PA_factor:.0f}", "batter-friendly"],
 ["Batting average", f"{em.model_AVG_factor:.0f}", "pitcher-friendly"], ["BABIP", f"{em.model_BABIP_factor:.0f}", "pitcher-friendly"], ["Caught-foul outs", f"{em.model_FOUL_OUT_PA_factor:.0f}", "pitcher-friendly"], ["Run scoring", f"{em.model_runs_factor:.0f}", "neutral"]]
s += tab(rows, [2.9 * inch, 1.3 * inch, 1.6 * inch])
s.append(P("All three conditions of the both-friendly definition hold. Among the 30 real parks, the model finds none with a home-run factor above 100 and a BABIP factor below 100 together (Figure 5); real parks sit between BABIP 99 and 103 because their geometry mostly trades home runs against hits in the same direction."))
s.append(fig("fig4_park_quadrant.png", "Figure 5. Home-run factor against BABIP factor for 30 real parks and Emerald Park.", 4.3))
s.append(P("5.3 Simulated league seasons", H2))
rows = [["Per game (both teams)", "League park", "Emerald Park", "Change"]] + [[n, f"{R[c]:.{d}f}", f"{E[c]:.{d}f}", pct(E[c], R[c])] for n, c, d in (("Runs", "runs_per_game", 2), ("Home runs", "HR_per_game", 2), ("Hits", "H_per_game", 2), ("Doubles", "doubles_per_game", 2), ("Triples", "triples_per_game", 2), ("Strikeouts", "K_per_game", 2), ("Walks and HBP", "BB_per_game", 2), ("Caught-foul outs", "foul_outs_per_game", 2), ("Extra-inning games, %", "extra_inning_pct", 1))]
s += tab(rows, [2.4 * inch, 1.2 * inch, 1.2 * inch, 1.0 * inch])
s.append(P(f"Home runs rise {IMP['HR'][0]:.1f}% (season-to-season s.d. {IMP['HR'][1]:.1f} points) while hits fall {abs(IMP['Hits'][0]):.1f}%. Doubles are flat ({IMP['2B'][0]:+.1f}%) because deep alleys are replaced by shallow ones on the pull side and deep center offsets them, and triples fall {abs(IMP['3B'][0]):.1f}%. "
 f"Strikeouts and walks are unchanged by construction because the park cannot change them in this model. Run scoring moves {IMP['Runs'][0]:+.1f}% with a season-to-season s.d. of {IMP['Runs'][1]:.1f}, which is indistinguishable from zero."))
s.append(fig("fig6_league_impact.png", "Figure 6. Percent change per game, Emerald Park versus a league-average park (5 simulated seasons).", 5.0))
s.append(P("5.4 Hitters", H2))
top, bot = w.head(5), w.tail(5)
s.append(P(f"Every hitter gains home runs, but power matters: the extra home runs per 600 plate appearances correlate with a hitter's baseline home-run rate at r = {S['corr_power']:.2f}. The average gain is {S['hr_extra_mean']:.1f} per 600 PA and the largest is {S['hr_extra_max']:.1f}. "
 f"By batting hand the average gains are {S['bats_mean']['R']:.1f} (right-handed), {S['bats_mean']['L']:.1f} (left-handed) and {S['bats_mean']['B']:.1f} (switch). The model builds in a pull tendency that rises with power, so the pull-side design helps power-pull hitters most."))
rows = [["Hitter", "HR/600 league park", "HR/600 Emerald", "Extra HR"]] + [[i, f"{r.REF:.1f}", f"{r.EMERALD:.1f}", f"{r.d:+.1f}"] for i, r in top.iterrows()] + [["...", "", "", ""]] + [[i, f"{r.REF:.1f}", f"{r.EMERALD:.1f}", f"{r.d:+.1f}"] for i, r in bot.iterrows()]
s += tab(rows, [2.3 * inch, 1.4 * inch, 1.3 * inch, .9 * inch])
s.append(fig("fig7_spray_chart.png", "Figure 7. 700 simulated batted balls for the 2019 home-run leader in each park. Lime dots are home runs; non-home-run balls are drawn no farther than the fence.", 6.4))
s.append(fig("fig8_player_effects.png", "Figure 8. Left: extra home runs against baseline power. Right: distribution of the effect across 207 hitters, by batting hand.", 6.2))
s.append(P("5.5 Pitchers", H2))
s.append(P(f"For pitchers I apply the league-level multipliers from the model to each pitcher's real 2019 line: home runs allowed x {S['f_hr']:.3f} and non-home-run hits allowed x {S['f_h']:.3f}, with strikeouts and walks unchanged, converting events to runs with linear-weight run values. "
 f"The mean change in ERA across {S['n_pitch']} pitchers is {S['mean_dERA']:+.2f}, and {100 * S['pct_better']:.0f}% of pitchers improve slightly. The spread is the story: the change in ERA correlates with a pitcher's home runs per nine innings at r = {S['corr_hr9_dERA']:.2f}. "
 "Pitchers who rarely allow home runs gain from the lost hits; home-run-prone pitchers are hurt. So Emerald Park is pitcher-friendly in the sense of hits and foul outs, but it is a park for pitchers who keep the ball in the park, not an across-the-board run-prevention park. This is an honest limit of the both-friendly idea: when scoring is held neutral, one group's gain is paid for by the other."))
s.append(fig("fig10_pitcher_effects.png", "Figure 9. Projected ERA change for pitchers with at least 100 innings in 2019.", 4.2))
s.append(P("6. Validation", H1))
s.append(P(f"<b>Out of sample.</b> (a) Simulated scoring in the reference park is {R.runs_per_game:.2f} runs per game against {9.66:.2f} in real 2019, {abs(100 * (R.runs_per_game / 9.66 - 1)):.1f}% high, which is expected because the lineups are each club's best nine regulars and bullpens are not modeled. "
 f"(b) Across the 30 real parks, the model's run factor correlates with Lahman's 2019 park factor at r = {s2['corr']:.2f}; the home-run factor at r = {s2['corr_hr']:.2f}. The model sees only fence distances, elevation and Fenway's wall, so this is a useful but partial agreement. "
 f"<b>In sample.</b> Hitter-level AVG and SLG agree with 2019 at r = {s2['val'][1]:.3f} and {s2['val'][2]:.3f} because s<sub>i</sub> and m<sub>i</sub> were fitted to them; this checks the calibration, not the model's predictive power."))
s.append(fig("fig5_validation.png", "Figure 10. Left: model park run factors against Lahman park factors for 30 parks. Right: simulated and real scoring.", 6.2))
s.append(P("7. Limitations", H1))
for t in ("<b>No Statcast.</b> Batted-ball distributions are assumed (normal exit velocity, launch angle and spray angle), then calibrated to real rates. The real joint distribution would change which hitters gain most. Re-running the pipeline on Statcast batted balls is the highest-value extension.",
          "<b>Park inputs.</b> Real-park fence distances are approximate, wall heights are uniform apart from Fenway, and weather, wind and roofs are absent, so real-park factors are only partly explained (r about 0.57).",
          "<b>Hit probabilities are stylized.</b> The fielding model is a smooth function of batted-ball type, fence distance and outfield depth, not tracked player positioning. The foul-territory and infield-speed multipliers are design assumptions, not measured quantities; 2.2x foul territory is deliberately extreme, at or beyond the largest current parks.",
          "<b>No behavioral response.</b> Hitters would change approach and pitchers would change location in a real Emerald Park. Teams would also build rosters around it. The estimates are first-order effects.",
          "<b>Simplified baseball.</b> Lineups face league-average pitching, bullpens and platoons are omitted, and baserunning follows fixed advance probabilities."):
    s.append(P("- " + t))
s.append(P("8. Conclusion", H1))
s.append(P(f"Inside this model, a park can be batter-friendly and pitcher-friendly at the same time without changing how many runs are scored. Short pull-side alleys convert power into {ab(E.HR_per_game, R.HR_per_game)} more home runs per game; deep center field, large foul territory and a slow grass infield remove {abs(IMP['Hits'][0]):.1f}% of hits and add {S['f_hr'] and (E.foul_outs_per_game - R.foul_outs_per_game):.2f} caught-foul outs per game. "
 "The price is a different kind of baseball: more true-outcome plate appearances, a premium on power and on pitchers who avoid home runs, and little change in the final score."))
s.append(PageBreak()); s.append(P("Appendix A. The 30 real parks and Emerald Park", H1))
rows = [["Park", "LF", "LCF", "CF", "RCF", "RF", "Elev", "Lahman BPF", "Model HR", "Model BABIP", "Model runs"]]
for r in pf.itertuples(): rows.append([r.park_code, f"{r.lf_line:.0f}", f"{r.lf_alley:.0f}", f"{r.cf:.0f}", f"{r.rf_alley:.0f}", f"{r.rf_line:.0f}", f"{r.elevation_ft:.0f}", "" if pd.isna(r.lahman_BPF_2019) else f"{r.lahman_BPF_2019:.0f}", f"{r.model_HR_PA_factor:.0f}", f"{r.model_BABIP_factor:.0f}", f"{r.model_runs_factor:.0f}"])
s += tab(rows, [.8 * inch] + [.45 * inch] * 5 + [.5 * inch, .75 * inch, .65 * inch, .8 * inch, .75 * inch], 7.5)
s.append(P("Distances in feet are approximate public figures. REF is the 30-park average; EMERALD is the hypothetical park. Factors are per plate appearance from the model; 100 is the reference park.", CAP))
s.append(P("Appendix B. Reproducibility", H1))
s.append(P("Run src/calib.py (real data and calibration), src/build_all.py (park factors, design grids, player and game simulations), src/figures.py (figures and pitcher projection), src/build_dash.py (dashboard) and src/paper.py (this PDF). All random seeds are fixed. Data source: Lahman Baseball Databank 2021.2 (CC BY-SA 3.0), distributed with the Python package lahman."))
doc.build(s, onFirstPage=foot, onLaterPages=foot); print("pdf ok")
