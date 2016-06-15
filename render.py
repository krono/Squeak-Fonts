#!/bin/env python
# -*- coding: utf-8 -*-
from fontTools.misc.py23 import *
import objc
objc.setVerbose(True)

from Quartz import *
import freetype
import os, math, sys, unicodedata


DEBUG=False
# DEBUG=True

def render(font_file, height=14, dark=False, MAX_UNICODE=0x23FF):
    # # Haha.
    import ctypes, ctypes.util
    CG = ctypes.cdll.LoadLibrary(ctypes.util.find_library('CoreGraphics'))
    CG.CGContextSetFontSmoothingBackgroundColor.restype = None

    bitPerComponent = 8
    componentsPerByte = 1
    bytePerPixel = 4
    bitPerPixel = bitPerComponent * bytePerPixel

    graphicsFont = CGFontCreateWithDataProvider(
        CGDataProviderCreateWithURL(
            CFURLCreateWithFileSystemPath(
                None, CFSTR(font_file), kCFURLPOSIXPathStyle,False)))

    freetypeFont = freetype.Face(font_file)

    def get_ccodes(fn):
        character2glyph = {0:0}
        glyph2character = {0:0}
        c, i = fn.get_first_char()
        while i:
            character2glyph.setdefault(c, i)
            glyph2character.setdefault(i, c)
            c, i = fn.get_next_char(c, i)
        if 0x2191 in character2glyph and 0x2190 in character2glyph:
            #squeakiness
            character2glyph[0x80] = character2glyph[0x5E] # ^
            character2glyph[0x81] = character2glyph[0x5F] # _
            character2glyph[0x82] = character2glyph[0x2191] # arrow up
            character2glyph[0x83] = character2glyph[0x2190] # arrow left
        return character2glyph, glyph2character

    character2glyph, glyph2character = get_ccodes(freetypeFont)

    def _c(ch):
        return character2glyph[ord(ch)]
    def _g(gl):
        return unichr(glyph2character[gl]).encode('utf-8')


    PerEmForReal = float(CGFontGetUnitsPerEm(graphicsFont))

    ascentForReal = CGFontGetAscent(graphicsFont) / PerEmForReal
    descentForReal = CGFontGetDescent(graphicsFont) / PerEmForReal

    heightForReal = ascentForReal + -descentForReal

    # derrive from desired pixel size
    font_size = round(height / heightForReal)
    # derrive from new size
    descent = descentForReal * font_size
    PerEm = PerEmForReal / font_size

    # print PerEmForReal, ascentForReal, descentForReal, heightForReal, font_size, descent, PerEm


    squeak_font_size = int(math.ceil(font_size * 72 / 100))
    squeak_descent = int(abs(round(descent)))
    squeak_ascent = int(round(ascentForReal * font_size))

    charcodes = character2glyph.keys()

    squeak_max_ascii = code_point_max = min(max(charcodes), MAX_UNICODE)

    squeak_name = CGFontCopyFullName(graphicsFont)
    if squeak_name == 'DejaVu Sans':
        squeak_name = 'DejaVu Sans Book'
    if dark:
        squeak_name += ' Dark'
    squeak_name_full = '%s %d' % (squeak_name, squeak_font_size)

    print squeak_name, "@", squeak_font_size


    def _e(font_pt):
        return font_pt / PerEm

    def get_glidx(character2glyph):
        keys = list(character2glyph.keys())
        keys.sort()
        return [character2glyph[c] for c in keys]

    glyphindices = get_glidx(character2glyph)

    ok, bboxes = CGFontGetGlyphBBoxes(graphicsFont, glyphindices, len(glyphindices), None)
    assert ok
    # print "bboxes ok?", ok

    ok, advances = CGFontGetGlyphAdvances(graphicsFont, glyphindices, len(glyphindices), None)
    # print "advances ok?", ok
    assert ok

    def get_positions(glyphindices, bboxes, advances, descent):
        max_advance = 0
        positions = []
        new_glyphindices = []
        xTable = []
        x = 0
        for code_point in range(code_point_max + 1):
            xTable.append(x)
            if code_point not in character2glyph:
                continue
            glyph = character2glyph[code_point]
            glyphindex = glyphindices.index(glyph)
            bbox = bboxes[glyphindex]
            advance = _e(advances[glyphindex])
            width = _e(bbox.size.width)

            add_left = abs(_e(bbox.origin.x)) if bbox.origin.x < 0 else 0
            w_advance = width + add_left # right is already in width

            x_advance = max(advance, w_advance) # not too snuggly please
            if add_left > 1: # those far-leftsies can cause trouble
                x_advance -= 1

            if height <= 10: #ok this is too tiny.
                pixel_advance = int(math.ceil(x_advance))
                y = math.floor(-descent)
            else:
                pixel_advance = int(round(x_advance))
                y = math.ceil(-descent)
            jitter = (pixel_advance - x_advance) / 2.0
            origin_x = x + add_left + jitter

            new_glyphindices.append(glyphindices[glyphindex])
            positions.append((x, CGPoint(origin_x, y)))
            # positions.append((x, CGPoint(origin_x, (-descent))))
            x += pixel_advance
            max_advance = max(max_advance, pixel_advance)
        xTable.append(x) # Fin
        return new_glyphindices, positions, xTable, max_advance, int(math.ceil(x))


    glyphindices, positions, xTable, max_advance, width = get_positions(glyphindices, bboxes, advances, descent)

    assert len(xTable) == code_point_max + 2, "%d is not %d" %(len(xTable), code_point_max + 2)


    ##########################################################################
    # Rendering
    #########################################################################

    colorspace = CGColorSpaceCreateDeviceRGB()
    if dark:
        context = CGBitmapContextCreate(None, width, height, bitPerComponent, width * bytePerPixel, colorspace, kCGImageAlphaPremultipliedFirst | kCGBitmapByteOrder32Host)
    else:
        context = CGBitmapContextCreate(None, width, height, bitPerComponent, width * bytePerPixel, colorspace, kCGImageAlphaNoneSkipFirst | kCGBitmapByteOrder32Host)

    CGContextSetTextMatrix(context, CGAffineTransformIdentity)


    # CGContextSetFlatness(context, 0.1);

    CGContextSetInterpolationQuality(context, kCGInterpolationHigh)

    CGContextSetAllowsAntialiasing(context, YES)
    CGContextSetShouldAntialias(context, YES)

    # CGContextSetAllowsFontSmoothing(context, YES)
    # CGContextSetShouldSmoothFonts(context, YES)

    CGContextSetAllowsFontSubpixelPositioning(context, YES)
    CGContextSetShouldSubpixelPositionFonts(context, YES)
    # CGContextSetAllowsFontSubpixelQuantization(context, YES)
    # CGContextSetShouldSubpixelQuantizeFonts(context, YES)

    WHITE = CGColorGetConstantColor(kCGColorWhite)
    BLACK = CGColorGetConstantColor(kCGColorBlack)

    bg = BLACK if dark else WHITE
    fg = WHITE if dark else BLACK

    GRAY = CGColorCreateGenericGray(0.25, 1.0)
    spbg = GRAY if dark else bg


    if dark:
        CGContextClearRect(context, NSMakeRect(0,0,width,height))
        CG.CGContextSetFontSmoothingBackgroundColor(context.__c_void_p__(), spbg.__c_void_p__())
    else:
        CGContextSetFillColorWithColor(context, bg)
        CGContextFillRect(context, NSMakeRect(0,0,width,height))

    CGContextSetFont(context, graphicsFont)
    CGContextSetTextDrawingMode(context, kCGTextFill)
    CGContextSetFillColorWithColor(context, fg)
    CGContextSetFontSize(context, font_size)

    for index in range(len(glyphindices)):
        with CGSavedGState(context):
            pos = positions[index][1]
            glyph_index = glyphindices[index]
            x = positions[index][0]
            if index + 1 < len(positions):
                w = positions[index + 1][0] - x
            else:
                w = width - x
            clip_rect = NSMakeRect(x,0,w,height)
            CGContextClipToRect(context, clip_rect)
            if DEBUG:
                with CGSavedGState(context):
                    CGContextSetStrokeColorWithColor(context, CGColorCreate(colorspace, [0.5,0.0,0.0,0.1]))
                    CGContextStrokeRect(context, clip_rect)
            CGContextShowGlyphsAtPositions(context, [glyph_index], [pos], 1)


    ##########################################################################
    # Persisting
    #########################################################################

    image = CGBitmapContextCreateImage(context)
    imageRep = NSBitmapImageRep.alloc().initWithCGImage_(image)
    data = imageRep.representationUsingType_properties_(NSPNGFileType, None)
    # data = imageRep.representationUsingType_properties_(NSBMPFileType, None)



    sf0_header = [
        0, #magic for new type
        squeak_font_size,
        squeak_ascent,
        squeak_descent,
        0, #min ascii
        squeak_max_ascii,
        max_advance,
        0, #emphasis
    ]

    filedir = os.path.abspath(os.path.dirname(font_file))

    filename_png = filedir + '/' + squeak_name_full + '.png'
    filename_txt = filedir + '/' + squeak_name_full + '.txt'


    success = data.writeToFile_atomically_(filename_png, False)
    if not success:
        print "Oh noes"
        exit(1)

    if dark:
        from subprocess import call
        call([
            'convert',
            '-background', 'White',
            '-flatten',
            filename_png,
            '-negate', filename_png,
              ])

    with open(filename_txt, 'w') as file_txt:
        print >> file_txt, ' '.join(map(str, sf0_header + xTable))

    # print >> sys.stderr, "PNG:%s" % filename_png
    # print >> sys.stderr, "TXT:%s" % filename_png
    print "Ok"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print >> sys.stderr, "render.py filename.{ttf|otf} [size] ['dark']"
        exit(2)
    font_file = sys.argv[1]
    height = int(sys.argv[2]) if len(sys.argv) > 2 else 14
    dark = len(sys.argv) > 3 and sys.argv[3] == 'dark'
    render(font_file, height, dark=dark, MAX_UNICODE=sys.maxint)
