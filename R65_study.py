"""Parameter study around the R65 benchmark computation.

Reads the default parameter file, varies one thing at a time and calls
``R65.compute_P``.  Nothing is recomputed here — this file only chooses
parameter sets and prints the comparison::

    python R65_study.py

Five investigations:

1. Q6 / Q7 — the two benchmark questions at design level.
2. Mean level vs the experiment — the two steel branches of 3.2.7(2).
3. Which mode governs at mean level — bending against both shear clauses.
4. Sensitivity of Q6 to the assumptions that EC2 does not fix.
5. Sensitivity of the inclined branch to the assumed eps_uk.
"""

from __future__ import annotations

import contextlib
import copy

import R65
from R65 import compute_P, format_result, load_params

BASE = load_params()


def run(**overrides):
    """compute_P on the default parameters with `overrides` applied."""
    p = copy.deepcopy(BASE)
    p.update(overrides)
    return compute_P(p)


@contextlib.contextmanager
def code_constant(name, value):
    """Temporarily override a module constant of R65.

    Needed for the assumptions that are deliberately *not* in params.yaml
    because they belong to the code side rather than to the specimen.
    """
    original = getattr(R65, name)
    setattr(R65, name, value)
    try:
        yield
    finally:
        setattr(R65, name, original)


def rule(title):
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


# ---------------------------------------------------------------------
# 1. The two benchmark questions, design level
# ---------------------------------------------------------------------
rule("1. Q6 and Q7 — design level")

q6 = run(case="with_stirrups")
q7 = run(case="without_stirrups")
print(format_result(q6))
print()
print(format_result(q7))
print(f"\na/d = {q6['a_over_d']:.2f}  ->  the point loads sit inside 2d of the supports,")
print("so 6.2.2(6) applies and is worth about"
      f" {100 * (q7['P_shear_av'] / q7['P'] - 1):.0f} % on Q7.")
print(f"removing the stirrups costs"
      f" {100 * (1 - q7['P_shear_av'] / q6['P']):.0f} %"
      f" ... {100 * (1 - q7['P'] / q6['P']):.0f} % of the design load.")

# ---------------------------------------------------------------------
# 2. Mean material level vs the experiment
# ---------------------------------------------------------------------
rule("2. Mean level vs the experiment — steel branch of 3.2.7(2)")
print("Same EC2 equations, gamma_M = 1.0, measured mean strengths, actions")
print("unfactored. This separates model bias from safety margin.\n")

print(f"{'steel branch':<28}{'M_R [kNm]':>11}{'P [kN]':>9}{'R_exp/R_calc':>14}")
for label, branch in (("3.2.7(2)b horizontal", "elasticperfectlyplastic"),
                      ("3.2.7(2)a inclined", "elasticplastic")):
    r = run(level="mean", branch=branch)
    print(f"{label:<28}{r['M_R']:>11.1f}{r['P']:>9.1f}{r['r_exp_over_calc']:>14.3f}")
print(f"\nmeasured R_exp = {BASE['r_exp']} kN")
print("The residual gap is strain hardening, which the horizontal branch discards:")
print("this beam is very under-reinforced and the steel is highly ductile.")

# ---------------------------------------------------------------------
# 3. Which mode governs at mean level
# ---------------------------------------------------------------------
rule("3. Which mode governs at mean level")
print("The comparison above is a bending comparison, which is only meaningful")
print("if the specimen could not have failed in shear first.\n")

m6 = run(level="mean", case="with_stirrups")
m7 = run(level="mean", case="without_stirrups")
print(f"6.1    bending                                        P = {m6['P_bending']:7.1f} kN")
print(f"6.2.3  with stirrups     theta = {m6['theta']:5.2f} deg"
      f"  V_R  = {m6['V_R']:6.1f} kN   P = {m6['P_shear']:7.1f} kN")
print(f"6.2.2  without stirrups                     V_R,c= {m7['V_R']:6.1f} kN"
      f"   P = {m7['P_shear']:7.1f} kN"
      f"  ({m7['P_shear_av']:.1f} kN with the a_v < 2d allowance)")
print(f"\nas built, bending governs by {m6['P_shear'] / m6['P_bending']:.1f}x"
      " — the section-2 comparison is a flexural one, confirmed.")
print("without stirrups the beam would have failed in shear at roughly"
      f" {m7['P_shear']:.0f}-{m7['P_shear_av']:.0f} kN, far below R_exp = {BASE['r_exp']} kN.")
print("\nCAVEAT the 6.2.2 mean figure is a hybrid: C_Rd,c = 0.18/gamma_C keeps the")
print("       characteristic-level constant 0.18 at gamma_C = 1, and nu = 0.6(1-f_ck/250)")
print("       in 6.2.3 is a strut effectiveness factor calibrated on f_ck, not a")
print("       strength. Neither is a true R(x_m). Immaterial at this margin.")

# ---------------------------------------------------------------------
# 4. Sensitivity of Q6 to the assumptions EC2 does not fix
# ---------------------------------------------------------------------
rule("4. Sensitivity of Q6 to the assumptions outside EC2")

print(f"{'variant':<42}{'M_Rd [kNm]':>12}{'P_d [kN]':>10}")
base_fyk = BASE["fym"] / R65.BIAS_STEEL
for label, fyk in (("f_yk = f_ym/1.1  (base)", base_fyk),
                   ("f_yk = f_ym - 1.645*30", BASE["fym"] - 1.645 * 30),
                   ("f_yk = f_ym  (no reduction)", BASE["fym"])):
    with code_constant("BIAS_STEEL", BASE["fym"] / fyk):
        r = run()
    print(f"{label:<42}{r['M_R']:>12.1f}{r['P']:>10.1f}")

with code_constant("ALPHA_CC", 0.85):
    r = run()
print(f"{'alpha_cc = 0.85 (German NA value)':<42}{r['M_R']:>12.1f}{r['P']:>10.1f}")

# ---------------------------------------------------------------------
# 5. Sensitivity of the inclined branch to the assumed eps_uk
# ---------------------------------------------------------------------
rule("5. Sensitivity to the assumed eps_uk, 3.2.7(2)a inclined branch")
print("eps_uk is never reached by this section, so it does not change the")
print("horizontal branch at all. It does set the slope of the inclined branch:")
print("E_h = (f_td - f_yd)/(eps_ud - eps_yd) with eps_ud = 0.9 eps_uk.\n")

print(f"{'eps_uk':>8}{'M horiz [kNm]':>16}{'M incl [kNm]':>15}{'P incl [kN]':>13}{'R_exp/R_calc':>14}")
for epsuk in (0.05, 0.075, 0.10, 0.15, 0.231):
    h = run(level="mean", epsuk=epsuk, branch="elasticperfectlyplastic")
    i = run(level="mean", epsuk=epsuk, branch="elasticplastic")
    mark = "  <- params.yaml" if epsuk == BASE["epsuk"] else ""
    print(f"{epsuk:>8.3f}{h['M_R']:>16.1f}{i['M_R']:>15.1f}"
          f"{i['P']:>13.1f}{i['r_exp_over_calc']:>14.3f}{mark}")
print("\n0.231 would be A_10 = 23.1 %, the elongation after fracture — NOT eps_uk.")
print("The qualitative conclusion holds across the range; the specific ratio")
print("does not, so it should be quoted as a range, not as a single number.")
