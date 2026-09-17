# Trabalho 03 — Processamento de Áudio Distribuído

Sistema cliente-servidor para envio, processamento e consulta de arquivos de áudio. O cliente desktop envia o arquivo e o tipo de processamento; o servidor aplica a operação com FFmpeg, gera a forma de onda, persiste metadados no PostgreSQL e devolve o resultado para reprodução, download e histórico.

## Descrição do projeto

O trabalho implementa um serviço de processamento de áudio em arquitetura cliente-servidor:

- O **cliente** (PySide6) escolhe um arquivo local (`mp3`, `wav`, `ogg`, `flac` ou `m4a`), seleciona o processamento, envia o áudio ao servidor e acompanha o histórico.
- O **servidor** (FastAPI) recebe o upload, extrai metadados com `ffprobe`, processa com FFmpeg, gera `waveform.png` com Librosa/Matplotlib e registra o job no banco.
- Os arquivos ficam no disco em pastas por data e UUID. Cada job guarda o original, o processado, a forma de onda e um `meta.json`.

Funcionalidades principais do cliente:

- Configuração do endereço do servidor
- Pré-visualização do áudio local (tocar / parar)
- Envio com parâmetros específicos (velocidade, bitrate ou formato)
- Histórico de processamentos
- Detalhes do original e do processado (formato, tamanho, duração, sample rate, canais, bitrate)
- Reprodução e download do original e do processado
- Visualização da forma de onda

## Arquitetura utilizada

Arquitetura **cliente-servidor** com comunicação HTTP/REST. O cliente não processa o áudio: ele apenas envia o arquivo e consome os endpoints da API.

```
┌─────────────────────────┐         HTTP / REST          ┌──────────────────────────────────┐
│  Cliente desktop        │  POST /api/upload            │  Servidor FastAPI (Uvicorn)      │
│  PySide6 + requests     │  GET  /api/history           │                                  │
│                         │  GET  /api/audio/{id}/{kind} │  routers → services              │
│  window / api / config  │  GET  /api/audio/{id}/info/  │    FFmpeg / ffprobe              │
└─────────────────────────┘           :8000              │    Librosa (waveform)            │
                                                         │    Storage em disco              │
                                                         └──────────────┬───────────────────┘
                                                                        │
                                                         ┌──────────────▼───────────────────┐
                                                         │  PostgreSQL 16                   │
                                                         │  tabela audios                   │
                                                         └──────────────────────────────────┘
```

Camadas do backend:

| Camada | Papel |
| --- | --- |
| `app/main.py` | Sobe a API, cria as tabelas e registra os routers |
| `app/routers/` | Endpoints de upload, histórico e arquivos |
| `app/services/` | FFmpeg, forma de onda e armazenamento em disco |
| `app/models.py` | Modelo SQLAlchemy (`Audio`) e schema Pydantic de resposta |
| `app/database.py` | Engine, sessão e `get_db` |
| `app/config.py` | `DATABASE_URL`, pasta de storage e caminhos do FFmpeg |

API:

| Método | Rota | Descrição |
| --- | --- | --- |
| `POST` | `/api/upload` | Envia o áudio e o tipo de processamento |
| `GET` | `/api/history` | Lista os processamentos (mais recentes primeiro) |
| `GET` | `/api/audio/{id}/{kind}` | Baixa `original`, `processed` ou `waveform` |
| `GET` | `/api/audio/{id}/info/{kind}` | Metadados do original ou do processado |

O armazenamento em disco segue:

```
storage/
  YYYY-MM-DD/
    <uuid>/
      audio.<ext>
      audio_processed.<ext>
      waveform.png
      meta.json
```

A stack pode subir com Docker Compose (PostgreSQL + backend com FFmpeg) ou em modo local (Postgres no Docker e API via `uv`).

## Instruções de instalação

### Requisitos

