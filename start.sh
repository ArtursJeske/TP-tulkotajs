#!/usr/bin/env bash
cd "$(dirname "$0")"
python3 -m pip install --quiet -r requirements.txt
[ -f fonts/DMSans-Regular.ttf ] || python3 setup_fonts.py
( sleep 2; command -v xdg-open >/dev/null && xdg-open http://127.0.0.1:5000 || open http://127.0.0.1:5000 ) &
python3 app.py
