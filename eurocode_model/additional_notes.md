# Notes — how to answer Q6/Q7 at a target failure probability of 10⁻⁶

Working notes, 2026-09-03 (glossary and GFM rows added 2026-09-04). Not a deliverable; scratch
reasoning for the safety-format part of the fib TG 2.4.3 benchmark. Numbers marked ✔ were
computed in-session with `R65.py` and now reproduce from `R65_study.py` investigation 4;
numbers marked ? are from memory and still need a source.

**If you are coming back to this cold, read §8 first** — it explains what PFM / GFM / ECOV
actually are and why they exist. Everything else assumes it.

---

## 0. The short answer

**No, you do not need FORM.** For this beam you don't even need Monte Carlo.

Three reasons, in order of how much they save you:

1. The 10⁻⁶ is almost certainly the **standard EN 1990 RC2 target expressed per year**
   (β = 4.7 → p_f = 1.3·10⁻⁶ ✔), which is the *same* reliability as β = 3.8 over 50 years
   — and that is exactly what γ_C = 1.5 / γ_S = 1.15 / γ_G = 1.35 are calibrated for.
   So **`R65.py` as it stands already answers Q6.** P_d = 159.0 kN.
2. The FORM has already been done for you, once, by the code committee: the split
   α_R = 0.8 / α_E = −0.7 in EN 1990 §C7 *is* the linearised design point. Re-deriving it
   per problem is what the semi-probabilistic format exists to avoid.
3. Within the resistance, R is essentially lognormal, so the design quantile is closed-form:
   R_d = R_m · exp(−α_R β V_R). Getting V_R needs **two** runs of `compute_P` (ECOV), not a
   design-point search.

The work worth doing is therefore not a reliability analysis — it is **computing Q6 by all
four safety formats and showing they agree**, which is precisely the comparison the TG's own
May-2026 slides make (slides 16, 21, 22).

---

## 1. First: pin down what 10⁻⁶ means — this is the one real ambiguity

The benchmark (`2026-07_fib_TG243_NLFEA_Example.pdf`, Q6) says only *"assuming a target
probability of failure of 10⁻⁶"*. It gives **no reference period**. That single omission
moves the answer by ~15 %, so it has to be stated as an assumption in the write-up.

β ↔ p_f, computed ✔:

| β | p_f | what it is (EN 1990 Tables B2/C2 ?) |
|---|---|---|
| 3.04 | 1.18·10⁻³ | α_R·β = 0.8 × 3.8 — the *resistance* quantile behind the EC2 γ_M |
| 3.80 | 7.24·10⁻⁵ | RC2, **50-year** reference period |
| 4.30 | 8.54·10⁻⁶ | RC3, 50-year |
| **4.70** | **1.30·10⁻⁶** | **RC2, 1-year reference period** ← this is the match |
| 4.75 | 1.02·10⁻⁶ | exactly p_f = 10⁻⁶ |

**Reading A (recommended).** 10⁻⁶ ≈ β = 4.7 per year ≡ β = 3.8 per 50 years ≡ ordinary
RC2 ≡ the reliability EC2's partial factors deliver. Q6 is then a normal EC2 design check
and the repo already answers it.

**Reading B.** 10⁻⁶ over 50 years → β = 4.75/50 yr, which is *stricter than RC3* (4.3).
For a laboratory beam that would be an odd thing to ask, but it is the literal reading.

Recommendation: answer with Reading A, state it in one sentence, and give Reading B as a
sensitivity so the TG can see both. Do **not** silently pick one.

### 1b. A second, subtler fork: is α_R = 0.8 legitimate here?

α_R = 0.8 assumes the load carries part of the uncertainty (EN 1990 §C7 permits it only for
0.16 < σ_E/σ_R < 7.6 ?). In this benchmark P is a *testing-machine* load with no scatter
modelled. Taken literally, σ_E → 0, resistance is the sole dominating variable, and the rule
says use **α_R = 1.0** — which puts the full β on the resistance and drops P_d to ~135–144 kN ✔.

