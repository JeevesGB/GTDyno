import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sys
import os

def generate_dyno_sheet(csv_path, save_plot=False):
    try:
        df = pd.read_csv(csv_path)
        if df.empty:
            raise ValueError("CSV file is empty.")

        row = df.iloc[0]

        # Get number of valid points
        num_points = int(row['TorqueCurvePoints'])

        # Extract RPM and Torque
        rpm_raw = np.array([float(row[f'TorqueCurveRPM{i}']) for i in range(1, 17)])
        torque_raw = np.array([float(row[f'TorqueCurve{i}']) for i in range(1, 17)])

        # Keep only valid points
        rpm_raw = rpm_raw[:num_points]
        torque_raw = torque_raw[:num_points]

        # Scale values correctly
        rpm = rpm_raw * 100.0
        torque_nm = torque_raw / 10.0

        # Calculate Power in hp
        power_kw = (torque_nm * rpm) / 9549.3
        power_hp = power_kw * 1.341

        # Find max values
        max_torque_idx = np.argmax(torque_nm)
        max_power_idx = np.argmax(power_hp)

        # ====================== PLOT ======================
        fig, ax1 = plt.subplots(figsize=(12, 7))

        color_torque = 'tab:blue'
        ax1.set_xlabel('Engine Speed (RPM)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Torque (Nm)', color=color_torque, fontsize=12, fontweight='bold')
        ax1.plot(rpm, torque_nm, color=color_torque, marker='o', linestyle='-', linewidth=2.5, 
                 markersize=6, label='Torque (Nm)')
        ax1.tick_params(axis='y', labelcolor=color_torque)
        ax1.grid(True, linestyle='--', alpha=0.7)

        ax2 = ax1.twinx()
        color_power = 'tab:red'
        ax2.set_ylabel('Power (hp)', color=color_power, fontsize=12, fontweight='bold')
        ax2.plot(rpm, power_hp, color=color_power, marker='o', linestyle='-', linewidth=2.5, 
                 markersize=6, label='Power (hp)')
        ax2.tick_params(axis='y', labelcolor=color_power)

        # Title
        car_id = row['CarId']
        layout = row['LayoutName']
        aspiration = row['Aspiration']
        displacement = int(row['Displacement'])

        plt.title(f'Engine Dyno Sheet — {car_id}\n'
                  f'{layout} • {aspiration} • {displacement} cc\n'
                  f'Max Torque: {torque_nm[max_torque_idx]:.1f} Nm @ {rpm[max_torque_idx]:.0f} RPM | '
                  f'Max Power: {power_hp[max_power_idx]:.0f} hp @ {rpm[max_power_idx]:.0f} RPM',
                  fontsize=14, fontweight='bold', pad=25)

        # Legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=11)

        # Vertical lines at peaks
        ax1.axvline(rpm[max_torque_idx], color=color_torque, linestyle='--', alpha=0.6, linewidth=1.5)
        ax2.axvline(rpm[max_power_idx], color=color_power, linestyle='--', alpha=0.6, linewidth=1.5)

        plt.tight_layout()

        if save_plot:
            save_path = csv_path.replace('.csv', '_dyno_sheet.png')
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved as: {save_path}")

        plt.show()

    except Exception as e:
        messagebox.showerror("Error", f"Failed to generate dyno sheet:\n{str(e)}")


# ====================== GUI ======================
def browse_file():
    filename = filedialog.askopenfilename(
        title="Select Engine CSV File",
        filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
    )
    if filename:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, filename)

def generate_from_gui():
    csv_path = entry_path.get().strip()
    if not csv_path or not os.path.isfile(csv_path):
        messagebox.showwarning("Warning", "Please select a valid CSV file.")
        return
    
    save_option = save_var.get()
    generate_dyno_sheet(csv_path, save_plot=save_option)


# Create main window
root = tk.Tk()
root.title("Engine Dyno Sheet Generator")
root.geometry("700x520")
root.resizable(True, True)

# Style
style = ttk.Style()
style.theme_use('clam')

# Title
tk.Label(root, text="Engine Dyno Sheet Generator", font=("Helvetica", 18, "bold")).pack(pady=15)

# File selection frame
frame = ttk.Frame(root, padding=20)
frame.pack(fill="x", padx=30)

ttk.Label(frame, text="CSV File:", font=("Helvetica", 10)).pack(anchor="w")
entry_frame = ttk.Frame(frame)
entry_frame.pack(fill="x", pady=5)

entry_path = ttk.Entry(entry_frame, width=70, font=("Consolas", 10))
entry_path.pack(side="left", expand=True, fill="x")

btn_browse = ttk.Button(entry_frame, text="Browse...", command=browse_file)
btn_browse.pack(side="right", padx=(10, 0))

# Options
save_var = tk.BooleanVar(value=True)
chk_save = ttk.Checkbutton(frame, text="Save plot as PNG next to CSV file", variable=save_var)
chk_save.pack(anchor="w", pady=10)

# Generate Button
btn_generate = ttk.Button(root, text="Generate Dyno Sheet", command=generate_from_gui, 
                         style="Accent.TButton")
btn_generate.pack(pady=20)

# Separator
ttk.Separator(root, orient="horizontal").pack(fill="x", padx=40, pady=10)

# Command Line Instructions
tk.Label(root, text="Command Line Usage (Alternative)", font=("Helvetica", 11, "bold")).pack(pady=(10,5))

cmd_text = tk.Text(root, height=8, font=("Consolas", 9), bg="#f8f8f8")
cmd_text.pack(fill="both", padx=40, pady=5)

cmd_instructions = """How to run from Command Line:

1. Save this script as dyno_generator.py

2. Put your CSV file (e.g. a2aan.csv) in the same folder

3. Run one of these commands:

   python dyno_generator.py a2aan.csv
   python dyno_generator.py "path/to/your/file.csv" --save

Note: The GUI version is recommended for ease of use.
"""
cmd_text.insert("1.0", cmd_instructions)
cmd_text.config(state="disabled")

# Footer
tk.Label(root, text="Made for realistic engine torque curve visualization", 
         font=("Helvetica", 9), fg="gray").pack(side="bottom", pady=10)

# Run the GUI
if __name__ == "__main__":
    # Allow command line usage as fallback
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        save_plot = "--save" in sys.argv
        if os.path.isfile(csv_file):
            generate_dyno_sheet(csv_file, save_plot=save_plot)
        else:
            print(f"Error: File '{csv_file}' not found.")
    else:
        root.mainloop()