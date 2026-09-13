import os
import librosa
import librosa.display
import matplotlib
matplotlib.use("Agg")  # evita abrir janelas gráficas (necessário em servidor)
import matplotlib.pyplot as plt


def generate_waveform(audio_path: str, folder_path: str) -> str:
    """Gera waveform.png a partir do arquivo de áudio e retorna o caminho salvo."""
    y, sr = librosa.load(audio_path, sr=None)

    plt.figure(figsize=(10, 3))
    librosa.display.waveshow(y, sr=sr)
    plt.axis("off")  # imagem limpa, sem eixos

    output_path = os.path.join(folder_path, "waveform.png")
    plt.savefig(output_path, bbox_inches="tight", pad_inches=0)
    plt.close()

    return output_path