# ANSYS models

Fully parameterized APDL input files for the reinforced concrete beam in a 4 point bending
setup using two symmetry planes. Two model types:

* `drucker_prager`: concrete with Drucker-Prager material model (and SOLID185 elements)
* `microplane`: concrete with Microplane material model (and CPT215 elements)

The ANSYS simulations are displacement-controlled: displacement is applied at the loading points, ramping up to the maximum displacement given by `"displacement[m]"` in `ansys_models/common/parameters.json`, and the run continues until that target
displacement is reached or the solver fails to converge.

### Input/Output

* Input: benchmark parameters (geometry, reinforcement, material strengths) from
  `../parameters.json` (see [Benchmark parameters](../README.md#benchmark-parameters)), plus the
  ANSYS-specific mesh, loading, solver and material parameters from
  `common/parameters.json` and `<model>/parameters.json` (see [Parameters](#parameters)).
* Output: Force and vertical displacement at the loading point, vertical displacement at the midspan of the beam, stored in `results/<model>/REINF_CONC_BEAM.txt`.
  This is a whitespace-delimited text table with a header line
  `--Kraft [N]--  --u_y Pilot [m]--  u_y Mitte [m]` followed by one row per
  load substep, with three columns: applied force [N], pilot-node
  displacement [m], and midspan displacement [m] (`u_y Mitte` = deflection at
  midspan).

## Running

First set up the `snakemake_environment` conda environment (snakemake + Jinja2, see `../environment_snakemake.yml`):

```
conda env create -f ../environment_snakemake.yml
conda activate snakemake_environment
```

Then, from within `ansys_models/`, run:

```
python run_benchmark.py                   # drucker_prager
python run_benchmark.py --model microplane
python run_benchmark.py --model both
```

Or call snakemake directly, e.g. `snakemake --cores 1 --config model=microplane`
(the default model is set in `config.yaml`).
To render only the input file (no ANSYS run):
`snakemake results/<model>/input.mac --cores 1 --config model=<model>`.
The rendered `results/<model>/input.mac` can also be run manually in ANSYS from
within `results/<model>/`.

The path to the ANSYS executable is set by `ANSYS_EXE` in `Snakefile`.

## Workflow

`common/input.mac.j2` is a Jinja template, and Snakemake renders the JSON values into it
to create the ANSYS entry point `results/<model>/input.mac`. No intermediate parameter
files are written.

1. `render_input`: merges `../parameters.json` (benchmark), `common/parameters.json` and
   `<model>/parameters.json` and validates the result: keys must be `name[unit]` with a
   valid APDL name, values must be numbers, and no name may be defined twice across the
   three files. It then renders `common/input.mac.j2` into `results/<model>/input.mac`.
2. `run_ansys`: runs ANSYS in batch mode on the rendered `input.mac` inside
   `results/<model>/`. It `/INPUT`s `common/prep.mac`, `solution.mac` and `post.mac`.
   `prep.mac` and `material.mac` pull in `<model>/element.mac` and
   `<model>/concrete_model.mac` through `%MAT_MODEL%`.

The rendered `input.mac` records every parameter value used in that run.

## Parameters

The ANSYS models read three JSON files:

* `../parameters.json`: benchmark parameters shared by all model types (geometry,
  reinforcement, material strengths), see [Benchmark parameters](../README.md#benchmark-parameters)
* `common/parameters.json`: parameters common to both ANSYS models
* `<model>/parameters.json`: parameters specific to one ANSYS model

Each file is `{group: {"name[unit]": value}}`, for example `"ele_length[m]": 0.05`.
Units are SI. Dimensionless parameters use `[-]`. The `[unit]` part only documents the
value: it is stripped before rendering, so `name` becomes the APDL scalar parameter. Group
names become comments in the rendered file. A group may appear in several files (e.g.
`concrete`), but each parameter only once.

### Common ANSYS parameters (`common/parameters.json`)

| Group | Parameter | Unit | Description |
|---|---|---|---|
| `geometry` | `height_load` | m | thickness of the loading plate |
| | `height_supp` | m | thickness of the support plate |
| | `num_cuts_12cm` | - | number of regular stirrup spacings (`x_stirrup_3`) |
| `mesh` | `ele_length` | m | element edge length |
| `loading` | `displacement` | m | target vertical displacement of the loading point (negative = downwards) |
| `solver` | `step_init` | - | initial number of substeps (`NSUBST`) |
| | `step_max` | - | maximum number of substeps |
| | `step_min` | - | minimum number of substeps |
| `reinforcement_steel` | `e_reinf` | N/m^2 | Young's modulus of the reinforcement |
| | `nu_reinf` | - | Poisson's ratio of the reinforcement |
| `plate_steel` | `e_supp` | N/m^2 | Young's modulus of the support and loading plates |
| | `nu_supp` | - | Poisson's ratio of the support and loading plates |
| `concrete` | `nu_c` | - | Poisson's ratio of the concrete |

### Drucker-Prager parameters (`drucker_prager/parameters.json`)

Used by `TB,CONCR,...` in `drucker_prager/concrete_model.mac`. The dilatation and HSD
parameters are only used when `switch_hsd` = 1.

| Group | Parameter | Unit | Description |
|---|---|---|---|
| `dilatation` | `del_t` | - | dilatancy parameter in tension (`DILA`) |
| | `del_c` | - | dilatancy parameter in compression (`DILA`) |
| `hsd` | `omega_ci` | - | relative stress at start of nonlinear hardening (HSD2, HSD6) |
| | `omega_cr` | - | residual relative stress in compression (HSD2, HSD6) |
| | `omega_tr` | - | residual relative stress in tension (HSD2, HSD6) |
| | `kappa_cr` | - | plastic strain at transition to residual compressive strength (HSD6) |
| | `kappa_tr` | - | plastic strain at transition to residual tensile strength (HSD6) |
| | `omega_cu` | - | relative stress at transition from power law to exponential softening (HSD2) |
| | `G_ft` | N/m | mode I fracture energy (HSD2) |
| `switches` | `switch_hsd` | - | 0 means no HSD, 1 means with HSD |
| | `switch_dp` | - | only used when `switch_hsd` = 1: 0 means HSD2 (exponential), 1 means HSD6 (linear) |

### Microplane parameters (`microplane/parameters.json`)

Used by `TB,MPLA,...` in `microplane/concrete_model.mac`.

| Parameter | Unit | Description |
|---|---|---|
| `sigVc0` | N/m^2 | volumetric stress at onset of compressive cap (`DPC`) |
| `R_MP` | - | cap aspect ratio (`DPC`) |
| `D_MP` | N^2/m^4 | cap hardening parameter (`DPC`) |
| `Rt` | - | tension cap aspect ratio (`DPC`) |
| `gamt0` | - | damage threshold in tension (`DPC`) |
| `gamc0` | - | damage threshold in compression (`DPC`) |
| `betat` | - | damage evolution parameter in tension (`DPC`) |
| `betac` | - | damage evolution parameter in compression (`DPC`) |
| `c_MP` | m^2 | nonlocal interaction range (`NLOCAL`) |
| `m_MP` | - | over-nonlocal averaging parameter (`NLOCAL`) |

### Derived parameters

Derived quantities stay in APDL: `eps_ry`, `R_c`, `R_t` and `R_b` are in
`common/input.mac.j2`, and `kappa_cm` and `kappa_cu` are in
`drucker_prager/concrete_model.mac`.