But Q6 asks for a *design value of P*, i.e. P as an action in a design situation, not as a
lab load. So α_R = 0.8 is the right call. Worth one line in the write-up, because someone in
the TG will ask, and the α_R = 1.0 number is cheap to report alongside.

---

## 2. Numbers, computed ✔ (bending, horizontal steel branch, `level` variants of `compute_P`)

M_R of the R65 section at the material levels each format needs:

| level | f_c [MPa] | f_y [MPa] | M_R [kNm] |
|---|---|---|---|
| mean x_m | 16.71 | 401.0 | **234.02** |
| characteristic x_k (γ_M = 1) | 8.71 | 364.5 | **203.63** |
| GFM reduced mean x_R (0.85 f_ck, 1.1 f_yk) | 7.40 | 401.0 | **217.07** |
| design x_d, EC2:2011 (1.5 / 1.15) | 8.71 | 364.5 | **171.41** |
| design x_d, EC2:2023 Annex A (1.46 / 1.20) | 8.71 | 364.5 | **165.83** |

**ECOV:** V_R = ln(234.02 / 203.63) / 1.645 = **0.0846** ✔
γ_R = exp(α_R β V_R) = exp(0.8 × 3.8 × 0.0846) = **1.293** ✔ — note how close this lands to
the GFM's tabulated γ_R = 1.27…1.30. Good internal consistency.

Resulting design loads (γ_G = 1.35, M_g = 9.223 kNm, a = 1.0 m), γ_Rd = 1.06 for bending
per EC2:2023 Annex A / MC2020 (TG slide 15):

| format | M_Rd [kNm] ✔ | P_d [kN] ✔ |
|---|---|---|
| mean resistance R_m (γ_G = 1.0, for reference) | 234.02 | 224.8 |
| **PFM, EC2:2011 — what the repo computes today** | **171.41** | **159.0** |
| GFM, R(x_R)/1.27 — γ_Rd implicit | 170.92 | 158.5 |
| ECOV, α_R = 0.8, β = 3.8, / γ_Rd = 1.06 | 170.73 | 158.3 |
| GFM, R(x_R)/1.27 / γ_Rd = 1.06 — γ_Rd explicit | 161.25 | 148.8 |
| PFM, EC2:2023 Annex A 1.46/1.20, / γ_Rd = 1.06 | 156.44 | 144.0 |
| *(Reading B / α_R = 1.0, β = 4.75, / 1.06)* | *147.74* | *135.3* |

**The headline result:** three formats — PFM 171.41, GFM 170.92, ECOV 170.73 kNm — agree
**within 0.4 %** ✔, reached from opposite ends (one from x_d, one from x_R, one from x_m).
That is the demonstration that EC2's partial factors, the GFM global factor and the ECOV all
target the same reliability, and it is the cleanest evidence that P_d ≈ 159 kN *is* the answer
at p_f = 10⁻⁶/yr.

Quote the answer as **P_d ≈ 159 kN**, with 144–149 kN as the variants that apply γ_Rd on top
of factors that arguably already contain it (see §8 on the double-counting). The spread is
driven entirely by **where the model uncertainty is booked**, not by the mechanics — which is
itself the finding worth putting to the TG.

---

## 3. Which parameter distributions — and how much they actually matter

Independent check: first-order variance propagation (MVFOSM, central differences on
`bending_resistance`) with JCSS-type input scatter ✔:

| variable | assumed | variance share | α_i |
|---|---|---|---|
| **θ_R model uncertainty** | lognormal, V = 0.06 | **54.9 %** | 0.741 |
| **f_y** | lognormal, V = 0.05 | **33.7 %** | 0.581 |
| A_s (via φ) | normal, V(A_s) = 0.02 | 5.4 % | 0.232 |
| d | normal, σ = 10 mm | 5.1 % | 0.225 |
| f_c | lognormal, V = 0.15 | **0.9 %** | 0.096 |
| b | normal, σ = 5 mm | 0.0 % | 0.011 |

→ V_R = 0.0544 without model uncertainty, **0.0810 with** ✔ — against the ECOV's 0.0846.
**Two completely independent routes, 4 % apart.** The lognormal-R assumption holds.

### Three consequences worth writing up

