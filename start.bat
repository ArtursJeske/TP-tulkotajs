@echo off
cd /d "%~dp0"
if not exist fonts\DMSans-Regular.ttf (
  echo Sagatavo fontus...
  python setup_fonts.py || goto :err
)
python -m pip install --quiet pymupdf flask fonttools
start "" http://127.0.0.1:5000
python app.py
goto :eof
:err
echo Neizdevas sagatavot fontus. Parbaudi interneta savienojumu.
pause
