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
from pathlib import Path
from pprint import pprint
from unittest.mock import patch

import requests

from callattendant.screening.nomorobo import NomoroboService

@patch.object(NomoroboService, "http_get")
def test_5622862616_should_score_1(mock_get):
    mock_get.return_value = Path("./nomorobo_content/nomorobo_5622862616.html").read_text(encoding="utf-8")
    nomorobo = NomoroboService()
    result = nomorobo.lookup_number("5622862616")
    pprint(result)
    assert result["score"] == 1

@patch.object(NomoroboService, "http_get")
def test_8886727156_should_be_spam(mock_get):
    mock_get.return_value = Path("./nomorobo_content/nomorobo_8886727156.html").read_text(encoding="utf-8")
    nomorobo = NomoroboService()
    result = nomorobo.lookup_number("8886727156")
    pprint(result)
    assert result["spam"] is True

@patch.object(NomoroboService, "http_get")
def test_8886727156_should_score_2(mock_get):
    mock_get.return_value = Path("./nomorobo_content/nomorobo_8886727156.html").read_text(encoding="utf-8")
    nomorobo = NomoroboService()
    result = nomorobo.lookup_number("8886727156")
    pprint(result)
    assert result["score"] == 2


@patch.object(NomoroboService, "http_get")
def test_404_not_marked_as_spam(mock_get):
    mock_get.side_effect = requests.exceptions.HTTPError()
    nomorobo = NomoroboService()
    result = nomorobo.lookup_number("1234567890")
    pprint(result)
    assert result["spam"] is False

@patch.object(NomoroboService, "http_get")
def test_9725551356_is_unknown(mock_get):
    mock_get.return_value = Path("./nomorobo_content/nomorobo_9725551356.html").read_text(encoding="utf-8")
    nomorobo = NomoroboService()
    result = nomorobo.lookup_number("9725551356")
    pprint(result)
    assert result["score"] == 0

@patch.object(NomoroboService, "http_get")
def test_9725551356_is_not_spam(mock_get):
    mock_get.return_value = Path("./nomorobo_content/nomorobo_9725551356.html").read_text(encoding="utf-8")
    nomorobo = NomoroboService()
    result = nomorobo.lookup_number("9725551356")
    pprint(result)
    assert result["spam"] is False

@patch.object(NomoroboService, "http_get")
def test_8554188397_should_score_2(mock_get):
    mock_get.return_value = Path("./nomorobo_content/nomorobo_8554188397.html").read_text(encoding="utf-8")
    nomorobo = NomoroboService()
    result = nomorobo.lookup_number("8554188397")
    pprint(result)
    assert result["score"] == 2