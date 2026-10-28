# ANSYS REINF BEAM

Fully parameterized APDL input files for reinforced concrete beam in a 4 point bending setup using two symmetry planes.

## Model

Two different model types

* `drucker_prager`: concrete with Drucker-Prager material model (and SOLID185 elements)
* `microplane`: concrete with Microplane material model (and CPT215 elements)

The simulation is displacement-controlled: displacement is applied at the loading
points, ramping up to the maximum displacement given by `"displacement[m]"` in
`ansys_models/common/parameters.json`, and the run continues until that target
displacement is reached or the solver fails to converge.

### Input/Output

* Input: geometry, mesh, loading, solver and material parameters from JSON files
  (`ansys_models/common/parameters.json` and `ansys_models/<model>/parameters.json`,
  see [Parameter files](#parameter-files)).
* Output: Force and vertical displacement at the loading point, vertical displacement at the midspan of the beam, stored in `ansys_models/results/<model>/REINF_CONC_BEAM.txt`.
  This is a whitespace-delimited text table with a header line
  `--Kraft [N]--  --u_y Pilot [m]--  u_y Mitte [m]` followed by one row per
  load substep, with three columns: applied force [N], pilot-node
  displacement [m], and midspan displacement [m] (`u_y Mitte` = deflection at
  midspan).

## Running

First set up the `snakemake_environment` conda environment (snakemake + Jinja2, see `environment_snakemake.yml`):

```
conda env create -f environment_snakemake.yml
conda activate snakemake_environment
```

Then, from within `ansys_models/`, run:

```
cd ansys_models
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

The path to the ANSYS executable is set by `ANSYS_EXE` in `ansys_models/Snakefile`.

## Workflow

`common/input.mac.j2` is a Jinja template, and Snakemake renders the JSON values into it
to create the ANSYS entry point `results/<model>/input.mac`. No intermediate parameter
files are written.

1. `render_input`: merges `common/parameters.json` with `<model>/parameters.json` and
   validates the result: keys must be `name[unit]` with a valid APDL name, values must be
   numbers, and no name may be defined twice. It then renders `common/input.mac.j2` into
   `results/<model>/input.mac`.
2. `run_ansys`: runs ANSYS in batch mode on the rendered `input.mac` inside
   `results/<model>/`. It `/INPUT`s `common/prep.mac`, `solution.mac` and `post.mac`.
   `prep.mac` and `material.mac` pull in `<model>/element.mac` and
   `<model>/concrete_model.mac` through `%MAT_MODEL%`.

The rendered `input.mac` records every parameter value used in that run.

## Parameter files

Each JSON file is `{group: {"name[unit]": value}}`, for example `"length_span[m]": 4`.
Units are SI. Dimensionless parameters use `[-]`. The `[unit]` part only documents the
value: it is stripped before rendering, so `name` becomes the APDL scalar parameter. Group
names become comments in the rendered file. Derived quantities stay in APDL: `eps_ry`, `R_c`,
`R_t` and `R_b` are in `input.mac.j2`, and `kappa_cm` and `kappa_cu` are in
`drucker_prager/concrete_model.mac`.

`drucker_prager/parameters.json` switches:
- `switch_hsd`: 0 means no HSD, 1 means with HSD.
- `switch_dp` (only used when `switch_hsd` = 1): 0 means HSD2 (exponential), 1 means HSD6 (linear).

## Repository layout

```
environment_snakemake.yml     conda environment (snakemake + Jinja2)
ansys_models/
  Snakefile                   workflow: render_input, run_ansys
  config.yaml                 default model (drucker_prager | microplane)
  run_benchmark.py            runs the workflow for one or both models
  common/
    input.mac.j2              Jinja template for the ANSYS entry point
    parameters.json           shared geometry/mesh/loading/solver/material parameters
    prep.mac                  geometry and mesh, element type from <model>/element.mac
    material.mac              steel/plate materials, concrete from <model>/concrete_model.mac
    solution.mac              boundary/symmetry conditions, nonlinear static solve
    post.mac                  writes force/displacements per substep to REINF_CONC_BEAM.txt
  drucker_prager/
    parameters.json           Drucker-Prager parameters and switches
    element.mac               SOLID185 element type
    concrete_model.mac        TB,CONCR,...,DP with HSD2/HSD6 hardening-softening
  microplane/
    parameters.json           Microplane parameters
    element.mac               CPT215 element type
    concrete_model.mac        TB,MPLA,...,DPC and NLOCAL data
  results/<model>/            rendered input.mac and ANSYS output
```
