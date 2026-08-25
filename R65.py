# %% [markdown]
# # Eurocode 2 design computation — fib TG 2.4.3 benchmark, specimen R65
#
# Four-point bending beam of Rüsch & Rehm (1963), answered **without FEM** by a
# classic design computation to DIN EN 1992-1-1:2011-01.
#
# * **Q6** — maximum design value of the point loads `P`, beam as built (with stirrups).
# * **Q7** — the same, with the stirrups removed from the shear spans.
#
# Built on [`structuralcodes`](https://github.com/fib-international/structuralcodes),
# *fib*'s own EC2 library. Clause numbers refer to DIN EN 1992-1-1:2011-01.
# Units are N and mm internally; results are printed in kN and kNm.
#
# Run as a script (`python R65.py`) or cell-by-cell in VS Code / PyCharm / Spyder.

# %%
import math

from shapely import Polygon
from structuralcodes.codes.ec2_2004 import shear
from structuralcodes.geometry import SurfaceGeometry, add_reinforcement
from structuralcodes.materials.concrete import ConcreteEC2_2004
from structuralcodes.materials.reinforcement import ReinforcementEC2_2004
from structuralcodes.sections import GenericSection

MM2, KN, KNM = 1.0, 1e-3, 1e-6  # N,mm -> kN, kNm

# %% [markdown]
# ## 1. Specimen data
#
# From the appendix of `2026-07_fib_TG243_NLFEA_Example.pdf`.

# %%
# geometry [mm]
B, H, D, D2 = 300.0, 625.0, 587.0, 38.5   # width, depth, eff. depth, top-steel depth
SPAN, OVERHANG, A_SHEAR = 4000.0, 255.0, 1000.0   # support spacing, overhang, shear span

# reinforcement
PHI_BOT, N_BOT = 26.0, 2      # 2 Ø26 = 1062 mm^2
PHI_TOP, N_TOP = 10.0, 2      # 2 Ø10 =  157 mm^2
ASW, S_W = 157.0, 120.0       # Ø10 two-legged stirrups @ 120 mm

# measured mean material properties [MPa]
FCM, FCTM, ECM = 16.71, 1.30, 25660.0
FYM, FUM = 401.0, 596.0
EPSUK = 0.10                  # assumed; A_10 = 23.1 % is elongation after fracture, not eps_uk

# partial factors, Table 2.1N
GAMMA_C, GAMMA_S, GAMMA_G, GAMMA_Q = 1.5, 1.15, 1.35, 1.5
ALPHA_CC = 1.0                # 3.1.6(1)P, EN recommended value

R_EXP = 259.2                 # measured failure load per point load [kN]

# %% [markdown]
# ## 2. Mean → characteristic
#
# **Concrete — source-backed.** Table 3.1 gives the inverse relations directly:
# `f_ck = f_cm − 8` and `f_ctk;0,05 = 0.7·f_ctm`. Self-consistency check below
# confirms the fib data sheet was generated with these same relations.
#
# **Steel — assumption, outside EC2.** EC2 has no mean→characteristic relation for
# reinforcement (Table 3.1's 0.7 factor is concrete-tensile-specific, CoV ≈ 18 %).
# The code-calibration bias factor 1.1 is used. This is the only material value in
# the whole computation not traceable to a document in this repo.

# %%
FCK = FCM - 8.0          # Table 3.1
FYK = FYM / 1.10         # ASSUMPTION - not EC2
FTK = FUM / 1.10         # ASSUMPTION - not EC2

print(f"Table 3.1   f_ck       = f_cm - 8   = {FCM} - 8      = {FCK:.2f} MPa")
print(f"Table 3.1   f_ctk;0,05 = 0.7 f_ctm  = 0.7 * {FCTM}   = {0.7 * FCTM:.3f} MPa")
print(f"ASSUMPTION  f_yk       = f_ym / 1.1 = {FYM} / 1.1  = {FYK:.1f} MPa")
print()
print("self-consistency of the given mean values with Table 3.1:")
print(f"   22*(f_cm/10)^0.3     = {22e3 * (FCM / 10) ** 0.3 / 1e3:7.2f} GPa  vs given E_cm  = {ECM / 1e3:.2f} GPa")
print(f"   0.30*f_ck^(2/3)      = {0.30 * FCK ** (2 / 3):7.2f} MPa  vs given f_ctm = {FCTM:.2f} MPa")
print()
print(f"NOTE f_ck = {FCK:.2f} MPa is below C12/15, the lowest row of Table 3.1.")
print("     EC2 has no structural minimum class (Table E.1N is durability only),")
print("     so the value is used as derived and NOT rounded up.")

