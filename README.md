
# fibTG243

Eurocode-conform solution of the *fib* TG 2.4.3 test case.

## Goal

`fib` TG 2.4 / WP 2.4.3 poses a benchmark on the Rüsch & Rehm (1963) beam test **R65**: compute the
maximum **design value** of the applied point loads `P`, with stirrups (question 6) and without
stirrups in the shear spans (question 7).

The benchmark asks for it by NLFEA. This repo deliberately answers the same two questions
**without FEM**, by a classic clause-by-clause design computation to DIN EN 1992-1-1:2011-01, as a
reference against which a nonlinear analysis can be judged.

| File | Role |
|---|---|
| [`params.yaml`](params.yaml) | the specimen and the variant to compute — the only input |
| [`R65.py`](R65.py) | the computation; `compute_P(params)` is the entry point |
| [`R65_study.py`](R65_study.py) | parameter study — run it for the results and their discussion |
| `2026-07_fib_TG243_NLFEA_Example.pdf` | the benchmark task and the R65 specimen data |
| `DINEN1992-1-1.pdf` | DIN EN 1992-1-1:2011-01 — the design standard |
| `2026-05-26_fibTG243_4rd_Meeting_Safety_concepts.pdf` | TG background on safety formats |

## Usage

```
conda env create -f environment.yml
conda activate fibtg243

python R65.py                 # one case, read from params.yaml
python R65.py other.yaml      # any parameter file
python R65_study.py           # all investigations, with commentary
```

`python R65.py` prints the governing load and everything behind it:

```
level = design   branch = elasticperfectlyplastic   case = with_stirrups
  materials      f_ck =   8.71 MPa   f_cd =  5.807 MPa   f_yk =  364.5 MPa   f_yd =  317.0 MPa
  self weight    g_k  = 4.6875 kN/m   M_g = 9.223 kNm   V_g = 9.375 kN   (gamma_G = 1.35)
  6.1            M_R  =   171.41 kNm  ->  P =   159.0 kN
  6.2.3          V_R  =   262.16 kN   ->  P =   249.5 kN   (theta = 39.84 deg, cot = 1.199, ...)
  ==>  P = 159.0 kN   (bending governs)
       P_k = P / 1.5 = 106.0 kN
```

### Computing P for a specific case

Edit `params.yaml`, or copy it and pass the copy. Three keys select the case:

| Key | Values | Meaning |
|---|---|---|
| `level` | `design` \| `mean` | characteristic strengths / γ_M with factored actions, or the measured means with γ_M = 1 and unfactored actions (for comparison against the experiment) |
| `branch` | `elasticperfectlyplastic` \| `elasticplastic` | steel law: horizontal top branch 3.2.7(2)b, or the inclined branch 3.2.7(2)a carrying strain hardening |
| `case` | `with_stirrups` \| `without_stirrups` | shear by the 6.2.3 truss (question 6), or by the empirical 6.2.2 (question 7) |

So question 6 is `level: design`, `case: with_stirrups`; question 7 is the same with
`case: without_stirrups`.

## Structure

`params.yaml` holds everything that comes from the benchmark definition — geometry, reinforcement,
the measured mean strengths, the unit weight of the concrete — each with its unit and a one-line
description, plus the three keys above.

Everything DIN EN 1992-1-1 fixes stays in `R65.py` as a named module constant — γ_C, γ_S, γ_G, γ_Q,
α_cc, E_s, k₁, the `f_ck = f_cm − 8` relation, `z = 0.9d`, the cot θ window of eq. (6.7N) — because
those are properties of the code, not of the test. A National Annex can be substituted without
touching a formula.

`R65.py` defines functions only, nothing runs at import time:

`make_materials` → `bending_resistance` → `self_weight` → `P_from_moment` / `P_from_shear` →
`shear_resistance` (6.2.3) / `shear_resistance_no_stirrups` (6.2.2) → **`compute_P`**

`compute_P(params)` returns a dict, so a benchmark platform can consume the result without parsing
text; `format_result` renders that same dict for the terminal. Load factors follow the level:
γ_G = 1.35 at `level: design`, γ_G = 1.0 at `level: mean`.

Built on [`structuralcodes`](https://github.com/fib-international/structuralcodes) — *fib*'s own EC2
library — which supplies the material models (3.1, 3.2), the section analysis for M_Rd (6.1 with the
constitutive laws of 3.1.7) and the shear equations (6.2.2, 6.2.3). Only the project-specific parts
are written here: the mean→characteristic conversion, the four-point-bending statics, the cot θ
optimisation and the a_v < 2d reduction.

## Decisions behind the numbers

The specimen data is given as **mean** values; EC2 is written in **characteristic** values. How that
gap is bridged is the one substantive choice in the whole computation.

- **Concrete — source-backed.** Table 3.1 supplies the inverse relations directly:
  `f_ck = f_cm − 8 = 8.71 MPa` and `f_ctk;0,05 = 0.7 f_ctm`. That the fib data sheet was generated
  with these same relations is confirmed by `22·(f_cm/10)^0.3 = 25.66 GPa`, reproducing the given
  `E_cm` exactly. Note `f_ck = 8.71 MPa` sits **below C12/15**, the lowest row of Table 3.1; EC2 has
  no structural minimum class (Table E.1N is a durability requirement), so it is used as derived and
  not rounded up, which would be unconservative.
- **Reinforcement — assumption, outside EC2.** EC2 gives no mean→characteristic relation for rebar,
  and Table 3.1's factor 0.7 is specific to the concrete tensile strength. The code-calibration bias
  factor is used instead: `f_yk = f_ym/1.1 = 364.5 MPa`. This is the only material value not
  traceable to a document in this repo; `R65_study.py` quantifies what it costs.
- **Nationally determined parameters — CEN recommended values.** `DINEN1992-1-1.pdf` is the German
  translation of EN 1992-1-1 and carries the recommended values; the German National Annex is a
  separate document, not present here. So α_cc = 1.0, C_Rd,c = 0.18/γ_C, k₁ = 0.15, 1 ≤ cot θ ≤ 2.5.
- **ε_uk = 0.10 is assumed.** The data sheet gives only A₁₀ = 23.1 %, the elongation after fracture,
  which is not ε_uk. The section never reaches it, so the horizontal branch is unaffected — but it
  sets the slope of the inclined branch.

**Scope:** ULS bending and shear, plus a mean-level comparison against the experiment. No detailing
checks (section 9.2) and no serviceability verifications (7.3, 7.4).

## Results

Run `python R65_study.py`. It prints the two benchmark answers, the mean-level comparison against
the measured `R_exp = 259.2 kN`, which failure mode governs, and the sensitivity of the answer to
the assumptions EC2 does not fix — each with the reasoning alongside.

