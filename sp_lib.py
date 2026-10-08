# -*- coding: utf-8 -*-
"""S+P datu lapas -> divvalodu PDF. Vārdnīca glabājas glossary.json."""
import json
import os
import re
import pymupdf

HERE = os.path.dirname(os.path.abspath(__file__))
GLOSSARY = os.path.join(HERE, 'glossary.json')
FONT_REG = os.path.join(HERE, 'fonts', 'DMSans-Regular.ttf')
FONT_BLD = os.path.join(HERE, 'fonts', 'DMSans-Bold.ttf')
RIGHT_MARGIN = 558.0

# kategorijas nosaukums -> cilvēkam saprotams apraksts (saskarnei)
KINDS = {
    'labels': 'Lauka nosaukums',
    'sections': 'Sekcijas virsraksts',
    'product_types': 'Produkta tips',
    'values': 'Vērtība',
    'sentences': 'Teikums',
}


def load_glossary():
    with open(GLOSSARY, encoding='utf-8') as f:
        return json.load(f)


def save_glossary(g):
    with open(GLOSSARY, 'w', encoding='utf-8') as f:
        json.dump(g, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------- tulkošana
def is_pure_data(t):
    """Skaitlis, kods, mērvienība, materiāls -> nekad netulko."""
    t = t.strip()
    if not t:
        return True
    pats = (
        r'[\d\s.,/×x+\-]+',
        r'[\d.,]+\s*(mm|cm|kg|g|HV|HB|HRC|N/mm²|St\.|pc\.|pcs\.)',
        r'(A2|A4|A5|C1|1\.4\d{3}|A2/1\.4\d{3}|A[245]-\d{2})',
        r'SW\s?\d+',
        r'(TX|PZ|PH|SW|M)\s?\d+',
        r'\d{8,14}',
    )
    return any(re.fullmatch(p, t) for p in pats)


class Translator:
    def __init__(self, glossary):
        self.g = glossary
        self.unknown = []      # [{'en':..., 'kind':...}]

    def miss(self, text, kind):
        if not any(u['en'] == text for u in self.unknown):
            self.unknown.append({'en': text, 'kind': kind})
        return text            # atstāj angliski, neizdomā

    def units(self, text):
        for en, lv in self.g.get('units', []):
            text = re.sub(r'(?<=\d\s)' + re.escape(en) + r'$', lv, text)
        return text

    def look(self, table, key, kind):
        t = self.g.get(table, {})
        return t[key] if key in t else self.miss(key, table)

    def run(self, text, kind):
        t = text.replace('\xa0', ' ').strip()
        if not t:
            return text
        if kind == 'section':
            return self.look('sections', t, kind)
        if kind == 'label':
            return self.look('labels', t, kind)
        if kind == 'title':
            m = re.match(r'^(.*?)(\s{2,})(.+)$', text.replace('\xa0', ' '))
            if m:
                code, gap, name = m.groups()
                return code + gap + self.look('product_types',
                                              name.strip(), kind)
            return text
        # vērtība
        if is_pure_data(t):
            return self.units(t)
        if t in self.g.get('sentences', {}):
            return self.g['sentences'][t]
        if t in self.g.get('values', {}):
            return self.g['values'][t]
        if ', ' in t:
            return ', '.join(
                x.strip() if is_pure_data(x)
                else self.look('values', x.strip(), kind)
                for x in t.split(','))
        if len(t.split()) >= 6:
            return self.look('sentences', t, kind)
        return self.units(self.look('values', t, kind))


# ------------------------------------------------------- izkārtojuma loģika
def classify(span):
    bold = 'Bold' in span['font']
    if span['size'] >= 11.5:
        return 'title'
    if span['color'] == 0xffffff or (bold and span['size'] >= 10):
        return 'section'
    return 'label' if bold else 'value'


def infer_alignment(spans):
    x0c, x1c = {}, {}
    for s in spans:
        if s['kind'] != 'value':
            continue
        a, b = round(s['bbox'][0]), round(s['bbox'][2])
        x0c[a] = x0c.get(a, 0) + 1
        x1c[b] = x1c.get(b, 0) + 1
    for s in spans:
        if s['kind'] != 'value':
            s['align'] = 'left'
        else:
            l = x0c.get(round(s['bbox'][0]), 0)
            r = x1c.get(round(s['bbox'][2]), 0)
            s['align'] = 'right' if r > l else 'left'


def background_of(drawings, rect):
    best, area = None, float('inf')
    for d in drawings:
        if not d.get('fill'):
            continue
        r = d['rect']
        if r.contains(rect) and r.get_area() < area:
            best, area = d['fill'], r.get_area()
    return best or (1, 1, 1)


def fit_size(text, font, size, max_w):
    while size > 5.0 and font.text_length(text, size) > max_w:
        size -= 0.25
    return size


# ------------------------------------------------------------------- galvenā
def build(src_path, outdir, glossary=None):
    """Atgriež (izvades_ceļš, [nezināmie])."""
    tr = Translator(glossary or load_glossary())
    src = pymupdf.open(src_path)
    out = pymupdf.open()
    out.insert_pdf(src, from_page=0, to_page=0)     # 1. lpp: EN oriģināls
    out.insert_pdf(src, from_page=0, to_page=0)     # 2. lpp: pārrakstīsim
    page = out[1]

    fr = pymupdf.Font(fontfile=FONT_REG)
    fb = pymupdf.Font(fontfile=FONT_BLD)
    drawings = page.get_drawings()

    spans = []
    for b in page.get_text('dict')['blocks']:
        if b['type'] != 0:
            continue
        for line in b['lines']:
            for s in line['spans']:
                if not s['text'].strip():
                    continue
                spans.append({
                    'text': s['text'], 'bbox': pymupdf.Rect(s['bbox']),
                    'size': s['size'], 'color': s['color'],
                    'bold': 'Bold' in s['font'], 'kind': classify(s),
                })
    infer_alignment(spans)

    for s in spans:
        s['lv'] = tr.run(s['text'], s['kind'])
        s['bg'] = background_of(drawings, s['bbox'])

    for s in spans:
        page.add_redact_annot(s['bbox'] + (-1, -1.5, 1, 1.5), fill=s['bg'])
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)

    page.insert_font(fontname='DMR', fontfile=FONT_REG)
    page.insert_font(fontname='DMB', fontfile=FONT_BLD)

    labels_x = sorted({s['bbox'][0] for s in spans if s['kind'] == 'label'})
    for s in spans:
        text, r = s['lv'], s['bbox']
        font = fb if s['bold'] else fr
        size = s['size']

        if s['kind'] == 'label':
            row = [t['bbox'][0] for t in spans
                   if t['kind'] == 'value' and abs(t['bbox'][1] - r.y0) < 3
                   and t['bbox'][0] > r.x0]
            max_w = (min(row) if row else RIGHT_MARGIN) - r.x0 - 4
        elif s['align'] == 'right':
            max_w = r.x1 - min(labels_x, default=r.x0) - 90
        else:
            max_w = RIGHT_MARGIN - r.x0

        size = fit_size(text, font, size, max_w)
        w = font.text_length(text, size)
        x = r.x1 - w if s['align'] == 'right' else r.x0
        y = r.y1 - (r.height - size) * 0.25
        c = s['color']
        page.insert_text((x, y), text, fontname=('DMB' if s['bold'] else 'DMR'),
                         fontsize=size,
                         color=((c >> 16 & 255) / 255, (c >> 8 & 255) / 255,
                                (c & 255) / 255))

    base = re.sub(r'\.pdf$', '', os.path.basename(src_path), flags=re.I)
    base = re.sub(r'^\d{10,}_', '', base)
    dst = os.path.join(outdir, base + '_EN-LV.pdf')
    out.save(dst, garbage=3, deflate=True)
    out.close()
    src.close()
    return dst, tr.unknown
