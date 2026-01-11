import csv
from core.dyno_math import compute_power_curve, find_peak

MAX_POINTS = 16

def export_gt2_engine_csv(engine, path):
    curve = engine.sorted_curve()

    if len(curve) > MAX_POINTS:
        raise ValueError("GT2 supports max 16 torque points")

    power_curve = compute_power_curve(curve)
    peak_power_rpm, peak_power = find_peak(power_curve)
    peak_torque_rpm, peak_torque = find_peak([(rpm, t) for rpm, t in curve])

    row = {
        "CarId": engine.car_id,
        "LayoutName": engine.layout,
        "ValvetrainName": engine.valvetrain,
        "Aspiration": engine.aspiration,
        "SoundFile": engine.sound_file,

        "Displacement": engine.displacement,
        "DisplayedPower": round(peak_power),
        "MaxPowerRPM": peak_power_rpm,
        "DisplayedTorque": round(peak_torque),
        "MaxTorqueRPMName": f"{peak_torque_rpm}rpm",

        "PowerMultiplier": engine.power_multiplier,
        "ClutchReleaseRPM": engine.clutch_release_rpm,
        "IdleRPM": engine.idle_rpm,
        "MaxRPM": engine.max_rpm,
        "RedlineRPM": engine.redline_rpm,

        "TorqueCurvePoints": len(curve),
    }

    for i in range(MAX_POINTS):
        if i < len(curve):
            rpm, torque = curve[i]
            row[f"TorqueCurve{i+1}"] = int(torque * 10)
            row[f"TorqueCurveRPM{i+1}"] = int(rpm / 100)
        else:
            row[f"TorqueCurve{i+1}"] = -1
            row[f"TorqueCurveRPM{i+1}"] = 255

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writeheader()
        writer.writerow(row)
