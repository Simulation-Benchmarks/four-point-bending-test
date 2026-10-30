
# fibTG243

Eurocode-conform solution of the *fib* TG 2.4.3 test case.

## Goal

`fib` TG 2.4 / WP 2.4.3 poses a benchmark on the Rüsch & Rehm (1963) beam test **R65**: compute the
maximum **design value** of the applied point loads `P`, with stirrups (question 6) and without
stirrups in the shear spans (question 7).

This model answers the questions **without FEM**, by a classic clause-by-clause
design computation to DIN EN 1992-1-1:2011-01, as a reference against which a nonlinear analysis
can be judged.

| File | Role |
|---|---|
| [`../parameters.json`](../parameters.json) | the specimen data of the benchmark — shared with the ANSYS models |
| [`params.json`](params.json) | the variant to compute and the assumptions outside the benchmark data |
| [`ec2_design_calculation.py`](ec2_design_calculation.py) | the computation; `compute_P(params)` is the entry point |
| [`parameter_study.py`](parameter_study.py) | parameter study — run it for the results and their discussion |
| [`Snakefile`](Snakefile) | Snakemake workflow running the parameter study |
| [`run_benchmark.py`](run_benchmark.py) | runs the Snakemake workflow from Python |
| [`environment.yml`](environment.yml) | conda environment `fibtg243` for the computation |
| [`results/`](results/) | `metrics.json` (the benchmark answers) and `parameter_study.log` (the full study output) |
| [`additional_notes.md`](additional_notes.md) | working notes on the target `p_f = 10⁻⁶` and the safety formats |

## Usage

### Computation and study

```
conda env create -f environment.yml
conda activate fibtg243

# from eurocode_model/
python ec2_design_calculation.py              # one case, read from params.json
python ec2_design_calculation.py other.json   # any model parameter file

# from the repository root — parameter_study imports eurocode_model.ec2_design_calculation
python -m eurocode_model.parameter_study      # all investigations, with commentary
```

`python ec2_design_calculation.py` prints the governing load and everything behind it:

```
level = design   branch = elasticperfectlyplastic   case = with_stirrups
  materials      f_ck =   8.71 MPa   f_cd =  5.807 MPa   f_yk =  364.5 MPa   f_yd =  317.0 MPa
  self weight    g_k  = 4.6875 kN/m   M_g = 9.223 kNm   V_g = 9.375 kN   (gamma_G = 1.35)
  bending after EC2 6.1            M_R  =   171.41 kNm  ->  P =   159.0 kN
  shear after EC2 6.2.3          V_R  =   262.22 kN   ->  P =   249.6 kN   (theta = 39.90 deg, ...)
  ==>  P = 159.0 kN   (bending governs)
       P_k = P / 1.5 = 106.0 kN
```

### Workflow

The Snakemake workflow runs the parameter study and writes `results/metrics.json` and
`results/parameter_study.log`. It needs the `snakemake_environment` (see
[`../environment_snakemake.yml`](../environment_snakemake.yml)). The study itself still runs in
`fibtg243`, which the rule activates via `conda run`, so that environment has to exist as well.

```
conda activate snakemake_environment
python eurocode_model/run_benchmark.py              # from anywhere in the repository
python eurocode_model/run_benchmark.py --cores 2    # other arguments are passed on to snakemake
```

### Computing P for a specific case

Edit `params.json`, or copy it and pass the copy. Three keys select the case:

| Key | Values | Meaning |
|---|---|---|
| `level` | `design` \| `mean` \| `characteristic` | characteristic strengths / γ_M with factored actions; the measured means with γ_M = 1 and unfactored actions (for comparison against the experiment); or characteristic strengths with γ_M = 1 — R(x_k), which paired with `mean` gives the ECOV coefficient of variation V_R |
| `branch` | `elasticperfectlyplastic` \| `elasticplastic` | steel law: horizontal top branch 3.2.7(2)b, or the inclined branch 3.2.7(2)a carrying strain hardening |
| `case` | `with_stirrups` \| `without_stirrups` | shear by the 6.2.3 truss (question 6), or by the empirical 6.2.2 (question 7) |

