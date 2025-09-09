#---------------------------------------|
import sys
import os
import re
import pandas as pd
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QListWidget, QVBoxLayout,
    QWidget, QPushButton, QLabel, QSplitter, QTextEdit, QColorDialog, 
    QHBoxLayout, QToolBar, QLineEdit, QScrollArea, QGridLayout,
    QSpacerItem, QSizePolicy , QFontComboBox
)
from PyQt6.QtCore import Qt
from PyQt6 import QtGui 
#---------------------------------------|
class DynoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Engine Dynograph Viewer")
        self.setGeometry(800, 800, 1800, 1250)
        self.torque_color = "#00FFFB"
        self.power_color = "#8CFF00"

# === Toolbar ===
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        #toolbar.addWidget(QLabel(" Engine Dynograph Viewer "))
        self.load_btn = QPushButton(" Load ENGINE CSV ")
        self.load_btn.clicked.connect(self.load_csv)
        toolbar.addWidget(self.load_btn)
        
        self.load_folder_btn = QPushButton(" Load FOLDER ")
        self.load_folder_btn.clicked.connect(self.load_folder)
        toolbar.addWidget(self.load_folder_btn)

        
        self.save_btn = QPushButton(" Save ")
        self.save_btn.clicked.connect(self.save_changes)
        toolbar.addWidget(self.save_btn)
        
        self.save_as_btn = QPushButton(" Save As ")
        self.save_as_btn.clicked.connect(self.save_as)
        toolbar.addWidget(self.save_as_btn)

        
        self.torque_color_btn = QPushButton(" Select Torque Color ")
        self.torque_color_btn.clicked.connect(self.set_torque_color)
        toolbar.addWidget(self.torque_color_btn)

        self.power_color_btn = QPushButton(" Select Power Color ")
        self.power_color_btn.clicked.connect(self.set_power_color)
        toolbar.addWidget(self.power_color_btn)

        splitter = QSplitter()

# === Left side (file list only) ===
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        self.file_list = QListWidget()
        self.file_list.itemSelectionChanged.connect(self.plot_selected)
        self.file_list.itemSelectionChanged.connect(self.fill_edit_fields)
        left_layout.addWidget(self.file_list)
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)

# === Right side (graph + metadata) ===
        right_widget = QWidget()
        right_layout = QHBoxLayout()

# --- Graph area ---
        graph_widget = QWidget()
        graph_layout = QVBoxLayout()
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.ax2 = self.ax.twinx()
        graph_layout.addWidget(self.canvas)
        graph_widget.setLayout(graph_layout)

# --- Metadata box ---
        meta_widget = QWidget()
        meta_layout = QVBoxLayout()
        meta_layout.addWidget(QLabel(" Engine Info "))
        self.meta_box = QTextEdit()
        self.meta_box.setReadOnly(True)
        meta_layout.addWidget(self.meta_box)
        meta_widget.setLayout(meta_layout)

        right_layout.addWidget(graph_widget, stretch=3)
        right_layout.addWidget(meta_widget, stretch=1)
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)

        self.setCentralWidget(splitter)
        self.data = None

# === Bottom editor area (scrollable) ===
        self.bottom_editor_scroll = QScrollArea()
        self.bottom_editor_scroll.setWidgetResizable(True)
        self.bottom_editor_widget = QWidget()
        self.bottom_layout = QGridLayout()
        self.bottom_layout.setColumnMinimumWidth(0, 100)   
        self.bottom_layout.setRowMinimumHeight(0, 50)
        self.bottom_layout.setColumnStretch(0, 0)          
        self.bottom_layout.setColumnStretch(1, 1)          
        self.bottom_editor_widget.setLayout(self.bottom_layout)
        self.bottom_editor_widget.setLayout(self.bottom_layout)
        self.bottom_editor_scroll.setWidget(self.bottom_editor_widget)

# === Main vertical layout ===
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addWidget(splitter)
        main_layout.addWidget(self.bottom_editor_scroll)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

# Apply default dark style
        self.apply_dark_theme()
#---------------------------------------|
    def set_torque_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.torque_color = color.name()
            self.plot_selected()
#---------------------------------------|
    def set_power_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.power_color = color.name()
            self.plot_selected()
#---------------------------------------|
    def apply_dark_theme(self):
        """Force a dark theme for both Qt and matplotlib."""
        dark_stylesheet = """
            QWidget { background-color: #1e1e1e; color: #ffffff; }
            QPushButton { background-color: #333333; color: #ffffff; border: 1px solid #555555; padding: 5px; }
            QPushButton:hover { background-color: #444444; }
            QListWidget { background-color: #2a2a2a; color: #ffffff; }
            QTextEdit { background-color: #2a2a2a; color: #ffffff; }
            QToolBar { background-color: #2a2a2a; border: none; }
        """
        self.setStyleSheet(dark_stylesheet)
    # Matplotlib dark settings
        self.figure.patch.set_facecolor("#1e1e1e")
        self.ax.set_facecolor("#1e1e1e")
        self.ax2.set_facecolor("#1e1e1e")
        for ax in [self.ax, self.ax2]:
            ax.tick_params(colors="white")
            ax.xaxis.label.set_color("white")
            ax.yaxis.label.set_color("white")
            ax.title.set_color("white")
            for spine in ax.spines.values():
                spine.set_color("#4f484a")
            ax.grid(color="#2B2529")
