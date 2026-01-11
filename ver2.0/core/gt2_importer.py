from core.engine_model import EngineModel

def import_gt2_engine_csv_row(row):
    points = int(row["TorqueCurvePoints"])

    curve = []
    for i in range(points):
        torque_nm = int(row[f"TorqueCurve{i+1}"]) / 10.0
        rpm = int(row[f"TorqueCurveRPM{i+1}"]) * 100
        curve.append((rpm, torque_nm))

    return EngineModel(
        car_id=row["CarId"],
        layout=row["LayoutName"],
        valvetrain=row["ValvetrainName"],
        aspiration=row["Aspiration"],
        sound_file=int(row["SoundFile"]),
        displacement=int(row["Displacement"]),
        idle_rpm=int(row["IdleRPM"]),
        max_rpm=int(row["MaxRPM"]),
        redline_rpm=int(row["RedlineRPM"]),
        clutch_release_rpm=int(row["ClutchReleaseRPM"]),
        power_multiplier=int(row["PowerMultiplier"]),
        curve=curve,
    )
