import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# ---- User configuration ----
IMAGE_FILE = "test_data.png"
OUTPUT_FILE = "digitized_data.txt"

# Data values of the two axis-calibration points (NOT the origin).
X_AXIS_VALUE = 0.025   # x-value of the point you click on the x-axis (at y = 0)
Y_AXIS_VALUE = 300.0    # y-value of the point you click on the y-axis (at x = 0)
# -----------------------------


def pixel_to_data(pixel_points, origin_px, x_ref_px, y_ref_px, x_val, y_val):
    """Map pixel coordinates to data coordinates using a 3-point calibration.

    Uses the origin and the two axis-reference points as a (possibly skewed)
    basis, so slightly rotated/uneven screenshots are still handled correctly.
    """
    origin = np.array(origin_px)
    basis = np.column_stack((np.array(x_ref_px) - origin, np.array(y_ref_px) - origin))
    basis_inv = np.linalg.inv(basis)

    data_points = []
    for p in pixel_points:
        a, b = basis_inv @ (np.array(p) - origin)
        data_points.append((a * x_val, b * y_val))
    return data_points


def main():
    img = mpimg.imread(IMAGE_FILE)

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(img)
    ax.set_title(
        "Step 1/2 - Calibration: click, in order,\n"
        "1) origin (0, 0)   2) x-axis point "
        f"({X_AXIS_VALUE}, 0)   3) y-axis point (0, {Y_AXIS_VALUE})"
    )
    fig.canvas.draw()

    calib = plt.ginput(3, timeout=0, show_clicks=True)
    if len(calib) < 3:
        raise RuntimeError("Calibration needs exactly 3 clicks: origin, x-axis point, y-axis point.")

    origin_px, x_ref_px, y_ref_px = calib

    ax.set_title(
        "Step 2/2 - Data points: left click = add point, right click = undo last,\n"
        "middle click or Enter = finish"
    )
    fig.canvas.draw()

    data_clicks = plt.ginput(n=-1, timeout=0, show_clicks=True)
    plt.close(fig)

    if not data_clicks:
        print("No data points were clicked. Exiting without saving.")
        return

    data_points = pixel_to_data(data_clicks, origin_px, x_ref_px, y_ref_px, X_AXIS_VALUE, Y_AXIS_VALUE)

    with open(OUTPUT_FILE, "w") as f:
        f.write("x\ty\n")
        for x, y in data_points:
            f.write(f"{x:.6g}\t{y:.6g}\n")

    print(f"Saved {len(data_points)} digitized points to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