# %% [markdown]
# ## 3. Materials
#
# One factory serves both safety levels: `"design"` applies γ_C = 1.5 / γ_S = 1.15 to
# the characteristic strengths, `"mean"` sets both to 1.0 and feeds the measured means.
# The mean level is what gets compared against the experiment.
#
# `elasticperfectlyplastic` is the horizontal top branch of 3.2.7(2)b;
# `elasticplastic` is the inclined branch of 3.2.7(2)a, which carries strain hardening.

# %%
def make_materials(level="design", branch="elasticperfectlyplastic"):
    """Return (concrete, steel) at the requested safety level."""
    if level == "design":
        fck, fyk, ftk, g_c, g_s = FCK, FYK, FTK, GAMMA_C, GAMMA_S
    elif level == "mean":
        fck, fyk, ftk, g_c, g_s = FCM, FYM, FUM, 1.0, 1.0
    else:
        raise ValueError(level)
    concrete = ConcreteEC2_2004(
        fck=fck, fctm=FCTM, Ecm=ECM, gamma_c=g_c, alpha_cc=ALPHA_CC,
        constitutive_law="parabolarectangle",   # 3.1.7(1), eq. (3.17)/(3.18)
    )
    steel = ReinforcementEC2_2004(
        fyk=fyk, Es=200000.0, ftk=ftk, epsuk=EPSUK, gamma_s=g_s,
        constitutive_law=branch,
    )
    return concrete, steel


c_d, s_d = make_materials("design")
print(f"design level:  f_cd = {c_d.fcd():.3f} MPa   f_yd = {s_d.fyd():.1f} MPa")
c_m, s_m = make_materials("mean")
print(f"mean level:    f_c  = {c_m.fcd():.3f} MPa   f_y  = {s_m.fyd():.1f} MPa")

# %% [markdown]
# ## 4. Bending resistance — 6.1 with the stress-strain law of 3.1.7

# %%
def bending_resistance(concrete, steel):
    """M_Rd [kNm] of the R65 cross-section by strain compatibility, 6.1(2)P."""
    poly = Polygon([(-B / 2, -H / 2), (B / 2, -H / 2), (B / 2, H / 2), (-B / 2, H / 2)])
    geo = SurfaceGeometry(poly=poly, material=concrete)
    z_bot, z_top = -H / 2 + (H - D), H / 2 - D2
    for y in (-B / 2 + 50.0, B / 2 - 50.0):          # two bars per layer
        geo = add_reinforcement(geo, (y, z_bot), PHI_BOT, steel)
        geo = add_reinforcement(geo, (y, z_top), PHI_TOP, steel)
    res = GenericSection(geo).section_calculator.calculate_bending_strength(theta=0, n=0)
    return abs(res.m_y) * KNM


M_RD = bending_resistance(c_d, s_d)
print(f"6.1 + 3.1.7(1)   M_Rd = {M_RD:.2f} kNm   (parabola-rectangle, design level)")

# %% [markdown]
# ## 5. Statics of the four-point bending beam
#
# Simply supported, span 4.00 m, two point loads `P` at 1.00 m from each support,
# 0.255 m overhangs. Self weight is a permanent action (γ_G = 1.35); `P` is entered
# directly as a **design** action, as fib question 6 asks for its design value.

# %%
G_K = 25.0e-9 * B * H * 1e3        # kN/m, gamma_c = 25 kN/m3 per EN 1991-1-1
_R = G_K * (SPAN + 2 * OVERHANG) / 2e3
M_G = _R * (SPAN / 2e3) - G_K * ((SPAN / 2 + OVERHANG) / 1e3) ** 2 / 2   # kNm, midspan
V_G = _R - G_K * OVERHANG / 1e3                                          # kN, at support

print(f"g_k = {G_K:.4f} kN/m    M_g = {M_G:.3f} kNm    V_g = {V_G:.3f} kN")
print(f"a/d = {A_SHEAR / D:.2f}   ->  a_v = {A_SHEAR:.0f} mm {'<' if A_SHEAR < 2 * D else '>='} 2d = {2 * D:.0f} mm")


def M_Ed(P_d):
    """Design moment in the constant-moment region [kNm]."""
    return GAMMA_G * M_G + P_d * A_SHEAR / 1e3


