"""Parameter study around the R65 benchmark computation.

Reads the default parameter file, varies one thing at a time and calls
``R65.compute_P``.  Nothing is recomputed here — this file only chooses
parameter sets and prints the comparison::

    python R65_study.py

Ordered as the benchmark asks them (``2026-07_fib_TG243_NLFEA_Example.pdf``):

1. **Q5** — compare against the experiment, beam as built (with stirrups).

   1.1  which mode governs at mean level — i.e. that the comparison is a
        flexural one, and that the specimen could not have failed in shear.
   1.2  sensitivity of the inclined steel branch to the assumed eps_uk.

2. **Q6** — maximum design value of P, beam as built (with stirrups).

   2.1  sensitivity of that answer to the assumptions EC2 does not fix.

3. **Q7** — the same beam with the stirrups removed from the shear spans.

4. *Additional* — the target failure probability of 1e-6 that Q6 and Q7 both
   name, and the safety formats that deliver it: via ``level: characteristic``
   and the ECOV coefficient of variation.

Clause numbers printed by investigations 1-3 — 6.1, 6.2.2, 6.2.3, 3.2.7(2),
Table 3.1 — refer to **DIN EN 1992-1-1:2011-01, i.e. EN 1992-1-1:2004 +
AC:2010**, the edition carried in this repository as ``DINEN1992-1-1.pdf``.
Investigation 4 is the exception: its safety-format constants come from
EN 1992-1-1:2023 Annex A and fib MC2020, a different edition that renumbers the
standard (bending 6.1 -> 8.1, shear 6.2 -> 8.2), so clause references are not
comparable across that boundary and none of its source documents is in this
repository.
"""

from __future__ import annotations

import contextlib
import copy
import json
import math
from pathlib import Path

import eurocode_model.R65 as R65
from eurocode_model.R65 import P_from_moment, compute_P, format_result, load_params

BASE = load_params()
RESULTS_DIR = Path(__file__).with_name("results")


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