1. **Only two numbers matter: V_fy and V_θ.** Sweeping V_fc from 0.10 to 0.20 moves V_R from
   0.0807 to 0.0812 ✔ — i.e. *not at all*. Sweeping V_fy from 0.03 to 0.06 moves V_R from
   0.0715 to 0.0868 ✔ (γ_R 1.24 → 1.30). So all the effort goes into sourcing V_fy and V_θ;
   arguing about concrete statistics is wasted work for this failure mode.

2. **This rescues the ECOV from the f_ck problem.** `f_ck = f_cm − 8` on a 16.71 MPa concrete
   implies V_fc = ln(16.71/8.71)/1.645 = **0.396** ✔ — a 40 % CoV, absurd, because the −8 MPa
   is an *absolute* offset calibrated on C20–C50 where it means V ≈ 0.15. That distortion
   would wreck an ECOV estimate for a concrete-governed mode. Here it contributes 0.9 % of the
   variance, so it is filtered out by the resistance function. **This must be stated
   explicitly** — the README already flags `f_ck = 8.71 MPa` as sitting below C12/15, and this
   is the reliability-side consequence of the same issue. It also means: *do not reuse this
   ECOV V_R for Q7*, where concrete governs (see §5).

3. **Model uncertainty is over half the variance** and is the least defensible number in the
   whole chain. It deserves to be the stated assumption, not a footnote.

### Distribution table to use (and where to source it)

| variable | distribution | mean | CoV / σ | source |
|---|---|---|---|---|
| f_c, in-situ cylinder | lognormal | f_cm = 16.71 | 0.15 | JCSS PMC Pt.3 ? / EC2:2023 Annex A ? |
| f_y | lognormal | f_ym = 401 | 0.03–0.05 | JCSS PMC Pt.3 ? |
| A_s | normal | nominal | 0.02 | JCSS PMC Pt.3 ? |
| d (bar position) | normal | 587 mm | σ ≈ 5–10 mm | JCSS PMC Pt.3 ? |
| b, h | normal | nominal | σ ≈ 5 mm | JCSS PMC Pt.3 ? |
| θ_R, bending | lognormal | 1.0 | 0.05–0.10 | γ_Rd = 1.06 ✔ (TG slide 15) |
| θ_R, shear | lognormal | 1.0 | ~0.15–0.25 | γ_Rd = 1.30 ✔ (TG slide 15) |
| f_ct, G_f | lognormal | 1.30 MPa / — | 0.30 / 0.15 | only matters for Q7 ? |

**Standards, in order of applicability here:**

- **EN 1992-1-1:2023 Annex A** — named directly on TG slides 12–15. Gives CoV and bias factors
  for adjusting γ_C/γ_S, and the nonlinear-analysis case γ_c = 1.46 | γ_s = 1.20 with
  γ_Rd = 1.06 (bending) / 1.30 (general) ✔. This is the most defensible source for this
  benchmark *because the TG itself is using it*.
- **fib Model Code 2020** (and MC2010 §4.5.2.3 / 7.11) — defines PFM / GFM / ECOV.
- **EN 1990 Annex B** (target β by consequence class) and **Annex C** (α_R = 0.8, α_E = −0.7);
  **Annex D** for the lognormal-R design-value formula.
- **JCSS Probabilistic Model Code (2001), Part 3 "Resistance models"** — the reference if a
  genuine full-probabilistic run is wanted. Freely available.
- **fib Bulletin 80 (2016)** — partial factors for existing structures; TG slide 13.
- **ISO 2394:2015** — general target-reliability principles.

⚠ **Traceability gap.** None of EC2:2023, MC2020, JCSS PMC or EN 1990 is in this repo — only
DIN EN 1992-1-1:2011 and the two TG PDFs. Every statistical parameter above is therefore in
the same category as the existing `BIAS_STEEL = 1.10` assumption that the README already
flags as "the only material value not traceable to a document in this repository". Keep that
discipline: either add the sources, or mark each number as an assumption and show the
sensitivity. **The `?` marks in this file are the to-do list.**

---

## 4. Effort ladder — what to actually implement

