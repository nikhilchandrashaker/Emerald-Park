import sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, "src")
from model import *
st = pickle.load(open("data/_state.pkl", "rb")); K, ref, parks = st["K"], st["ref"], st["parks"]
pl = pd.read_csv("data/players_2019_calibrated.csv")
players = pl.to_dict("records")
N = 40000; draws = [make_draws(N, 1000 + i) for i in range(len(players))]
W = pl.PA.values / pl.PA.sum()
WTS = dict(BB=.60, HBP=.62, B1=.74, B2=1.04, B3=1.31, HR=1.67)
def league_vec(park, k=10000):
    return sum(w * pa_probs(p, draws[i], park, ref, K, k) for i, (p, w) in enumerate(zip(players, W)))
def stats(v):
    k, bb, hb, b1, b2, b3, hr, ofb, ogb, fo = v
    ab = 1 - bb - hb; h = b1 + b2 + b3 + hr
    return dict(HR_PA=hr, AVG=h/ab, OBP=(h+bb+hb)/1, SLG=(b1+2*b2+3*b3+4*hr)/ab, ISO=(b2+2*b3+3*hr)/ab,
                BABIP=(b1+b2+b3)/(ab-k-hr), XBH_PA=b2+b3+hr, K_PA=k, FOUL_OUT_PA=fo, H_PA=h,
                RAO=WTS["BB"]*bb+WTS["HBP"]*hb+WTS["B1"]*b1+WTS["B2"]*b2+WTS["B3"]*b3+WTS["HR"]*hr)
def factors(park, k=10000, rv=None):
    rv = rv if rv is not None else stats(league_vec(ref, k)); s = stats(league_vec(park, k))
    f = {m: 100 * s[m] / rv[m] for m in s}
    return s, f
def emerald(L=305, A=400, CF=425, foul=1.8, infield=0.92, elev=None):
    return Park("Emerald Park", [L, A, CF, A, L], ref.elev if elev is None else elev, foul=foul, infield=infield)
if __name__ == "__main__":
    rv = stats(league_vec(ref))
    print("REF", {k: round(v, 4) for k, v in rv.items()})
    for L in (305, 315, 325):
        for A in (385, 400, 415):
            s, f = factors(emerald(L, A), rv=rv)
            print(L, A, {k: round(f[k]) for k in ("HR_PA","AVG","BABIP","SLG","ISO","RAO")})
