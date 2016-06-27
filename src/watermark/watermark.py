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

from PIL import Image


def main():
    parser = argparse.ArgumentParser('Watermarks an image')
    parser.add_argument('source', type=argparse.FileType(mode='rb'),
                        help='Source image')
    parser.add_argument('-o', '--output', type=argparse.FileType(mode='wb'),
                        help='Destination for watermarked image')
    parser.add_argument('-w', '--watermark', type=argparse.FileType(mode='rb'),
                        help='Watermark image')

    args = parser.parse_args()

    source = Image.open(args.source)
    if source.mode != 'RGBA':
        source = source.convert('RGBA')
    s_xsize, s_ysize = source.size
    watermark = Image.open(args.watermark)
    if watermark.mode != 'RGBA':
        watermark = watermark.convert('RGBA')
    mask = watermark.split()[3].point(lambda i: i * .3)
    w_xsize, w_ysize = watermark.size
    for pos_x in range(0, s_xsize, w_xsize):
        for pos_y in range(0, s_ysize, w_ysize):
            box = (pos_x, pos_y, pos_x + w_xsize, pos_y + w_ysize)
            source.paste(watermark, box, mask=mask)
    source.save(args.output, format='JPEG')


if __name__ == '__main__':
    main()
