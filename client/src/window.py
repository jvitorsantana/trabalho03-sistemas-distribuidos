from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
  QApplication,
  QComboBox,
  QDoubleSpinBox,
  QFileDialog,
  QFormLayout,
  QGroupBox,
  QHBoxLayout,
  QHeaderView,
  QLabel,
  QLineEdit,
  QMainWindow,
  QMessageBox,
  QPushButton,
  QTableWidget,
  QTableWidgetItem,
  QVBoxLayout,
  QWidget,
)

import api
import config
from waveform_dialog import WaveformDialog

PROCESSINGS = {
  'normalize': 'Normalização de volume',
  'mono': 'Conversão para mono',
  'speed': 'Alteração de velocidade',
  'bitrate': 'Redução da taxa de bits',
  'convert': 'Conversão de formato',
}

HISTORY_COLUMNS = ['Data', 'Arquivo', 'Processamento', 'Formato', 'Duração', 'Tamanho']


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
    self.resize(950, 850)

    self.file_path = None
    self.file_info = ''
    self.history_audios = []

    # Player do arquivo escolhido no computador
    self.player = QMediaPlayer()
    self.audio_output = QAudioOutput()
    self.player.setAudioOutput(self.audio_output)
    self.player.durationChanged.connect(self.show_duration)

    # Player dos áudios que estão no servidor
    self.server_player = QMediaPlayer()
    self.server_audio_output = QAudioOutput()
    self.server_player.setAudioOutput(self.server_audio_output)
    self.server_player.errorOccurred.connect(self.show_player_error)

    central = QWidget()
    layout = QVBoxLayout(central)
    layout.addWidget(self.build_server_box())
    layout.addWidget(self.build_file_box())
    layout.addWidget(self.build_processing_box())
    layout.addWidget(self.build_details_box())
    layout.addWidget(self.build_history_box(), 1)
    self.setCentralWidget(central)

    QTimer.singleShot(0, self.refresh_history)

  def build_server_box(self):
    self.server_input = QLineEdit(config.SERVER_URL)
    self.server_input.setPlaceholderText('Exemplo: 192.168.0.10:8000')
    self.server_input.returnPressed.connect(self.refresh_history)

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
    self.play_button.clicked.connect(self.play_local)
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

  def build_details_box(self):
    self.result_label = QLabel('Envie um áudio ou selecione um item do histórico.')
    self.result_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

    box = QGroupBox('Detalhes do áudio')
    box_layout = QVBoxLayout(box)
    box_layout.addWidget(self.result_label)
    return box

  def build_history_box(self):
    self.refresh_button = QPushButton('Atualizar histórico')
    self.refresh_button.clicked.connect(self.refresh_history)
    self.play_original_button = QPushButton('Tocar original')
    self.play_original_button.clicked.connect(self.play_original_from_server)
    self.play_processed_button = QPushButton('Tocar processado')
    self.play_processed_button.clicked.connect(self.play_processed_from_server)
    self.stop_server_button = QPushButton('Parar')
    self.stop_server_button.clicked.connect(self.server_player.stop)

    self.download_original_button = QPushButton('Baixar original')
    self.download_original_button.clicked.connect(self.download_original)
    self.download_processed_button = QPushButton('Baixar processado')
    self.download_processed_button.clicked.connect(self.download_processed)
    self.waveform_button = QPushButton('Ver forma de onda')
    self.waveform_button.clicked.connect(self.show_waveform)

    self.history_status = QLabel('')

    self.history_table = QTableWidget(0, len(HISTORY_COLUMNS))
    self.history_table.setHorizontalHeaderLabels(HISTORY_COLUMNS)
    self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
    self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
    self.history_table.verticalHeader().setVisible(False)
    self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
    self.history_table.setToolTip('Clique duas vezes para tocar o áudio processado')
    self.history_table.currentCellChanged.connect(self.show_selected_details)
    self.history_table.cellDoubleClicked.connect(self.play_double_clicked)

    # Primeira linha: atualizar e tocar
    play_row = QHBoxLayout()
    play_row.addWidget(self.refresh_button)
    play_row.addWidget(self.play_original_button)
    play_row.addWidget(self.play_processed_button)
    play_row.addWidget(self.stop_server_button)
    play_row.addStretch()

    # Segunda linha: baixar e ver a forma de onda
    files_row = QHBoxLayout()
    files_row.addWidget(self.download_original_button)
    files_row.addWidget(self.download_processed_button)
    files_row.addWidget(self.waveform_button)
    files_row.addStretch()

    box = QGroupBox('Histórico')
    box_layout = QVBoxLayout(box)
    box_layout.addLayout(play_row)
    box_layout.addLayout(files_row)
    box_layout.addWidget(self.history_status)
    box_layout.addWidget(self.history_table)
    return box

  def server_url(self):
    url = self.server_input.text().strip().rstrip('/')
    if not url.startswith('http://') and not url.startswith('https://'):
      url = 'http://' + url
    return url

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

  def start_waiting(self, label, message):
    # Mostra a mensagem no texto indicado e troca o cursor pelo de espera
    label.setText(message)
    QApplication.setOverrideCursor(Qt.WaitCursor)
    QApplication.processEvents()

  def stop_waiting(self):
    QApplication.restoreOverrideCursor()

  def send_file(self):
    self.send_button.setEnabled(False)
    self.start_waiting(self.result_label, 'Enviando e processando, aguarde...')

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
    self.refresh_history()
    self.history_table.selectRow(0)
    self.show_details(audio, 'Áudio enviado e processado com sucesso!')

  def show_details(self, audio, title):
    processing = PROCESSINGS.get(audio['processing_type'], audio['processing_type'])
    audio_format = audio['original_ext'].upper()
    size = format_size(audio['size_bytes'] or 0)
    duration = format_duration(audio['duration_sec'] or 0)
    bitrate = (audio['bitrate'] or 0) // 1000
    date = format_date(audio['created_at'])

    lines = [
      title,
      f'Arquivo: {audio["original_name"]}   |   ID: {audio["id"]}',
      f'Processamento: {processing}',
      'Informações do arquivo original:',
      f'Formato: {audio_format}   |   Tamanho: {size}   |   Duração: {duration}',
      f'Taxa de amostragem: {audio["sample_rate"]} Hz   |   Canais: {audio["channels"]}   |   Bitrate: {bitrate} kbps',
      f'Recebido em: {date}',
    ]
    self.result_label.setText('\n'.join(lines))

  def refresh_history(self):
    self.start_waiting(self.history_status, 'Carregando histórico...')

    try:
      audios = api.get_history(self.server_url())
    except RuntimeError as error:
      self.stop_waiting()
      self.history_status.setText(str(error))
      return

    self.stop_waiting()
    self.show_history(audios)

  def show_history(self, audios):
    self.history_audios = audios
    self.history_table.setRowCount(len(audios))

    for row, audio in enumerate(audios):
      processing = PROCESSINGS.get(audio['processing_type'], audio['processing_type'] or '-')
      values = [
        format_date(audio['created_at']),
        audio['original_name'],
        processing,
        audio['original_ext'].upper(),
        format_duration(audio['duration_sec'] or 0),
        format_size(audio['size_bytes'] or 0),
      ]
      for column, value in enumerate(values):
        self.history_table.setItem(row, column, QTableWidgetItem(value))

    self.history_status.setText(f'{len(audios)} áudio(s) no servidor.')

  def show_selected_details(self, row, column, previous_row, previous_column):
    if row < 0 or row >= len(self.history_audios):
      return
    self.show_details(self.history_audios[row], 'Áudio selecionado no histórico:')

  def selected_audio(self):
    # Devolve o áudio da linha selecionada, ou None se nada estiver selecionado
    row = self.history_table.currentRow()
    if row < 0 or row >= len(self.history_audios):
      self.history_status.setText('Selecione um áudio na tabela primeiro.')
      return None
    return self.history_audios[row]

  def play_local(self):
    self.server_player.stop()
    self.player.play()

  def play_original_from_server(self):
    self.play_from_server('original')

  def play_processed_from_server(self):
    self.play_from_server('processed')

  def play_double_clicked(self, row, column):
    self.play_from_server('processed')

  def play_from_server(self, kind):
    audio = self.selected_audio()
    if audio is None:
      return

    url = api.get_file_url(self.server_url(), audio['id'], kind)

    self.player.stop()
    self.server_player.setSource(QUrl(url))
    self.server_player.play()

    if kind == 'original':
      version = 'original'
    else:
      version = 'processado'
    self.history_status.setText(f'Tocando o áudio {version} de {audio["original_name"]}.')

  def show_player_error(self, error, error_string):
    self.history_status.setText('Não foi possível tocar o áudio: ' + error_string)

  def download_original(self):
    self.download_file('original')

  def download_processed(self):
    self.download_file('processed')

  def download_file(self, kind):
    audio = self.selected_audio()
    if audio is None:
      return

    # Sugere um nome como musica_original.mp3 ou musica_processado.ogg
    name = Path(audio['original_name']).stem
    if kind == 'original':
      ext = audio['original_ext']
      suggested_name = f'{name}_original.{ext}'
    else:
      ext = audio['path_processed'].rsplit('.', 1)[-1]
      suggested_name = f'{name}_processado.{ext}'

    path, selected_filter = QFileDialog.getSaveFileName(
      self, 'Salvar áudio', suggested_name, f'Áudio (*.{ext})'
    )
    if not path:
      return

    self.start_waiting(self.history_status, 'Baixando o arquivo...')
    try:
      api.download_file(self.server_url(), audio['id'], kind, path)
    except RuntimeError as error:
      self.stop_waiting()
      self.history_status.setText('O download falhou.')
      QMessageBox.warning(self, 'Erro no download', str(error))
      return

    self.stop_waiting()
    self.history_status.setText(f'Arquivo salvo em {path}')

  def show_waveform(self):
    audio = self.selected_audio()
    if audio is None:
      return

    self.start_waiting(self.history_status, 'Carregando a forma de onda...')
    try:
      image_bytes = api.get_file_content(self.server_url(), audio['id'], 'waveform')
    except RuntimeError as error:
      self.stop_waiting()
      self.history_status.setText('Não foi possível carregar a forma de onda.')
      QMessageBox.warning(self, 'Erro na forma de onda', str(error))
      return

    self.stop_waiting()
    self.history_status.setText('')
    dialog = WaveformDialog(self, f'Forma de onda de {audio["original_name"]}', image_bytes)
    dialog.exec()
