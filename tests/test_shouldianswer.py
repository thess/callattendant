#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pprint import pprint

import pytest

from callattendant.screening.shouldianswer import ShouldIAnswer


@pytest.fixture(scope='function')
def should_i_answer():
    should_i_answer = ShouldIAnswer()
    return should_i_answer


def test_8886727156_should_score_0(should_i_answer):
    result = should_i_answer.lookup_number("8886727156")
    pprint(result)
    assert result["score"] == 0


def test_8886727156_is_not_spam(should_i_answer):
    result = should_i_answer.lookup_number("8886727156")
    pprint(result)
    assert result["spam"] is not True


def test_1234567890_not_marked_as_spam(should_i_answer):
    result = should_i_answer.lookup_number("1234567890")
    pprint(result)
    assert result["spam"] is False


def test_9725551356_is_unknown(should_i_answer):
    result = should_i_answer.lookup_number("9725551356")
    pprint(result)
    assert result["score"] == 0


def test_9725551356_is_not_spam(should_i_answer):
    result = should_i_answer.lookup_number("9725551356")
    pprint(result)
    assert result["spam"] is False


def test_8554188397_is_spam(should_i_answer):
    result = should_i_answer.lookup_number("8554188397")
    pprint(result)
    assert result["spam"]
