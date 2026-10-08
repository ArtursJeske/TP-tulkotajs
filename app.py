# -*- coding: utf-8 -*-
"""Vietējā lietotne S+P datu lapu tulkošanai.

Palaišana:  python3 app.py    ->  http://127.0.0.1:5000
"""
import io
import os
import time
import zipfile

from flask import Flask, Response, jsonify, request, send_file

import sp_lib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out')
UPLOADS = os.path.join(HERE, 'uploads')
os.makedirs(OUT, exist_ok=True)
os.makedirs(UPLOADS, exist_ok=True)

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024


def find_index():
    """index.html var būt mapē static/ vai blakus app.py."""
    for folder in (os.path.join(HERE, 'static'), HERE):
        if os.path.exists(os.path.join(folder, 'index.html')):
            return folder
    return None


def check_setup():
    """Pārbauda failus pirms palaišanas un pasaka, kas iztrūkst."""
    problems = []
    if find_index() is None:
        problems.append(
            'Nav atrasts index.html.\n'
            '     Tam jābūt vai nu mapē  static\\index.html ,\n'
            '     vai blakus app.py.')
    for f in ('DMSans-Regular.ttf', 'DMSans-Bold.ttf'):
        if not os.path.exists(os.path.join(HERE, 'fonts', f)):
            problems.append(f'Nav fonta fails fonts\\{f} — palaid: python setup_fonts.py')
    if not os.path.exists(os.path.join(HERE, 'glossary.json')):
        problems.append('Nav glossary.json — tam jābūt blakus app.py.')
    return problems


def read_bytes(path):
    with open(path, 'rb') as f:
        return f.read()


@app.get('/')
def index():
    folder = find_index()
    if folder is None:
        return ('<h1>Nav atrasts index.html</h1>'
                '<p>Tam jābūt mapē <code>static\\index.html</code> '
                'vai blakus <code>app.py</code>.</p>'), 500
    html = read_bytes(os.path.join(folder, 'index.html'))
    return Response(html, mimetype='text/html; charset=utf-8',
                    headers={'Cache-Control': 'no-store'})


@app.get('/favicon.ico')
def favicon():
    return '', 204


def run_batch(batch):
    """Apstrādā visus failus partijā ar pašreizējo vārdnīcu."""
    folder = os.path.join(UPLOADS, batch)
    glossary = sp_lib.load_glossary()
    results, unknown = [], {}
    for name in sorted(os.listdir(folder)):
        src = os.path.join(folder, name)
        try:
            dst, miss = sp_lib.build(src, OUT, glossary)
            for m in miss:
                unknown[m['en']] = m['kind']
            results.append({'name': name, 'out': os.path.basename(dst),
                            'missing': len(miss), 'ok': True})
        except Exception as e:                           # noqa: BLE001
            results.append({'name': name, 'ok': False, 'error': str(e)})
    return jsonify(
        batch=batch,
        results=results,
        unknown=[{'en': k, 'kind': v} for k, v in unknown.items()],
        kinds=sp_lib.KINDS,
    )


@app.post('/api/process')
def process():
    files = request.files.getlist('files')
    if not files:
        return jsonify(error='Nav iesniegts neviens fails'), 400

    batch = time.strftime('%Y%m%d-%H%M%S')
    folder = os.path.join(UPLOADS, batch)
    os.makedirs(folder, exist_ok=True)
    for f in files:
        name = os.path.basename(f.filename or 'fails.pdf')
        if not name.lower().endswith('.pdf'):
            continue
        f.save(os.path.join(folder, name))
    return run_batch(batch)


@app.post('/api/rebuild')
def rebuild():
    batch = request.get_json(force=True).get('batch', '')
    folder = os.path.join(UPLOADS, os.path.basename(batch))
    if not os.path.isdir(folder):
        return jsonify(error='Partija nav atrasta'), 404
    return run_batch(os.path.basename(batch))


@app.get('/api/glossary')
def get_glossary():
    g = sp_lib.load_glossary()
    return jsonify(glossary=g, kinds=sp_lib.KINDS)


@app.post('/api/glossary')
def add_words():
    """Pieņem [{en, lv, kind}] un ieraksta vārdnīcā."""
    items = request.get_json(force=True).get('items', [])
    g = sp_lib.load_glossary()
    added = 0
    for it in items:
        en = (it.get('en') or '').strip()
        lv = (it.get('lv') or '').strip()
        kind = it.get('kind')
        if not (en and lv and kind in sp_lib.KINDS):
            continue
        g.setdefault(kind, {})[en] = lv
        added += 1
    sp_lib.save_glossary(g)
    return jsonify(added=added, total=sum(
        len(v) for v in g.values() if isinstance(v, dict)))


@app.get('/static/index.html')
def index_alias():
    return index()


@app.get('/fonts/<name>')
def fonts(name):
    path = os.path.join(HERE, 'fonts', os.path.basename(name))
    if not os.path.isfile(path):
        return '', 404
    return Response(read_bytes(path), mimetype='font/ttf')


@app.get('/out/<name>')
def download(name):
    path = os.path.join(OUT, os.path.basename(name))
    if not os.path.isfile(path):
        return 'Fails nav atrasts', 404
    return send_file(io.BytesIO(read_bytes(path)), mimetype='application/pdf',
                     as_attachment=True, download_name=os.path.basename(path))


@app.post('/api/zip')
def make_zip():
    names = request.get_json(force=True).get('names', [])
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in names:
            p = os.path.join(OUT, os.path.basename(n))
            if os.path.exists(p):
                z.write(p, os.path.basename(p))
    buf.seek(0)
    return send_file(buf, mimetype='application/zip',
                     as_attachment=True, download_name='datu_lapas_EN-LV.zip')


if __name__ == '__main__':
    issues = check_setup()
    if issues:
        print('\n  Pirms palaišanas jāsakārto:\n')
        for i in issues:
            print('   *', i)
        print('\n  Mape, kurā skripts skatās:', HERE)
        print('  Tur atrastie faili:', ', '.join(sorted(os.listdir(HERE))))
        input('\n  Nospied Enter, lai aizvērtu.')
        raise SystemExit(1)
    print('\n  Datu lapu tulkotājs -> http://127.0.0.1:5000')
    print('  Lapa tiek padota no:', os.path.join(find_index(), 'index.html'))
    print('  Apturēt: Ctrl+C\n')
    app.run(host='127.0.0.1', port=5000, debug=False)
