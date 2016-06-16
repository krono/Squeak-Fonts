#!/usr/bin/env python
# -*- coding: utf-8 -*-

print "Loading Renderer..."
from render import render
print "."
from subprocess import call
import sys
SIZES = [10, 14, 19, 22, 27, 32]
SUFFIXES = ['.otf', '.ttf', '.ttc']
SUFFIXES.extend([s.upper() for  s in SUFFIXES])

def do(FONTS, SIZES):
    for font in FONTS:
        print '===', font, '==='
        for size in SIZES:
            render(font, size, dark=False)
            render(font, size, dark=True)

def find_fonts(dirname='DejaVu'):

    def check(filename):
        return (any([filename.endswith(suffix) for suffix in SUFFIXES])
                and os.path.exists(os.path.join(dirname, filename)))

    import os
    if not os.path.isdir(dirname):
        raise Error("Cannot find directory %s" % dirname)
    return [os.path.join(dirname, f) for f in filter(check, os.listdir(dirname))]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >> sys.stderr, "make_fonts_in_dir.py dirname [noopt]"
        exit(2)
    dirname = sys.argv[1]
    fonts = find_fonts(dirname)
    opt = False if (len(sys.argv) > 2 and sys.argv[2] == 'noopt') else True
    do(fonts, SIZES)
    if opt:
        call(['find', dirname] + '-name *.png -exec open -a ImageOptim {} +'.split())
    print "Done"
