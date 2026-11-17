## R65: Experimental Setup

The experimental setup description and the values are obtained from (Rüsch & Rehm 1963, see [Reference](#reference)).

| Item | Value |
|---|---|
| Beam dimensions b / d / L | 30 / 62.5 / 451 cm |
| Span l | 400 cm, centre to centre of the supports |
| Supports | Support centres 25.5 cm from each beam end, on 30 cm wide bearing plates. In the dataset frame (x = 0 at the centre of support A): support A at x = 0, support B at x = 400 cm |
| Loading | Two point loads P at the quarter points, 100 cm from each support (x = 100 and 300 cm), on 20 cm wide load plates, giving a 200 cm constant-moment zone |


**General procedure that applies to R65:**

- **Specimen and supports.** Concrete strength W is measured on 20 cm cubes. The beams sat on supports that could rotate and slide freely. They were usually tested upside down (tension zone on top) so cracks were easier to see, and the reversed self-weight was included in the calculations.
- **Load steps.** Load was raised in steps. Each step added 500 kg/cm² to the calculated steel stress σ_eII. At load stage 5, the beam was cycled 14 times between self-weight plus loading rig and the load giving σ_eII = 2500 kg/cm². Steps were 20–50 min apart.
- **Measured Quantities:**
  - Concrete strain: MPA strain gauges with 50 cm gauge length (refer: [r65_edge_strain/README.md](r65_edge_strain/README.md))
  - Midspan deflection: roller gauges reading to 0.1 mm (refer: [r65_midspan_deflection/README.md](r65_midspan_deflection/README.md))

## R65: Specimen Data

| Parameter | Value | Approx. SI |
|---|---|---|
| Concrete strength W₂₈ | 205 kg/cm² | 20.1 MPa |
| Steel type | Hi-Bond, new form ("Bond-Stahl 2") | |
| Reinforcement | 2 Ø26 mm, A = 10.44 cm² as printed (nominal 2 Ø26 is 10.62 cm²) | |
| Reinforcement ratio μ = Fe/(b·h) | 0.60 % | |
| Yield strength σ_s | 4090 kg/cm² | 401 MPa |
| Tensile strength σ_B | 6080 kg/cm² | 596 MPa |
| Elongation at fracture δ₁₀ | 23.1 % | |
| Rib geometry | rib height 0.046Ø, rib spacing 0.58Ø, rib inclination 57°, rib length 1.46Ø | |
| Section values | h = 58.5 cm, x = 20.0 cm, z = 51.9 cm | |
| Steel stress at the load points | σ_eII = 0.185·P kg/cm² (P in kg) | |
| Self-weight | g = 0.47 t/m | 4.6 kN/m |
| Age at test | 14 days | |

## Reference

Rüsch, H.; Rehm, G. (1963): *Versuche mit Betonformstählen, Teil I.* Deutscher Ausschuss für Stahlbeton, Heft 140.

