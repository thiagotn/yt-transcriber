#!/usr/bin/env python3
"""
transcribe_youtube.py
─────────────────────────────────────────────────────────────────────────────
Faz download do áudio de um vídeo do YouTube, envia para a AssemblyAI
transcrever (em inglês), e salva o resultado em três formatos:
  - .txt  → texto corrido
  - .srt  → legenda com timestamps (pronto pra usar em players)
  - .json → resposta completa da API (útil para debug ou reprocessamento)

Uso:
    python transcribe_youtube.py <URL_DO_VIDEO> [--translate]

Exemplos:
    python transcribe_youtube.py "https://www.youtube.com/watch?v=XXXXX"
    python transcribe_youtube.py "https://www.youtube.com/watch?v=XXXXX" --translate

Dependências (instalar antes de rodar):
    pip install yt-dlp assemblyai python-dotenv

Variável de ambiente necessária:
    ASSEMBLYAI_API_KEY=sua_chave_aqui
    (coloque num arquivo .env na mesma pasta, ou exporte no terminal)

Conta gratuita AssemblyAI: https://www.assemblyai.com
    → Tem ~5h de crédito gratuito no cadastro, suficiente pra um vídeo de 4h+.

Autor: gerado para uso pessoal
─────────────────────────────────────────────────────────────────────────────
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ─── Dependências externas ───────────────────────────────────────────────────

def check_and_import():
    """Verifica se as dependências estão instaladas e importa."""
    missing = []
    try:
        import assemblyai
    except ImportError:
        missing.append("assemblyai")
    try:
        import dotenv
    except ImportError:
        missing.append("python-dotenv")

    if missing:
        print(f"[ERRO] Dependências faltando: {', '.join(missing)}")
        print(f"       Rode: pip install {' '.join(missing)}")
        sys.exit(1)

    # Verifica yt-dlp (ferramenta de linha de comando)
    result = subprocess.run(["yt-dlp", "--version"], capture_output=True)
    if result.returncode != 0:
        print("[ERRO] yt-dlp não encontrado.")
        print("       Rode: pip install yt-dlp")
        sys.exit(1)

check_and_import()

import assemblyai as aai
from dotenv import load_dotenv

# ─── Configuração ────────────────────────────────────────────────────────────

load_dotenv()  # Carrega .env se existir

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

if not ASSEMBLYAI_API_KEY:
    print("[ERRO] Variável ASSEMBLYAI_API_KEY não encontrada.")
    print("       Crie um arquivo .env com: ASSEMBLYAI_API_KEY=sua_chave")
    print("       Ou exporte: export ASSEMBLYAI_API_KEY=sua_chave")
    sys.exit(1)

aai.settings.api_key = ASSEMBLYAI_API_KEY

# ─── Funções utilitárias ─────────────────────────────────────────────────────

def log(msg: str, emoji: str = "→"):
    """Print com timestamp simples."""
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {emoji}  {msg}")


def sanitize_filename(name: str) -> str:
    """Remove caracteres inválidos para nome de arquivo."""
    invalid = r'\/:*?"<>|'
    for ch in invalid:
        name = name.replace(ch, "_")
    return name[:80]  # Limita o tamanho


# ─── Etapa 1: Download do áudio ──────────────────────────────────────────────

def download_audio(url: str, output_dir: Path) -> tuple[Path, str]:
    """
    Baixa o áudio do vídeo em formato MP3 usando yt-dlp.
    Retorna o caminho do arquivo MP3 e o título do vídeo.
    """
    log("Obtendo informações do vídeo...", "🔍")

    # Primeiro pega o título sem baixar nada
    result = subprocess.run(
        ["yt-dlp", "--get-title", url],
        capture_output=True,
        text=True
    )
    title = result.stdout.strip() if result.returncode == 0 else "video"
    safe_title = sanitize_filename(title)

    audio_path = output_dir / f"{safe_title}.mp3"

    # Se já baixou antes, reutiliza
    if audio_path.exists():
        log(f"Áudio já existe, pulando download: {audio_path.name}", "✅")
        return audio_path, title

    log(f"Baixando áudio: {title}", "⬇️")
    log("(Isso pode levar alguns minutos dependendo da sua conexão)", "⏳")

    cmd = [
        "yt-dlp",
        "-x",                          # Extrai apenas o áudio
        "--audio-format", "mp3",       # Formato de saída
        "--audio-quality", "0",        # Melhor qualidade
        "--no-playlist",               # Não baixa playlists
        "-o", str(audio_path),         # Caminho de saída
        url
    ]

    result = subprocess.run(cmd, capture_output=False)  # Mostra progresso

    if result.returncode != 0:
        print("[ERRO] Falha no download. Verifique a URL e tente novamente.")
        sys.exit(1)

    if not audio_path.exists():
        # yt-dlp às vezes adiciona extensão automaticamente
        # Procura por qualquer MP3 gerado
        mp3_files = list(output_dir.glob(f"{safe_title}*.mp3"))
        if mp3_files:
            audio_path = mp3_files[0]
        else:
            print("[ERRO] Arquivo de áudio não encontrado após download.")
            sys.exit(1)

    size_mb = audio_path.stat().st_size / (1024 * 1024)
    log(f"Download concluído: {audio_path.name} ({size_mb:.1f} MB)", "✅")

    return audio_path, title


# ─── Etapa 2: Transcrição via AssemblyAI ─────────────────────────────────────

def transcribe_audio(audio_path: Path, translate: bool = False) -> aai.Transcript:
    """
    Envia o arquivo de áudio para a AssemblyAI e aguarda a transcrição.

    Parâmetros:
        audio_path: caminho local do MP3
        translate:  se True, usa o endpoint de tradução automática para inglês
                    (útil se o vídeo for em outro idioma; para inglês, deixe False)

    A AssemblyAI aceita arquivos grandes direto — sem necessidade de chunking.
    O progresso é mostrado a cada 30 segundos durante o processamento.
    """
    log(f"Enviando áudio para AssemblyAI: {audio_path.name}", "☁️")
    log("Upload pode levar alguns minutos para arquivos grandes...", "⏳")

    config = aai.TranscriptionConfig(
        language_code="en",            # Idioma do áudio (inglês)
        punctuate=True,                # Adiciona pontuação automaticamente
        format_text=True,              # Capitalização e formatação
        speech_model=aai.SpeechModel.best,  # Modelo mais preciso
    )

    # Se quiser tradução automática para inglês (útil para outros idiomas)
    # Nota: AssemblyAI traduz PARA inglês, não para português.
    # A tradução PT será feita em etapa separada via LLM.
    if translate:
        config = aai.TranscriptionConfig(
            language_detection=True,   # Detecta o idioma automaticamente
            punctuate=True,
            format_text=True,
            speech_model=aai.SpeechModel.best,
        )

    transcriber = aai.Transcriber()

    log("Iniciando transcrição...", "🎙️")
    log("Estimativa para 4h de áudio: 15–25 minutos", "⏱️")

    # Submete e aguarda — a biblioteca já faz polling internamente
    transcript = transcriber.transcribe(str(audio_path), config=config)

    if transcript.status == aai.TranscriptStatus.error:
        print(f"[ERRO] Falha na transcrição: {transcript.error}")
        sys.exit(1)

    log("Transcrição concluída!", "✅")
    return transcript


# ─── Etapa 3: Exportar resultados ────────────────────────────────────────────

def export_txt(transcript: aai.Transcript, output_path: Path):
    """Salva a transcrição como texto corrido."""
    output_path.write_text(transcript.text, encoding="utf-8")
    log(f"Texto salvo: {output_path.name}", "📄")


def export_srt(transcript: aai.Transcript, output_path: Path):
    """
    Gera arquivo SRT a partir dos utterances/words da transcrição.
    SRT é compatível com VLC, mpv, e pode ser importado no YouTube.
    """
    words = transcript.words
    if not words:
        log("Sem dados de palavras para gerar SRT.", "⚠️")
        return

    def ms_to_srt_time(ms: int) -> str:
        """Converte milissegundos para formato HH:MM:SS,mmm do SRT."""
        s, ms = divmod(ms, 1000)
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    # Agrupa palavras em blocos de ~10 segundos (padrão legível)
    CHUNK_MS = 10_000
    blocks = []
    current_words = []
    chunk_start = words[0].start

    for word in words:
        current_words.append(word.text)
        if word.end - chunk_start >= CHUNK_MS:
            blocks.append({
                "start": chunk_start,
                "end": word.end,
                "text": " ".join(current_words)
            })
            current_words = []
            chunk_start = word.end

    # Último bloco
    if current_words:
        blocks.append({
            "start": chunk_start,
            "end": words[-1].end,
            "text": " ".join(current_words)
        })

    srt_lines = []
    for i, block in enumerate(blocks, start=1):
        srt_lines.append(str(i))
        srt_lines.append(
            f"{ms_to_srt_time(block['start'])} --> {ms_to_srt_time(block['end'])}"
        )
        srt_lines.append(block["text"])
        srt_lines.append("")  # Linha em branco entre blocos

    output_path.write_text("\n".join(srt_lines), encoding="utf-8")
    log(f"Legenda SRT salva: {output_path.name} ({len(blocks)} blocos)", "🎞️")


def export_json(transcript: aai.Transcript, output_path: Path):
    """Salva a resposta completa da API em JSON (útil para reprocessamento)."""
    data = {
        "id": transcript.id,
        "status": str(transcript.status),
        "text": transcript.text,
        "words": [
            {"text": w.text, "start": w.start, "end": w.end, "confidence": w.confidence}
            for w in (transcript.words or [])
        ]
    }
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"JSON salvo: {output_path.name}", "📦")


def print_translation_hint(txt_path: Path):
    """Mostra dica de como traduzir o resultado com um LLM."""
    print()
    print("─" * 60)
    print("📋  PRÓXIMO PASSO: Tradução para Português")
    print("─" * 60)
    print(f"""
