from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

MAX_WIDTH = 900


class WaveformDialog(QDialog):
  def __init__(self, parent, title, image_bytes):
    super().__init__(parent)
    self.setWindowTitle(title)

    pixmap = QPixmap()
    pixmap.loadFromData(image_bytes)

    self.image_label = QLabel()
    self.image_label.setAlignment(Qt.AlignCenter)
    if pixmap.isNull():
      self.image_label.setText('Não foi possível abrir a imagem da forma de onda.')
    else:
      if pixmap.width() > MAX_WIDTH:
        pixmap = pixmap.scaledToWidth(MAX_WIDTH, Qt.SmoothTransformation)
      self.image_label.setPixmap(pixmap)

    close_button = QPushButton('Fechar')
    close_button.clicked.connect(self.accept)

    layout = QVBoxLayout(self)
    layout.addWidget(self.image_label)
    layout.addWidget(close_button, alignment=Qt.AlignRight)