#---------------------------------------|
    def plot_selected(self):
        if self.data is None:
            return
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            self.ax.clear()
            self.ax2.clear()
            self.meta_box.clear()
            self.canvas.draw()
            return

        self.ax.clear()
        self.ax2.clear()
        self.meta_box.clear()
        self.apply_dark_theme() 

        for item in selected_items:
            car_label = item.text()
            row = self.data[self.data["CarLabel"] == car_label].iloc[0] if "CarLabel" in self.data.columns else self.data[self.data["CarId"] == car_label].iloc[0]

# === GT2 format detection ===
            if "TorqueCurve1" in self.data.columns and "TorqueCurveRPM1" in self.data.columns:
                torque_points = int(row.get("TorqueCurvePoints", 0))
                torques_nm = [float(row.get(f"TorqueCurve{i+1}", 0)) / 10 for i in range(torque_points)]
                rpms = [int(row.get(f"TorqueCurveRPM{i+1}", 0)) * 100 for i in range(torque_points)]

                max_torque = max(torques_nm) if torques_nm else 0
                self.ax.plot(rpms, torques_nm, color=self.torque_color,
                             label=f"{car_label} - Torque ({max_torque:.1f} Nm)")

                powers = [(t * rpm) / 9549 for t, rpm in zip(torques_nm, rpms)]
                max_power = max(powers) if powers else 0
                self.ax2.plot(rpms, powers, linestyle="--", color=self.power_color,
                              label=f"{car_label} - Power (HP) ({max_power:.1f} HP)")

                metadata = {
                    "Displacement (cc)": f"{row.get('Displacement', 'N/A')}",
                    "Max Power": f"{row.get('DisplayedPower', 0)} HP @ {row.get('MaxPowerRPM', 0)}",
                    "Max Torque": f"{row.get('DisplayedTorque', 0)} Nm @ {row.get('MaxTorqueRPMName', 0)}",
                    "Idle RPM": f"{row.get('IdleRPM', 'N/A')}",
                    "Rev Limit": f"{row.get('RedlineRPM', 'N/A')}",
                    "Max RPM": f"{row.get('MaxRPM', 'N/A')}",
                }
                self.meta_box.append(f"==== {car_label} (GT2) ====")
                for k, v in metadata.items():
                    self.meta_box.append(f"{k}: {v}")
                self.meta_box.append("\n")

    # === GT4-style format ===
            else:
                torque_points = int(row.get("torquepoint", 0))
                torques_kgfm = [float(row.get(f"torque{chr(65+i)}", 0)) / 100 for i in range(torque_points)]
                torques_nm = [t * 9.80665 for t in torques_kgfm]
                rpms = [int(row.get(f"rpm{chr(65+i)}", 0)) * 100 for i in range(torque_points)]

                max_torque = max(torques_nm) if torques_nm else 0
                self.ax.plot(rpms, torques_nm, color=self.torque_color,
                             label=f"{car_label} - Torque ({max_torque:.1f} Nm)")

                powers = [(t * rpm) / 9549 for t, rpm in zip(torques_nm, rpms)]
                max_power = max(powers) if powers else 0
                self.ax2.plot(rpms, powers, linestyle="--", color=self.power_color,
                              label=f"{car_label} - Power (HP) ({max_power:.1f} HP)")

                max_torque_kgfm = float(row.get("torquevalue", 0)) / 100
                max_torque_nm = max_torque_kgfm * 9.80665
                metadata = {
                    "Displacement (cc)": f"{row.get('displacement', 'N/A')}",
                    "Max Power": f"{row.get('psvalue', 0)} HP @ {row.get('psrpm', 0)}",
                    "Max Torque": f"{max_torque_nm:.1f} Nm ({max_torque_kgfm:.2f} kgfm) @ {row.get('torquerpm', 0)}",
                    "Idle RPM": f"{row.get('idlerpm', 'N/A')}",
                    "Rev Limit": f"{row.get('revlimit', 'N/A')}",
                    "Shift Limit": f"{row.get('shiftlimit', 'N/A')}",
                }
                self.meta_box.append(f"==== {car_label} (GT4) ====")
                for k, v in metadata.items():
                    self.meta_box.append(f"{k}: {v}")
                self.meta_box.append("\n")

        self.ax.set_xlabel("RPM")
        self.ax.set_ylabel("Torque (Nm)")
        self.ax2.set_ylabel("Power (HP)")
        self.ax.set_title("Torque & Power vs RPM Dynograph")
        self.ax.set_xlim(0, 10000)
        self.ax.set_ylim(0, 1000)
        self.ax2.set_ylim(0, 1000)
        lines1, labels1 = self.ax.get_legend_handles_labels()
        lines2, labels2 = self.ax2.get_legend_handles_labels()
        self.ax.legend(lines1 + lines2, labels1 + labels2)
        self.canvas.draw()
