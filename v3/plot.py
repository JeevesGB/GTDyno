import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QSplitter, QStatusBar, QComboBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


KG_M_TO_NM = 9.80665   # Accurate conversion: 1 kgf·m = 9.80665 Nm


class DynoPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.figure = Figure(figsize=(7.5, 6), dpi=110, facecolor='#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        self.ax1 = self.figure.add_subplot(111)
        self.ax2 = self.ax1.twinx()

        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)

    def update_plot(self, row, unit="Nm"):
        self.ax1.clear()
        self.ax2.clear()

        try:
            num_points = int(row['TorqueCurvePoints'])
            rpm_raw = np.array([float(row[f'TorqueCurveRPM{i}']) for i in range(1, 17)])[:num_points]
            torque_raw = np.array([float(row[f'TorqueCurve{i}']) for i in range(1, 17)])[:num_points]

            rpm = rpm_raw * 100.0
            torque_kgm = torque_raw / 10.0                     # raw stored value

            if unit == "kgm":
                torque_nm = torque_kgm * KG_M_TO_NM
                torque_display = torque_kgm
                torque_label = "Torque (kgm)"
            else:
                torque_nm = torque_kgm
                torque_display = torque_nm
                torque_label = "Torque (Nm)"

            power_hp = ((torque_nm * rpm) / 9549.3) * 1.341

            if len(rpm) == 0:
                return

            max_t_idx = np.argmax(torque_nm)
            max_p_idx = np.argmax(power_hp)

            color_torque = '#00bfff'
            color_power = '#ff4d4d'

            self.ax1.plot(rpm, torque_display, 'o-', color=color_torque, linewidth=2.8, markersize=6, label=torque_label)
            self.ax2.plot(rpm, power_hp, 'o-', color=color_power, linewidth=2.8, markersize=6, label='Power (hp)')

            self.ax1.set_xlabel('Engine Speed (RPM)', color='white', fontsize=11, fontweight='bold')
            self.ax1.set_ylabel(torque_label, color=color_torque, fontsize=11, fontweight='bold')
            self.ax2.set_ylabel('Power (hp)', color=color_power, fontsize=11, fontweight='bold')

            self.ax1.tick_params(colors='white')
            self.ax2.tick_params(colors='white')
            self.ax1.grid(True, linestyle='--', alpha=0.5, color='#444')

            car_id = row.get('CarId', 'Engine')
            self.figure.suptitle(f'Live Preview — {car_id}  |  Unit: {unit}', 
                               color='white', fontsize=14, fontweight='bold')

            self.ax1.legend(loc='upper left', fontsize=10, labelcolor='white')

            self.ax1.axvline(rpm[max_t_idx], color=color_torque, linestyle='--', alpha=0.75, linewidth=1.5)
            self.ax2.axvline(rpm[max_p_idx], color=color_power, linestyle='--', alpha=0.75, linewidth=1.5)

            self.canvas.draw()

        except Exception:
            pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GT Dyno Sheet Generator — PyQt6 (Supports kgm)")
        self.resize(1400, 800)

        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #121212; color: #ffffff; }
            QTableWidget { background-color: #1e1e1e; gridline-color: #333333; }
            QHeaderView::section { background-color: #2d2d2d; padding: 6px; }
            QPushButton { padding: 8px 16px; }
        """)

        self.current_row = None
        self.current_csv_path = None
        self.current_unit = "Nm"   # Default

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)

        header_layout = QHBoxLayout()
        header = QLabel("GT Dyno Sheet Generator")
        header.setFont(QFont("Helvetica", 18, QFont.Weight.Bold))
        header_layout.addWidget(header)

        unit_label = QLabel("Torque Unit:")
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Nm", "kgm (GT2 / Gran Turismo)"])
        self.unit_combo.currentTextChanged.connect(self.on_unit_changed)
        header_layout.addStretch()
        header_layout.addWidget(unit_label)
        header_layout.addWidget(self.unit_combo)

        main_layout.addLayout(header_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, stretch=1)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(12, 12, 12, 12)

        self.torque_label = QLabel("Torque Curve Editor")
        left_layout.addWidget(self.torque_label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Point", "RPM ×100", "Torque"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.cellChanged.connect(self.on_cell_changed)
        left_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("Load CSV")
        self.btn_save = QPushButton("Save As New CSV")
        self.btn_generate = QPushButton("Generate Full Dyno Sheet")

        self.btn_load.clicked.connect(self.load_csv)
        self.btn_save.clicked.connect(self.save_edited)
        self.btn_generate.clicked.connect(self.generate_full_sheet)

        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_generate)
        left_layout.addLayout(btn_layout)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.addWidget(QLabel("Live Dyno Preview"))
        self.preview = DynoPreview()
        right_layout.addWidget(self.preview)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([550, 850])

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

    def on_unit_changed(self, text):
        self.current_unit = "kgm" if "kgm" in text else "Nm"
        self.table.setHorizontalHeaderLabels(["Point", "RPM ×100", f"Torque ({self.current_unit})"])
        if self.current_row is not None:
            self.update_table()
            self.update_preview()

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        try:
            df = pd.read_csv(path)
            self.current_csv_path = path
            self.current_row = df.iloc[0].copy()

            self.update_table()
            self.update_preview()
            self.statusBar.showMessage(f"Loaded: {os.path.basename(path)}", 5000)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")

    def update_table(self):
        if self.current_row is None:
            return

        self.table.setRowCount(16)
        for i in range(1, 17):
            point = i
            rpm_val = float(self.current_row[f'TorqueCurveRPM{i}'])
            torque_raw = float(self.current_row[f'TorqueCurve{i}'])   # stored as x10

            torque_display = torque_raw / 10.0                     # base value
            if self.current_unit == "kgm":
                torque_display = torque_display                     # show as kgm (game value)
            # else: keep as Nm

            self.table.setItem(i-1, 0, QTableWidgetItem(str(point)))
            self.table.setItem(i-1, 1, QTableWidgetItem(str(rpm_val)))
            self.table.setItem(i-1, 2, QTableWidgetItem(f"{torque_display:.2f}"))

            self.table.item(i-1, 0).setFlags(self.table.item(i-1, 0).flags() & ~Qt.ItemFlag.ItemIsEditable)

    def on_cell_changed(self, row, col):
        if self.current_row is None or col != 2:   # only torque column is editable
            return

        try:
            displayed_val = float(self.table.item(row, col).text())
            point = row + 1

            if self.current_unit == "kgm":
                stored_val = displayed_val * 10.0
            else:
                stored_val = displayed_val * 10.0

            self.current_row[f'TorqueCurve{point}'] = stored_val

            valid = 0
            for i in range(1, 17):
                if float(self.current_row[f'TorqueCurveRPM{i}']) >= 0:
                    valid = i
                else:
                    break
            self.current_row['TorqueCurvePoints'] = valid

            self.update_preview()

        except ValueError:
            QMessageBox.warning(self, "Invalid", "Please enter a valid number.")
            self.update_table()   # revert

    def update_preview(self):
        if self.current_row is not None:
            self.preview.update_plot(self.current_row, self.current_unit)

    def save_edited(self):
        if self.current_row is None:
            QMessageBox.warning(self, "Warning", "Load a file first.")
            return

        path, _ = QFileDialog.getSaveAsFileName(
            self, "Save Edited CSV As",
            os.path.basename(self.current_csv_path or "engine_edited.csv").replace(".csv", "_edited.csv"),
            "CSV Files (*.csv)"
        )
        if path:
            try:
                new_df = pd.DataFrame([self.current_row])
                new_df.to_csv(path, index=False)
                QMessageBox.information(self, "Saved", f"Saved successfully:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def generate_full_sheet(self):
        if self.current_row is None:
            QMessageBox.warning(self, "Warning", "Load a CSV first.")
            return

        try:
            rpm_raw = np.array([float(self.current_row[f'TorqueCurveRPM{i}']) for i in range(1, 17)])
            torque_raw = np.array([float(self.current_row[f'TorqueCurve{i}']) for i in range(1, 17)])
            num_points = int(self.current_row['TorqueCurvePoints'])

            rpm = rpm_raw[:num_points] * 100.0
            torque_kgm = torque_raw[:num_points] / 10.0

            torque_nm = torque_kgm * KG_M_TO_NM if self.current_unit == "kgm" else torque_kgm
            power_hp = ((torque_nm * rpm) / 9549.3) * 1.341

            fig, ax1 = plt.subplots(figsize=(12, 7))
            torque_label = f'Torque ({self.current_unit})'

            ax1.plot(rpm, torque_kgm if self.current_unit == "kgm" else torque_nm, 
                     'o-', color='tab:blue', linewidth=2.5, markersize=6, label=torque_label)
            ax2 = ax1.twinx()
            ax2.plot(rpm, power_hp, 'o-', color='tab:red', linewidth=2.5, markersize=6, label='Power (hp)')

            ax1.set_xlabel('Engine Speed (RPM)')
            ax1.set_ylabel(torque_label, color='tab:blue')
            ax2.set_ylabel('Power (hp)', color='tab:red')
            ax1.grid(True, linestyle='--', alpha=0.7)

            max_t = np.argmax(torque_nm)
            max_p = np.argmax(power_hp)

            ax1.set_title(f'Engine Dyno Sheet — {self.current_row.get("CarId", "Engine")}\n'
                          f'Max Torque: {torque_kgm[max_t]:.2f} {self.current_unit} @ {rpm[max_t]:.0f} RPM | '
                          f'Max Power: {power_hp[max_p]:.0f} hp @ {rpm[max_p]:.0f} RPM', pad=25)

            ax1.legend(loc='upper left')
            plt.tight_layout()
            plt.show()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate plot:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MainWindow()
    window.show()
    sys.exit(app.exec())