O arquivo '{txt_path.name}' contém a transcrição em inglês.

Para traduzir, você pode:

1. CLAUDE / CHATGPT (arquivos menores, até ~100KB):
   → Abra o .txt e cole em blocos de ~3000 palavras
   → Prompt sugerido:
     "Traduza o texto abaixo para português brasileiro,
      mantendo termos técnicos em inglês quando apropriado.
      Preserve a estrutura do texto."

2. DEEPL (mais rápido para textos longos):
   → https://www.deepl.com/translator
   → Suporta arquivos .txt diretamente

3. Script de tradução automática (via API Claude/OpenAI):
   → Peça pra gerar um script que lê o .txt em chunks
     e traduz cada bloco preservando o contexto
""")
    print("─" * 60)


# ─── Ponto de entrada ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Transcreve vídeos do YouTube usando AssemblyAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python transcribe_youtube.py "https://youtube.com/watch?v=XXXXX"
  python transcribe_youtube.py "https://youtu.be/XXXXX" --translate
        """
    )
    parser.add_argument("url", help="URL do vídeo do YouTube")
    parser.add_argument(
        "--translate",
        action="store_true",
        help="Ativa detecção de idioma automática (para vídeos não-inglês)"
    )
    parser.add_argument(
        "--output-dir",
        default="./output",
        help="Pasta de saída (padrão: ./output)"
    )
    parser.add_argument(
        "--skip-download",
        metavar="AUDIO_FILE",
        help="Pula o download e usa um MP3 já existente"
    )

    args = parser.parse_args()

    # Cria pasta de saída
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print()
    print("═" * 60)
    print("  🎙️  YouTube Transcriber — powered by AssemblyAI")
    print("═" * 60)
    print()

    # ── Etapa 1: Download ──────────────────────────────────────────
    if args.skip_download:
        audio_path = Path(args.skip_download)
        title = audio_path.stem
        if not audio_path.exists():
            print(f"[ERRO] Arquivo não encontrado: {audio_path}")
            sys.exit(1)
        log(f"Usando áudio existente: {audio_path.name}", "📂")
    else:
        audio_path, title = download_audio(args.url, output_dir)

    safe_title = sanitize_filename(title)
    base_path = output_dir / safe_title

    # ── Etapa 2: Transcrição ───────────────────────────────────────
    json_cache = Path(f"{base_path}.json")

    if json_cache.exists():
        # Permite retomar sem re-transcrever se já tiver o JSON
        log("Cache JSON encontrado, pulando transcrição.", "♻️")
        log(f"Para re-transcrever, delete: {json_cache.name}", "💡")
        with open(json_cache, encoding="utf-8") as f:
            cached = json.load(f)
        # Reconstrói objeto simples para exportação
        txt_path = Path(f"{base_path}.txt")
        srt_path = Path(f"{base_path}.srt")
        txt_path.write_text(cached["text"], encoding="utf-8")
        log(f"Texto re-exportado de cache: {txt_path.name}", "📄")
    else:
        transcript = transcribe_audio(audio_path, translate=args.translate)

        # ── Etapa 3: Exportar ──────────────────────────────────────
        txt_path = Path(f"{base_path}.txt")
        srt_path = Path(f"{base_path}.srt")

        export_txt(transcript, txt_path)
        export_srt(transcript, srt_path)
        export_json(transcript, json_cache)

    # ── Resumo final ───────────────────────────────────────────────
    print()
    log("Arquivos gerados:", "📁")
    for f in output_dir.iterdir():
        if f.stem == safe_title:
            size_kb = f.stat().st_size / 1024
            print(f"       {f.name} ({size_kb:.0f} KB)")

    print_translation_hint(txt_path)


if __name__ == "__main__":
    main()
