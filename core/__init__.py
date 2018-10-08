#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Every time you don't DOC your code god kills a kitten."""

from datetime import datetime
from os import path

BASE_DIR = path.dirname(path.abspath(__file__))


def error_log(msg):
    log = "{} - {}\n".format(datetime.now(), msg)
    print(log)
    with open(path.join(BASE_DIR, "../logs/error.log"), "a") as f:
        f.write(log)


def info_log(msg):
    log = "{} - {}\n".format(datetime.now(), msg)
    print(log)
    with open(path.join(BASE_DIR, "../logs/info.log"), "a") as f:
        f.write(log)
