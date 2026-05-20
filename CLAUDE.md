# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Single-file Go tool that downloads audio from YouTube videos using `yt-dlp` and transcribes them via AssemblyAI, exporting `.txt`, `.srt`, and `.json` outputs.

## Setup

```bash
# Install Go dependencies
go mod tidy

# Install yt-dlp (still required as an external process)
pip install yt-dlp

# Configure API key
cp .env.example .env
# Edit .env and set ASSEMBLYAI_API_KEY
```

## Build & Run

```bash
# Run directly
go run main.go "https://www.youtube.com/watch?v=XXXXX"

# Build binary
go build -o yt-transcriber .
./yt-transcriber "https://www.youtube.com/watch?v=XXXXX"

# Flags
--translate          # Auto-detect language (non-English audio)
--skip-download FILE # Use existing MP3, skip yt-dlp
--output-dir DIR     # Output directory (default: ./output)
```

## Architecture

`main.go` is the entire application — three sequential stages:

1. **Download** (`downloadAudio`): calls `yt-dlp` via `os/exec` to extract MP3 audio. Skips if MP3 already exists in output dir.
2. **Transcription** (`transcribeAudio`): uploads MP3 to AssemblyAI via `TranscribeFromReader` and waits for completion. Uses `aai.SpeechModelBest`. Without `--translate`, forces `language_code="en"`; with it, enables `language_detection=true` instead.
3. **Export** (`exportTXT`, `exportSRT`, `exportJSON`): writes the three output files. SRT groups words into ~10-second blocks using word-level timestamps from the API.

**Caching**: if a `.json` file matching the video title already exists in the output dir, the script skips transcription and re-exports `.txt` and `.srt` from cache. Delete the `.json` to force re-transcription. When loading from cache, both txt and srt are regenerated (improvement over the original Python version).

**Types**: `transcriptCache` / `wordData` are the internal structs used for both the JSON cache and the export pipeline. The AssemblyAI SDK returns pointer types (`*string`, `*int64`, `*float64`) — `derefStr` handles nil-safe string dereferencing.

## Dependencies

- `github.com/AssemblyAI/assemblyai-go-sdk v1.10.0` — archived as of April 2025, but fully functional at this version
- `github.com/joho/godotenv` — loads `.env` file
- `yt-dlp` — external CLI tool, invoked via subprocess

## Output files

All outputs go to `./output/` (or `--output-dir`):
- `titulo.mp3` — downloaded audio
- `titulo.txt` — plain text transcript
- `titulo.srt` — subtitles with timestamps (10s blocks)
- `titulo.json` — full API response (used as cache)
