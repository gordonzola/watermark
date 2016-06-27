#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2016 Damien Nicolas <damien@gordon.re>
#
# Distributed under terms of the MIT license.

"""
Main Watermark script
"""
import argparse
import re
from functools import partial

from PIL import Image


def arg_type(x, min_val, max_val):
    x = int(x)
    if x < min_val or x > max_val:
        raise argparse.ArgumentTypeError('Value must be between {} and {}'
                                         .format(min_val, max_val))
    return x


def dimensions(s):
    match = re.match(r'^(\d+)x(\d+)$', s)
    if match is None:
        raise argparse.ArgumentTypeError('Incorrect dimensions')
    return [int(i) for i in match.groups()]


def main():
    parser = argparse.ArgumentParser('Watermarks an image')
    parser.add_argument('source', type=argparse.FileType(mode='rb'),
                        help='Source image')
    parser.add_argument('-o', '--output', type=argparse.FileType(mode='wb'),
                        required=True,
                        help='Destination for watermarked image')
    parser.add_argument('-w', '--watermark', type=argparse.FileType(mode='rb'),
                        required=True,
                        help='Watermark image')
    parser.add_argument('--opacity', type=partial(arg_type, min_val=0,
                                                  max_val=100),
                        default=50,
                        help='Watermark opacity (from 0, transparent, to 100, '
                             'opaque)')
    parser.add_argument('--thumbnail', type=dimensions,
                        help='Generates a thumbnail (ex: 100x150)')

    args = parser.parse_args()

    source = Image.open(args.source)
    if source.mode != 'RGBA':
        source = source.convert('RGBA')
    if args.thumbnail:
        thumb_ratio = args.thumbnail[0] / args.thumbnail[1]
        source_ratio = source.size[0] / source.size[1]
        if thumb_ratio != source_ratio:
            if source_ratio > thumb_ratio:
                thumb_y = source.size[1]
                thumb_x = thumb_y * thumb_ratio
                thumb_size = (thumb_x, thumb_y)
            elif source_ratio < thumb_ratio:
                thumb_x = source.size[0]
                thumb_y = thumb_x / thumb_ratio
                thumb_size = (thumb_x, thumb_y)
            box = (source.size[0] / 2 - thumb_size[0] / 2,
                   source.size[1] / 2 - thumb_size[1] / 2,
                   source.size[0] / 2 + thumb_size[0] / 2,
                   source.size[1] / 2 + thumb_size[1] / 2)
            source = source.crop(box)
        source.thumbnail(args.thumbnail)
    s_xsize, s_ysize = source.size
    watermark = Image.open(args.watermark)
    if watermark.mode != 'RGBA':
        watermark = watermark.convert('RGBA')
    mask = watermark.split()[3].point(lambda i: i * args.opacity / 100)
    w_xsize, w_ysize = watermark.size
    for pos_x in range(0, s_xsize, w_xsize):
        for pos_y in range(0, s_ysize, w_ysize):
            box = (pos_x, pos_y, pos_x + w_xsize, pos_y + w_ysize)
            source.paste(watermark, box, mask=mask)
    source.save(args.output, format='JPEG')


if __name__ == '__main__':
    main()
