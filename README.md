# REINF BEAM 4 POINT BENDING

Benchmark of a reinforced concrete beam in a 4 point bending setup. The ANSYS models use
fully parameterized APDL input files and two symmetry planes.

## Model

Three different model types

* `drucker_prager`: ANSYS, concrete with Drucker-Prager material model (and SOLID185 elements)
* `microplane`: ANSYS, concrete with Microplane material model (and CPT215 elements)
* `eurocode`: TODO: description

## Benchmark parameters

`parameters.json` holds the benchmark data shared by all model types. The file is
`{group: {"name[unit]": value}}`, for example `"length_span[m]": 4`. Units are SI.
Dimensionless parameters use `[-]`.

`geometry`:

| Parameter | Unit | Description |
|---|---|---|
| `length_span` | m | span between the support centres |
| `length_cant` | m | overhang of the beam beyond the support centre |
| `length_load` | m | distance from midspan to the loading point |
| `height_tot` | m | total height of the beam |
| `depth_tot` | m | total width of the beam |
| `d_eff` | m | effective depth (top fibre to lower reinforcement) |
| `height_cover` | m | vertical distance from the top/bottom surface to the longitudinal bar axis |
| `width_cover` | m | lateral distance from the side surface to the longitudinal bar axis |
| `width_supp` | m | width of the support plate along the span |
| `width_load` | m | width of the loading plate along the span |
| `x_stirrup_1` | m | distance from the beam end to the first stirrup |
| `x_stirrup_2` | m | distance from the first to the second stirrup |
| `x_stirrup_3` | m | regular stirrup spacing after the second stirrup |

`reinforcement`:

| Parameter | Unit | Description |
|---|---|---|
| `diam_reinf_lower` | m | diameter of the lower longitudinal bars |
| `n_reinf_lower` | - | number of lower longitudinal bars |
| `diam_reinf_upper` | m | diameter of the upper longitudinal bars |
| `n_reinf_upper` | - | number of upper longitudinal bars |
| `diam_reinf_stir` | m | stirrup diameter |
| `n_legs_stir` | - | number of stirrup legs |

`reinforcement_steel`:

| Parameter | Unit | Description |
|---|---|---|
| `sig_ry` | N/m^2 | yield strength |
| `sig_ru` | N/m^2 | ultimate strength |
| `eps_ru` | - | strain at ultimate strength |

`concrete`:

| Parameter | Unit | Description |
|---|---|---|
| `e_c` | N/m^2 | Young's modulus |
| `sig_cc` | N/m^2 | uniaxial compressive strength |
| `sig_ct` | N/m^2 | uniaxial tensile strength |

`d_eff`, `n_reinf_lower`, `n_reinf_upper` and `n_legs_stir` are not used by the ANSYS
models: their symmetry quarter contains one lower bar, one upper bar and one stirrup leg,
placed explicitly from the cover and stirrup position parameters.