#---------------------------------------|
    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with ENGINE CSVs")
        if folder:
            import os
            all_files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".csv")]
            if not all_files:
                return

            dataframes = []
            for f in all_files:
                try:
                    df = pd.read_csv(f)
                    dataframes.append(df)
                except Exception as e:
                    print(f"Error reading {f}: {e}")
                    continue

            if dataframes:
                self.data = pd.concat(dataframes, ignore_index=True)
                self.file_list.clear()

                if "CarLabel" in self.data.columns:
                    id_col = "CarLabel"
                elif "CarId" in self.data.columns:
                    id_col = "CarId"
                else:
                    id_col = self.data.columns[0]

                for _, row in self.data.iterrows():
                    label = row.get(id_col, "Unknown")
                    self.file_list.addItem(str(label))
#---------------------------------------|
    def save_changes(self):
        selected_items = self.file_list.selectedItems()
        if not selected_items or self.data is None:
            return
        car_label = selected_items[0].text()
        idx = self.data[self.data["CarLabel"] == car_label].index
        if len(idx) == 0:
            return
        idx = idx[0]
        try:
            for col, edit in self.edit_fields.items():
                val = edit.text()
                dtype = self.data[col].dtype
                if pd.api.types.is_integer_dtype(dtype):
                    try:
                        self.data.at[idx, col] = int(val)
                        edit.setStyleSheet("")  
                    except Exception:
                        edit.setStyleSheet("background-color: #ffcccc;")  
                        continue
                elif pd.api.types.is_float_dtype(dtype):
                    try:
                        self.data.at[idx, col] = float(val)
                        edit.setStyleSheet("")
                    except Exception:
                        edit.setStyleSheet("background-color: #ffcccc;")
                        continue
                else:
                    self.data.at[idx, col] = val
                    edit.setStyleSheet("")
        except Exception as e:
            print("Error updating values:", e)
            self.plot_selected()
            self.fill_edit_fields()    
#---------------------------------------|
    def save_as(self):
        if self.data is None:
            return
        file, _ = QFileDialog.getSaveFileName(
            self,
            "Save As",
            "",
            "CSV Files (*.csv)"
        )
        if file:
            try:
                self.data.to_csv(file, index=False)
                print(f"Saved as {file}")
            except Exception as e:
                print(f"Error saving file: {e}")
#---------------------------------------|
    def load_csv(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select ENGINE CSV", "", "CSV Files (*.csv)")
        if file:
            self.data = pd.read_csv(file)
            self.file_list.clear()

            if "CarLabel" in self.data.columns:  # GT3 / Concept
                id_col = "CarLabel"
            elif "CarId" in self.data.columns:  # GT2
                id_col = "CarId"
            else:
                id_col = self.data.columns[0]  # fallback

            for _, row in self.data.iterrows():
                label = row.get(id_col, "Unknown")
                self.file_list.addItem(str(label))
#---------------------------------------|
    def extract_number(self, s):
        if isinstance(s, str):
            match = re.search(r'\d+', s)
            return int(match.group()) if match else 0
        try:
            return int(s)
        except Exception:
            return 0
#---------------------------------------|
    def fill_edit_fields(self):
        # Clear previous editors
        for i in reversed(range(self.bottom_layout.count())):
            widget = self.bottom_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
        self.edit_fields = {}

        selected_items = self.file_list.selectedItems()
        if not selected_items or self.data is None:
            return

        car_label = selected_items[0].text()

        # Detect identifier column (CarLabel for GT4, CarId for GT2)
        if "CarLabel" in self.data.columns:
            row = self.data[self.data["CarLabel"] == car_label].iloc[0]
        elif "CarId" in self.data.columns:
            row = self.data[self.data["CarId"] == car_label].iloc[0]
        else:
            row = self.data.iloc[0]  # fallback

        fields_per_row = 6  # Number of fields per row in the grid
        columns = list(self.data.columns)
        for idx, col in enumerate(columns):
            grid_row = idx // fields_per_row
            grid_col = (idx % fields_per_row) * 2  # label, then editor

            label = QLabel(f"{col}:")
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            label_font = label.font()
            label_font.setPointSize(10)
            label.setFont(label_font)

            dtype = self.data[col].dtype
            edit = QLineEdit(str(row[col]))
            edit_font = edit.font()
            edit.setFont(edit_font)
            edit_font.setPointSize(30)
            edit.setFixedHeight(30)
            edit.setMaximumWidth(200)

            if pd.api.types.is_integer_dtype(dtype):
                edit.setValidator(QtGui.QIntValidator())
            elif pd.api.types.is_float_dtype(dtype):
                edit.setValidator(QtGui.QDoubleValidator())

            self.bottom_layout.addWidget(label, grid_row, grid_col)
            self.bottom_layout.addWidget(edit, grid_row, grid_col + 1)
            self.edit_fields[col] = edit
#---------------------------------------|
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DynoApp()
    window.show()
    sys.exit(app.exec())
#---------------------------------------|