#!/usr/bin/env python
# -*- coding: utf-8 -*-

print "Loading Renderer..."
from render import render
from subprocess import call

def do(FONTS, SIZES):
    for font in FONTS:
        print '===', font, '==='
        for size in SIZES:
            render(font, size, dark=False, MAX_UNICODE=0xFF)
            render(font, size, dark=True, MAX_UNICODE=0xFF)

SIZES=[10, 14, 19, 22, 27, 32]
# 4,5,3,5,5
FONTS=[
    'DejaVu/DejaVuSans-Bold.ttf',
    'DejaVu/DejaVuSans-BoldOblique.ttf',
    'DejaVu/DejaVuSans-Oblique.ttf',
    'DejaVu/DejaVuSans.ttf',
]

do(FONTS, SIZES)
SIZES = [11, 15, 20]
FONTS = [
    'Fira/FiraMono-Medium.otf',
    'Fira/FiraMono-Regular.otf',

    'Fira/FiraSans-Italic.otf',
    'Fira/FiraSans-Medium.otf',
    'Fira/FiraSans-MediumItalic.otf',
    'Fira/FiraSans-Regular.otf',
]
# do(FONTS, SIZES)


# call('find . -name *.png -exec open -a ImageOptim {} +'.split())

print "Done"
