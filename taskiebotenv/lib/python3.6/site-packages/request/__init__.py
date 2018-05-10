#!/usr/bin/env python
from get import GET
from post import POST

__all__ = ["REQUEST"]


def get_request():
    kwargs = dict()
    kwargs.update(GET)
    kwargs.update(POST)
    return kwargs


REQUEST = get_request()
