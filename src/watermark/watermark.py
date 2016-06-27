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
import os
import logging
from functools import partial

from PIL import Image

logging.basicConfig(level=logging.INFO)


def process_image(source, output, watermark, thumbnail, opacity):
    source = Image.open(source)
    if source.mode != 'RGBA':
        source = source.convert('RGBA')
    if thumbnail:
        thumb_ratio = thumbnail[0] / thumbnail[1]
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
        source.thumbnail(thumbnail)
    s_xsize, s_ysize = source.size
    watermark = Image.open(watermark)
    if watermark.mode != 'RGBA':
        watermark = watermark.convert('RGBA')
    mask = watermark.split()[3].point(lambda i: i * opacity / 100)
    w_xsize, w_ysize = watermark.size
    for pos_x in range(0, s_xsize, w_xsize):
        for pos_y in range(0, s_ysize, w_ysize):
            box = (pos_x, pos_y, pos_x + w_xsize, pos_y + w_ysize)
            source.paste(watermark, box, mask=mask)
    source.save(output, format='JPEG')


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


def arg_directory(mode='r'):
    modes = {'r': os.R_OK, 'w': os.W_OK}
    verbs = {'r': 'readable', 'w': 'writable'}
    if mode not in modes:
        raise argparse.ArgumentTypeError('Invalid directory mode')

    def readable_dir(prospective_dir):
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError(
                '{0} is not a valid path'
                .format(prospective_dir))
        if os.access(prospective_dir, modes[mode]):
            return prospective_dir
        else:
            raise argparse.ArgumentTypeError(
                '{0} is not a {1} dir'
                .format(prospective_dir, verbs[mode]))
    return readable_dir


def main():
    parser = argparse.ArgumentParser('Watermarks an image')
    subs = parser.add_subparsers(dest='action')

    single = subs.add_parser('single')
    single.add_argument('source', type=argparse.FileType(mode='rb'),
                        help='Source image')
    single.add_argument('output', type=argparse.FileType(mode='wb'),
                        help='Destination for watermarked image')

    batch = subs.add_parser('batch')
    batch.add_argument('source_dir', type=arg_directory('r'),
                       help='Source directory')
    batch.add_argument('output_dir', type=arg_directory('w'),
                       help='Destination directory for watermarked images')

    for p in [single, batch]:
        p.add_argument('-w', '--watermark', type=argparse.FileType(mode='rb'),
                       required=True, help='Watermark image')
        p.add_argument('--opacity', type=partial(arg_type, min_val=0,
                                                 max_val=100),
                       default=50,
                       help='Watermark opacity (from 0, transparent, to 100, '
                            'opaque)')
        p.add_argument('--thumbnail', type=dimensions,
                       help='Generates a thumbnail (ex: 100x150)')
        p.add_argument('-d', '--debug', action='store_true',
                       help='Show debug exceptions')

    args = parser.parse_args()

    if args.action == 'single':
        logging.info('Processing image {}'.format(args.source.name))
        try:
            process_image(args.source, args.output, args.watermark,
                          args.thumbnail, args.opacity)
        except Exception as e:
            logging.error(e)
            if args.debug:
                raise e
    else:
        logging.info('Processing files in directory {}'.format(args.source_dir))
        for file_name in os.listdir(args.source_dir):
            file_path = os.path.join(args.source_dir, file_name)
            if os.path.isfile(file_path):
                output_path = os.path.join(args.output_dir, file_name)
                try:
                    with open(file_path, 'rb') as source:
                        with open(output_path, 'wb') as output:
                            logging.info('Processing image {}'
                                        .format(file_name))
                            process_image(source, output, args.watermark,
                                          args.thumbnail, args.opacity)
                except Exception as e:
                    if os.path.isfile(output_path):
                        os.remove(output_path)
                    logging.error(e)


if __name__ == '__main__':
    main()
