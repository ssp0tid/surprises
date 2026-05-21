# AudioWave - Implementation Plan

## 1. Project Overview and Architecture

### 1.1 Project Overview
AudioWave is a CLI tool for audio waveform visualization and frequency spectrum analysis. It provides capabilities to analyze audio files and generate visual representations including waveform images, real-time frequency spectrum bars, and beat detection visualization. The tool calculates and displays comprehensive audio statistics.

### 1.2 Core Design Philosophy
- **Modularity**: Each functionality is isolated into independent modules
- **CLI-first**: All operations accessible via command-line interface
- **Pipeline architecture**: Audio flows through processing stages (load → analyze → visualize)
- **Extensibility**: Easy to add new visualization types and analysis algorithms

### 1.3 Architecture Layers

```
┌─────────────────────────────────────────┐
│           CLI Interface Layer           │
│    (argparse, commands, options)        │
├─────────────────────────────────────────┤
│         Command Execution Layer         │
│   (command handlers, orchestration)     │
├─────────────────────────────────────────┤
│         Audio Processing Layer          │
│  (loaders, analyzers, transformations)  │
├─────────────────────────────────────────┤
│        Visualization Layer              │
│   (matplotlib renderers, formatters)   │
├─────────────────────────────────────────┤
│           Core Utilities                │
│    (logging, config, exceptions)        │
└─────────────────────────────────────────┘
```

---

## 2. Core Modules and Their Responsibilities

### 2.1 Module Overview

| Module | Responsibility | Public API |
|--------|----------------|------------|
| `cli` | Argument parsing, command dispatch | `main()`, `create_parser()` |
| `audio.loader` | Load audio files, format detection | `load_audio(path) -> AudioData` |
| `audio.analyzer` | Statistical analysis, feature extraction | `analyze(audio_data) -> AnalysisResult` |
| `audio.beat` | Beat detection algorithm | `detect_beats(audio_data) -> BeatInfo` |
| `audio.spectrum` | FFT, frequency analysis | `compute_spectrum(audio_data) -> SpectrumData` |
| `visual.waveform` | Waveform image generation | `render(audio_data, options) -> Figure` |
| `visual.spectrum` | Spectrum visualization | `render(spectrum_data, options) -> Figure` |
| `visual.beats` | Beat visualization overlay | `render(beats, audio_data) -> Figure` |
| `visual.stats` | Statistics display | `render_stats(stats) -> Figure` |
| `utils.config` | Configuration management | `get_config()`, `load_config()` |
| `utils.logging` | Logging setup | `setup_logging()` |

### 2.2 Module Details

#### cli/
- **Purpose**: Command-line interface entry point
- **Components**:
  - `main.py` - Entry point with argument parser
  - `commands.py` - Command handler classes
  - `formatters.py` - Output formatting (text, JSON)

#### audio/
- **Purpose**: Audio loading and analysis
- **Components**:
  - `loader.py` - Multi-format audio loading (MP3, WAV, FLAC, OGG)
  - `analyzer.py` - Statistical computations
  - `beat.py` - Beat detection using energy envelope
  - `spectrum.py` - Frequency domain analysis
  - `types.py` - Data structures

#### visual/
- **Purpose**: Visualization generation
- **Components**:
  - `waveform.py` - Waveform plot generation
  - `spectrum.py` - Frequency spectrum bars
  - `beats.py` - Beat markers overlay
  - `stats.py` - Audio statistics display
  - `styles.py` - Matplotlib style configurations

#### utils/
- **Purpose**: Shared utilities
- **Components**:
  - `config.py` - Configuration management
  - `logging.py` - Logging configuration
  - `exceptions.py` - Custom exception classes

---

## 3. CLI Interface Design

### 3.1 Command Structure

```
audiowave [GLOBAL OPTIONS] <command> [command options]

Commands:
  analyze     Analyze audio file and show statistics
  waveform    Generate waveform visualization
  spectrum    Generate frequency spectrum visualization
  beats       Detect and visualize beats
  all         Generate all visualizations at once

Global Options:
  -v, --verbose    Enable verbose output
  -q, --quiet      Suppress non-essential output
  --config FILE    Custom configuration file
  --help           Show help message
```

### 3.2 Command Details

#### `audiowave analyze <file>`

Analyzes audio file and displays statistics.

```
Options:
  --json              Output in JSON format
  -o, --output FILE   Save statistics to file
  --channels N       Channel to analyze (0=left, 1=right, -1=all)
```

**Output Example:**
```
Audio File: example.mp3
Duration: 3:45.2
Sample Rate: 44100 Hz
Channels: 2 (Stereo)
Bit Depth: 16-bit
File Size: 4.2 MB
Bitrate: 320 kbps

Statistics:
  Peak Amplitude: 0.95
  RMS Level: -12.3 dB
  Dynamic Range: 68.2 dB
  Crest Factor: 14.2
```

