# Emerald Park: a ballpark that is both pitcher-friendly and batter-friendly

A baseball analytics project built on **real 2019 MLB data**. It asks: *can one field help hitters and pitchers at the same time, and what would it do to the league?* I design a hypothetical park, **Emerald Park**, simulate batted balls and full seasons in it, and compare it with a league-average park.

**Open `emerald_park_dashboard.html` in any browser** (no install, works offline). The paper is `emerald_park_research_paper.pdf`.

## Headline results (model estimates, 5 simulated seasons x 2,430 games per park)

| Per game (both teams) | League-average park | Emerald Park | Change |
|---|---|---|---|
| Home runs | 3.16 | 3.56 | +12.9% |
| Hits | 18.60 | 18.01 | -3.2% |
| Caught-foul outs | 0.42 | 0.93 | +120.9% |
| Runs | 9.96 | 10.02 | +0.6% (neutral) |

Per plate appearance, Emerald Park's factors (100 = league-average park): home runs **114**, isolated power **110**, BABIP **95**, run scoring **100**.

**What "both-friendly" means here.** (1) Batter-friendly: home-run factor of at least 108. (2) Pitcher-friendly: BABIP factor of at most 97 and more caught-foul outs. (3) Run-neutral: run scoring within 2% of a league-average park. Emerald Park meets all three. Among the 30 real parks, none has a home-run factor above 100 and a BABIP factor below 100 together.

**An honest caveat.** Because scoring stays neutral, the park redistributes value rather than lowering everyone's ERA: the mean ERA change across 130 2019 pitchers is -0.01, but it correlates with home runs per nine (r = 0.83). Pitchers who avoid home runs gain; home-run-prone pitchers lose.

## The park

| Feature | Emerald Park | League-average park |
|---|---|---|
| Left / right lines | 310 ft | 332 / 328 ft |
| Alleys | 350 ft | 377 ft |
| Center field | 430 ft | 403 ft |
| Foul territory | 2.2x | 1.0x |
| Infield speed | 0.86x (slow, lush grass) | 1.0x |

Short pull-side alleys turn power into home runs (batter-friendly). Deep center field, huge foul territory and a slow infield take away hits and add foul-ball outs (pitcher-friendly).

## Dashboard features

- Why it is both: KPI tiles, effect chart, a quadrant of all 30 real parks plus Emerald Park, and the park spec.
- **Swing simulator:** pick any of 207 real 2019 hitters from the dropdown, swing once, take 25 swings, or simulate 600 plate appearances. Every swing is judged in both parks (same exit velocity, launch angle and spray angle), so you see exactly which balls turn into home runs.
- League impact: simulated league table and the biggest home-run gainers.
- Green field theme throughout.

## Files

```
emerald_park_dashboard.html       interactive dashboard + swing simulator (self-contained)
emerald_park_research_paper.pdf   11-page paper with models, equations and 10 figures
data/
  players_2019_calibrated.csv     207 real hitters: 2019 line + fitted power (s) and contact (m) parameters
  parks_mlb_2019_and_emerald.csv  30 real parks + reference + Emerald: dimensions, Lahman park factor, model factors
  sim_player_park_results.csv     per-hitter results in the reference park and in Emerald Park
  sim_league_seasons.csv          5 simulated seasons per park
  sim_game_log_season1.csv        game-by-game log (4,860 games)
  sim_batted_balls_sample.csv     sample batted balls (exit velo, launch angle, spray angle, carry, HR flag)
  pitchers_2019_emerald_projection.csv  130 pitchers: real 2019 line and projected Emerald Park line
  design_space_*.csv              park-design sweeps (alley x center field; foul territory x infield speed)
  dashboard_data.json, calibration_constants.json, league_impact_pct.json
  raw/                            Lahman 2019 tables used (Batting, People, Teams, Pitching)
figures/                          10 green figures used in the paper
src/                              full pipeline (see below)
```

## How the model works

1. **Real rates:** each hitter's 2019 strikeout, walk and HBP rates are used as-is.
2. **Batted balls:** exit velocity, launch angle and spray angle are drawn from distributions; each hitter's power parameter is fitted so his simulated home-run rate equals his real 2019 rate, and a contact multiplier matches his real BABIP.
3. **Flight and fence:** carry = 0.68 v^2 sin(2 LA) / g x elevation term; a home run needs the carry to clear the fence at that spray angle.
4. **Hits and outs:** hit probability depends on ground ball / line drive / fly ball, how close the ball lands to the wall, outfield size, foul territory and infield speed.
5. **Games:** a base-state game simulator plays each club's real 2019 lineup.

## What is real and what is modeled

- **Real:** 2019 batting and pitching lines, team run totals and park factors (Lahman Baseball Databank 2021.2; 2019 is the last full season in that release).
- **Modeled:** exit velocity, launch angle, spray angle (no Statcast access in the build environment), fielding and hit probabilities, base running.
- **Approximate:** the 30 real parks' fence distances are approximate public figures; please verify before citing. Walls are 8 ft except Fenway's 37 ft left-field wall.

## Validation

- Simulated reference-park scoring: 9.96 runs per game vs. 9.66 real in 2019 (3.1% high; best-nine lineups, no bullpens).
- Model park run factors vs. Lahman 2019 park factors across 30 parks: r = 0.57 (home-run factor: r = 0.46). Out of sample, and only partly explained because the model sees fence distances and elevation only.
- Hitter-level AVG and SLG match 2019 (r = 1.00, 0.98) because the parameters were fitted to them. That checks the calibration, not predictive power.

## Limitations

No Statcast batted balls, approximate park inputs, no wind/weather/roof, stylized fielding, league-average pitching and no bullpens, and no behavioral response from hitters, pitchers or roster builders. Treat percentages as model estimates, not forecasts.

## Reproduce

```bash
pip install numpy pandas matplotlib reportlab pillow
npm install chart.js@4.4.1        # only needed to rebuild the dashboard (it is inlined)
python src/calib.py               # real data + calibration
python src/build_all.py           # park factors, design sweeps, player + game simulations
python src/figures.py             # figures + pitcher projections
python src/build_dash.py          # dashboard (expects chart.js at /tmp/node_modules; edit the path if needed)
python src/paper.py               # research paper PDF
```

All random seeds are fixed. To update to newer seasons, point `src/calib.py` at newer Lahman CSVs (or Statcast batted-ball data) and change `YEAR`.

## Credits

Data: Lahman Baseball Databank (CC BY-SA 3.0). Author: Nikhil Chandrashaker.
