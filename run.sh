#!/bin/bash
# This script is called by cron every day.
# It activates the venv and runs the scraper.
# Uses absolute paths because cron has no concept of "current folder".

PROJECT="/Users/polinastina/Desktop/chem-price-tracker"
PYTHON="$PROJECT/venv/bin/python3"
LOG="$PROJECT/scraper.log"

echo "-------------------------------------------" >> "$LOG"
echo "Run started: $(date)" >> "$LOG"

cd "$PROJECT" && "$PYTHON" scraper.py >> "$LOG" 2>&1

echo "Run finished: $(date)" >> "$LOG"