| # | route | effort | what it buys |
|---|---|---|---|
| 0 | State that EC2 PSF ≡ β 3.8/50 yr ≡ 4.7/1 yr ≡ p_f ≈ 10⁻⁶/yr | 0 lines | answers Q6 |
| 1 | **ECOV** — add `level: characteristic`, 2 runs → V_R → γ_R | ~10 lines | the "easy way" asked about |
| 2 | **GFM + PFM(2023)** → reproduce the TG's own comparison table | ~20 lines | **highest value per line** |
| 3 | MVFOSM / Taylor, finite differences → V_R + α_i | ~60 lines | validates 1, names the dominant variable |
| 4 | Closed-form vectorised M_R surrogate + 10⁷ MC | ~100 lines | true quantile, no lognormal assumption |
| 5 | FORM / SORM | more | design point, exact α_i — **not needed** |

Levels 0–3 are already done in scratch (`scratchpad/probe.py`, `scratchpad/taylor.py`) and
produced every ✔ number above. Porting them into `R65_study.py` as investigations 4 and 5 is
the natural next step.

**On level 4, if it's ever wanted:** crude MC at 10⁻⁶ needs ~10⁸ samples, impossible through
the `structuralcodes` section solver. But the section is under-reinforced and the steel yields
comfortably (x/d ≈ 0.41, ε_s ≈ 0.005 ≫ ε_yd ≈ 0.0016), so a rectangular-stress-block
closed form M_R = A_s f_y (d − λx/2) + top-steel term is vectorisable in numpy and lands
within ~4 % of the `structuralcodes` value. Validate it against `bending_resistance` on a few
hundred points, then 10⁸ samples run in seconds. That is *easier* than FORM, not harder, and
it needs no assumption about the shape of R.

**On level 5 — when FORM would genuinely be required:** (a) if a competing failure mode had
comparable probability, making it a series-system problem; (b) if the limit state were
strongly nonlinear in the dominant variable — it is not, R is near-linear in f_y;
(c) if you needed the design point to *calibrate* new partial factors rather than apply
existing ones. None applies to Q6.

### Concrete change needed in `R65.py`

`make_materials` currently has two levels: `design` (char. strengths ÷ γ_M) and `mean`
(measured means, γ_M = 1). ECOV needs a third — **characteristic strengths with γ_M = 1** —
which is a ~4-line addition:

```python
elif level == "characteristic":
    fck = p["fcm"] - DELTA_FCK
    fyk, ftk = p["fym"] / BIAS_STEEL, p["fum"] / BIAS_STEEL
    gamma_c, gamma_s = 1.0, 1.0
```

Then a `gfm` level (f_cR = 0.85 α_cc f_ck, f_yR = 1.10 f_yk, γ_M = 1) for level 2.

**Do the ECOV on M_R, not on P.** Self-weight is an *action*, not a resistance — running the
ratio R_m/R_k on the `P` returned by `compute_P` would drag γ_G M_g into the CoV and corrupt
V_R. Get γ_R from M_R(x_m)/M_R(x_k), apply it to M_R, and only then convert to P via
`P_from_moment`. (Effect is small here — M_g is 4 % of M_R — but it is wrong in principle.)

---

## 5. Q7 (no stirrups) is *not* the same problem — don't reuse anything from Q6

Three reasons the Q6 machinery breaks for Q7, all worth flagging to the TG:

1. **γ_Rd jumps from 1.06 to 1.30** ✔ (TG slide 15). Shear model uncertainty is far larger.
2. **The ECOV V_R will be dominated by the f_ck distortion.** Eq. (6.2) goes as f_ck^(1/3),
   and here f_ck is 48 % below f_cm with an implied V_fc = 0.396 ✔. Unlike bending, that
   feeds straight through. An ECOV V_R computed for Q7 will be badly overstated. Either use a
   JCSS-based V_fc = 0.15 with a Taylor propagation, or say plainly that ECOV is unreliable
   for this mode on this specimen.
3. **C_Rd,c = 0.18/γ_C is already a characteristic-level constant** — the README/`R65.py`
   docstring already notes that evaluating 6.2.2 at γ_C = 1 gives a mean-material /
   characteristic-model hybrid, not R(x_m). ECOV needs a true R(x_m); eq. (6.2) cannot give one.
   This is a genuine limitation, not a modelling choice.