def V_Ed(P_d):
    """Design shear just inside the support [kN]."""
    return GAMMA_G * V_G + P_d


def P_from_moment(M_Rd):
    return (M_Rd - GAMMA_G * M_G) / (A_SHEAR / 1e3)


def P_from_shear(V_Rd):
    return V_Rd - GAMMA_G * V_G

# %% [markdown]
# ## 6. Q6 — beam as built, with stirrups (6.2.3)
#
# `VRds` and `VRdmax` both validate θ against 21.8°–45°, i.e. exactly the
# eq. (6.7N) limits 1 ≤ cot θ ≤ 2.5. The strut angle is chosen to maximise the
# resistance, which is where the two curves cross.

# %%
Z = 0.9 * D                     # 6.2.3(1), inner lever arm
AC = B * H
FCD, FCK_ = c_d.fcd(), FCK


def shear_with_stirrups(theta_deg):
    v_s = shear.VRds(Asw=ASW, s=S_W, z=Z, theta=theta_deg, fyk=FYK, gamma_s=GAMMA_S)
    v_max = shear.VRdmax(bw=B, z=Z, fck=FCK_, theta=theta_deg, NEd=0.0, Ac=AC, fcd=FCD)
    return min(v_s, v_max) * KN, v_s * KN, v_max * KN


_grid = [21.8 + i * (45.0 - 21.8) / 400 for i in range(401)]
THETA_OPT = max(_grid, key=lambda t: shear_with_stirrups(t)[0])
V_RD, V_RDS, V_RDMAX = shear_with_stirrups(THETA_OPT)

print(f"6.2.3(2) eq.(6.7N)  theta_opt = {THETA_OPT:.2f} deg  ->  cot theta = {1 / math.tan(math.radians(THETA_OPT)):.3f}")
print(f"6.2.3(3) eq.(6.8)   V_Rd,s   = {V_RDS:.1f} kN")
print(f"6.2.3(3) eq.(6.9)   V_Rd,max = {V_RDMAX:.1f} kN")
print(f"                    V_Rd     = {V_RD:.1f} kN")
print()

P_BEND = P_from_moment(M_RD)
P_SHEAR = P_from_shear(V_RD)
P_Q6 = min(P_BEND, P_SHEAR)
GOVERNS = "bending" if P_BEND < P_SHEAR else "shear"

print(f"P_d from bending  = {P_BEND:.1f} kN")
print(f"P_d from shear    = {P_SHEAR:.1f} kN")
print(f"==> Q6:  P_d = {P_Q6:.1f} kN   ({GOVERNS} governs)")
print(f"         P_k = P_d / {GAMMA_Q} = {P_Q6 / GAMMA_Q:.1f} kN")
print(f"    check M_Ed = {M_Ed(P_Q6):.1f} kNm <= M_Rd = {M_RD:.1f} kNm")
print(f"    check V_Ed = {V_Ed(P_Q6):.1f} kN  <= V_Rd = {V_RD:.1f} kN")

# %% [markdown]
# ## 7. Q7 — stirrups removed from the shear spans (6.2.2)
#
# The beam then has no shear reinforcement anywhere (Section B of the fib drawing
# shows the constant-moment region was already without stirrups).
#
# Because a_v < 2d, clause 6.2.2(6) permits the contribution of the point load to
# be reduced by β = a_v/2d. `a_v` is taken as the support-to-load centre distance,
# which is conservative — the true clear distance between bearing plate edges is
# shorter and would give a smaller β.

# %%
ASL = N_BOT * math.pi / 4 * PHI_BOT**2
V_RDC = shear.VRdc(fck=FCK_, d=D, Asl=ASL, bw=B, NEd=0.0, Ac=AC,
                   fcd=FCD, k1=0.15, gamma_c=GAMMA_C) * KN
V_EDMAX = shear.VEdmax_unreinf(bw=B, d=D, fck=FCK_, fcd=FCD) * KN
BETA = A_SHEAR / (2 * D)

P_Q7_PLAIN = P_from_shear(V_RDC)
P_Q7_BETA = (V_RDC - GAMMA_G * V_G) / BETA

