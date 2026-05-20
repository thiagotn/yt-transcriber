package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	aai "github.com/AssemblyAI/assemblyai-go-sdk"
	"github.com/joho/godotenv"
)

const srtChunkMS = 10_000

func logMsg(emoji, msg string) {
	fmt.Printf("[%s] %s  %s\n", time.Now().Format("15:04:05"), emoji, msg)
}

func derefStr(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}

func sanitizeFilename(name string) string {
	for _, ch := range `\/:*?"<>|` {
		name = strings.ReplaceAll(name, string(ch), "_")
	}
	if len(name) > 80 {
		return name[:80]
	}
	return name
}

// wordData and transcriptCache mirror the JSON cache format from the Python version.
type wordData struct {
	Text       string  `json:"text"`
	Start      int64   `json:"start"`
	End        int64   `json:"end"`
	Confidence float64 `json:"confidence"`
}

type transcriptCache struct {
	ID     string     `json:"id"`
	Status string     `json:"status"`
	Text   string     `json:"text"`
	Words  []wordData `json:"words"`
}

// Stage 1: Download

func downloadAudio(url, outputDir string) (audioPath, title string, err error) {
	logMsg("🔍", "Obtendo informações do vídeo...")

	out, _ := exec.Command("yt-dlp", "--get-title", url).Output()
	title = "video"
	if len(out) > 0 {
		title = strings.TrimSpace(string(out))
	}

	safeTitle := sanitizeFilename(title)
	audioPath = filepath.Join(outputDir, safeTitle+".mp3")

	if _, statErr := os.Stat(audioPath); statErr == nil {
		logMsg("✅", "Áudio já existe, pulando download: "+filepath.Base(audioPath))
		return audioPath, title, nil
	}

	logMsg("⬇️", "Baixando áudio: "+title)
	logMsg("⏳", "(Isso pode levar alguns minutos dependendo da sua conexão)")

	cmd := exec.Command("yt-dlp",
		"-x", "--audio-format", "mp3", "--audio-quality", "0",
		"--no-playlist", "-o", audioPath, url,
	)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err = cmd.Run(); err != nil {
		return "", "", fmt.Errorf("falha no download: %w", err)
	}

	if _, statErr := os.Stat(audioPath); os.IsNotExist(statErr) {
		matches, _ := filepath.Glob(filepath.Join(outputDir, safeTitle+"*.mp3"))
		if len(matches) == 0 {
			return "", "", fmt.Errorf("arquivo de áudio não encontrado após download")
		}
		audioPath = matches[0]
	}

	info, _ := os.Stat(audioPath)
	logMsg("✅", fmt.Sprintf("Download concluído: %s (%.1f MB)", filepath.Base(audioPath), float64(info.Size())/(1024*1024)))
	return audioPath, title, nil
}

// Stage 2: Transcription

func transcribeAudio(audioPath string, translate bool) (*transcriptCache, error) {
	client := aai.NewClient(os.Getenv("ASSEMBLYAI_API_KEY"))

	logMsg("☁️", "Enviando áudio para AssemblyAI: "+filepath.Base(audioPath))
	logMsg("⏳", "Upload pode levar alguns minutos para arquivos grandes...")

	speechModel := aai.SpeechModelBest
	params := &aai.TranscriptOptionalParams{
		Punctuate:   aai.Bool(true),
		FormatText:  aai.Bool(true),
		SpeechModel: &speechModel,
	}

	if translate {
		params.LanguageDetection = aai.Bool(true)
	} else {
		lang := aai.TranscriptLanguageCode("en")
		params.LanguageCode = &lang
	}

	f, err := os.Open(audioPath)
	if err != nil {
		return nil, fmt.Errorf("erro ao abrir áudio: %w", err)
	}
	defer f.Close()

	logMsg("🎙️", "Iniciando transcrição...")
	logMsg("⏱️", "Estimativa para 4h de áudio: 15–25 minutos")

	t, err := client.Transcripts.TranscribeFromReader(context.Background(), f, params)
	if err != nil {
		return nil, fmt.Errorf("erro na transcrição: %w", err)
	}

	logMsg("✅", "Transcrição concluída!")

	ct := &transcriptCache{
		ID:     derefStr(t.ID),
		Status: string(t.Status),
		Text:   derefStr(t.Text),
	}
	for _, w := range t.Words {
		wd := wordData{Text: derefStr(w.Text)}
		if w.Start != nil {
			wd.Start = *w.Start
		}
		if w.End != nil {
			wd.End = *w.End
		}
		if w.Confidence != nil {
			wd.Confidence = *w.Confidence
		}
		ct.Words = append(ct.Words, wd)
	}
	return ct, nil
}

