# CodePix - Code Screenshot Generator

A self-hosted Flask web app that renders code as syntax-highlighted PNG images.

## Features

- Paste any code and render it as a PNG image
- Multiple syntax highlighting themes: Default, Monokai, Solarized Dark/Light, Dracula, Github, Colorful
- Auto language detection
- Clean, dark-themed UI

## Installation

```bash
cd codepix
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
source venv/bin/activate
python app.py
```

Then open http://127.0.0.1:5000 in your browser.

1. Paste your code into the textarea
2. Select a theme from the dropdown
3. Click "Export PNG" to download the image

## Requirements

- Flask >= 2.0
- Pygments >= 2.0
- Pillow >= 9.0
- DejaVu Sans Mono font (system font, usually pre-installed)