#### `audiowave waveform <file>`

Generates waveform visualization.

```
Options:
  -o, --output FILE   Output image path (default: <input>_waveform.png)
  --width N           Image width in pixels (default: 1920)
  --height N         Image height in pixels (default: 400)
  --color COLOR      Waveform color (default: #2196F3)
  --background COLOR Background color (default: #FFFFFF)
  --style {classic,seaborn,ggplot,dark}  Matplotlib style
  --dpi N            Image DPI (default: 100)
  --mono             Mono channel if stereo (use first channel)
  --zoom LEVEL       Zoom level for detail view (1-10)
```

#### `audiowave spectrum <file>`

Generates frequency spectrum visualization.

```
Options:
  -o, --output FILE   Output image path (default: <input>_spectrum.png)
  --width N           Image width (default: 1280)
  --height N          Image height (default: 720)
  --bars N            Number of frequency bars (default: 64)
  --log               Use logarithmic frequency scale
  --db-range N        dB range for display (default: 80)
  --color COLOR       Bar color (default: #4CAF50)
  --background COLOR  Background color (default: #1a1a2e)
  --style {classic,seaborn,ggplot,dark}   Matplotlib style
  --dpi N             Image DPI (default: 100)
  --window {hann,hamming,blackman}       FFT window function
```

#### `audiowave beats <file>`

Detects and visualizes beats.

```
Options:
  -o, --output FILE   Output image path (default: <input>_beats.png)
  --width N           Image width (default: 1920)
  --height N          Image height (default: 600)
  --sensitivity N    Beat detection sensitivity 0.1-2.0 (default: 1.0)
  --min-bpm N         Minimum BPM to detect (default: 60)
  --max-bpm N         Maximum BPM to detect (default: 200)
  --show-bpm          Display detected BPM on image
  --color COLOR       Beat marker color (default: #FF5722)
  --background COLOR  Background color (default: #FFFFFF)
  --style {classic,seaborn,ggplot,dark}  Matplotlib style
  --dpi N             Image DPI (default: 100)
```

#### `audiowave all <file>`

Generates all visualizations at once.

```
Options:
  -o, --output-dir DIR  Output directory (default: ./audiowave_output/)
  --prefix STR          Filename prefix (default: <audio_filename>)
  --format {png,jpg,svg,pdf}  Image format (default: png)
  --all-options        Apply all options from all commands
```

### 3.3 Global Behavior

- **Progress indication**: Display progress for long operations
- **Error handling**: Graceful error messages with suggested fixes
- **Logging levels**:
  - Default: Show warnings and errors
  - Verbose (-v): Show info messages
  - Quiet (-q): Show only errors

---

## 4. Audio Processing Pipeline

### 4.1 Pipeline Stages

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    LOAD     │───▶│   ANALYZE   │───▶│ TRANSFORM   │───▶│  VISUALIZE  │
│             │    │             │    │             │    │             │
│ 1. Detect   │    │ 1. Stats    │    │ 1. Normalize│    │ 1. Create  │
│    format   │    │ 2. Spectrum │    │ 2. Downmix  │    │    figure   │
│ 2. Decode   │    │ 3. Beats    │    │ 3. Resample │    │ 2. Render   │
│ 3. Validate │    │             │    │             │    │ 3. Save     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### 4.2 Stage Details

#### Stage 1: Load
1. **Format detection**: Magic bytes, file extension
2. **Decoding**: Use soundfile (libsndfile) for best format support
3. **Validation**: Check for corruption, unsupported features

#### Stage 2: Analyze
1. **Statistics**: Duration, sample rate, channels, bit depth, RMS, peak
2. **Spectrum**: FFT with configurable window
3. **Beats**: Energy-based onset detection

#### Stage 3: Transform
1. **Normalization**: Peak normalization to [-1, 1]
2. **Downmix**: Stereo to mono if requested
3. **Resample**: Resample for display if needed

#### Stage 4: Visualize
1. **Create figure**: Matplotlib Figure with subplots
2. **Render**: Draw data to axes
3. **Save**: Export to file or display

---

## 5. Visualization Components

### 5.1 Waveform Visualization
- **Display**: Time-domain signal amplitude
- **Features**:
  - Full track overview
  - Zoom capability for detail
  - Stereo channels in separate subplots or merged
  - Peak markers
- **Styling**: Configurable colors, background, line width

### 5.2 Frequency Spectrum
- **Display**: Frequency bars showing magnitude per frequency band
- **Features**:
  - Linear or logarithmic frequency scale
  - Configurable bar count
  - dB amplitude scale
  - Frequency labels (Hz/kHz)
