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

# unit inversion (alternative use pint)
MM2, KN, KNM = 1.0, 1e-3, 1e-6  # N,mm -> kN, kNm

# %% [markdown]
# ## 1. Specimen data
#
# From the appendix of `2026-07_fib_TG243_NLFEA_Example.pdf`.

# %%
# geometry [mm]
B, H, D, D2 = 300.0, 625.0, 587.0, 38.5   # width, depth, eff. depth, top-steel depth (Betondeckung)
SPAN, OVERHANG, A_SHEAR = 4000.0, 255.0, 1000.0   # support spacing, overhang, shear span

# reinforcement
# bending
PHI_BOT, N_BOT = 26.0, 2      # 2 Ø26 = 1062 mm^2
PHI_TOP, N_TOP = 10.0, 2      # 2 Ø10 =  157 mm^2
# shear
ASW, S_W = 157.0, 120.0       # Ø10 two-legged stirrups @ 120 mm

# measured mean material properties [MPa]
FCM, FCTM, ECM = 16.71, 1.30, 25660.0
FYM, FUM = 401.0, 596.0
EPSUK = 0.10                  # characteristik strain at the ultimate stress level: assumed; 

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
    # NOTE: EPSUK (characteristic strain at ULS) assumed to be 0.10 - not reached in the end
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
    # define beam cross-section geometry
    poly = Polygon([(-B / 2, -H / 2), (B / 2, -H / 2), (B / 2, H / 2), (-B / 2, H / 2)])
    geo = SurfaceGeometry(poly=poly, material=concrete)
    z_bot, z_top = -H / 2 + (H - D), H / 2 - D2
    # add bending reinforcement bars
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
_R = G_K * (SPAN + 2.0 * OVERHANG) / 2e3 # reaction forces as support
# maximum moment and querkraft 
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


# main functions to compute P
def P_from_moment(M_Rd):
    """compute P_d (design_value) from M_ed=GAMMA_G * M_G +  P_d * A_SHEAR/1e3 <= M_rd """
    return (M_Rd - GAMMA_G * M_G) / (A_SHEAR / 1e3)


def P_from_shear(V_Rd):
    """compute P_d (design_value) from V_ed=GAMMA_G * V_G +  P_d <= V_rd """
    return V_Rd - GAMMA_G * V_G

# %% [markdown]
# ## 6. Shear resistance (6.2.2, 6.2.3) and Q6 — beam as built
#
# Both functions take the material objects, exactly like `bending_resistance`, so
# the same code serves the design level here and the mean level in section 8.
#
# **With stirrups, 6.2.3.** `VRds` (eq. 6.8, stirrups yield) rises with cot θ,
# `VRdmax` (eq. 6.9, struts crush) falls; the resistance is the smaller of the two
# and is therefore largest where the curves cross. Both library functions validate
# θ against 21.8°–45°, i.e. exactly the eq. (6.7N) limits 1 ≤ cot θ ≤ 2.5, which is
# what `THETA_GRID` spans. The longitudinal steel does *not* enter: the truss is a
# mechanical model and A_sl is its chord, checked separately by eq. (6.18).
#
# **Without stirrups, 6.2.2.** Purely empirical, so ρ_l *does* appear explicitly —
# it stands in for dowel action, crack width and compression-zone depth. Note that
# C_Rd,c = 0.18/γ_C has 0.18 as a characteristic-level constant, so evaluating this
# at γ_C = 1 gives a mean-material / characteristic-model hybrid (see section 8).

# %%
Z = 0.9 * D                     # 6.2.3(1), inner lever arm
AC = B * H
ASL = N_BOT * math.pi / 4 * PHI_BOT**2
# theta within [21.8, 45] deg, from 1 <= cot theta <= 2.5, eq. (6.7N)
THETA_GRID = [21.8 + i * (45.0 - 21.8) / 400 for i in range(401)]


