# Wedding Face Finder

[![CI](https://github.com/rayansanjrani-arch/wedding-face-finder/actions/workflows/ci.yml/badge.svg)](https://github.com/rayansanjrani-arch/wedding-face-finder/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Code style](https://img.shields.io/badge/code%20style-black-black)

&gt; AI-powered face recognition for wedding and event photography. Upload thousands of photos, take a selfie, find every moment you're in — under three seconds.

## Architecture

┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Client    │────▶│  Flask API   │────▶│  Face Engine    │
│  (Browser)  │     │  (REST + Jinja)│    │  (dlib/CNN-HOG) │
└─────────────┘     └──────────────┘     └─────────────────┘
│
▼
┌──────────────┐
│  SQLite +    │
│  SQLAlchemy  │
└──────────────┘

## Quick Start

### Linux / macOS
```bash
git clone https://github.com/rayansanjrani-arch/wedding-face-finder.git
cd wedding-face-finder
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py