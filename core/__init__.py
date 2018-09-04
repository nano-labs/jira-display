#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Every time you don't DOC your code god kills a kitten."""

from datetime import datetime

def error_log(msg):
    log = "{} - {}\n".format(datetime.now(), msg)
    print(log)
    with open("logs/error.log", "a") as f:
        f.write(log)

def info_log(msg):
    log = "{} - {}\n".format(datetime.now(), msg)
    print(log)
    with open("logs/info.log", "a") as f:
        f.write(log)
