# Installation Guide

## Requirements

- Docker Desktop
- WSL2
- Ubuntu 22.04
- Python 3.10+
- Tutor

## Steps

Install tutor:
```bash
python3 -m venv venv
source venv/bin/activate
pip install "tutor[full]"
```

Run Open edX:
```bash
tutor config save
tutor local launch
```