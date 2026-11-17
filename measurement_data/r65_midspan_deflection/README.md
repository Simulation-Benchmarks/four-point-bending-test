# R65 midspan deflection

This folder holds the measured midspan deflection of beam R65. The values come from the curve "Durchbiegung f in Balkenmitte" (report p. 129, Rüsch/Rehm, DAfStb Heft 140, 1963). The report publishes the stress vs. deflections plot, which was digitized from the scan.

| File | Content |
|---|---|
| `sensors.csv` | The deflection gauge: `sensor_id, measurement, x_cm, y_cm, z_cm, instrument, resolution_mm` |
| `stress_displacement.csv` | One row per reading: `sensor_id, reading_id, stage_id, reading_no, sigma_eII_kg_cm2, sigma_source, sigma_eII_digitized_kg_cm2, f_mm, note` |
| `load_displacement.csv` | The same readings, with σ_eII replaced by the load (computed using the analytical formula): `sensor_id, reading_id, stage_id, reading_no, P_kg, P_total_kg, M_mt, load_source, f_mm, note` |
| `flags.csv` | `reading_id, stage_id, note`: readings that need care, and why |
| `checks.txt` | Plausibility report, including a cross-check against [r65_edge_strain](../r65_edge_strain/) |

`f_mm` is the midspan deflection in mm, positive in the direction of the load. It is measured from the reading at the plot origin.

### Gauge

The midspan deflection was read with a roller deflection gauge (*Rollenmeßapparat*) graduated in 0.1 mm. This is stated in section 4.4 p. 8, Rüsch/Rehm, DAfStb Heft 140, 1963.

- The gauge sits at x = 200 cm, in the coordinate frame of `r65_edge_strain`.
- Where it was attached across the section is not shown, so `y_cm` and `z_cm` are empty.

### Readings and load stages

The curve has 15 markers. Stage ids follow `r65_edge_strain` (stage n raises σ_eII by 500 kg/cm²):

| stage_id | Readings | σ_eII (kg/cm²) | Meaning |
|---|---|---|---|
| `LS0` | 1 | 0 | Plotted origin, the reference reading |
| `PC1`, `PC2` | 1 each | ≈ 470, 700 (digitized) | Readings before cracking. They are not on the 500 kg/cm² grid, and the report does not list them. |
| `LS2`, `LS3`, `LS4`, `LS6`, `LS7` | 2 each | 500·n | Two readings at the same load (`reading_no` 1 and 2) |
| `LS5`, `LS5c14` | 1 each | 2500 | Stage 5 before and after the 14 load cycles |

**Note**:

The `sigma_source` column in [stress_displacement.csv](stress_displacement.csv) tells you where the value in `sigma_eII_kg_cm2` comes from. Each row has two stress values:

| Column | Meaning |
|---|---|
| `sigma_eII_kg_cm2` | The σ_eII to use for analysis. |
| `sigma_eII_digitized_kg_cm2` | The σ_eII read from the marker position on the scanned plot. Kept for reference. |

`stage_nominal`: σ_eII is the nominal value of the load stage given in the report (1000, 1500, 2000, … kg/cm²). The report gives the stress for these stages, so that exact value is used. The digitized position is kept only as a check. For example, reading R06 was read off the plot at 1457 kg/cm², but its stage value is 1500 kg/cm². Across all stage readings the largest gap is 43 kg/cm², within the 50 kg/cm² tolerance.

`digitized`: The report gives no stage value for these readings, so σ_eII is the stress read from the marker position on the scanned curve. The value is rounded to the nearest 5 kg/cm² (e.g. 471 → 470). This applies to PC1 and PC2 (readings R02 and R03). They were taken before cracking at about 470 and 700 kg/cm² (P ≈ 2.5 t and 3.8 t). The report says it sometimes loaded in finer steps before the first crack (σ_eR = 950 kg/cm²), but it does not list those steps.

**Special case - the origin (R01):** R01 is labelled `stage_nominal` with σ_eII = 0 and f = 0, because it is the reference reading at the axis crossing. Its digitized value of 22 kg/cm² is drawing noise.

**Deflection is always digitized:** `sigma_source` describes only the stress value. `f_mm` is digitized in every row, because the report publishes the deflections only as a plotted curve ("Durchbiegung f in Balkenmitte", report p. 129).

**Remarks:**

**About the pairs.** The two readings at stage 5 are documented: the 14 load cycles at σ_eII = 2500 kg/cm² (setup document §4.3), and the crack tables mark them as 2,5 and 2,5¹⁴. The pairs at the other stages are not explained in the report.

The most likely explanation is a reading when the stage was reached and another at the end of the 20–50 minute hold, the difference being creep. Three things point that way:

- the second reading is always the larger one;
- the gaps are 0.12–0.35 mm;
- the gap after the 14 cycles is clearly larger, at 0.60 mm.

This is an interpretation. It is not stated in the report.

**About PC1/PC2.** The digitized σ_eII values (471 and 700 kg/cm²) correspond to P ≈ 2.5 t and 3.8 t. The report says it sometimes loaded in finer steps before the first crack (σ_eR = 950 kg/cm²), but does not give them. For these two readings σ_eII is the digitized value, rounded to 5 kg/cm² (`sigma_source = digitized`). For all other readings it is the stage value (`stage_nominal`).

### Load

The load is defined as in `r65_edge_strain/load_stages.csv`:

- **P** = σ_eII / 0.185 (report p. 126) is the effective load per load point. It includes self-weight. The jack force is not reported.
- **P_total** = 2P, both load points.
- **M** = P × 1.0 m, the moment in the constant-moment zone.

### Method of data extraction
  1. The embedded scan image was extracted, and the σ_eII and f grid lines were calibrated in the same way as for the strains.
  2. Each of the 15 circle markers was located by normalized cross-correlation with ring templates, refined to subpixel accuracy.
  3. Each marker centre was converted to f (mm) and σ_eII (kg/cm²).


### Caveats

- **Resolution of the gauge.** The gauge was graduated in 0.1 mm. `f_mm` is given to 0.01 mm because that is what the drawing resolves, but the measurement itself is only good to about 0.1 mm. On top of that comes the accuracy of the hand-drawn plot.
- **Markers drawn off the grid line.** Some markers sit 2–3 px off their grid line, up to 43 kg/cm² at LS3. This is a drafting inaccuracy, which is why σ_eII uses the stage value.
- **Origin.** The origin marker sits on the axis crossing. Its digitized σ (22 kg/cm²) is drawing noise. It is the reference reading, with σ_eII = 0 and f = 0.
- **Cross-check with the edge strains.** `checks.txt` compares f with the deflection obtained by integrating the curvatures from `r65_edge_strain` (virtual work, unit load at midspan). They agree within about 10 %, from 0.70 mm at LS2 to 7.7 mm at LS7, against 0.68–0.80 and 8.3–8.7 mm plotted. The strain-based value is lower at high loads, which is expected: the gauges sit inside the edges, and shear deformation is not included.