// Stage 3: Export

func exportTXT(ct *transcriptCache, path string) error {
	if err := os.WriteFile(path, []byte(ct.Text), 0644); err != nil {
		return err
	}
	logMsg("📄", "Texto salvo: "+filepath.Base(path))
	return nil
}

func msToSRTTime(ms int64) string {
	s := ms / 1000
	rem := ms % 1000
	m := s / 60
	s %= 60
	h := m / 60
	m %= 60
	return fmt.Sprintf("%02d:%02d:%02d,%03d", h, m, s, rem)
}

func exportSRT(ct *transcriptCache, path string) error {
	if len(ct.Words) == 0 {
		logMsg("⚠️", "Sem dados de palavras para gerar SRT.")
		return nil
	}

	type srtBlock struct {
		start, end int64
		text       string
	}

	var blocks []srtBlock
	var cur []string
	chunkStart := ct.Words[0].Start

	for _, w := range ct.Words {
		cur = append(cur, w.Text)
		if w.End-chunkStart >= srtChunkMS {
			blocks = append(blocks, srtBlock{chunkStart, w.End, strings.Join(cur, " ")})
			cur = nil
			chunkStart = w.End
		}
	}
	if len(cur) > 0 {
		last := ct.Words[len(ct.Words)-1]
		blocks = append(blocks, srtBlock{chunkStart, last.End, strings.Join(cur, " ")})
	}

	var sb strings.Builder
	for i, b := range blocks {
		fmt.Fprintf(&sb, "%d\n%s --> %s\n%s\n\n", i+1, msToSRTTime(b.start), msToSRTTime(b.end), b.text)
	}

	if err := os.WriteFile(path, []byte(sb.String()), 0644); err != nil {
		return err
	}
	logMsg("🎞️", fmt.Sprintf("Legenda SRT salva: %s (%d blocos)", filepath.Base(path), len(blocks)))
	return nil
}

