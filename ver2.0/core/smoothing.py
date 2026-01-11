def smooth_curve(curve, strength=0.3):
    if len(curve) < 3:
        return curve[:]

    smoothed = []
    for i, (rpm, torque) in enumerate(curve):
        if i == 0 or i == len(curve) - 1:
            smoothed.append((rpm, torque))
            continue

        prev_t = curve[i - 1][1]
        next_t = curve[i + 1][1]
        avg = (prev_t + torque + next_t) / 3
        new_t = torque + (avg - torque) * strength
        smoothed.append((rpm, new_t))

    return smoothed
