#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_nomorobo.py
#
#  Copyright 2020 Bruce Schubert  <bruce@emxsys.com>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

from pprint import pprint

import pytest

from callattendant.screening.nomorobo import NomoroboService

test_username = "<your-username>"
test_password = "<your-password>"

@pytest.fixture(scope='function')
def nomorobo():
    nomorobo = NomoroboService(test_username, test_password)
    return nomorobo

def test_5622862616_should_score_1(nomorobo):
    result = nomorobo.lookup_number("5622862616")
    pprint(result)
    assert result["score"] == 1

def test_8886727156_should_be_spam(nomorobo):
    result = nomorobo.lookup_number("8886727156")
    pprint(result)
    assert result["spam"] is True

def test_8886727156_should_score_2(nomorobo):
    result = nomorobo.lookup_number("8886727156")
    pprint(result)
    assert result["score"] == 2

def test_404_not_marked_as_spam(nomorobo):
    result = nomorobo.lookup_number("1234567890")
    pprint(result)
    assert result["spam"] is False

def test_9725551356_is_unknown(nomorobo):
    result = nomorobo.lookup_number("9725551356")
    pprint(result)
    assert result["score"] == 0

def test_9725551356_is_not_spam(nomorobo):
    result = nomorobo.lookup_number("9725551356")
    pprint(result)
    assert result["spam"] is False

def test_8554188397_should_score_2(nomorobo):
    result = nomorobo.lookup_number("8554188397")
    pprint(result)
    assert result["score"] == 2
