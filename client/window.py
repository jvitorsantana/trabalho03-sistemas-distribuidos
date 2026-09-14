from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

class MainWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.setWindowTitle('Cliente de Processamento de Áudio')
    self.resize(900, 650)

    central = QWidget()
    layout = QVBoxLayout(central)
    layout.addWidget(QLabel('tá rodando'))
    self.setCentralWidget(central)