from pathlib import Path

import requests

TIMEOUT = 120

def get_error_message(response):
  try:
    detail = response.json().get('detail')
  except (ValueError, AttributeError):
    detail = None

  if isinstance(detail, str):
    return detail
  return f'O servidor respondeu com o erro {response.status_code}.'


def upload_audio(server_url, file_path, processing_type, speed_factor, target_bitrate, target_format):
  data = {'processing_type': processing_type}
  if processing_type == 'speed':
    data['speed_factor'] = speed_factor
  elif processing_type == 'bitrate':
    data['target_bitrate'] = target_bitrate
  elif processing_type == 'convert':
    data['target_format'] = target_format

  try:
    with open(file_path, 'rb') as file:
      files = {'file': (Path(file_path).name, file)}
      response = requests.post(server_url + '/api/upload', data=data, files=files, timeout=TIMEOUT)
  except requests.RequestException:
    raise RuntimeError('Não foi possível falar com o servidor. Confira o endereço e se ele está rodando.')

  if response.status_code != 200:
    raise RuntimeError(get_error_message(response))
  return response.json()