- **Styling**: Gradient colors, dark theme option

### 5.3 Beat Detection Visualization
- **Display**: Waveform with beat markers overlay
- **Features**:
  - Beat timestamps marked
  - BPM display
  - Beat intensity visualization
- **Styling**: Beat markers with configurable appearance

### 5.4 Statistics Display
- **Display**: Text-based statistics or as image overlay
- **Features**:
  - All calculated statistics
  - Formatted for readability
  - Exportable as text/JSON

---

## 6. File Structure

```
audiowave/
├── audiowave/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── commands.py
│   │   └── formatters.py
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── analyzer.py
│   │   ├── beat.py
│   │   ├── spectrum.py
│   │   └── types.py
│   ├── visual/
│   │   ├── __init__.py
│   │   ├── waveform.py
│   │   ├── spectrum.py
│   │   ├── beats.py
│   │   ├── stats.py
│   │   └── styles.py
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       ├── logging.py
│       └── exceptions.py
├── tests/
│   ├── __init__.py
│   ├── test_audio_loader.py
│   ├── test_analyzer.py
│   ├── test_beat_detection.py
│   ├── test_spectrum.py
│   ├── test_visual_waveform.py
│   ├── test_visual_spectrum.py
│   └── test_cli.py
├── pyproject.toml
├── setup.py
├── requirements.txt
├── requirements-dev.txt
├── MANIFEST.in
├── README.md
├── LICENSE
└── PLAN.md
```

---

## 7. Dependencies

### 7.1 Core Dependencies

```txt
numpy>=1.21.0
scipy>=1.7.0
matplotlib>=3.4.0
soundfile>=0.11.0
click>=8.0.0
tqdm>=4.62.0
```

### 7.2 Development Dependencies

```txt
pytest>=7.0.0
pytest-cov>=3.0.0
black>=22.0.0
flake8>=4.0.0
mypy>=0.950
isort>=5.10.0
```

### 7.3 Dependency Justifications

| Package | Purpose | Version Rationale |
|---------|---------|-------------------|
| numpy | Array operations, FFT support | 1.21+ for better performance |
| scipy | Signal processing, FFT | 1.7+ for up-to-date algorithms |
| matplotlib | Visualization rendering | 3.4+ for modern features |
| soundfile | Audio file loading | 0.11+ for format support |
| click | CLI framework | 8.0+ for type hints support |
| tqdm | Progress bars | 4.62+ for modern API |

---

## 8. Implementation Phases/Milestones

### Phase 1: Foundation (Week 1)
**Goal**: Core infrastructure and audio loading

- [ ] Create project structure and package initialization
- [ ] Set up logging and configuration system
- [ ] Implement custom exception classes
- [ ] Implement audio loader with format detection
- [ ] Create data structures (AudioData, AnalysisResult)
- [ ] Basic CLI skeleton with --help
- [ ] Write unit tests for loader module

### Phase 2: Audio Analysis (Week 2)
**Goal**: Statistical analysis and spectrum computation

- [ ] Implement audio analyzer (statistics calculation)
- [ ] Implement spectrum analyzer (FFT-based)
- [ ] Add window function support (Hann, Hamming, Blackman)
- [ ] Add configurable FFT parameters
- [ ] Implement beat detection algorithm
- [ ] Write unit tests for analysis modules
- [ ] Integration test with real audio files

### Phase 3: Visualizations (Week 3)
**Goal**: All visualization components

- [ ] Implement waveform renderer
- [ ] Implement spectrum visualization
- [ ] Implement beat visualization overlay
- [ ] Implement statistics display
- [ ] Add style system and themes
- [ ] Add image export options (PNG, JPG, SVG, PDF)
- [ ] Write integration tests for visual components

### Phase 4: CLI Integration (Week 4)
**Goal**: Complete command-line interface

- [ ] Implement all CLI commands
- [ ] Add argument validation
- [ ] Add progress indicators
- [ ] Add verbose/quiet modes
- [ ] Implement output formatters (text, JSON)
- [ ] End-to-end testing with sample files
- [ ] Write CLI integration tests

### Phase 5: Polish and Release (Week 5)
**Goal**: Bug fixes, optimization, release

- [ ] Performance optimization for large files
- [ ] Memory usage optimization
- [ ] Error message improvements
- [ ] Documentation completion
- [ ] Code coverage to 80%+
- [ ] Type hints completion
- [ ] Setup.py/pip installable package
- [ ] Release preparation

---

## 9. Data Structures for Audio Data

### 9.1 Core Data Structures