print(f"6.2.2(1) eq.(6.2)   rho_l = {ASL / (B * D):.5f}   V_Rd,c = {V_RDC:.2f} kN")
print(f"6.2.2(6)            beta  = a_v/2d = {BETA:.4f}")
print(f"6.2.2(6) eq.(6.5)   limit = {V_EDMAX:.0f} kN   (not governing)")
print()
print(f"==> Q7:  P_d = {P_Q7_PLAIN:.1f} kN  (plain 6.2.2)")
print(f"         P_d = {P_Q7_BETA:.1f} kN  (with the a_v < 2d allowance)")
print(f"    reduction vs Q6: {100 * (1 - P_Q7_BETA / P_Q6):.0f} % ... {100 * (1 - P_Q7_PLAIN / P_Q6):.0f} %")

# %% [markdown]
# ## 8. Mean material level vs the experiment
#
# Same EC2 equations, γ_M = 1.0 and the measured mean strengths. This separates
# model bias from safety margin. The horizontal steel branch ignores strain
# hardening, which for this very under-reinforced section is the dominant effect.

# %%
print(f"{'steel branch':<26}{'M_R [kNm]':>11}{'P [kN]':>9}{'R_exp/R_calc':>14}")
for label, br in (("3.2.7(2)b horizontal", "elasticperfectlyplastic"),
                  ("3.2.7(2)a inclined", "elasticplastic")):
    m = bending_resistance(*make_materials("mean", br))
    p = m / (A_SHEAR / 1e3) - M_G          # self weight unfactored at mean level
    print(f"{label:<26}{m:>11.1f}{p:>9.1f}{R_EXP / p:>14.3f}")
print(f"\nmeasured R_exp = {R_EXP} kN")

# %% [markdown]
# ## 9. Sensitivity
#
# How the Q6 answer moves with the assumptions that are *not* fixed by the standard.

# %%
print(f"{'variant':<40}{'M_Rd [kNm]':>12}{'P_d [kN]':>10}")
for label, fyk_ in (("f_yk = f_ym/1.1  (base)", FYM / 1.1),
                    ("f_yk = f_ym - 1.645*30", FYM - 1.645 * 30),
                    ("f_yk = f_ym  (no reduction)", FYM)):
    c = ConcreteEC2_2004(fck=FCK, fctm=FCTM, Ecm=ECM, gamma_c=GAMMA_C,
                         alpha_cc=ALPHA_CC, constitutive_law="parabolarectangle")
    s = ReinforcementEC2_2004(fyk=fyk_, Es=200000.0, ftk=FTK, epsuk=EPSUK,
                              gamma_s=GAMMA_S, constitutive_law="elasticperfectlyplastic")
    m = bending_resistance(c, s)
    print(f"{label:<40}{m:>12.1f}{P_from_moment(m):>10.1f}")

c = ConcreteEC2_2004(fck=FCK, fctm=FCTM, Ecm=ECM, gamma_c=GAMMA_C, alpha_cc=0.85,
                     constitutive_law="parabolarectangle")
m = bending_resistance(c, s_d)
print(f"{'alpha_cc = 0.85 (German NA value)':<40}{m:>12.1f}{P_from_moment(m):>10.1f}")

# %% [markdown]
# ## 10. Check against the independent hand calculation
#
# The values below were derived by hand while scoping the work, before any code was
# written. They validate that `structuralcodes` is being *used* correctly — the
# arithmetic came from a separate route.

# %%
_checks = [
    ("f_cd", c_d.fcd(), 5.807, 0.1),
    ("f_yd", s_d.fyd(), 316.96, 0.1),
    ("M_Rd (parabola-rectangle)", M_RD, 171.41, 0.5),
    ("M_Rd vs stress block 172.07", M_RD, 172.07, 1.0),   # 3.1.7(3), ~0.4 % apart
    ("V_Rd,c", V_RDC, 58.18, 0.5),
    ("V_Rd (stirrups)", V_RD, 262.2, 1.0),
    ("Q6 P_d", P_Q6, 159.0, 1.0),
    ("Q7 P_d plain", P_Q7_PLAIN, 45.5, 1.0),
    ("Q7 P_d with beta", P_Q7_BETA, 53.4, 1.0),
]
for name, got, want, tol_pct in _checks:
    dev = 100 * abs(got - want) / want
    flag = "ok " if dev <= tol_pct else "!! "
    print(f"{flag}{name:<32} computed {got:>9.2f}   hand {want:>9.2f}   dev {dev:>5.2f} %")
assert all(100 * abs(g - w) / w <= t for _, g, w, t in _checks), "hand-calculation check failed"
print("\nall checks passed")