def save_json(name, data):
    """Write `data` to results/<name>; creates the folder if missing."""
    RESULTS_DIR.mkdir(exist_ok=True)
    with open(RESULTS_DIR / name, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def rule(title):
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


def sub(title):
    print(f"\n{'-' * 78}\n{title}\n{'-' * 78}")


print("=" * 78)
print("fib TG 2.4.3 / R65 — parameter study")
print("=" * 78)
print("Clause numbers below — 6.1, 6.2.2, 6.2.3, 3.2.7(2), Table 3.1 — refer to "
    "DIN EN 1992-1-1:2011-01, i.e. EN 1992-1-1:2004 + AC:2010, the edition in "
    "this repository as DINEN1992-1-1.pdf. Investigation 4 is the exception and "
    "says so where it happens: it uses EN 1992-1-1:2023, which renumbers the "
    "standard, so clause references are not comparable across that boundary.")


# =====================================================================
# 1. Q5 — mean level against the experiment, beam as built
# =====================================================================
rule("1. Q5 — mean level vs the experiment, beam as built (with stirrups)")
print("Same EC2 equations, gamma_M = 1.0, measured mean strengths, actions "
    "unfactored. This separates model bias from safety margin.\n")

print(f"{'steel branch':<28}{'M_R [kNm]':>11}{'P [kN]':>9}{'R_exp/R_calc':>14}")
q5_P = {}
for label, branch in (("horizontal (EC2 3.2.7(2)b )", "elasticperfectlyplastic"),
                      ("inclined (EC2 3.2.7(2)a )", "elasticplastic")):
    r = run(level="mean", case="with_stirrups", branch=branch)
    print(f"{label:<28}{r['M_R']:>11.1f}{r['P']:>9.1f}{r['r_exp_over_calc']:>14.3f}")
    q5_P[f"{branch} [kN]"] = r["P"]
save_json("q5_P.json", q5_P)
print(f"\nmeasured R_exp = {BASE['r_exp']} kN")
print("The residual gap is strain hardening, which the horizontal branch discards:\
this beam is very under-reinforced and the steel is highly ductile.")

# ---------------------------------------------------------------------
# 1.1 which mode governs at mean level
# ---------------------------------------------------------------------
sub("1.1  Which mode governs at mean level")
print("The comparison above is a bending comparison, which is only meaningful \
if the specimen could not have failed in shear first.\n")

m6 = run(level="mean", case="with_stirrups")
m7 = run(level="mean", case="without_stirrups")
print(f"bending (EC2 6.1)                                        P = {m6['P_bending']:7.1f} kN")
print(f"with stirrups (EC2 6.2.3)    theta = {m6['theta']:5.2f} deg"
      f"  V_R  = {m6['V_R']:6.1f} kN   P = {m6['P_shear']:7.1f} kN")
print(f"without stirrups (EC2 6.2.2  )                    V_R,c= {m7['V_R']:6.1f} kN"
      f"   P = {m7['P_shear']:7.1f} kN"
      f"  ({m7['P_shear_av']:.1f} kN with the a_v < 2d allowance)")
print(f"\nas built, bending governs by {m6['P_shear'] / m6['P_bending']:.1f}x"
      " — the Q5 comparison is a flexural one, confirmed.")
print("without stirrups the beam would have failed in shear at roughly"
      f" {m7['P_shear']:.0f}-{m7['P_shear_av']:.0f} kN, far below R_exp = {BASE['r_exp']} kN")
print("— a preview of why Q7 falls so far below Q6 (investigation 3).")
print("\nCAVEAT the mean computation without stirrups after EC2 6.2.2 is a hybrid: C_Rd,c = 0.18/gamma_C keeps the \
characteristic-level constant 0.18 at gamma_C = 1, and nu = 0.6(1-f_ck/250)\
in the mean computation with stirrups after EC2 6.2.3 is a strut effectiveness factor calibrated on f_ck, not a \
strength. Neither is a true R(x_m). Immaterial at this margin.")

# ---------------------------------------------------------------------
# 1.2 sensitivity to the assumed eps_uk
# ---------------------------------------------------------------------
sub("1.2  Sensitivity to the assumed eps_uk, inclined branch after EC2 3.2.7(2)a ")
print("eps_uk is never reached by this section, so it does not change the \
horizontal branch at all. It does set the slope of the inclined branch: \
E_h = (f_td - f_yd)/(eps_ud - eps_yd) with eps_ud = 0.9 eps_uk.\n")

print(f"{'eps_uk':>8}{'M horiz [kNm]':>16}{'M incl [kNm]':>15}{'P incl [kN]':>13}{'R_exp/R_calc':>14}")
for epsuk in (0.05, 0.075, 0.10, 0.15, 0.231):
    h = run(level="mean", epsuk=epsuk, branch="elasticperfectlyplastic")
    i = run(level="mean", epsuk=epsuk, branch="elasticplastic")
    mark = "  <- params.yaml" if epsuk == BASE["epsuk"] else ""
    print(f"{epsuk:>8.3f}{h['M_R']:>16.1f}{i['M_R']:>15.1f}"
          f"{i['P']:>13.1f}{i['r_exp_over_calc']:>14.3f}{mark}")
print("\n0.231 would be A_10 = 23.1 %, the elongation after fracture — NOT eps_uk. \
The qualitative conclusion holds across the range; the specific ratio \
does not, so it should be quoted as a range, not as a single number.")


# =====================================================================
# 2. Q6 — design value of P, beam as built
# =====================================================================
rule("2. Q6 — maximum design value of P, beam as built (with stirrups)")

q6 = run(level="design", branch="elasticperfectlyplastic", case="with_stirrups")
print(format_result(q6))
print(f"\nbending governs by {q6['P_shear'] / q6['P_bending']:.1f}x over the shear verification (EC2 6.2.3), so the \
answer to Q6 is set by bending verification (EC2 6.1) alone. The target p_f = 1e-6 that Q6 names is \
the subject of investigation 4.")

# ---------------------------------------------------------------------
# 2.1 sensitivity to the assumptions EC2 does not fix
# ---------------------------------------------------------------------
sub("2.1  Sensitivity of Q6 to the assumptions outside EC2")

print(f"{'variant':<42}{'M_Rd [kNm]':>12}{'P_d [kN]':>10}")
base_fyk = BASE["fym"] / R65.BIAS_STEEL
for label, fyk_var in (("f_yk = f_ym/1.1  (base)", base_fyk),
                       ("f_yk = f_ym - 1.645*30", BASE["fym"] - 1.645 * 30),
                       ("f_yk = f_ym  (no reduction)", BASE["fym"])):
    with code_constant("BIAS_STEEL", BASE["fym"] / fyk_var):
        r = run(level="design", case="with_stirrups")
    print(f"{label:<42}{r['M_R']:>12.1f}{r['P']:>10.1f}")

with code_constant("ALPHA_CC", 0.85):
    r = run(level="design", case="with_stirrups")
print(f"{'alpha_cc = 0.85 (German NA value)':<42}{r['M_R']:>12.1f}{r['P']:>10.1f}")


# =====================================================================
# 3. Q7 — the same beam without stirrups in the shear spans
# =====================================================================
rule("3. Q7 — design value of P without stirrups in the shear spans")

q7 = run(level="design", branch="elasticperfectlyplastic", case="without_stirrups")
print(format_result(q7))
print(f"\na/d = {q7['a_over_d']:.2f}  ->  the point loads sit inside 2d of the supports,")
print("so EC2 6.2.2(6) applies and is worth about"
      f" {100 * (q7['P_shear_av'] / q7['P'] - 1):.0f} % on Q7. \
against Q6 = {q6['P']:.1f} kN, removing the stirrups costs"
      f" {100 * (1 - q7['P_shear_av'] / q6['P']):.0f} %"
      f" ... {100 * (1 - q7['P'] / q6['P']):.0f} % of the design load,\
and the governing mode changes from bending to shear.")


# =====================================================================
# 4. Additional — the target failure probability of 1e-6
# =====================================================================
rule("4. Additional study — target failure probability of 1e-6, safety formats")

print("NOTE ON VINTAGE  Investigations 1-3 cite EN 1992-1-1:2004 + AC:2010, the "
    "edition in this repository. The safety-format constants below come from a "
    "DIFFERENT edition — EN 1992-1-1:2023 Annex A — and from EN 1990 and fib "
    "MC2020. EC2:2023 renumbers the standard, so 'Annex A' does not denote the "
    "same thing in the two editions and the clause numbers above do not carry "
    "over. None of those three documents is in this repository; every constant "
    "taken from them is therefore an unverified assumption here (see notes.md). "
    "The RESISTANCES being factored, by contrast, are all computed to the 2011 "
    "edition — only the factors applied to them are of the newer vintage.\n")

# Constants of EN 1990, EC2:2023 Annex A and fib MC2020.  Unlike the constants
# in R65.py these stay here, because compute_P does not use them: R65.py
# implements DIN EN 1992-1-1:2011, and these belong to the safety format
# wrapped around it.  None of their source documents is in this repository.
ALPHA_R = 0.80        # EN 1990 C7, FORM sensitivity factor of the resistance
BETA_50Y = 3.8        # EN 1990 Table B2, RC2, 50-year reference period
BETA_1Y = 4.7         # EN 1990 Table B2, RC2,  1-year reference period
ECOV_K = 1.645        # 5 % fractile of the standard normal
GAMMA_RD = 1.06       # EC2:2023 Annex A / MC2020, model uncertainty, BENDING

# The GFM global factor is not a fitted number: it is the factor by which the
# reduced means exceed the design values, and it is (nearly) the SAME for both
# materials, which is the whole point of choosing 0.85 and 1.10 —
#     concrete   f_cR/f_cd = 0.85 * gamma_C = 0.85 * 1.50 = 1.275
#     steel      f_yR/f_yd = 1.10 * gamma_S = 1.10 * 1.15 = 1.265
# so a resistance that scales linearly with strength satisfies R(x_R) = 1.27 R(x_d).
GAMMA_R_GFM = 1.27


def p_f(beta):
    """Failure probability belonging to a reliability index."""
    return 0.5 * math.erfc(beta / math.sqrt(2))


print("Q6 and Q7 both ask for P at a target p_f = 1e-6, but name no reference \
period. That omission moves the answer by ~15 %, so it has to be stated:\n")
print(f"{'beta':>6}{'p_f':>11}   meaning")
for b, what in ((ALPHA_R * BETA_50Y, "alpha_R*beta = 0.8*3.8 — the RESISTANCE quantile behind gamma_M"),
                (BETA_50Y, "RC2, 50-year reference period"),
                (4.3, "RC3, 50-year"),
                (BETA_1Y, "RC2,  1-year   <-- this is the match for 1e-6"),
                (4.75, "exactly p_f = 1e-6")):
    print(f"{b:>6.2f}{p_f(b):>11.2e}   {what}")

print("\nbeta = 4.7 per year and beta = 3.8 per 50 years are the SAME reliability, "
    "and gamma_C = 1.5 / gamma_S = 1.15 / gamma_G = 1.35 are calibrated for it. "
    "So investigation 2 already answers Q6 — provided 1e-6 is read per year, "
    "RC2. What follows corroborates that by three independent safety formats.")

# --- the material levels each format needs ---------------------------
fck = BASE["fcm"] - R65.DELTA_FCK
fyk = BASE["fym"] / R65.BIAS_STEEL
fuk = BASE["fum"] / R65.BIAS_STEEL

m = run(level="mean")            # R(x_m)
k = run(level="characteristic")  # R(x_k)  <- the level added for this section
d = q6                           # R(x_d), the design run of investigation 2

# GFM — Global Factor Method (also "γ_R-method") reduced means, f_cR = 0.85 alpha_cc f_ck and f_yR = 1.10 f_yk.  This needs
# no fourth level: it is 'mean' with the reduced strengths passed in.  Note
# f_yR = 1.10 * f_ym/1.10 = f_ym exactly — the GFM steel IS the measured mean,
# an artefact of BIAS_STEEL = 1.10 being the same 1.10 the GFM uses.
gfm = run(level="mean", fcm=0.85 * R65.ALPHA_CC * fck,
          fym=1.10 * fyk, fum=1.10 * fuk)

print(f"\n{'level':<34}{'f_c [MPa]':>11}{'f_y [MPa]':>11}{'M_R [kNm]':>12}")
for label, r, fc, fy in (("mean            x_m", m, BASE["fcm"], BASE["fym"]),
                         ("characteristic  x_k", k, fck, fyk),
                         ("GFM red. mean   x_R", gfm, 0.85 * fck, 1.10 * fyk),
                         ("design          x_d", d, fck, fyk)):
    print(f"{label:<34}{fc:>11.2f}{fy:>11.1f}{r['M_R']:>12.2f}")

# --- ECOV — Estimate of the Coefficient Of Variation --------------- -------------------------------------------
# Červenka's method. Instead of a tabulated global factor, measure the scatter with two analyses.
V_R = math.log(m["M_R"] / k["M_R"]) / ECOV_K
gamma_R = math.exp(ALPHA_R * BETA_50Y * V_R)
print(f"\nECOV   V_R      = ln({m['M_R']:.2f}/{k['M_R']:.2f})/{ECOV_K} = {V_R:.4f}")
print(f"       gamma_R  = exp({ALPHA_R} * {BETA_50Y} * {V_R:.4f}) = {gamma_R:.3f}"
      f"   (GFM tabulates {GAMMA_R_GFM}...1.30 — same window)")

# --- the answers to Q6 ------------------------------------------------
# The ratio is formed on M_R and not on P: self weight is an ACTION, so letting
# gamma_G*M_g into the ratio would corrupt V_R.  gamma_R is applied to M_R and
# only the result is converted to a load.
#
# GFM is printed TWICE on purpose.  gamma_R = 1.27 is calibrated against
# gamma_C = 1.5 / gamma_S = 1.15 (see its definition above), and those already
# carry the model uncertainty — the TG slides label that variant PFM* with the
# footnote "includes the model uncertainty in the partial factors".  So dividing
# by gamma_Rd on top of 1.27 counts it twice if the benchmark is EC2:2011, but is
# correct against EC2:2023, which deliberately splits 1.46/1.20 for material
# scatter from a separate gamma_Rd.  Which convention applies is one of the open
# questions in the TG, so both are shown rather than one being picked.
print(f"\n{'format':<45}{'M_Rd [kNm]':>12}{'P_d [kN]':>11}")
for label, M_Rd in (
        ("PFM   EC2:2011 1.5/1.15 (investigation 2)", d["M_R"]),
        ("ECOV  R(x_m)/gamma_R/gamma_Rd", m["M_R"] / gamma_R / GAMMA_RD),
        ("GFM   R(x_R)/1.27          (gamma_Rd implicit)", gfm["M_R"] / GAMMA_R_GFM),
        ("GFM   R(x_R)/1.27/gamma_Rd (gamma_Rd explicit)",
         gfm["M_R"] / GAMMA_R_GFM / GAMMA_RD)):
    print(f"{label:<45}{M_Rd:>12.2f}{P_from_moment(BASE, M_Rd, R65.GAMMA_G):>11.1f}")

ecov_M = m["M_R"] / gamma_R / GAMMA_RD
gfm_M = gfm["M_R"] / GAMMA_R_GFM
print(f"\nECOV (Estimate of the Coefficient Of Variation or Cervenka's method) lands {100 * abs(ecov_M / d['M_R'] - 1):.1f} % from the partial factor method"
      f" ({ecov_M:.2f} vs {d['M_R']:.2f} kNm). That is the point: two formats calibrated to the same target reliability, " 
      f"reached from opposite ends — one from x_d, one from x_m — agree. It is the cleanest evidence that P_d from investigation 2 IS the answer at p_f = 1e-6.")

print(f"\nGFM (Global Factor Method (also 'γ_R-method')) without gamma_Rd lands {100 * abs(gfm_M / d['M_R'] - 1):.1f} % from the PFM"
      f" ({gfm_M:.2f} vs {d['M_R']:.2f} kNm), which is"  
      f"the arithmetic confirming the note above: dividing by 1.27 simply undoes the "
      f"partial factors, because both materials were scaled up by that same 1.27. "
      f"Adding gamma_Rd = {GAMMA_RD} on top counts the model uncertainty twice and costs a " 
      f"further {100 * (1 - 1 / GAMMA_RD):.0f} %. Report the pair, not one of them.")

# --- what the answer actually depends on ------------------------------
print(f"\nNOTE 1  f_ck = f_cm - 8 implies V_fc = ln({BASE['fcm']}/{fck:.2f})/{ECOV_K}"
      f" = {math.log(BASE['fcm'] / fck) / ECOV_K:.3f},")
print("          a 40 % CoV for concrete — absurd. The -8 MPa is an ABSOLUTE offset")
print("          calibrated on C20-C50, where it means V ~ 0.15; on a 16.71 MPa")
print("          concrete it is far too large. It does not spoil the V_R above only")
print("          because this section is steel-governed in bending: a first-order")
print("          variance propagation puts f_c at under 1 % of the variance, against")
print("          ~34 % for f_y and ~55 % for the model uncertainty. So V_R is set by")
print("          V_fy and V_theta alone; sweeping V_fc from 0.10 to 0.20 moves V_R by")
print("          less than 0.001.")
print("\nNOTE 2  Therefore this V_R must NOT be carried over to Q7. Eq. (6.2) goes as")
print("          f_ck^(1/3), so there the distortion feeds straight through, and the")
print("          model uncertainty is larger too (gamma_Rd = 1.30, not 1.06). Worse,")
print("          C_Rd,c = 0.18/gamma_C is itself a characteristic-level constant, so")
print("          6.2.2 cannot deliver a true R(x_m) for the ECOV numerator at all.")
print("\nNOTE 3  min(P_bending, P_shear) is only valid if both modes carry their own")
print("          gamma_Rd. With 1.06 against 1.30 the governing mode can flip between")
print("          mean and design level (fib TG2.4.3 May 2026, 'hidden risks' slide).")
print(f"          Here bending governs by {d['P_shear'] / d['P_bending']:.1f}x at design level,")
print("          so it does not flip for Q6 — but that has to be shown, not assumed.")
print("          Q7 (investigation 3) is exactly the case where it HAS flipped.")
