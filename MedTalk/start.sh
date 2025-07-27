#!/bin/bash
source /Users/jaemin/Desktop/Edge\ AI/.venv/bin/activate
cd "/Users/jaemin/Desktop/Edge AI/malpuli_ai"
uvicorn malpuli_ai.main:app --reload