### The failure-mode-transition trap — likely the most interesting thing to report

TG slide 23 ("Hidden Risks of Failure Mode Sensitivity/Transition") is about exactly this
beam's situation. Because γ_Rd differs by mode (1.06 vs 1.30), **the governing mode can flip
between mean level and design level**. So:

> `res["P"] = min(res["P_bending"], res["P_shear"])` is only valid if both are evaluated at
> the *same* reliability level with their *own* γ_Rd.

Taking the minimum of two mean-level resistances and then applying one global γ_R is wrong.
Compute R_d per mode with its own V_R and γ_Rd, *then* take the minimum. At design level with
stirrups, bending governs at 159.0 vs 249.5 kN ✔ — a wide enough margin that the flip does not
occur for Q6, but it should be *shown* rather than assumed, and Q7 needs checking properly.

Also, strictly, p_f = 10⁻⁶ is a target for the **beam**, not per mode. As a series system the
modal probabilities add, so if two modes contributed equally each would need ~5·10⁻⁷. Ignored
by every code format; worth one sentence, no more.

---

## 6. Open questions / to-do

- [ ] Decide and **state** the reference period for the 10⁻⁶ (Reading A vs B, §1). Consider
      asking the TG directly — the benchmark text is genuinely ambiguous and everyone
      answering it is making this choice silently.
- [ ] Source V_fy and V_θ properly (§3) — they are the only two numbers that move the answer.
- [ ] Get EC2:2023 Annex A and the JCSS PMC into the repo, or mark all statistics as
      assumptions in the README's "Decisions behind the numbers" section.
- [x] Add `level: characteristic` to `make_materials`; port the ECOV comparison into
      `R65_study.py` as investigation 4. *(done, branch `safety-format-ecov`)*
- [ ] Port `taylor.py` (MVFOSM variance propagation) as investigation 5. Its results are
      currently only **quoted** in investigation 4's CAVEAT 1, not recomputed — so the
      variance shares (f_c < 1 %, f_y ~34 %, θ_R ~55 %) are unverifiable from the repo.
      Needs the JCSS input CoVs, i.e. the item above.
- [ ] No `level: gfm` was added — the GFM runs as `level: mean` with reduced strengths passed
      in, because f_yR = 1.10·f_yk = f_ym exactly. Revisit if `BIAS_STEEL` ever changes from
      1.10, at which point that coincidence breaks and a real level is warranted.
- [ ] Redo the format comparison for the **inclined steel branch** — strain hardening raises
      R_m but also changes V_R, and the study already shows the branch matters at mean level.
- [ ] Q7: decide whether to report an ECOV value at all, or only PFM/GFM with γ_Rd = 1.30 (§5).
- [ ] Check whether the 6.2.2(6) a_v < 2d reduction (β = 0.852) interacts with the safety
      format — it is a model choice inside R, so it should sit *inside* the ECOV runs, not be
      applied afterwards.

## 7. Scratch files

`probe.py` (safety formats, ECOV) is superseded — it is now investigation 4 of
`R65_study.py`, and every ✔ number in §2 reproduces exactly from there.

`taylor.py` (MVFOSM, the §3 variance shares) still lives only in the session scratchpad and
**will be lost when it is cleaned up**. It imports `R65.py` unmodified and is ~60 lines; if
the §3 table matters, port it before then.

---

## 8. Glossary — what the safety formats actually are

All of these are answers to **one** problem, and it is a problem that only appears in
*nonlinear* analysis.

In a sectional design calculation you can put γ_C on the concrete and γ_S on the steel and
trust the resistance to scale with them. In NLFEA you run **one** expensive analysis with
**one** set of material numbers and get **one** resistance. You cannot factor at the end,
because the numbers you feed in change the stiffness, the crack pattern, the redistribution —
and possibly which failure mode you get. So the question becomes:

> **Which single set of material values do I feed the analysis, and what do I divide by?**

