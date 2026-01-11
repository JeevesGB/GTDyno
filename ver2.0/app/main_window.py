from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from plot.dyno_plot import plot_engine
from core.gt2_exporter import export_gt2_engine_csv
from app.curve_editor import CurveEditor

class MainWindow(QMainWindow):
    def __init__(self, engine):
        super().__init__()
        self.engine = engine
        self.setWindowTitle("GTDyno v2.0")

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax2 = self.ax.twinx()
        self.canvas = FigureCanvas(self.fig)

        self.editor = CurveEditor(engine, self.redraw)

        save_btn = QPushButton("Export GT2 CSV")
        save_btn.clicked.connect(self.save_csv)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.editor)
        layout.addWidget(save_btn)

        w = QWidget()
        w.setLayout(layout)
        self.setCentralWidget(w)

        self.redraw()

    def redraw(self):
        plot_engine(
            self.ax,
            self.ax2,
            self.engine,
            colors={"torque": "#00FFFB", "power": "#8CFF00"},
        )
        self.canvas.draw()

    def save_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV (*.csv)")
        if path:
            export_gt2_engine_csv(self.engine, path)
