from pprint import pprint

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

class TwilioService(object):

    account_sid=""
    auth_token=""

    def lookup_number(self, number):

        # Assuming not spam
        reason = "Unknown"
        score = 0
        status = "failed"

        client = Client(self.account_sid, self.auth_token)

        try:
            number_details = client.lookups.v1.phone_numbers(number).fetch(
                add_ons=["nomorobo_spamscore"]
            )
            add_ons = number_details.add_ons
            pprint(add_ons)
            if(
                add_ons
                and add_ons.get("status") == "successful"
                and "nomorobo_spamscore" in add_ons.get("results", {})
            ):
                nomorobo_result = add_ons["results"]["nomorobo_spamscore"]["result"]
                status = nomorobo_result.get("status", "failed")
                score = nomorobo_result.get("score", 0)
                reason = nomorobo_result.get("message", "Unknown")
            else:
                print("Twilio lookup failed; is nomorobo_spamscore installed?")
                reason = "Twilio Nomorobo lookup failed"

        except TwilioRestException as e:
            # Handle Twilio-specific errors (e.g., invalid number, auth issues)
            print("Twilio lookup failed: {}".format(e))
            reason = f"Twilio API error: {str(e)}"
        except Exception as e:
            # Handle unexpected errors (e.g., network issues)
            print("Twilio lookup failed: {}".format(e))
            reason = f"Unexpected error: {str(e)}"

        spam = False if score < self.spam_threshold else True

        return {"spam": spam, "score": score, "reason": reason}


    def __init__(self, spam_threshold=1, account_sid=None, auth_token=None):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.spam_threshold = spam_threshold


