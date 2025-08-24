#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
#  nomorobo.py
#
#  Copyright 2018 Bruce Schubert <bruce@emxsys.com>
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


import requests
from bs4 import BeautifulSoup

class NomoroboService(object):

    def lookup_number(self, number):
        auth_payload = {
            'email': self.email,
            'password': self.password,
            'math': '',
            'remember': 'on',
            '_token': ''  # filled in after GET /login
        }
        check_form = "/lookup/{}-{}-{}".format(number[0:3], number[3:6], number[6:])
        query_args = {
            'base_url': 'https://www.nomorobo.com',
            'login_uri': '/login',
            'login_post': '/login',
            'lookup_uri': check_form,
            'payload': auth_payload
        }
        allowed_codes = [404]  # allow not found response
        try:
            content = self.http_transact(query_args, allowed_codes)
            soup = BeautifulSoup(content, "lxml")  # lxml HTML parser: fast
        except Exception as err:
            print("Nomorobo number lookup failed: {}".format(err))
            return {"spam": False, "score": 0, "reason": "Lookup failed"}

        reason = ""
        score = 0  # = no spam

        result = soup.find_all("h2", class_="title")
        if len(result) > 1:
            # The second title is the phone number
            phone_number = result[1].get_text()
            # cleanup text
            phone_number = phone_number.translate({ord(c): None for c in " ()-"})
            if (phone_number == number):
                # The phone number matches the one we are looking up
                # Now look for the spam score
                mfn_items = soup.find_all(class_="mfn-inline-editor")
                if len(mfn_items) > 3:
                    reason = mfn_items[3].get_text().replace("\n", "").strip(" ")
                    test_upper = reason.upper()
                    if test_upper.find("UNKNOWN") > -1:
                        score = 0
                    elif test_upper.find("SCAM") > -1:
                        score = 2
                    elif test_upper.find("ROBOCALL") > -1:
                        # cleanup text and remove newlines and trailing period
                        reason = reason + ' (' + mfn_items[4].get_text() + ')'
                        reason = reason.translate({ord(c): None for c in "\n."})

                        # This is a robocaller; look for severity for escalation
                        severity = soup.find_all(class_="button_severe")
                        if len(severity) > 0:
                            label = severity[0].get_text().upper()
                            if label.find("SEVERE") > -1 or label.find("HIGH") > -1 or label.find("ELEVATED") > -1:
                                score = 2
                            else:
                                score = 1
                    else:
                        score = 1

        spam = False if score < self.spam_threshold else True

        return {"spam": spam, "score": score, "reason": reason}

    def http_transact(self, query_args, allowed_codes=None):
        data = ""
        # Handle network errors in the caller
        try:
            with requests.Session() as s:
                if len(query_args['login_uri']) > 0:
                    response = s.get(query_args['base_url'] + query_args['login_uri'], timeout=5)
                    signin = BeautifulSoup(response._content, 'lxml')

                    token = signin.find('input', {'name': "_token"})['value']
                    query_args['payload']['_token'] = token
                    res = s.post(query_args['base_url'] + query_args['login_post'], data=query_args['payload'])
                    if res.status_code != 200:
                        res.raise_for_status()

                response = s.get(query_args['base_url'] + query_args['lookup_uri'], timeout=5)
                if response.status_code == 200:
                    data = response.text
                elif response.status_code not in allowed_codes:
                    response.raise_for_status()
        except requests.HTTPError as e:
            # Print HTTP error code and throw exception to caller
            code = e.response.status_code
            print("HTTPError: {}".format(code))
            raise

        return data

    def __init__(self, email, password, spam_threshold=2):
        self.email = email
        self.password = password
        self.spam_threshold = spam_threshold
