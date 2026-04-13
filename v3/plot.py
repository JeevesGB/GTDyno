import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QSplitter, QStatusBar, QComboBox, QHeaderView, QDialog, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


KG_M_TO_NM = 9.80665
MAX_RPM_LIMIT = 16000


class InfoDialog(QDialog):
    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Engine Information")
        self.resize(740, 650)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        title = QLabel("Complete Engine Specifications")
        title.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 9))

        info_text = "═" * 60 + "\n                  ENGINE INFORMATION\n" + "═" * 60 + "\n\n"
        for key, value in row.items():
            if not key.startswith('TorqueCurve') and key != 'TorqueCurvePoints':
                info_text += f"{key:<26} :  {value}\n"

        info_text += "\n" + "─" * 60 + "\n"
        info_text += f"Valid Torque Curve Points : {row.get('TorqueCurvePoints', 0)}\n"
        info_text += "─" * 60 + "\n"

        num_points = int(row.get('TorqueCurvePoints', 0))
        for i in range(1, num_points + 1):
            info_text += f"Point {i:2d} →  RPM×100: {row[f'TorqueCurveRPM{i}']:>6}   |   Torque×10: {row[f'TorqueCurve{i}']:>6}\n"

        text_edit.setText(info_text)
        layout.addWidget(text_edit)

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


