from core.dyno_math import compute_power_curve

def plot_engine(ax, ax2, engine, colors):
    curve = engine.sorted_curve()
    if not curve:
        return

    rpms = [r for r, _ in curve]
    torques = [t for _, t in curve]
    powers = [p for _, p in compute_power_curve(curve)]

    ax.clear()
    ax2.clear()

    ax.plot(rpms, torques, color=colors["torque"], label="Torque (Nm)")
    ax2.plot(rpms, powers, "--", color=colors["power"], label="Power (HP)")

    ax.set_xlabel("RPM")
    ax.set_ylabel("Torque (Nm)")
    ax2.set_ylabel("Power (HP)")

    ax.legend()
    ax.grid(True)
