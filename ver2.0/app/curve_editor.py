from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem

class CurveEditor(QTableWidget):
    def __init__(self, engine, on_change):
        super().__init__()
        self.engine = engine
        self.on_change = on_change
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["RPM", "Torque (Nm)"])
        self.refresh()

        self.cellChanged.connect(self._cell_changed)

    def refresh(self):
        self.setRowCount(len(self.engine.curve))
        for row, (rpm, torque) in enumerate(self.engine.curve):
            self.setItem(row, 0, QTableWidgetItem(str(rpm)))
            self.setItem(row, 1, QTableWidgetItem(f"{torque:.1f}"))

    def _cell_changed(self, row, col):
        try:
            rpm = int(self.item(row, 0).text())
            torque = float(self.item(row, 1).text())
            self.engine.curve[row] = (rpm, torque)
            self.on_change()
        except Exception:
            pass
