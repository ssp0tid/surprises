# AudioWave

CLI tool for audio waveform visualization and frequency spectrum analysis.

## Installation

```bash
pip install audiowave
```

Or install from source:

```bash
git clone https://github.com/audiowave/audiowave.git
cd audiowave
pip install -e .
```

## Requirements

- Python 3.8+
- numpy>=1.21.0
- scipy>=1.7.0
- matplotlib>=3.4.0
- soundfile>=0.11.0
- click>=8.0.0
- tqdm>=4.62.0

## Usage

### Analyze audio file

```bash
audiowave analyze audio.mp3
audiowave analyze audio.wav --json
audiowave analyze audio.flac -o stats.txt --channels 0
```

### Generate waveform visualization

```bash
audiowave waveform audio.mp3
audiowave waveform audio.wav -o waveform.png --color "#FF5722" --background "#1a1a2e"
audiowave waveform audio.mp3 --width 1920 --height 600 --style dark --dpi 150
```

### Generate frequency spectrum

```bash
audiowave spectrum audio.mp3
audiowave spectrum audio.wav --bars 128 --log
audiowave spectrum audio.flac -o spectrum.png --window hamming
```

### Detect and visualize beats

```bash
audiowave beats audio.mp3
audiowave beats audio.wav --show-bpm --sensitivity 1.5
audiowave beats audio.mp3 --min-bpm 80 --max-bpm 180
```

### Generate all visualizations

```bash
audiowave all audio.mp3
audiowave all audio.wav -o ./output --prefix myaudio --format svg
```

## Options

### Global options

- `-v, --verbose` - Enable verbose output
- `-q, --quiet` - Suppress non-essential output
- `--config FILE` - Custom configuration file

### Analyze command

- `--json` - Output in JSON format
- `-o, --output FILE` - Save statistics to file
- `--channels N` - Channel to analyze (0=left, 1=right, -1=all)

### Waveform command

- `-o, --output FILE` - Output image path
- `--width N` - Image width (default: 1920)
- `--height N` - Image height (default: 400)
- `--color COLOR` - Waveform color (default: #2196F3)
- `--background COLOR` - Background color (default: #FFFFFF)
- `--style {classic,seaborn,ggplot,dark}` - Matplotlib style
- `--dpi N` - Image DPI (default: 100)
- `--mono` - Use mono channel
- `--zoom LEVEL` - Zoom level for detail view (1-10)

### Spectrum command

- `-o, --output FILE` - Output image path
- `--width N` - Image width (default: 1280)
- `--height N` - Image height (default: 720)
- `--bars N` - Number of frequency bars (default: 64)
- `--log` - Use logarithmic frequency scale
- `--db-range N` - dB range (default: 80)
- `--color COLOR` - Bar color (default: #4CAF50)
- `--background COLOR` - Background color (default: #1a1a2e)
- `--style {classic,seaborn,ggplot,dark}` - Matplotlib style
- `--dpi N` - Image DPI (default: 100)
- `--window {hann,hamming,blackman}` - FFT window function

### Beats command

- `-o, --output FILE` - Output image path
- `--width N` - Image width (default: 1920)
- `--height N` - Image height (default: 600)
- `--sensitivity N` - Beat detection sensitivity (default: 1.0)
- `--min-bpm N` - Minimum BPM (default: 60)
- `--max-bpm N` - Maximum BPM (default: 200)
- `--show-bpm` - Display detected BPM on image
- `--color COLOR` - Beat marker color (default: #FF5722)
- `--background COLOR` - Background color (default: #FFFFFF)
- `--style {classic,seaborn,ggplot,dark}` - Matplotlib style
- `--dpi N` - Image DPI (default: 100)

### All command

- `-o, --output-dir DIR` - Output directory (default: ./audiowave_output/)
- `--prefix STR` - Filename prefix
- `--format {png,jpg,svg,pdf}` - Image format (default: png)
- `--all-options` - Apply all options from all commands

## Supported Audio Formats

- WAV
- MP3
- FLAC
- OGG
- AIFF

## Development

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

## License

MIT License