from pprint import pprint

from callattendant.screening.twilio import TwilioService

account_sid=""
auth_token=""

def test_9892812836_should_score_1():
    twilio = TwilioService(account_sid=account_sid, auth_token=auth_token)
    result = twilio.lookup_number("9892812836")
    pprint(result)
    assert result["score"] == 1

def test_9892812836_should_be_spam_when_threshold_is_1():
    twilio = TwilioService(account_sid=account_sid, auth_token=auth_token)
    result = twilio.lookup_number("9892812836")
    pprint(result)
    assert result["spam"] is True

def test_2057567368_should_score_1():
    twilio = TwilioService(account_sid=account_sid, auth_token=auth_token)
    result = twilio.lookup_number("2057567368")
    pprint(result)
    assert result["score"] == 1

def test_404_not_marked_as_spam():
    twilio = TwilioService(account_sid=account_sid, auth_token=auth_token)
    result = twilio.lookup_number("1234567890")
    pprint(result)
    assert result["spam"] is False

def test_9725551356_is_unknown():
    twilio = TwilioService(account_sid=account_sid, auth_token=auth_token)
    result = twilio.lookup_number("9725551356")
    pprint(result)
    assert result["score"] == 0

def test_9725551356_is_not_spam():
    twilio = TwilioService(account_sid=account_sid, auth_token=auth_token)
    result = twilio.lookup_number("+9725551356")
    pprint(result)
    assert result["spam"] is False
