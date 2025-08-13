#!/bin/bash
source .env
export GEMINI_API_KEY
source venv/bin/activate
python -m pudb asrepl.py