So question 6 is `"level[-]": "design"`, `"case[-]": "with_stirrups"`; question 7 is the same with
`"case[-]": "without_stirrups"`.

## Structure

[`../parameters.json`](../parameters.json) holds everything that comes from the benchmark definition — geometry, reinforcement, the measured mean strengths. It is shared with the ANSYS models, so it uses their `"name[unit]"` keys in SI units;
`load_params` in `ec2_design_calculation.py` maps them to its own names (`b`, `h`, `d`, `fcm`, …) and
converts to N and mm. The stirrup area `asw` is derived from the stirrup diameter and the number of legs.

[`params.json`](params.json) holds what the benchmark does not give, in the same convention: the
assumed `epsuk`, the unit weight `gamma_concrete` of reinforced
concrete (EN 1991-1-1 Table A.1 — not the partial factor γ_C), plus the three keys above. The
measured failure load `R_exp` is a reference value, not an input, and is the constant `R_EXP` in
`ec2_design_calculation.py`.

Everything DIN EN 1992-1-1 fixes stays in `ec2_design_calculation.py` as a named module constant — γ_C,
γ_S, γ_G, γ_Q, α_cc, E_s, k₁, the `f_ck = f_cm − 8` relation, `z = 0.9d`, the cot θ window of
eq. (6.7N) — because those are properties of the code, not of the test. A National Annex can be
substituted without touching a formula.

`ec2_design_calculation.py` defines functions only, nothing runs at import time:

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
  traceable to the benchmark data or to EC2; `parameter_study.py` quantifies what it costs.
- **Nationally determined parameters — CEN recommended values.** DIN EN 1992-1-1:2011-01 is the
  German translation of EN 1992-1-1 and carries the recommended values; the German National Annex is
  a separate document and is not used here. So α_cc = 1.0, C_Rd,c = 0.18/γ_C, k₁ = 0.15,
  1 ≤ cot θ ≤ 2.5.
- **ε_uk = 0.10 is assumed.** The data sheet gives only A₁₀ = 23.1 %, the elongation after fracture,
  which is not ε_uk. The section never reaches it, so the horizontal branch is unaffected — but it
  sets the slope of the inclined branch.

## Results

Run `python -m eurocode_model.parameter_study` from the repository root, or the workflow via
`run_benchmark.py`. It follows the order the benchmark asks its questions in, with the reasoning
alongside each result:

| | investigation |
|---|---|
| **1** | **Q5** — mean level against the measured `R_exp = 259.2 kN`, beam as built |
| 1.1 | which mode governs at mean level, i.e. that the Q5 comparison is a flexural one |
| 1.2 | sensitivity of the inclined steel branch to the assumed `ε_uk` |
| **2** | **Q6** — maximum design value of `P`, beam as built |
| 2.1 | sensitivity of that answer to the assumptions EC2 does not fix |
| **3** | **Q7** — the same beam without stirrups in the shear spans |
| **4** | *additional* — the target `p_f = 10⁻⁶` named by Q6 and Q7, and the safety formats (PFM / GFM / ECOV) that deliver it |

The full output goes to `results/parameter_study.log` when run through the workflow. The answers
themselves are written to `results/metrics.json`, in kN per point load:

| Key | Value |
|---|---|
| `load_carrying_capacity_elasticperfectlyplastic [kN]` | Q5 — mean-level `P`, horizontal steel branch |
| `load_carrying_capacity_elasticplastic [kN]` | Q5 — mean-level `P`, inclined steel branch |
| `max_load_1e-6_p_f_stirrups [kN]` | Q6 — design `P`, beam as built |
| `max_load_1e-6_p_f_no_stirrups [kN]` | Q7 — design `P` without stirrups, without the a_v < 2d allowance |
