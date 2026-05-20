# 🎙️ YouTube Transcriber

Transcreve vídeos do YouTube (inclusive longos, como 4h+) usando AssemblyAI
e exporta em `.txt`, `.srt` e `.json`.

---

## 1. Pré-requisitos

- [Go 1.21+](https://go.dev/dl/)
- `yt-dlp`: `pip install yt-dlp`
- Conta gratuita na AssemblyAI: https://www.assemblyai.com
  - Tem ~5h de crédito gratuito no cadastro

---

## 2. Instalação

```bash
# Clonar e baixar dependências
git clone https://github.com/thiagotn/yt-transcriber.git
cd yt-transcriber
go mod tidy

# Compilar (opcional)
go build -o yt-transcriber .
```

---

## 3. Configuração

```bash
cp .env.example .env
# Edite e coloque sua chave da AssemblyAI
# (Dashboard → API Keys em assemblyai.com)
nano .env
```

---

## 4. Uso

```bash
# Uso básico
go run main.go "https://www.youtube.com/watch?v=XXXXX"

# Apenas baixar o MP3 (sem transcrever)
go run main.go "https://www.youtube.com/watch?v=XXXXX" --audio-only

# Com detecção de idioma automática (vídeos não-inglês)
go run main.go "https://www.youtube.com/watch?v=XXXXX" --translate

# Pular o download (usar MP3 já baixado)
go run main.go "https://..." --skip-download ./output/meu_video.mp3

# Pasta de saída customizada
go run main.go "https://..." --output-dir ~/Downloads/transcricoes

# Usando o binário compilado
./yt-transcriber "https://www.youtube.com/watch?v=XXXXX"
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
e re-exporta os arquivos `.txt` e `.srt` automaticamente.

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
