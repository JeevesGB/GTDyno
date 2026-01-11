import sys
from PyQt6.QtWidgets import QApplication
from core.engine_model import EngineModel
from app.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    engine = EngineModel(
        car_id="a2ran",
        layout="I4",
        valvetrain="DOHC",
        aspiration="NA",
        sound_file=21507,
        displacement=1839,
        idle_rpm=250,
        max_rpm=7000,
        redline_rpm=6500,
        curve=[
            (1000, 122.0),
            (1500, 128.9),
            (2000, 137.9),
            (2500, 144.7),
            (3000, 145.6),
        ],
    )

    win = MainWindow(engine)
    win.show()
    sys.exit(app.exec())