- Python **3.12+**
- [uv](https://docs.astral.sh/uv/) (gerenciador de dependências usado no projeto)
- [Docker](https://www.docker.com/) e Docker Compose (banco e, opcionalmente, o servidor)
- FFmpeg e ffprobe (obrigatórios se o servidor rodar fora do Docker)

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd Trabalho03
```

### 2. Banco de dados

Na raiz do projeto (sobe Postgres e também o backend):

```bash
docker compose up --build
```

Somente o Postgres (quando o backend for local):

```bash
docker compose -f backend/docker-compose.yml up -d
```

### 3. Servidor (modo local)

```bash
cd backend
copy .env.example .env
uv sync
```

Instale o FFmpeg no sistema e garanta que `ffmpeg` e `ffprobe` estejam no `PATH`. No Windows, o backend também procura o pacote instalado via WinGet (`Gyan.FFmpeg`).

### 4. Cliente

```bash
cd client
uv sync
```

## Instruções de execução do servidor

### Opção A — Docker (recomendado)

Na raiz:

```bash
docker compose up --build
```

A API fica em `http://localhost:8000`. A documentação interativa do FastAPI fica em `http://localhost:8000/docs`.

O container do backend já inclui FFmpeg. Os arquivos processados são gravados em `backend/storage`.

### Opção B — Local (uv + Uvicorn)

Com o Postgres no ar e o `.env` configurado:

```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API também fica em `http://localhost:8000`.

## Instruções de execução do cliente

Com o servidor rodando:

```bash
cd client
uv run python src/main.py
```

Na tela **Servidor**, informe o endereço da API. O padrão é `http://localhost:8000`. Em outra máquina da rede, use o IP do host, por exemplo `192.168.0.10:8000` (o cliente adiciona `http://` se faltar).

Fluxo típico:

1. Escolher o arquivo de áudio
2. Ouvir o original, se quiser
3. Selecionar o tipo de processamento e os parâmetros
4. Enviar para o servidor
5. Consultar detalhes, histórico, reprodução, download e forma de onda

## Configuração do banco de dados

PostgreSQL 16, criado pelo Docker Compose.

URL usada pelo backend **dentro** da rede Docker (`docker-compose.yml` da raiz):

```text
postgresql://audio_user:audio_pass@postgres:5432/audio_db
```

URL usada pelo backend **local** (`backend/.env.example`):

```text
DATABASE_URL=postgresql://audio_user:audio_pass@localhost:5432/audio_db
```

As tabelas são criadas na subida da API (`Base.metadata.create_all`). A tabela `audios` guarda:

- identificação (`id` UUID)
- nome, extensão, MIME e tamanho do arquivo original
- duração, sample rate, canais e bitrate
- tipo de processamento
- data de criação
- caminhos do original e do processado

## Exemplos de processamento disponíveis

Formatos de entrada aceitos no cliente: **mp3**, **wav**, **ogg**, **flac**, **m4a**.

| Tipo (`processing_type`) | O que faz | Parâmetro extra |
| --- | --- | --- |
| `normalize` | Normaliza o volume (`loudnorm`, alvo I=-16) | — |
| `mono` | Converte para 1 canal | — |
| `speed` | Altera a velocidade sem mudar o tom (`atempo`) | `speed_factor` entre **0.5** e **2.0** (padrão 1.5) |
| `bitrate` | Reduz a taxa de bits | `target_bitrate`: **32k**, **64k**, **96k** ou **128k** (padrão 64k). Se o original não for mp3/m4a, a saída vira mp3 |
| `convert` | Converte o formato | `target_format`: **mp3**, **wav**, **ogg**, **flac** ou **m4a** |

Exemplos:

- Normalizar um `wav` de palestra → `normalize`
- Transformar um estéreo em mono → `mono`
- Acelerar 1.5x um podcast → `speed` com `speed_factor=1.5`
- Compactar um mp3 para 64 kbps → `bitrate` com `target_bitrate=64k`
- Converter `wav` para `ogg` → `convert` com `target_format=ogg`

## Prints da interface

Substitua os links abaixo pelas URLs das imagens.

**Tela principal do cliente (servidor, arquivo, processamento, detalhes e histórico)**

![Tela principal do cliente](COLE_O_LINK_AQUI)

**Envio e detalhes do áudio processado**

![Detalhes do áudio processado](COLE_O_LINK_AQUI)

**Histórico com reprodução e download**

![Histórico de processamentos](COLE_O_LINK_AQUI)

**Forma de onda**

![Janela da forma de onda](COLE_O_LINK_AQUI)

## Prints da organização dos arquivos

**Estrutura do repositório (cliente, backend e Docker Compose)**

![Organização do repositório](COLE_O_LINK_AQUI)

**Pastas do backend (`app`, routers, services)**

![Organização do backend](COLE_O_LINK_AQUI)

**Pastas do cliente (`src`)**

![Organização do cliente](COLE_O_LINK_AQUI)

**Storage no disco (`storage/YYYY-MM-DD/<uuid>/`)**

![Organização do storage](COLE_O_LINK_AQUI)

Referência da árvore do projeto:

```text
Trabalho03/
├── docker-compose.yml          # Postgres + backend
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── docker-compose.yml      # somente Postgres
│   ├── pyproject.toml
│   ├── .env.example
│   ├── storage/                # áudios processados (gerado em runtime)
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models.py
│       ├── routers/
│       │   ├── upload.py
│       │   ├── history.py
│       │   └── files.py
│       └── services/
│           ├── ffmpeg_service.py
│           ├── waveform_service.py
│           └── storage_service.py
└── client/
    ├── pyproject.toml
    └── src/
        ├── main.py
        ├── window.py
        ├── api.py
        ├── config.py
        └── waveform_dialog.py
```
