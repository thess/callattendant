#!/usr/bin/env python
#
# file: listfiles.py
#
#
# Copyright 2021 Bob Alexander <callattendant@LoadAccumulator.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Implement routines for working with the list files, i.e. blocknameslist.txt,
# blocknumberslist.txt, etc. These files hold lists of regular expressions, one
# per line, of patterns to permit or block

import os

def read_list_file_list(fname):
    list = {}
    try:
        with open(fname) as file:
            for line in file:
                keyval = line.split(':', 1)
                if len(keyval) > 0:
                    key = keyval[0].strip()
                    if key != '':
                        if len(keyval) > 1:
                            val = keyval[1].strip()
                        else:
                            val = ''
                        list[key] = val
    except FileNotFoundError:
        pass

    return list


def read_list_file_text(fname):
    contents = ''
    try:
        with open(fname) as file:
            contents = file.read()
    except FileNotFoundError:
        pass

    return contents

def write_list_file_text(fname, text):
    with open(fname, 'w') as file:
        file.write(text)