```python
from dataclasses import dataclass
from typing import Optional, List, Tuple
import numpy as np

@dataclass
class AudioData:
    """Container for loaded audio data."""
    samples: np.ndarray           # Audio samples, shape (samples, channels)
    sample_rate: int             # Sample rate in Hz
    channels: int                # Number of channels
    bit_depth: int               # Bit depth
    duration: float              # Duration in seconds
    filepath: str                # Source file path
    format: str                  # Audio format (mp3, wav, flac, ogg)

@dataclass
class AudioStatistics:
    """Statistical analysis results."""
    duration: float              # Duration in seconds
    sample_rate: int             # Sample rate in Hz
    channels: int                # Number of channels
    bit_depth: int               # Bit depth
    peak_amplitude: float        # Peak amplitude (0-1)
    rms_level: float             # RMS level
    rms_db: float                # RMS in dB
    crest_factor: float          # Crest factor (peak/RMS)
    dynamic_range: float        # Dynamic range in dB

@dataclass
class SpectrumData:
    """Frequency spectrum data."""
    frequencies: np.ndarray      # Frequency bins
    magnitudes: np.ndarray       # Magnitude values (linear)
    magnitudes_db: np.ndarray    # Magnitude in dB
    sample_rate: int             # Original sample rate
    window_type: str             # FFT window used

@dataclass
class BeatInfo:
    """Beat detection results."""
    beats: np.ndarray           # Beat timestamps in seconds
    bpm: float                  # Estimated tempo (beats per minute)
    confidence: float           # Detection confidence (0-1)
    energy_envelope: np.ndarray # Energy envelope for visualization
    onset_times: np.ndarray     # Onset detection timestamps

@dataclass
class AnalysisResult:
    """Complete analysis results."""
    audio: AudioData
    statistics: AudioStatistics
    spectrum: Optional[SpectrumData] = None
    beats: Optional[BeatInfo] = None
```

### 9.2 Internal Data Types

```python
# For visualization data
VisualizationData = Tuple[np.ndarray, Dict[str, Any]]

# For configuration
ConfigDict = Dict[str, Any]

# For command results
CommandResult = Union[AudioData, AnalysisResult, VisualizationData]
```

---

## 10. Error Handling Approach

### 10.1 Exception Hierarchy

```
AudioWaveError (base exception)
├── AudioLoadError
│   ├── UnsupportedFormatError
│   ├── CorruptedFileError
│   └── FileAccessError
├── AudioAnalysisError
│   ├── InsufficientDataError
│   └── AnalysisTimeoutError
├── VisualizationError
│   ├── RenderError
│   └── ExportError
├── ConfigurationError
│   └── ConfigFileError
│   └── InvalidOptionError
└── CLIError
    ├── InvalidArgumentError
    └── CommandExecutionError
```

### 10.2 Error Handling Strategy

1. **Layer-specific handling**: Each module catches and transforms exceptions
2. **User-friendly messages**: Error messages include suggested fixes
3. **Logging**: All errors logged with context
4. **Graceful degradation**: Partial results returned when possible

### 10.3 Implementation Pattern

```python
class AudioLoadError(AudioWaveError):
    """Raised when audio file cannot be loaded."""
    def __init__(self, filepath: str, reason: str):
        self.filepath = filepath
        self.reason = reason
        super().__init__(
            f"Cannot load '{filepath}': {reason}. "
            f"Supported formats: MP3, WAV, FLAC, OGG"
        )
```

### 10.4 Validation Approach

- **Input validation**: Validate file paths, arguments before processing
- **Audio validation**: Check loaded audio for corruption
- **Config validation**: Validate configuration options
- **Range validation**: Ensure numeric arguments in valid ranges

---

## 11. Additional Considerations

### 11.1 Performance Considerations
- Stream large files instead of loading entirely into memory
- Use chunked FFT for long audio files
- Cache computed spectrum data
- Use multiprocessing for batch operations

### 11.2 Memory Management
- Use memory-mapped files for large audio
- Release matplotlib figures after saving
- Clear numpy arrays when no longer needed

### 11.3 Extensibility Points
- Plugin system for custom visualizations
- Configurable color palettes
- Custom analysis algorithms
- Export format plugins

### 11.4 Future Enhancements (Out of Scope)
- Real-time audio input (microphone)
- Video export
- Audio comparison
- AI-based analysis
- GUI application

---

## 12. Quick Start Example

```bash
# Install
pip install -e .

# Analyze audio
audiowave analyze audio.mp3

# Generate waveform
audiowave waveform audio.mp3 -o waveform.png

# Generate spectrum
audiowave spectrum audio.mp3 --bars 128 --log

# Detect beats
audiowave beats audio.mp3 --show-bpm

# Generate all at once
audiowave all audio.mp3 -o-dir ./output/
```

---

*Plan created: 2026-04-19*
*Project: AudioWave CLI Tool*