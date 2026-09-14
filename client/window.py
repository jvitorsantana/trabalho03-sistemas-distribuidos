from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
  QApplication,
  QComboBox,
  QDoubleSpinBox,
  QFileDialog,
  QFormLayout,
  QGroupBox,
  QHBoxLayout,
  QLabel,
  QLineEdit,
  QMainWindow,
  QMessageBox,
  QPushButton,
  QVBoxLayout,
  QWidget,
)

import api
import config

PROCESSINGS = {
  'normalize': 'Normalização de volume',
  'mono': 'Conversão para mono',
  'speed': 'Alteração de velocidade',
  'bitrate': 'Redução da taxa de bits',
  'convert': 'Conversão de formato',
}


def format_size(size_bytes):
  if size_bytes < 1024 * 1024:
    return f'{size_bytes / 1024:.1f} KB'
  return f'{size_bytes / (1024 * 1024):.1f} MB'


def format_duration(seconds):
  minutes = int(seconds // 60)
  rest = int(seconds % 60)
  return f'{minutes}:{rest:02d}'


def format_date(text):
  date = datetime.fromisoformat(text)
  if date.tzinfo is None:
    date = date.replace(tzinfo=timezone.utc)
  return date.astimezone().strftime('%d/%m/%Y %H:%M')


class MainWindow(QMainWindow):
  def __init__(self):
    super().__init__()
    self.setWindowTitle('Cliente de Processamento de Áudio')
    self.resize(900, 650)

    self.file_path = None
    self.file_info = ''

    # Player do áudio original
    self.player = QMediaPlayer()
    self.audio_output = QAudioOutput()
    self.player.setAudioOutput(self.audio_output)
    self.player.durationChanged.connect(self.show_duration)

    central = QWidget()
    layout = QVBoxLayout(central)
    layout.addWidget(self.build_server_box())
    layout.addWidget(self.build_file_box())
    layout.addWidget(self.build_processing_box())
    layout.addWidget(self.build_result_box())
    layout.addStretch()
    self.setCentralWidget(central)

  def build_server_box(self):
    self.server_input = QLineEdit(config.SERVER_URL)

    box = QGroupBox('Servidor')
    box_layout = QHBoxLayout(box)
    box_layout.addWidget(QLabel('Endereço:'))
    box_layout.addWidget(self.server_input)
    return box

  def build_file_box(self):
    self.choose_button = QPushButton('Escolher arquivo')
    self.choose_button.clicked.connect(self.choose_file)
    self.file_label = QLabel('Nenhum arquivo escolhido')
    self.info_label = QLabel('')

    self.play_button = QPushButton('Tocar')
    self.play_button.clicked.connect(self.player.play)
    self.stop_button = QPushButton('Parar')
    self.stop_button.clicked.connect(self.player.stop)
    self.play_button.setEnabled(False)
    self.stop_button.setEnabled(False)

    file_row = QHBoxLayout()
    file_row.addWidget(self.choose_button)
    file_row.addWidget(self.file_label, 1)

    player_row = QHBoxLayout()
    player_row.addWidget(QLabel('Original:'))
    player_row.addWidget(self.play_button)
    player_row.addWidget(self.stop_button)
    player_row.addStretch()

    box = QGroupBox('Arquivo de áudio')
    box_layout = QVBoxLayout(box)
    box_layout.addLayout(file_row)
    box_layout.addWidget(self.info_label)
    box_layout.addLayout(player_row)
    return box

  def build_processing_box(self):
    self.processing_combo = QComboBox()
    for value, label in PROCESSINGS.items():
      self.processing_combo.addItem(label, value)
    self.processing_combo.currentIndexChanged.connect(self.update_options)

    self.speed_input = QDoubleSpinBox()
    self.speed_input.setRange(0.5, 2.0)
    self.speed_input.setSingleStep(0.1)
    self.speed_input.setValue(1.5)

    self.bitrate_combo = QComboBox()
    self.bitrate_combo.addItems(['32k', '64k', '96k', '128k'])
    self.bitrate_combo.setCurrentText('64k')

    self.format_combo = QComboBox()
    self.format_combo.addItems(['mp3', 'wav', 'ogg', 'flac', 'm4a'])

    self.send_button = QPushButton('Enviar para o servidor')
    self.send_button.setEnabled(False)
    self.send_button.clicked.connect(self.send_file)

    box = QGroupBox('Processamento')
    form = QFormLayout(box)
    form.addRow('Tipo:', self.processing_combo)
    form.addRow('Velocidade:', self.speed_input)
    form.addRow('Taxa de bits:', self.bitrate_combo)
    form.addRow('Formato de saída:', self.format_combo)
    form.addRow(self.send_button)

    self.update_options()
    return box

  def build_result_box(self):
    self.result_label = QLabel('Nenhum áudio enviado ainda.')
    self.result_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

    box = QGroupBox('Resultado do servidor')
    box_layout = QVBoxLayout(box)
    box_layout.addWidget(self.result_label)
    return box

  def server_url(self):
    return self.server_input.text().strip().rstrip('/')

  def choose_file(self):
    path, selected_filter = QFileDialog.getOpenFileName(
      self, 'Escolher áudio', '', 'Áudios (*.mp3 *.wav *.ogg *.flac *.m4a)'
    )
    if path:
      self.load_file(path)

  def load_file(self, path):
    self.file_path = Path(path)
    size = self.file_path.stat().st_size
    ext = self.file_path.suffix.lstrip('.').upper()

    self.file_label.setText(self.file_path.name)
    self.file_info = f'Formato: {ext}   |   Tamanho: {format_size(size)}'
    self.info_label.setText(self.file_info + '   |   Duração: carregando...')

    self.player.stop()
    self.player.setSource(QUrl.fromLocalFile(str(self.file_path)))
    self.play_button.setEnabled(True)
    self.stop_button.setEnabled(True)
    self.send_button.setEnabled(True)

  def show_duration(self, duration_ms):
    if duration_ms > 0:
      duration = format_duration(duration_ms / 1000)
      self.info_label.setText(self.file_info + '   |   Duração: ' + duration)

  def update_options(self):
    processing = self.processing_combo.currentData()
    self.speed_input.setEnabled(processing == 'speed')
    self.bitrate_combo.setEnabled(processing == 'bitrate')
    self.format_combo.setEnabled(processing == 'convert')

  def start_waiting(self, message):
    self.result_label.setText(message)
    QApplication.setOverrideCursor(Qt.WaitCursor)
    QApplication.processEvents()

  def stop_waiting(self):
    QApplication.restoreOverrideCursor()

  def send_file(self):
    self.send_button.setEnabled(False)
    self.start_waiting('Enviando e processando, aguarde...')

    try:
      audio = api.upload_audio(
        self.server_url(),
        self.file_path,
        self.processing_combo.currentData(),
        self.speed_input.value(),
        self.bitrate_combo.currentText(),
        self.format_combo.currentText(),
      )
    except RuntimeError as error:
      self.stop_waiting()
      self.send_button.setEnabled(True)
      self.result_label.setText('O envio falhou.')
      QMessageBox.warning(self, 'Erro no envio', str(error))
      return

    self.stop_waiting()
    self.send_button.setEnabled(True)
    self.show_result(audio)

  def show_result(self, audio):
    processing = PROCESSINGS.get(audio['processing_type'], audio['processing_type'])
    audio_format = audio['original_ext'].upper()
    size = format_size(audio['size_bytes'] or 0)
    duration = format_duration(audio['duration_sec'] or 0)
    bitrate = (audio['bitrate'] or 0) // 1000
    date = format_date(audio['created_at'])

    lines = [
      'Áudio enviado e processado com sucesso!',
      f'ID: {audio["id"]}',
      f'Processamento: {processing}',
      'Informações do arquivo original:',
      f'Formato: {audio_format}   |   Tamanho: {size}   |   Duração: {duration}',
      f'Taxa de amostragem: {audio["sample_rate"]} Hz   |   Canais: {audio["channels"]}   |   Bitrate: {bitrate} kbps',
      f'Recebido em: {date}',
    ]
    self.result_label.setText('\n'.join(lines))
