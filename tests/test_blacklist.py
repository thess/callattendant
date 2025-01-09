#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  test_blacklist.py
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

import sqlite3

import pytest

from callattendant.screening.blacklist import Blacklist

BRUCE = {"NAME": "Bruce", "NMBR": "1234567890", "DATE": "1012", "TIME": "0600"}


@pytest.fixture(scope='function')
def blacklist():
    # Create the test db in RAM
    db = sqlite3.connect(":memory:")

    # Mock the application config, which is a dict-based object
    config = {}
    config['DEBUG'] = False
    config['TESTING'] = True

    # Create the blacklist to be tested
    blacklist = Blacklist(db, config)

    return blacklist


def test_can_add_caller_to_blacklist(blacklist):
    assert blacklist.add_caller(BRUCE, "Test")


def test_adding_duplicate_fails(blacklist):
    assert blacklist.add_caller(BRUCE, "Test Add")
    assert blacklist.add_caller(BRUCE, "Test Update") is False


def test_check_number_returns_correct_reason(blacklist):
    test_reason = "SpecificReason"
    blacklist.add_caller(BRUCE, test_reason)
    is_blacklisted, (reason, name) = blacklist.check_number(BRUCE.get("NMBR"))

    assert is_blacklisted is True
    assert reason == test_reason


def test_check_number_returns_none_if_not_present(blacklist):
    blacklist.add_caller(BRUCE, "Test Reason")
    test_number = "1111111111"
    is_blacklisted, reason = blacklist.check_number(test_number)
    assert not is_blacklisted


def test_get_number_returns_entry(blacklist):
    test_reason = "ABC12345"
    blacklist.add_caller(BRUCE, test_reason)
    caller = blacklist.get_number(BRUCE.get("NMBR"))
    assert caller[0][0] == BRUCE.get("NMBR")
    assert caller[0][1] == BRUCE.get("NAME")
    assert caller[0][2] == test_reason


def test_update_number(blacklist):
    test_reason = "ABC12345"
    new_reason = "XYZ98765"
    new_name = "Joe"
    blacklist.add_caller(BRUCE, test_reason)
    blacklist.update_number(BRUCE.get("NMBR"), new_name, new_reason)
    caller = blacklist.get_number(BRUCE.get("NMBR"))
    assert caller[0][0] == BRUCE.get("NMBR")
    assert caller[0][1] == new_name
    assert caller[0][2] == new_reason


def test_removing_number(blacklist):
    blacklist.add_caller(BRUCE, "Test Reason")
    assert len(blacklist.get_number(BRUCE.get("NMBR"))) == 1
    blacklist.remove_number(BRUCE.get("NMBR"))
    assert len(blacklist.get_number(BRUCE.get("NMBR"))) == 0
