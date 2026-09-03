# fibTG243

aim: eurocode conform solution of the fib TG2.3.4 test case

## Context

`fib` TG 2.4 / WP 2.4.3 benchmark (`2026-07_fib_TG243_NLFEA_Example.pdf`) using the Rüsch & Rehm (1963) beam test **R65** computing the maximum **design value** of the applied point loads `P` — with stirrups
(question 6) and without stirrups in the shear spans (question 7).

This repo deliberately answers the same two questions **without FEM**, by a classic clause-by-clause
design computation to DIN EN 1992-1-1:2011-01 as a reference. 

Sources in this repo:

| File | Role |
|---|---|
| `DINEN1992-1-1.pdf` | DIN EN 1992-1-1:2011-01 — the design standard |
| `2026-07_fib_TG243_NLFEA_Example.pdf` | the benchmark task and the R65 specimen data |
| `2026-05-26_fibTG243_4rd_Meeting_Safety_concepts.pdf` | TG background on safety formats |

## Case data (fib appendix, specimen R65)

| | |
|---|---|
| Geometry | L = 4.510 m, span 4.00 m (overhangs 0.255 m), b = 0.300 m, h = 0.625 m, d = 0.587 m |
| Loading | two point loads P at 1.00 m from each support → 2.00 m constant-moment region |
| Bottom reinforcement | 2 Ø26 = 1062 mm² (d = 587 mm) |
| Top reinforcement | 2 Ø10 = 157 mm² (d₂ = 38.5 mm) |
| Stirrups | Ø10 two-legged, A_sw = 157 mm², s = 120 mm, shear spans only |
| Concrete | f_cm = 16.71 MPa, f_ctm = 1.30 MPa, E_cm = 25.66 GPa |
| Reinforcing steel | f_ym = 401 MPa, f_um = 596 MPa, A₁₀ = 23.1 % |
| Experiment | R_exp = 259.2 kN per point load |

## Settled decisions

### Concrete — fully source-backed, no assumption

The specimen data gives mean values; EC2 is written in characteristic values. Table 3.1 of
DIN EN 1992-1-1 (printed p. 30 = PDF p. 34) supplies the inverse relations directly:

```
f_ck       = f_cm − 8         = 16.71 − 8    = 8.71 MPa
f_ctk;0,05 = 0.7 · f_ctm      = 0.7 · 1.30   = 0.91 MPa
f_cd       = α_cc f_ck / γ_C  = 1.0·8.71/1.5 = 5.807 MPa   (eq. 3.15)
```

A self-consistency check confirms this is the intended reading: `22·(16.71/10)^0.3 = 25.66 GPa`
reproduces the given `E_cm` exactly, and `0.30·8.71^(2/3) = 1.27 ≈ 1.30` the given `f_ctm`. The fib
data sheet was evidently generated with these same Table 3.1 relations.

Two caveats are recorded but do not block the computation:

1. Table 3.1 defines the mean strength *belonging to* a characteristic class. Inverting it to infer
   `f_ck` from one batch's measured `f_cm` is an application of the relation rather than its literal
   purpose — but it is the only route EC2 offers.
2. `f_ck = 8.71 MPa` lies **below C12/15**, the lowest row of Table 3.1. EC2 has no *structural*
   minimum class: the only minimum-class statement is Table E.1N (printed p. 221), a **durability**
   requirement tied to exposure classes and irrelevant to a laboratory specimen. The value is
   therefore used as derived and **not** rounded up to C12/15, which would be unconservative.

### Reinforcing steel — assumption, flagged as outside EC2

EC2 provides no mean→characteristic relation for reinforcement. Table 3.1's factor 0.7 is specific
to the concrete tensile strength (it implies a CoV of about 18 %, far too severe for rebar at
CoV ≈ 5 %) and must not be transferred. The code-calibration bias factor 1.1 is used instead:

```
f_yk = f_ym / 1.1 = 401 / 1.1  = 364.5 MPa
f_yd = f_yk / γ_S = 364.5/1.15 = 317.0 MPa
```

