# Setup

## Requirements

- Python 3.11+
- CMake (for dlib)
- 4GB RAM minimum

## Installation

```bash
git clone &lt;repo&gt;
cd wedding-face-finder
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
flask db upgrade
python run.py