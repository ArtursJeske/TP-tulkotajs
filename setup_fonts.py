# -*- coding: utf-8 -*-
"""Lejupielādē DM Sans un izveido Regular/Bold ar latviešu diakritiku."""
import os, urllib.request
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

URL = ('https://raw.githubusercontent.com/google/fonts/main/ofl/dmsans/'
       'DMSans%5Bopsz%2Cwght%5D.ttf')
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs('fonts', exist_ok=True)
var = 'fonts/dmsans-variable.ttf'
if not os.path.exists(var):
    print('Lejupielādē DM Sans...')
    urllib.request.urlretrieve(URL, var)
for name, wght in [('DMSans-Regular', 400), ('DMSans-Bold', 700)]:
    f = TTFont(var)
    instantiateVariableFont(f, {'wght': wght, 'opsz': 9}, inplace=True)
    f.save(f'fonts/{name}.ttf')
    print('Izveidots', name)