Each acronym is a different answer to that. Note this repo's "analysis" is a *sectional* EC2
calculation, not NLFEA — which is exactly why the formats agree so closely here (§2). They
were invented for the case where they do not: the TG's own punching example spreads
4490–5881 kN (31 %) against 238–267 kN (12 %) for bending (slides 21–22).

| format | # runs | materials fed in | divide by |
|---|---|---|---|
| **PFM** — Partial Factor Method | 1 | design values x_d | γ_Rd |
| **GFM** — Global Factor Method (γ_R-method) | 1 | reduced means x_R | γ_R = 1.27 (tabulated) [× γ_Rd] |
| **ECOV** — Estimate of the Coefficient Of Variation | 2 | means x_m *and* characteristic x_k | γ_R (derived) × γ_Rd |
| **PFM** — full probabilistic | many | random fields, LHS/MC | γ_Rd |

### PFM
Feed f_cd = f_ck/γ_C and f_yd = f_yk/γ_S; take R(x_d). The objection: here f_cd = 5.807 MPa
against a real 16.71 MPa, so a nonlinear run would be simulating **a beam that does not
exist** — three times too weak in compression. Harmless for a sectional check like this repo's;
the reason the other formats were invented once NLFEA arrived.

### GFM
Run the analysis on materials closer to reality, then divide by one global factor. The reduced
means f_cR = 0.85·f_ck and f_yR = 1.10·f_yk look arbitrary until you take their ratio to the
design values:

```
concrete   f_cR/f_cd = 0.85 × 1.50 = 1.275
steel      f_yR/f_yd = 1.10 × 1.15 = 1.265
```

**Both materials are scaled up from their design values by the same ≈1.27.** That is the whole
trick: if the resistance scales linearly with strength then R(x_R) ≈ 1.27·R(x_d), so dividing
by 1.27 recovers the design resistance while the *analysis itself* ran on realistic materials.
Confirmed here — R(x_R)/1.27 = 170.92 vs R(x_d) = 171.41, **0.3 % apart** ✔.

⚠ **The γ_Rd double-counting trap.** Because 1.27 is calibrated against γ_C = 1.5 / γ_S = 1.15,
and those already carry the model uncertainty (the TG slides label that variant **PFM\*** with
the footnote *"includes the model uncertainty in the partial factors"*), dividing by γ_Rd on
top of 1.27 applies it **twice** — costing a further 6 % and dropping the answer to 148.8 kN.
Against EC2:2023 it *is* correct to stack, because 1.46/1.20 covers material scatter only and
γ_Rd is split out deliberately. Which convention applies is an open TG question, so
investigation 4 prints **both rows** rather than choosing.

### ECOV
Červenka's method. Instead of a tabulated global factor, **measure** the scatter with two
analyses. Assume R is lognormal; then

- R(x_m) = 234.02 kNm is the **mean**,
- R(x_k) = 203.63 kNm is the **5 % fractile** (you fed in 5 % fractile materials),
- so V_R = ln(R_m/R_k)/1.645 = 0.0846, and any quantile is closed form:
  R_d = R_m·exp(−α_R·β·V_R) = R_m/γ_R.

**This is the entire reason `level: characteristic` exists** — it is nothing but the
denominator of that ratio.

*Advantage over GFM:* γ_R comes out specific to this structure and this failure mode. Ductile
bending gives V_R = 0.085 and γ_R = 1.29; a brittle shear failure would give a much larger one.
The tabulated 1.27 cannot tell them apart. *Cost:* two analyses instead of one.

*Known weakness:* "5 % fractile inputs → 5 % fractile output" is exact only for a monotone
function of **one** variable. Two independent 5 % fractiles co-occurring is far rarer than 5 %,
so ECOV tends to **overstate** V_R when several variables matter. Here f_y dominates (§3), so
the assumption is close to satisfied — which is a further reason the agreement in §2 is good,
and a reason not to expect it for Q7.

### Two things that are *not* what they look like
- γ_R is a **resistance-side** factor throughout. None of this touches γ_G = 1.35 on the load
  side — that is the α_E = −0.7 half of the same EN 1990 calibration.
- **PFM** is used on the TG slides for *both* "Partial Factor Method" and "full probabilistic
  method", in the same deck. Read it from context.
