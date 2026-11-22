"""Emerald Park batted-ball model (Python reference implementation; the dashboard re-implements the same equations in JS)."""
import numpy as np
G = 32.174
ANG = np.array([-45, -22.5, 0, 22.5, 45.0])
EV_MU, EV_SD, LA_MU, LA_SD, PHI_SD = 88.0, 14.0, 12.0, 25.0, 23.0
Q_FOUL0 = 0.008
CAT = ["K", "BB", "HBP", "1B", "2B", "3B", "HR", "OUT_FB", "OUT_GB", "FOUL_OUT"]

class Park:
    def __init__(s, name, dims, elev=0, heights=None, foul=1.0, infield=1.0):
        s.name, s.dims, s.elev, s.foul, s.infield = name, np.array(dims, float), elev, foul, infield
        s.heights = np.array(heights if heights is not None else [8]*5, float)
        s.carry = 1 + 1.2e-5 * elev
    def fence(s, phi): return np.interp(phi, ANG, s.dims), np.interp(phi, ANG, s.heights)

def make_draws(n, seed):
    r = np.random.default_rng(seed)
    return dict(la=r.standard_normal(n), ev=r.standard_normal(n), phi=r.standard_normal(n), side=r.random(n))

def pull_of(s): return float(np.clip(10 + 0.35 * s, 4, 18))

def batted(draws, s, bats, park, ref, K, k=None):
    n = len(draws["la"]); sl = slice(0, k or n)
    la = LA_MU + LA_SD * draws["la"][sl]
    ev = np.clip(EV_MU + s + EV_SD * draws["ev"][sl] - 0.012 * (la - 17) ** 2, 40, 122)
    u = draws["side"][sl]
    side = {"R": np.ones_like(u), "L": -np.ones_like(u), "B": np.where(u < 0.65, -1.0, 1.0)}[bats]
    phi = -side * pull_of(s) + PHI_SD * draws["phi"][sl]
    phi = np.clip(np.where(np.abs(phi) > 45, np.sign(phi) * (90 - np.abs(phi)), phi), -45, 45)
    d = np.where(la >= 8, 0.68 * (ev * 1.4667) ** 2 * np.sin(np.radians(2 * la)) / G * park.carry, 0.0)
    D, H = park.fence(phi); Dr, _ = ref.fence(phi)
    hr = (la >= 17) & (la <= 52) & (d >= D + 1.4 * H)
    gb, ld = la < 10, (la >= 10) & (la < 25)
    near = (d >= D - 45) & ~gb
    p_gb = np.clip(0.17 + 0.005 * (ev - 80), .05, .6) * park.infield
    p_ld = np.where(near, .85, np.clip(.62 + .008 * (ev - 90), .15, .9))
    p_fb = np.where(near, np.minimum(.15 + .6 * (d - (D - 45)) / 45, .9), np.where(la > 50, .02, .09 * (D / Dr) ** 1.5))
    p = np.clip(K["c"] * np.where(gb, p_gb, np.where(ld, p_ld, p_fb)), 0, .95)
    t3 = np.clip(.03 + .004 * (D - 375), .01, .3)
    p2 = K["a2"] * np.where(near, .60, np.where(gb, .045, .16)); p3 = K["a3"] * np.where(near, t3, np.where(gb, .003, .02))
    return dict(ev=ev, la=la, phi=phi, d=d, hr=hr, gb=gb, p_hit=np.where(hr, 0, p), p2=p2, p3=p3)

def bip_probs(b):
    n = len(b["ev"]); ph = b["p_hit"]
    h2, h3 = ph * b["p2"], ph * b["p3"]; h1 = ph - h2 - h3
    out = 1 - ph - b["hr"]
    return np.array([h1.sum(), h2.sum(), h3.sum(), b["hr"].sum(), (out * ~b["gb"]).sum(), (out * b["gb"]).sum()]) / n

def pa_probs(pl, draws, park, ref, K, k=None):
    bp = bip_probs(batted(draws, pl["s"], pl["bats"], park, ref, dict(K, c=K["c"] * pl.get("m", 1.0)), k))
    kk, bb, hb = pl["k_rate"], pl["bb_rate"], pl["hbp_rate"]; inplay = 1 - kk - bb - hb
    q = Q_FOUL0 * park.foul
    return np.array([kk, bb, hb, *(inplay * (1 - q) * bp), inplay * q])
