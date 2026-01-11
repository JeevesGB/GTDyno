def torque_to_power_hp(torque_nm: float, rpm: int) -> float:
    return (torque_nm * rpm) / 9549.0


def compute_power_curve(curve):
    return [(rpm, torque_to_power_hp(t, rpm)) for rpm, t in curve]


def find_peak(curve):
    return max(curve, key=lambda p: p[1]) if curve else (0, 0)
