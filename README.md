# 🎙️ YouTube Transcriber

Transcreve vídeos do YouTube (inclusive longos, como 4h+) usando AssemblyAI
e exporta em `.txt`, `.srt` e `.json`.

---

## 1. Pré-requisitos

- Python 3.9+
- Conta gratuita na AssemblyAI: https://www.assemblyai.com
  - Tem ~5h de crédito gratuito no cadastro

---

## 2. Instalação

```bash
# Instalar dependências Python
pip install yt-dlp assemblyai python-dotenv
```

---

## 3. Configuração

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite e coloque sua chave da AssemblyAI
# (Dashboard → API Keys em assemblyai.com)
nano .env
```

---

## 4. Uso

```bash
# Uso básico
python transcribe_youtube.py "https://www.youtube.com/watch?v=XXXXX"

# Com detecção de idioma automática (vídeos não-inglês)
python transcribe_youtube.py "https://www.youtube.com/watch?v=XXXXX" --translate

# Pular o download (usar MP3 já baixado)
python transcribe_youtube.py "https://..." --skip-download ./output/meu_video.mp3

# Pasta de saída customizada
python transcribe_youtube.py "https://..." --output-dir ~/Downloads/transcricoes
```

---

## 5. Arquivos gerados

Tudo vai para a pasta `./output/`:

| Arquivo | Descrição |
|---------|-----------|
| `titulo_video.mp3` | Áudio baixado do YouTube |
| `titulo_video.txt` | Transcrição em texto corrido |
| `titulo_video.srt` | Legenda com timestamps (abre no VLC, mpv) |
| `titulo_video.json` | Resposta completa da API (cache) |

---

## 6. Retomar sem re-transcrever

Se o script foi interrompido após a transcrição, o cache `.json` evita
cobranças desnecessárias. Basta rodar novamente — ele detecta o cache
e apenas re-exporta os arquivos.

Para forçar uma nova transcrição, delete o `.json`:
```bash
rm output/titulo_video.json
```

---

## 7. Traduzir o resultado para português

Após gerar o `.txt`, você tem algumas opções:

- **DeepL** (https://deepl.com) — cola ou sobe o `.txt` direto
- **Claude / ChatGPT** — cole em blocos de ~3000 palavras
- **Script de tradução** — peça pra gerar um script que traduz em chunks via API

---

## 8. Estimativas de tempo e custo

| Duração do vídeo | Tempo de transcrição | Custo AssemblyAI |
|---|---|---|
| 1 hora | ~5 min | ~$0.37 |
| 4 horas | ~20 min | ~$1.48 |
| 4h18min | ~22 min | ~$1.60 |

O plano gratuito cobre as primeiras ~5 horas. Depois disso é pago.
