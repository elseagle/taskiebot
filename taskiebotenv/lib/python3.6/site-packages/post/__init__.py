#!/usr/bin/env python
import cgi

__all__ = ["POST"]


def get_post():
    kwargs = dict()
    fs = cgi.FieldStorage()
    for k in fs.keys():
        v = fs[k].value
        kwargs[k] = v
    return kwargs


POST = get_post()
