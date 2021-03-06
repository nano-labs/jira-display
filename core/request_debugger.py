# -*- coding: utf-8 -*-
"""
Debug snipet for requests library.

Replaces the requests library adding some debug code on it.
"""

import urllib.request, urllib.parse, urllib.error
import inspect
import json
from functools import wraps
from datetime import datetime
import requests
from requests import Session

MAX_DEPTH = 1
LOG = "log"
CURL = "curl"
REQUESTS = PYTHON = "python"
VERBOSE_FORMAT = LOG


def requests_to_curl(method, url, *args, **kwargs):
    """Return the request as cURL string."""
    kwargs = args[1]
    headers = ['-H "%s:%s"' % (k, v)
               for k, v in list(kwargs.get("headers", {}).items())]
    cookies = ['-H "Cookie:%s=%s"' % (k, v)
               for k, v in list(kwargs.get("cookies", {}).items())]
    headers = " ".join(headers + cookies)
    params = urllib.parse.urlencode(kwargs.get("params", ""))

    body = kwargs.get("data")
    if isinstance(body, dict):
        body = json.dumps(body)
    body = "-d '%s'" % body if body else ""

    proxies = kwargs.get("proxies") or {}
    proxies = " ".join(["--proxy %s://%s" % (proto, uri)
                        for proto, uri in list(proxies.items())])

    if params:
        url = "%s%s%s" % (url, "&" if "?" in url else "?", params)

    curl = """curl -i -X %(method)s %(proxies)s %(headers)s %(body)s '%(url)s'""" % {
           "url": url, "method": method.upper(), "headers": headers,
           "body": body, "proxies": proxies}

    return curl


def requests_string(method, url, *args, **kwargs):
    """Return a string that contains a python requests call."""
    kwargs = args[1]
    args = args[0]
    args_string = (", %s" % ", ".join([i for i in args])) if args else ""
    kwargs_string = ", ".join(["%s=%s" % (k, v) for k, v in list(kwargs.items())])
    line = 'requests.%s("%s"%s, %s)' % (
                        method, url, args_string, kwargs_string)
    return line


def log_string(method, url, *args, **kwargs):
    """Return a simple log string."""
    line = '%s - %s: %s %s %s' % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                  method.upper(), url, str(args), kwargs)
    return line


def cprint(string, color):
    """Print a colored line."""
    color_code = {"red": 1, "gray": 0}.get(color, 0)
    print("\033[9%sm%s\033[0m" % (color_code, string))


def add_logger(func):
    """Adiciona o print ao método."""
    @wraps(func)
    def logger(*args, **kwargs):
        """Printa de modo amigável todos os requests feitos."""
        _args = list(args)
        url = kwargs.get("url") or _args.pop(0)
        log_format = {"python": requests_string,
                      "curl": requests_to_curl,
                      "log": log_string}.get(VERBOSE_FORMAT) or log_string
        request_line = log_format(func.__name__, url, _args, kwargs)

        tabbing = ""
        if MAX_DEPTH:
            code_point = inspect.currentframe().f_back
            arquivo = code_point.f_code.co_filename
            arquivo_linha = code_point.f_lineno
            track = [(arquivo, arquivo_linha)]
            while len(track) < MAX_DEPTH:
                code_point = code_point.f_back
                if not code_point:
                    break
                arquivo = code_point.f_code.co_filename
                arquivo_linha = code_point.f_lineno
                if arquivo not in [i for i, j in track]:
                    track = [(arquivo, arquivo_linha)] + track

            for a, l in track:
                cprint("%s%s Line: %s" % (tabbing, a, l), "gray")
                tabbing += "  "

        cprint("%s%s" % (tabbing, request_line), "red")
        return func(*args, **kwargs)

    return logger


for method in ["get", "post", "put"]:
    func = getattr(requests, method)
    logged_func = add_logger(func)
    setattr(requests, method, logged_func)

    func = getattr(Session, method)
    logged_func = add_logger(func)
    setattr(Session, method, logged_func)
