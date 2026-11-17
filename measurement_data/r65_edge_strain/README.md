# R65 concrete edge strains

This folder holds the measured concrete edge strains of beam R65. The strains come from the figure "Randverformungsverlauf im Längsschnitt" (report p. 127, Rüsch/Rehm, DAfStb Heft 140, 1963). The report publishes the stress vs. strain plot for different sensors, so they were digitized from the scan.

| File | Content |
|---|---|
| `sensors.csv` | One row per strain gauge: `sensor_id, measurement, x_start_cm, x_end_cm, x_mid_cm, y_cm, z_cm, gauge_length_cm` |
| `load_stages.csv` | `stage_id, sigma_eII_kg_cm2, P_kg, M_mt, note` |
| `strains.csv` | `sensor_id` plus one column per `stage_id`; concrete strain in **permille**, tension positive, compression negative |
| `flags.csv` | `sensor_id, stage_id, note`: values that need care, and why |
| `checks.txt` | Plausibility report |

### Coordinate frame

The frame describes the beam in its structural orientation, not the upside-down test position.

- **x** runs along the beam from the centre of support A (0) to support B (400 cm). The load points are at x = 100 and 300 cm, so the constant-moment zone is x = 100–300 cm.
- **y** runs across the width: 0 is the front face (Vorderseite) and 30 is the back face (Rückseite).
- **z** runs over the height: 0 is the tension (bottom) edge and 62.5 is the compression (top) edge.

### Sensors

The beam has 32 demountable mechanical strain gauges (Setzdehnungsmesser), each with a 50 cm gauge length. They are arranged in 4 rows of 8 gauges, covering the span gap-free from A to B:

| Row | z (cm) | Measuring points A→B | Sensor ids |
|---|---|---|---|
| Front face, tension (3.5 cm from the edge) | 3.5 | 1…8 | T01…T08 |
| Back face, tension | 3.5 | 16…9 | T16…T09 |
| Front face, compression (1.0 cm from the edge) | 61.5 | 1…8 | C01…C08 |
| Back face, compression | 61.5 | 16…9 | C16…C09 |

The number in a sensor id is the measuring-point number used in the report. Gauge k, counted from A, spans x = 50(k−1) … 50k cm. A strain value is the mean strain over that span. The plot draws it at the midpoint of the span.

### Load stages

Load stage n raises the calculated steel stress σ_eII by 500 kg/cm². The figure plots six stages: LS2, LS3, LS4, LS5c14, LS6 and LS7.

- **LS5c14** is stage 5 after the 14 load cycles. Stage 5 before the cycles is not plotted.
- **P** = σ_eII / 0.185 (report p. 126). This is the effective load per load point, including self-weight. The jack force is not reported.
- **M** = P × 1.0 m, the moment in the constant-moment zone. It already includes self-weight. The report's values at cracking and at maximum load (M = 26.5 mt with Q = 26.5 t) are consistent with this.

### Method of data extraction
  1. The embedded scan image was extracted at native resolution.
  2. Every grid line was calibrated with two pixel points, so the strain axis is interpolated piecewise-linearly between neighbouring grid lines.
  3. Each polyline segment was traced along its central 70 % with a robust straight-line fit.
  4. The value at each measuring point is the mean of the left and right segment lines, evaluated on the grid line.

### Caveats

- **Peaks.** At sharp peaks the two hand-drawn lines do not meet exactly on the grid line. The value is their mean. Where they differ by more than 0.02 ‰, the value is flagged (up to 0.064 ‰, at T14/LS7).
- **End gauges** (T01, T08, T09, T16, C01, C08, C09, C16). These values are small and the least reliable, because the lines nearly overlap at the end vertices. Some of them are not monotonic in load; those cases are flagged.
- **C16 / LS6 is missing.** The MP16→MP15 segment of the LS6 compression curve is not drawn in the figure, so C15/LS6 uses only its right segment.
- **What the plausibility checks found.**
  - At LS7 the mean tension strain in the constant-moment zone is 1.71 ‰. This is close to σ_eII / E_s = 1.67 ‰.
  - Front and back agree to within about 0.05 ‰ in compression. In tension they differ by up to about 0.19 ‰ at LS7, which reflects the local cracking.
  - The mean strain against σ_eII curve on p. 129 was not cross-checked automatically.
- **Accuracy of the drawing itself.** These are values read from a drawing, so their accuracy is limited by how carefully it was drawn. That is likely of the order of 0.01–0.03 ‰, more than the digitizing error.

