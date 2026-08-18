import numpy as np
import matplotlib.pyplot as plt

DATA_FILE = "REINF_CONC_BEAM.txt"
DIGITIZED_FILE = "digitized_data.txt"
PARAMS_FILE = "parameters_material.txt"
FAILURE_LOAD_KN = 259.0


def parse_material_params(filepath):
    """Parse 'name = expr ! comment' lines into a dict of evaluated values.

    Expressions may reference variables defined earlier in the file
    (e.g. "eps_ry = sig_ry/e_reinf"), mirroring the APDL parameter file.
    """
    params = {}
    with open(filepath, "r") as f:
        for line in f:
            code = line.split("!", 1)[0].strip()
            if "=" not in code:
                continue
            name, expr = code.split("=", 1)
            name, expr = name.strip(), expr.strip()
            if not name or not expr:
                continue
            try:
                params[name] = eval(expr, {"__builtins__": {}}, params)
            except (SyntaxError, NameError, ZeroDivisionError):
                continue
    return params


def format_concrete_info(p):
    """Build info-box text for the concrete parameters currently active in
    parameters_material.txt (linear params + the model selected by switch_model)."""
    lines = ["Concrete Parameters"]
    lines.append(f"e_c = {p['e_c']/1e9:.1f} GPa   nu_c = {p['nu_c']:.2f}")
    lines.append(f"sig_cc = {p['sig_cc']/1e6:.2f} MPa   sig_ct = {p['sig_ct']/1e6:.2f} MPa")

    if p.get("switch_model") == 0:
        lines.append("Model: Drucker-Prager")
        lines.append(
            f"R_c = {p['R_c']/1e6:.2f} MPa   R_t = {p['R_t']/1e6:.2f} MPa   R_b = {p['R_b']/1e6:.2f} MPa"
        )
        lines.append(f"del_t = {p['del_t']}   del_c = {p['del_c']}")
        if p.get("switch_hsd") == 1:
            variant = "HSD6 (linear)" if p.get("switch_dp") == 1 else "HSD2 (exponential)"
            lines.append(f"HSD: {variant}")
            lines.append(
                f"omega_ci = {p['omega_ci']}   omega_cr = {p['omega_cr']}   omega_tr = {p['omega_tr']}"
            )
            if p.get("switch_dp") == 1:
                lines.append(f"kappa_cr = {p['kappa_cr']}   kappa_tr = {p['kappa_tr']}")
            else:
                lines.append(f"omega_cu = {p['omega_cu']}   kappa_cu = {p['kappa_cu']:.5f}")
                lines.append(f"G_ft = {p['G_ft']:.0f}")
        else:
            lines.append("HSD: off")
    else:
        lines.append("Model: Microplane (M7)")
        lines.append(
            f"sigVc0 = {p['sigVc0']/1e6:.2f} MPa   R_MP = {p['R_MP']}   D_MP = {p['D_MP']:.1e}"
        )
        lines.append(f"Rt = {p['Rt']}   gamt0 = {p['gamt0']}   gamc0 = {p['gamc0']:.1e}")
        lines.append(f"betat = {p['betat']:.1e}   betac = {p['betac']:.1e}")
        lines.append(f"c_MP = {p['c_MP']:.1e}   m_MP = {p['m_MP']}")

    return "\n".join(lines)

# Data file layout: 4 header/blank lines, then whitespace-separated
# columns "Kraft [N]" (force) and "Verschiebung [m]" (deflection).
force_n, deflection_load, deflection_middle = np.loadtxt(DATA_FILE, skiprows=4, unpack=True)

# Force and deflection are stored as negative values (FEM sign convention).
# Convert to magnitudes for a conventional load-deflection plot.
force_kn = np.abs(force_n) / 1000.0
deflection_load_mm = np.abs(deflection_load) * 1000.0
deflection_middle_mm = np.abs(deflection_middle) * 1000.0

# Digitized experimental data (from digitizer.py): tab-separated, header row "x\ty".
exp_deflection_m, exp_force_kn = np.loadtxt(DIGITIZED_FILE, skiprows=1, unpack=True)
exp_deflection_mm = exp_deflection_m * 1000.0  # convert to mm

fig, ax = plt.subplots(figsize=(8, 6))

ax.plot(deflection_middle_mm, force_kn, color="#1f5fa8", linewidth=2, label="FEM at Midspan")
ax.plot(deflection_load_mm, force_kn, color="#d6d6d6f4", linewidth=2, linestyle="--", label="FEM at Load Point")  
ax.plot(
    exp_deflection_mm,
    exp_force_kn,
    color="#d9782d",
    marker="o",
    markersize=5,
    linewidth=1.5,
    label="Experimental Data",
)

ax.axhline(
    FAILURE_LOAD_KN,
    color="red",
    linestyle="--",
    linewidth=1.5,
    label="Reported Failure Load: {:.1f} kN".format(FAILURE_LOAD_KN),
)

ax.set_xlabel("Deflection [mm]")
ax.set_ylabel("Force [kN]")
ax.set_title("Load-Deflection Curve")
ax.grid(True, linestyle=":", alpha=0.5)
ax.legend(loc="lower right")

material_params = parse_material_params(PARAMS_FILE)
info_text = format_concrete_info(material_params)
ax.text(
    0.02,
    0.98,
    info_text,
    transform=ax.transAxes,
    fontsize=8,
    family="monospace",
    va="top",
    ha="left",
    bbox=dict(boxstyle="round", facecolor="white", alpha=0.85, edgecolor="gray"),
)

fig.tight_layout()
# plt.show()

# Save plot to png file with current date and time in filename
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
plt.savefig(f"plots/load_deflection_curve_{timestamp}.png", dpi=300)

