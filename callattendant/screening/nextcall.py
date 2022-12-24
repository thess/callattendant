#!/usr/bin/env python
#
# file: nextcall.py
#
#
# Copyright 2022 Bob Alexander <callattendant@LoadAccumulator.com>
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

# Implement routines that set a flag indicating the next incoming call should
# be permitted, and testing/clearing that flag

import os

class NextCall(object):
    """Track state of the next call flag"""
    def __init__(self, config):
        self.flag_file = config.get("PERMIT_NEXT_CALL_FLAG")

    def is_next_call_permitted(self):
        return os.path.exists(self.flag_file)

    def toggle_next_call_permitted(self):
        if os.path.exists(self.flag_file):
            os.remove(self.flag_file)
            return False
        else:
            with open(self.flag_file, 'w') as file:
                file.write('Permit')
            return True