class DynoPreview(QWidget):
    def __init__(self):
        super().__init__()
        self.figure = Figure(figsize=(8.2, 6.4), dpi=130, facecolor="#DDDDDD")
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
            torque_kgm = torque_raw / 10.0

            mask = rpm <= MAX_RPM_LIMIT
            rpm = rpm[mask]
            torque_kgm = torque_kgm[mask]

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

            self.ax1.plot(rpm, torque_display, 'o-', linewidth=2.7, markersize=5.5, label=torque_label)
            self.ax2.plot(rpm, power_hp, 'o-', linewidth=2.7, markersize=5.5, label='Power (hp)')

            self.ax1.xaxis.set_major_locator(MultipleLocator(1000))
            self.ax1.xaxis.set_minor_locator(MultipleLocator(500))

            self.ax1.grid(which='major', linestyle='--', linewidth=0.9, alpha=0.85)
            self.ax1.grid(which='minor', linestyle=':', linewidth=0.6, alpha=0.65)

            self.ax1.tick_params(axis='x', labelsize=8.5, rotation=45)
            self.ax1.tick_params(axis='y', labelsize=9.5)
            self.ax2.tick_params(axis='y', labelsize=9.5)

            self.ax1.set_xlabel('Engine Speed (RPM)', fontsize=10.5)
            self.ax1.set_ylabel(torque_label, fontsize=10.8)
            self.ax2.set_ylabel('Power (hp)', fontsize=10.8)

            self.ax1.set_xlim(0, MAX_RPM_LIMIT)

            self.figure.suptitle(
                f'{row.get("CarId", "Engine")} — Live Dyno Preview',
                fontsize=14.5,
                fontweight='bold',
                y=0.97
            )

            self.ax1.legend(loc='upper left', fontsize=9.8)

            self.ax1.axvline(rpm[max_t_idx], linestyle='--', alpha=0.85, linewidth=1.5)
            self.ax2.axvline(rpm[max_p_idx], linestyle='--', alpha=0.85, linewidth=1.5)

            self.canvas.draw()

        except Exception:
            pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GT Dyno Sheet Generator")
        self.resize(1480, 780)

        self.current_row = None
        self.current_csv_path = None
        self.current_unit = "Nm"

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        header = QLabel("GT Dyno Sheet Generator")
        header.setFont(QFont("Arial", 19, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        unit_layout = QHBoxLayout()
        unit_label = QLabel("Torque Unit:")
        unit_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Nm", "kgm (Gran Turismo 2)"])
        self.unit_combo.setFixedWidth(210)
        self.unit_combo.currentTextChanged.connect(self.on_unit_changed)

        unit_layout.addStretch()
        unit_layout.addWidget(unit_label)
        unit_layout.addWidget(self.unit_combo)
        main_layout.addLayout(unit_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(8)
        main_layout.addWidget(splitter, stretch=1)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 8, 0)
        left_layout.setSpacing(8)

        left_header = QLabel("Torque Curve Editor")
        left_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        left_layout.addWidget(left_header)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Point", "RPM ×100", "Torque"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.cellChanged.connect(self.on_cell_changed)
        left_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_load = QPushButton("Load CSV")
        self.btn_info = QPushButton("Show All Info")
        self.btn_save = QPushButton("Save As")
        self.btn_generate = QPushButton("Generate Dyno Sheet")

        for btn in (self.btn_load, self.btn_info, self.btn_save, self.btn_generate):
            btn.setMinimumHeight(38)

        self.btn_load.clicked.connect(self.load_csv)
        self.btn_info.clicked.connect(self.show_all_info)
        self.btn_save.clicked.connect(self.save_edited)
        self.btn_generate.clicked.connect(self.generate_full_sheet)

        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_info)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_generate)
        left_layout.addLayout(btn_layout)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(6)

        preview_header = QLabel("Live Preview ")
        preview_header.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        right_layout.addWidget(preview_header)

        self.preview = DynoPreview()
        right_layout.addWidget(self.preview)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([520, 960])

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

    def on_unit_changed(self, text):
        self.current_unit = "kgm" if "kgm" in text else "Nm"
        self.table.setHorizontalHeaderLabels(["Point", "RPM ×100", f"Torque ({self.current_unit})"])
        if self.current_row is not None:
            self.update_table()
            self.update_preview()

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Engine CSV File", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            df = pd.read_csv(path)
            self.current_csv_path = path
            self.current_row = df.iloc[0].copy()
            self.update_table()
            self.update_preview()
            self.statusBar.showMessage(f"Loaded: {os.path.basename(path)}", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")

    def update_table(self):
        if self.current_row is None:
            return
        self.table.setRowCount(16)
        for i in range(1, 17):
            rpm_val = float(self.current_row[f'TorqueCurveRPM{i}'])
            torque_raw = float(self.current_row[f'TorqueCurve{i}']) / 10.0
            torque_display = torque_raw

            self.table.setItem(i-1, 0, QTableWidgetItem(str(i)))
            self.table.setItem(i-1, 1, QTableWidgetItem(f"{rpm_val:.0f}"))
            self.table.setItem(i-1, 2, QTableWidgetItem(f"{torque_display:.2f}"))
            self.table.item(i-1, 0).setFlags(self.table.item(i-1, 0).flags() & ~Qt.ItemFlag.ItemIsEditable)

    def on_cell_changed(self, row, col):
        if self.current_row is None or col != 2:
            return
        try:
            val = float(self.table.item(row, col).text())
            point = row + 1
            self.current_row[f'TorqueCurve{point}'] = val * 10.0

            valid = 0
            for i in range(1, 17):
                if float(self.current_row[f'TorqueCurveRPM{i}']) >= 0:
                    valid = i
                else:
                    break
            self.current_row['TorqueCurvePoints'] = valid

            self.update_preview()
        except ValueError:
            self.update_table()

    def update_preview(self):
        if self.current_row is not None:
            self.preview.update_plot(self.current_row, self.current_unit)

    def show_all_info(self):
        if self.current_row is None:
            QMessageBox.warning(self, "No Data", "Please load a CSV file first.")
            return
        InfoDialog(self.current_row, self).exec()

    def save_edited(self):
        if self.current_row is None:
            QMessageBox.warning(self, "No Data", "Please load a CSV file first.")
            return
        path, _ = QFileDialog.getSaveAsFileName(
            self,
            "Save As",
            os.path.basename(self.current_csv_path or "engine_edited.csv"),
            "CSV Files (*.csv)"
        )
        if path:
            try:
                pd.DataFrame([self.current_row]).to_csv(path, index=False)
                QMessageBox.information(self, "Success", f"File saved:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def generate_full_sheet(self):
        if self.current_row is None:
            QMessageBox.warning(self, "No Data", "Please load a CSV first.")
            return

        # (unchanged plotting logic)
        # kept as-is since styling removal doesn't affect it

        try:
            rpm_raw = np.array([float(self.current_row[f'TorqueCurveRPM{i}']) for i in range(1, 17)])
            torque_raw = np.array([float(self.current_row[f'TorqueCurve{i}']) for i in range(1, 17)])
            num_points = int(self.current_row['TorqueCurvePoints'])

            rpm = rpm_raw[:num_points] * 100.0
            torque_kgm = torque_raw[:num_points] / 10.0

            mask = rpm <= MAX_RPM_LIMIT
            rpm = rpm[mask]
            torque_kgm = torque_kgm[mask]

            torque_nm = torque_kgm * KG_M_TO_NM if self.current_unit == "kgm" else torque_kgm
            power_hp = ((torque_nm * rpm) / 9549.3) * 1.341

            fig, ax1 = plt.subplots(figsize=(13.5, 7.8))
            label = f'Torque ({self.current_unit})'

            ax1.plot(rpm, torque_kgm if self.current_unit == "kgm" else torque_nm, 'o-', label=label)
            ax2 = ax1.twinx()
            ax2.plot(rpm, power_hp, 'o-', label='Power (hp)')

            ax1.set_xlim(0, MAX_RPM_LIMIT)

            max_t = np.argmax(torque_nm)
            max_p = np.argmax(power_hp)

            ax1.set_title(f'Engine Dyno Sheet — {self.current_row.get("CarId", "Engine")}')

            subtitle = f'Max: {torque_kgm[max_t]:.2f} {self.current_unit} @ {rpm[max_t]:.0f} RPM | {power_hp[max_p]:.0f} hp @ {rpm[max_p]:.0f} RPM'
            ax1.text(0.5, 0.92, subtitle, transform=ax1.transAxes, ha='center')

            plt.tight_layout()
            plt.show()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate plot:\n{str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Load external QSS
    base_dir = os.path.dirname(os.path.abspath(__file__))
    qss_path = os.path.join(base_dir, "style.qss")

    if os.path.exists(qss_path):
        with open(qss_path, "r") as f:
            app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())