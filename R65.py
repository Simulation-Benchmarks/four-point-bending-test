"""Eurocode 2 design computation — fib TG 2.4.3 benchmark, specimen R65.

Four-point bending beam of Rüsch & Rehm (1963), answered **without FEM** by a
classic design computation to DIN EN 1992-1-1:2011-01.

* **Q6** — maximum design value of the point loads ``P``, beam as built
  (``case: with_stirrups``).
* **Q7** — the same with the stirrups removed from the shear spans
  (``case: without_stirrups``).

The specimen and the variant of the computation are described entirely by a
parameter file; everything the Eurocode fixes is a constant in this module.
``compute_P`` is the single entry point::

    python R65.py [params.yaml]

Built on `structuralcodes <https://github.com/fib-international/structuralcodes>`_,
*fib*'s own EC2 library.  Clause numbers refer to DIN EN 1992-1-1:2011-01.
Units are N and mm internally; results are returned in kN and kNm.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import yaml
from shapely import Polygon
from structuralcodes.codes.ec2_2004 import shear
from structuralcodes.geometry import SurfaceGeometry, add_reinforcement
from structuralcodes.materials.concrete import ConcreteEC2_2004
from structuralcodes.materials.reinforcement import ReinforcementEC2_2004
from structuralcodes.sections import GenericSection

# unit inversion (alternative use pint)
KN, KNM = 1e-3, 1e-6            # N, Nmm -> kN, kNm

# =====================================================================
# Constants of DIN EN 1992-1-1:2011-01 and EN 1990.
#
# These are properties of the code, not of the specimen, so they do not
# belong in the parameter file.  The nationally determined parameters are
# the CEN recommended values: the German National Annex is a separate
# document and is not available in this repository.
# =====================================================================
GAMMA_C = 1.5           # Table 2.1N, concrete
GAMMA_S = 1.15          # Table 2.1N, reinforcement
GAMMA_G = 1.35          # EN 1990 Table A1.2(B), permanent action
GAMMA_Q = 1.5           # EN 1990 Table A1.2(B), variable action
ALPHA_CC = 1.0          # 3.1.6(1)P, NDP, EN recommended value
ES = 200000.0           # 3.2.7(4), modulus of elasticity of reinforcement [MPa]
K1 = 0.15               # 6.2.2(1), NDP, EN recommended value
DELTA_FCK = 8.0         # Table 3.1, f_ck = f_cm - 8 [MPa]
Z_FACTOR = 0.9          # 6.2.3(1), inner lever arm z = 0.9 d

# ASSUMPTION, outside EC2.  EC2 gives no mean -> characteristic relation for
# reinforcement (the 0.7 of Table 3.1 is specific to the concrete tensile
# strength, CoV ~ 18 %, and must not be transferred to rebar at CoV ~ 5 %).
# The code-calibration bias factor is used instead.  This is the only material
# value in the whole computation not traceable to a document in this repository.
BIAS_STEEL = 1.10

# theta within [21.8, 45] deg, from 1 <= cot theta <= 2.5, eq. (6.7N).
# Both VRds and VRdmax reject angles outside this window.
THETA_GRID = [21.8 + i * (45.0 - 21.8) / 400 for i in range(401)]

DEFAULT_PARAMS = Path(__file__).with_name("params.yaml")


def load_params(path=DEFAULT_PARAMS):
    """Read a benchmark parameter file into a plain dict."""
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def make_materials(p):
    """Return (concrete, steel) at the safety level requested by ``p``.

    ``level: design`` applies gamma_C = 1.5 / gamma_S = 1.15 to strengths
    converted from the measured means; ``level: mean`` feeds the measured means
    with gamma_M = 1.0, which is what gets compared against the experiment.
    """
    level = p["level"]
    if level == "design":
        fck = p["fcm"] - DELTA_FCK              # Table 3.1
        fyk = p["fym"] / BIAS_STEEL             # ASSUMPTION - not EC2
        ftk = p["fum"] / BIAS_STEEL             # ASSUMPTION - not EC2
        gamma_c, gamma_s = GAMMA_C, GAMMA_S
    elif level == "mean":
        fck, fyk, ftk = p["fcm"], p["fym"], p["fum"]
        gamma_c, gamma_s = 1.0, 1.0
    else:
        raise ValueError(f"unknown level {level!r}, expected 'design' or 'mean'")

    concrete = ConcreteEC2_2004(
        fck=fck, fctm=p["fctm"], Ecm=p["ecm"], gamma_c=gamma_c,
        alpha_cc=ALPHA_CC,
        constitutive_law="parabolarectangle",   # 3.1.7(1), eq. (3.17)/(3.18)
    )
    # NOTE epsuk is assumed, see params.yaml. It is not reached by this section,
    # but it does set the slope of the inclined branch 3.2.7(2)a.
    steel = ReinforcementEC2_2004(
        fyk=fyk, Es=ES, ftk=ftk, epsuk=p["epsuk"], gamma_s=gamma_s,
        constitutive_law=p["branch"],
    )
    return concrete, steel


def bending_resistance(p, concrete, steel):
    """M_R [kNm] of the R65 cross-section by strain compatibility, 6.1(2)P.

    No lever-arm assumption is made: the neutral axis follows from equilibrium
    of the parabola-rectangle concrete block against both reinforcement layers.
    """
    b, h, d, d2 = p["b"], p["h"], p["d"], p["d2"]
    # define beam cross-section geometry
    poly = Polygon([(-b / 2, -h / 2), (b / 2, -h / 2), (b / 2, h / 2), (-b / 2, h / 2)])
    geo = SurfaceGeometry(poly=poly, material=concrete)
    z_bot, z_top = -h / 2 + (h - d), h / 2 - d2
    # add bending reinforcement bars, two per layer
    for y in (-b / 2 + 50.0, b / 2 - 50.0):
        geo = add_reinforcement(geo, (y, z_bot), p["phi_bot"], steel)
        geo = add_reinforcement(geo, (y, z_top), p["phi_top"], steel)
    res = GenericSection(geo).section_calculator.calculate_bending_strength(theta=0, n=0)
    return abs(res.m_y) * KNM


def self_weight(p):
    """Self weight of the beam: (g_k [kN/m], M_g [kNm], V_g [kN]).

    Simply supported over ``span`` with an ``overhang`` at each end, so the
    overhangs relieve the midspan moment and the support shear.
    """
    g_k = p["gamma_concrete"] * 1e-9 * p["b"] * p["h"] * 1e3        # kN/m
    span, overhang = p["span"], p["overhang"]
    reaction = g_k * (span + 2.0 * overhang) / 2e3                  # kN
    M_g = reaction * (span / 2e3) - g_k * ((span / 2 + overhang) / 1e3) ** 2 / 2
    V_g = reaction - g_k * overhang / 1e3
    return g_k, M_g, V_g


def P_from_moment(p, M_R, gamma_g):
    """P [kN] from  M_Ed = gamma_G M_g + P a_shear <= M_R."""
    _, M_g, _ = self_weight(p)
    return (M_R - gamma_g * M_g) / (p["a_shear"] / 1e3)


def P_from_shear(p, V_R, gamma_g, beta=1.0):
    """P [kN] from  V_Ed = gamma_G V_g + beta P <= V_R.

    ``beta`` < 1 applies the 6.2.2(6) reduction of the contribution of a point
    load applied within 2d of the support.
    """
    _, _, V_g = self_weight(p)
    return (V_R - gamma_g * V_g) / beta


def shear_resistance(p, concrete, steel, theta_deg=None):
    """V_R of a shear span WITH stirrups, 6.2.3 (variable strut inclination).

    Returns (V_R, V_R,s, V_R,max, theta) in kN and degrees.

    VRds (eq. 6.8, stirrups yield) rises with cot theta, VRdmax (eq. 6.9,
    struts crush) falls; the resistance is the smaller of the two and is
    therefore largest where the two curves cross.  theta is searched over
    THETA_GRID, i.e. the eq. (6.7N) window, unless an angle is passed in.

    The longitudinal steel does NOT enter: the truss is a mechanical model and
    A_sl is its chord, checked separately by eq. (6.18).
    """
    z = Z_FACTOR * p["d"]
    ac = p["b"] * p["h"]

    def at(theta):
        v_s = shear.VRds(Asw=p["asw"], s=p["s_w"], z=z, theta=theta,
                         fyk=steel.fyk, gamma_s=steel.gamma_s)           # stirrups yield
        v_max = shear.VRdmax(bw=p["b"], z=z, fck=concrete.fck, theta=theta,
                             NEd=0.0, Ac=ac, fcd=concrete.fcd())         # struts crush
        return min(v_s, v_max) * KN, v_s * KN, v_max * KN

    # get optimal theta within the range allowed by EC2
    theta = theta_deg if theta_deg is not None else max(THETA_GRID, key=lambda t: at(t)[0])
    return (*at(theta), theta)


def shear_resistance_no_stirrups(p, concrete):
    """V_R,c WITHOUT shear reinforcement [kN], 6.2.2(1) eq. (6.2).

    Purely empirical, so the longitudinal ratio rho_l appears explicitly — it
    stands in for dowel action, crack width and compression-zone depth.

    Note C_Rd,c = 0.18/gamma_C: the 0.18 is itself a characteristic-level
    constant, so evaluating this at gamma_C = 1 gives a mean-material /
    characteristic-model hybrid, not a true mean resistance R(x_m).
    """
    asl = p["n_bot"] * math.pi / 4 * p["phi_bot"] ** 2
    return shear.VRdc(fck=concrete.fck, d=p["d"], Asl=asl, bw=p["b"], NEd=0.0,
                      Ac=p["b"] * p["h"], fcd=concrete.fcd(), k1=K1,
                      gamma_c=concrete.gamma_c) * KN


def compute_P(p):
    """Maximum point load P for one parameter set. Main entry point.

    Returns a dict of the governing load and everything behind it.  At
    ``level: design`` the actions are factored (gamma_G = 1.35) and P is a
    design value; at ``level: mean`` the actions are unfactored and P is the
    calculated mean resistance, directly comparable with the experiment.
    """
    concrete, steel = make_materials(p)
    gamma_g = GAMMA_G if p["level"] == "design" else 1.0
    g_k, M_g, V_g = self_weight(p)
    d, b = p["d"], p["b"]

    res = {
        "level": p["level"], "branch": p["branch"], "case": p["case"],
        "fck": concrete.fck, "fcd": concrete.fcd(),
        "fyk": steel.fyk, "fyd": steel.fyd(),
        "gamma_g": gamma_g, "g_k": g_k, "M_g": M_g, "V_g": V_g,
        "rho_l": p["n_bot"] * math.pi / 4 * p["phi_bot"] ** 2 / (b * d),
        "a_over_d": p["a_shear"] / d,
    }

    # bending, 6.1
    res["M_R"] = bending_resistance(p, concrete, steel)
    res["P_bending"] = P_from_moment(p, res["M_R"], gamma_g)

    # shear, 6.2.2 or 6.2.3 depending on the case
    if p["case"] == "with_stirrups":
        V_R, V_Rs, V_Rmax, theta = shear_resistance(p, concrete, steel)
        res.update(V_R=V_R, V_Rs=V_Rs, V_Rmax=V_Rmax, theta=theta,
                   cot_theta=1 / math.tan(math.radians(theta)))
        res["P_shear"] = P_from_shear(p, V_R, gamma_g)
    elif p["case"] == "without_stirrups":
        V_R = shear_resistance_no_stirrups(p, concrete)
        # 6.2.2(6): a point load closer than 2d to the support may have its
        # contribution reduced by beta = a_v/2d.  a_v is taken as the
        # support-to-load centre distance, which is conservative — the clear
        # distance between the bearing plate edges is shorter.
        beta = min(p["a_shear"] / (2 * d), 1.0)
        res.update(V_R=V_R, beta=beta,
                   V_Ed_limit=shear.VEdmax_unreinf(bw=b, d=d, fck=concrete.fck,
                                                   fcd=concrete.fcd()) * KN)
        res["P_shear"] = P_from_shear(p, V_R, gamma_g)
        res["P_shear_av"] = P_from_shear(p, V_R, gamma_g, beta=beta)
    else:
        raise ValueError(f"unknown case {p['case']!r}, expected 'with_stirrups' "
                         "or 'without_stirrups'")

    # governing load
    res["P"] = min(res["P_bending"], res["P_shear"])
    res["governs"] = "bending" if res["P_bending"] < res["P_shear"] else "shear"
    if p["level"] == "design":
        res["P_k"] = res["P"] / GAMMA_Q
    # comparing against the experiment is only meaningful at mean level: a
    # design value carries the safety margin the experiment does not know about
    if p.get("r_exp") and p["level"] == "mean":
        res["r_exp"] = p["r_exp"]
        res["r_exp_over_calc"] = p["r_exp"] / res["P"]
    return res


def format_result(res):
    """Human-readable report of one compute_P result."""
    L = [f"level = {res['level']}   branch = {res['branch']}   case = {res['case']}",
         f"  materials      f_ck = {res['fck']:6.2f} MPa   f_cd = {res['fcd']:6.3f} MPa"
         f"   f_yk = {res['fyk']:6.1f} MPa   f_yd = {res['fyd']:6.1f} MPa",
         f"  self weight    g_k  = {res['g_k']:.4f} kN/m   M_g = {res['M_g']:.3f} kNm"
         f"   V_g = {res['V_g']:.3f} kN   (gamma_G = {res['gamma_g']})",
         f"  6.1            M_R  = {res['M_R']:8.2f} kNm  ->  P = {res['P_bending']:7.1f} kN"]
    if res["case"] == "with_stirrups":
        L.append(f"  6.2.3          V_R  = {res['V_R']:8.2f} kN   ->  P = {res['P_shear']:7.1f} kN"
                 f"   (theta = {res['theta']:.2f} deg, cot = {res['cot_theta']:.3f},"
                 f" V_R,s = {res['V_Rs']:.1f}, V_R,max = {res['V_Rmax']:.1f} kN)")
    else:
        L.append(f"  6.2.2          V_R,c= {res['V_R']:8.2f} kN   ->  P = {res['P_shear']:7.1f} kN"
                 f"   (rho_l = {res['rho_l']:.5f}, eq. 6.5 limit {res['V_Ed_limit']:.0f} kN)")
        L.append(f"  6.2.2(6)       a_v < 2d allowance, beta = {res['beta']:.4f}"
                 f"  ->  P = {res['P_shear_av']:7.1f} kN")
    L.append(f"  ==>  P = {res['P']:.1f} kN   ({res['governs']} governs)")
    if "P_k" in res:
        L.append(f"       P_k = P / {GAMMA_Q} = {res['P_k']:.1f} kN")
    if "r_exp" in res:
        L.append(f"       R_exp = {res['r_exp']:.1f} kN  ->  R_exp/R_calc = {res['r_exp_over_calc']:.3f}")
    return "\n".join(L)


if __name__ == "__main__":
    params_file = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PARAMS
    params = load_params(params_file)
    result = compute_P(params)
    print(f"fib TG 2.4.3 / R65 — DIN EN 1992-1-1:2011-01   [{params_file}]\n")
    print(format_result(result))
