#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Every time you don't DOC your code god kills a kitten."""

from core.request_debugger import requests
import json
from os import path
import traceback
from core import error_log
from core.base import Manager

BASE_DIR = path.dirname(path.abspath(__file__))


def screen_saver(config):
    """Because why not? Let's call it 'Benchmark'."""
    import serial
    from PIL import Image
    from PIL import GifImagePlugin
    from time import sleep
    image = Image.open(path.join(BASE_DIR, "images/si.gif"))
    gif = []
    for frame in range(image.n_frames):
        image.seek(frame)
        f = image.copy()
        gif.append(f.convert(mode="1"))

    ser = serial.Serial(config['serial_port'], 57600, timeout=1)
    f = True
    while True:
        for _image in gif:
            # f = not f
            # if f:
            #     continue
            ser.write(b'I')
            bit_position = 0
            binary = ''
            for pixel in _image.getdata():
                bit_position += 1
                binary += str(int(pixel > 0))
                if bit_position == 8:
                    ser.write(bytes([int(binary, 2)]))
                    bit_position = 0
                    binary = ''
            sleep(0.08)

def main():
    config = {}
    with open(path.join(BASE_DIR, "config.json"), "r") as config_file:
        config = json.load(config_file)

    # screen_saver(config)

    while True:
        try:
            manager = Manager(config)
            manager.start()
            manager.run()
        except Exception as exc:
            error_log(exc)
            error_log(traceback.format_exc())


if __name__ == '__main__':
    main()