This is the one material value in the computation that is **not** traceable to a document in this
repo. A sensitivity study over alternative bases (5 % fractile with σ = 30 MPa → 352 MPa; mean value
→ 401 MPa) accompanies the results.

### Nationally determined parameters — EN recommended values only

`DINEN1992-1-1.pdf` is the German translation of EN 1992-1-1 carrying the **CEN recommended** NDP
values. The German National Annex (DIN EN 1992-1-1/NA) is a separate document, not present in this
repo — page 13 of the PDF only *lists* which clauses are nationally determined. Accordingly:

| NDP | Value used | Clause |
|---|---|---|
| α_cc | 1.0 | 3.1.6(1)P |
| C_Rd,c | 0.18 / γ_C | 6.2.2(1) |
| v_min | eq. (6.3N) | 6.2.2(1) |
| k₁ | 0.15 | 6.2.2(1) |
| cot θ | 1 ≤ cot θ ≤ 2.5, eq. (6.7N) | 6.2.3(2) |
| ν | eq. (6.6N) | 6.2.2(6) |

Every NDP is kept as a named argument in the code so that a National Annex can be substituted later
without touching a formula.

### Scope

ULS bending and shear, plus a mean-level comparison against the experiment. No detailing checks
(section 9.2) and no serviceability verifications (sections 7.3, 7.4).

## Results

Computed by `R65.py`:

| Case | Value |
|---|---|
| M_Rd (bending, design level) | 171.4 kNm — parabola-rectangle 3.1.7(1); the 3.1.7(3) stress block gives 172.1 kNm, 0.4 % apart |
| **Q6: P_d with stirrups** | **159.0 kN** — bending governs; P_k = P_d/1.5 = 106.0 kN |
| Shear at that load | V_Ed = 171.6 kN vs V_Rd = 262.2 kN at θ_opt = 39.8° (cot θ = 1.199) → ample, not governing |
| **Q7: P_d without stirrups** | **45.5 kN** plain 6.2.2, **53.4 kN** with the a_v < 2d allowance — a 66–71 % reduction |
| Mean level, horizontal branch | P = 224.8 kN vs R_exp = 259.2 → R_exp/R_calc = 1.153 |
| Mean level, inclined branch | P = 243.2 kN vs R_exp = 259.2 → R_exp/R_calc = 1.066 |

Two observations:

1. **a/d = 1.70**, so the point loads sit *inside* 2d of the supports (a_v = 1000 mm < 2d = 1174 mm)
   and the short-shear-span clauses 6.2.2(6) / 6.2.3(8) apply. Immaterial for Q6, where bending
   governs by a wide margin, but worth +17 % on Q7. `a_v` is taken as the support-to-load centre
   distance of 1000 mm, which is conservative: the true clear distance between the bearing plate
   edges is shorter and would give a smaller β.
2. The mean-level underestimate is **strain hardening**, confirmed. Switching from the horizontal
   top branch of 3.2.7(2)b to the inclined branch of 3.2.7(2)a moves R_exp/R_calc from 1.153 to
   1.066 — so most of the residual gap to the experiment is the hardening that the horizontal branch
   discards, not model error. This beam is very under-reinforced (ρ_l = 0.60 %) and the steel is
   highly ductile (A₁₀ = 23.1 %, f_um/f_ym = 1.49), so the effect is large.


## Implementation

A single file, [`R65.py`](R65.py): it runs as a plain script
(`python R65.py`).

It is built on [`structuralcodes`](https://github.com/fib-international/structuralcodes) — *fib*'s
own EC2 library — which supplies the material models (3.1, 3.2), the section analysis for M_Rd
(6.1 with the constitutive laws of 3.1.7) and the shear equations (6.2.2, 6.2.3). Only the
project-specific parts are written here: the mean→characteristic conversion, the four-point-bending
statics, the cot θ optimisation and the a_v < 2d reduction, which the library does not cover.

```
conda env create -f environment.yml
conda activate fibtg243
python R65.py
```

`structuralcodes` is not published on conda-forge, so `environment.yml` installs it from PyPI in a
`pip:` section while its dependencies come from conda-forge.