def shear_resistance(concrete, steel, theta_deg=None):
    """V_Rd of a shear span with stirrups, 6.2.3.

    Returns (V_Rd, V_Rd,s, V_Rd,max, theta) in kN and degrees. theta is chosen to
    maximise V_Rd over THETA_GRID unless an angle is passed in.
    """
    def at(theta):
        v_s = shear.VRds(Asw=ASW, s=S_W, z=Z, theta=theta,
                         fyk=steel.fyk, gamma_s=steel.gamma_s)          # stirrups yield
        v_max = shear.VRdmax(bw=B, z=Z, fck=concrete.fck, theta=theta,
                             NEd=0.0, Ac=AC, fcd=concrete.fcd())        # struts crush
        return min(v_s, v_max) * KN, v_s * KN, v_max * KN

    # get optimal theta within ranges of EC
    theta = theta_deg if theta_deg is not None else max(THETA_GRID, key=lambda t: at(t)[0])
    return (*at(theta), theta)


def shear_resistance_no_stirrups(concrete):
    """V_Rd,c without shear reinforcement [kN], 6.2.2(1) eq. (6.2)."""
    return shear.VRdc(fck=concrete.fck, d=D, Asl=ASL, bw=B, NEd=0.0, Ac=AC,
                      fcd=concrete.fcd(), k1=0.15, gamma_c=concrete.gamma_c) * KN


V_RD, V_RDS, V_RDMAX, THETA_OPT = shear_resistance(c_d, s_d)

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
V_RDC = shear_resistance_no_stirrups(c_d)
V_EDMAX = shear.VEdmax_unreinf(bw=B, d=D, fck=c_d.fck, fcd=c_d.fcd()) * KN
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
# ### 8b. Which mode governs at mean level
#
# The comparison above is a *bending* comparison, which is only meaningful if the
# specimen could not have failed in shear first. The same two shear functions,
# given the mean materials, settle that.
#
# The truss (6.2.3) takes mean values cleanly — stirrup yield at f_ym is a real
# physical event. Two caveats, neither of which matters at this margin:
#
# * ν = 0.6(1 − f_ck/250) is a strut *effectiveness* factor calibrated on f_ck, so
#   substituting f_cm uses the fit outside its calibration rather than taking a mean.
# * 6.2.2 is worse: C_Rd,c = 0.18/γ_C keeps the characteristic-level constant 0.18
#   at γ_C = 1, so V_R,c below is mean-material / characteristic-model. EC2 gives no
#   mean value of that constant and the background documents are not in this repo,
#   so the figure is reported as a hybrid and labelled as such — not as R(x_m).

# %%
V_RD_M, V_RDS_M, V_RDMAX_M, THETA_M = shear_resistance(c_m, s_m)
V_RDC_M = shear_resistance_no_stirrups(c_m)
P_BEND_M = bending_resistance(*make_materials("mean")) / (A_SHEAR / 1e3) - M_G

print(f"6.2.3  with stirrups   theta_opt = {THETA_M:.2f} deg (cot = {1 / math.tan(math.radians(THETA_M)):.3f})"
      f"   V_R = {V_RD_M:.1f} kN  ->  P = {V_RD_M - V_G:.1f} kN")
print(f"6.2.2  no stirrups     rho_l = {ASL / (B * D):.5f}"
      f"                    V_R,c = {V_RDC_M:.1f} kN  ->  P = {V_RDC_M - V_G:.1f} kN"
      f"  ({(V_RDC_M - V_G) / BETA:.1f} kN with the a_v < 2d allowance)")
print(f"6.1    bending (horizontal branch)                             "
      f"           ->  P = {P_BEND_M:.1f} kN")
print()
print(f"as built, bending governs at mean level by {(V_RD_M - V_G) / P_BEND_M:.1f}x"
      " — the section-8 comparison against R_exp is a flexural one.")
print("without stirrups the beam would have failed in shear at roughly"
      f" {V_RDC_M - V_G:.0f}-{(V_RDC_M - V_G) / BETA:.0f} kN, far below R_exp = {R_EXP} kN.")



