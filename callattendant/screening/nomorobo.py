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
        url = "https://www.nomorobo.com/lookup/{}-{}-{}".format(number[0:3], number[3:6], number[6:])
        allowed_codes = [404]  # allow not found response
        try:
            content = self.http_get(url, allowed_codes)
            soup = BeautifulSoup(content, "lxml")  # lxml HTML parser: fast
        except Exception as err:
            print("Nomorobo number lookup failed: {}".format(err))
            return {"spam": False, "score": 0, "reason": "Lookup failed"}

        score = 0  # = no spam
        reason = ""

        divs = soup.findAll(class_="column_attr")
        for text in divs:
            if text.get_text().upper().find("SCAM") > -1:
                reason = text.get_text().strip()
                score = 2
                break
            if text.get_text().upper().find("UNKNOWN") > -1:
                reason = text.get_text().strip()
                score = 0
                break
            if text.get_text().upper().find("ROBOCALL") > -1:
                reason = text.get_text().strip()
                # This is a robocaller; look for severity for escalation
                severity = soup.findAll(class_="button_severe")
                if len(severity) > 0:
                    label = severity[0].getText().upper()
                    if label.find("SEVERE") > -1 or label.find("HIGH") > -1 or label.find("ELEVATED") > -1:
                        score = 2
                    else:
                        score = 1
                else:
                    score = 1
                break

        spam = False if score < self.spam_threshold else True

        return {"spam": spam, "score": score, "reason": reason}

    def http_get(self, url, allowed_codes=None):
        data = ""
        # Handle network errors in the caller
        try:
            response = requests.get(url, timeout=5)
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

    def __init__(self, spam_threshold=2):
        self.spam_threshold = spam_threshold