func exportJSON(ct *transcriptCache, path string) error {
	data, err := json.MarshalIndent(ct, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(path, data, 0644); err != nil {
		return err
	}
	logMsg("📦", "JSON salvo: "+filepath.Base(path))
	return nil
}

func printTranslationHint(txtName string) {
	sep := strings.Repeat("─", 60)
	fmt.Println()
	fmt.Println(sep)
	fmt.Println("📋  PRÓXIMO PASSO: Tradução para Português")
	fmt.Println(sep)
	fmt.Printf(`
O arquivo '%s' contém a transcrição em inglês.

Para traduzir:
  1. DEEPL: https://www.deepl.com/translator (suporta .txt direto)
  2. CLAUDE / CHATGPT: cole em blocos de ~3000 palavras
`, txtName)
	fmt.Println(sep)
}

func main() {
	translateFlag := flag.Bool("translate", false, "Ativa detecção de idioma automática (para vídeos não-inglês)")
	outputDir := flag.String("output-dir", "./output", "Pasta de saída (padrão: ./output)")
	skipDownload := flag.String("skip-download", "", "Pula o download e usa um MP3 já existente")
	audioOnly := flag.Bool("audio-only", false, "Apenas baixa o MP3, sem transcrever")
	flag.Parse()

	if flag.NArg() < 1 {
		fmt.Fprintln(os.Stderr, "Uso: yt-transcriber <URL> [--translate] [--output-dir DIR] [--skip-download FILE]")
		os.Exit(1)
	}
	videoURL := flag.Arg(0)

	_ = godotenv.Load()

	if !*audioOnly && os.Getenv("ASSEMBLYAI_API_KEY") == "" {
		fmt.Fprintln(os.Stderr, "[ERRO] ASSEMBLYAI_API_KEY não encontrada. Crie um .env ou exporte a variável.")
		os.Exit(1)
	}

	if _, err := exec.LookPath("yt-dlp"); err != nil {
		fmt.Fprintln(os.Stderr, "[ERRO] yt-dlp não encontrado. Instale com: pip install yt-dlp")
		os.Exit(1)
	}

	if err := os.MkdirAll(*outputDir, 0755); err != nil {
		fmt.Fprintf(os.Stderr, "[ERRO] Não foi possível criar pasta de saída: %v\n", err)
		os.Exit(1)
	}

	fmt.Println()
	fmt.Println(strings.Repeat("═", 60))
	fmt.Println("  🎙️  YouTube Transcriber — powered by AssemblyAI")
	fmt.Println(strings.Repeat("═", 60))
	fmt.Println()

	// Stage 1: Audio
	var audioPath, title string
	if *audioOnly && *skipDownload != "" {
		fmt.Fprintln(os.Stderr, "[ERRO] --audio-only e --skip-download não podem ser usados juntos.")
		os.Exit(1)
	}
	if *skipDownload != "" {
		audioPath = *skipDownload
		title = strings.TrimSuffix(filepath.Base(audioPath), filepath.Ext(audioPath))
		if _, err := os.Stat(audioPath); os.IsNotExist(err) {
			fmt.Fprintf(os.Stderr, "[ERRO] Arquivo não encontrado: %s\n", audioPath)
			os.Exit(1)
		}
		logMsg("📂", "Usando áudio existente: "+filepath.Base(audioPath))
	} else {
		var err error
		audioPath, title, err = downloadAudio(videoURL, *outputDir)
		if err != nil {
			fmt.Fprintf(os.Stderr, "[ERRO] %v\n", err)
			os.Exit(1)
		}
	}

	if *audioOnly {
		fmt.Println()
		logMsg("✅", fmt.Sprintf("Áudio disponível em: %s", audioPath))
		return
	}

	safeTitle := sanitizeFilename(title)
	basePath := filepath.Join(*outputDir, safeTitle)
	jsonPath := basePath + ".json"
	txtPath := basePath + ".txt"
	srtPath := basePath + ".srt"

	// Stage 2: Transcription (with cache)
	var ct *transcriptCache

	if _, err := os.Stat(jsonPath); err == nil {
		logMsg("♻️", "Cache JSON encontrado, pulando transcrição.")
		logMsg("💡", "Para re-transcrever, delete: "+filepath.Base(jsonPath))
		data, err := os.ReadFile(jsonPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "[ERRO] lendo cache: %v\n", err)
			os.Exit(1)
		}
		ct = new(transcriptCache)
		if err := json.Unmarshal(data, ct); err != nil {
			fmt.Fprintf(os.Stderr, "[ERRO] cache JSON inválido: %v\n", err)
			os.Exit(1)
		}
	} else {
		var err error
		ct, err = transcribeAudio(audioPath, *translateFlag)
		if err != nil {
			fmt.Fprintf(os.Stderr, "[ERRO] %v\n", err)
			os.Exit(1)
		}
		if err := exportJSON(ct, jsonPath); err != nil {
			fmt.Fprintf(os.Stderr, "[ERRO] salvando JSON: %v\n", err)
			os.Exit(1)
		}
	}

	// Stage 3: Export
	if err := exportTXT(ct, txtPath); err != nil {
		fmt.Fprintf(os.Stderr, "[ERRO] %v\n", err)
		os.Exit(1)
	}
	if err := exportSRT(ct, srtPath); err != nil {
		fmt.Fprintf(os.Stderr, "[ERRO] %v\n", err)
		os.Exit(1)
	}

	// Summary
	fmt.Println()
	logMsg("📁", "Arquivos gerados:")
	entries, _ := os.ReadDir(*outputDir)
	for _, e := range entries {
		if strings.HasPrefix(e.Name(), safeTitle) {
			info, _ := e.Info()
			fmt.Printf("       %s (%.0f KB)\n", e.Name(), float64(info.Size())/1024)
		}
	}

	printTranslationHint(filepath.Base(txtPath))
}
