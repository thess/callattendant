#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
#  callscreener.py
#
#  Copyright 2018  <pi@rhombus1>
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


import re
import sys

from screening.blacklist import Blacklist
from screening.whitelist import Whitelist
from screening.nomorobo import NomoroboService
from screening.shouldianswer import ShouldIAnswer
import yaml


class CallScreener(object):
    """The CallScreener provides blacklist and whitelist checks"""

    def is_whitelisted(self, callerid):
        """Returns true if the number is on a whitelist"""
        number = callerid['NMBR']
        name = callerid["NAME"]
        try:
            is_whitelisted, reason = self._whitelist.check_number(callerid['NMBR'])
            if is_whitelisted:
                return True, reason
            else:
                print(">> Checking permitted patterns...")
                patternlist = self.config.get("CALLERID_PATTERNS")["permitnames"]
                for key in patternlist.keys():
                    match = re.search(key, name, re.IGNORECASE)
                    if match:
                        reason = patternlist[key]
                        print(reason)
                        return True, reason

                patternlist = self.config["CALLERID_PATTERNS"]["permitnumbers"]
                for key in patternlist.keys():
                    match = re.search(key, number)
                    if match:
                        reason = patternlist[key]
                        print(reason)
                        return True, reason
                return False, "Not found"
        finally:
            sys.stdout.flush()

    def is_blacklisted(self, callerid):
        """Returns true if the number is on a blacklist"""
        number = callerid['NMBR']
        name = callerid["NAME"]
        try:
            is_blacklisted, reason = self._blacklist.check_number(number)
            if is_blacklisted:
                return True, reason
            else:
                print(">> Checking blocked patterns...")
                patternlist = self.config["CALLERID_PATTERNS"]["blocknames"]
                for key in patternlist.keys():
                    match = re.search(key, name, re.IGNORECASE)
                    if match:
                        reason = patternlist[key]
                        print(reason)
                        return True, reason

                patternlist = self.config["CALLERID_PATTERNS"]["blocknumbers"]
                for key in patternlist.keys():
                    match = re.search(key, number)
                    if match:
                        reason = patternlist[key]
                        print(reason)
                        return True, reason

                if self._blockservice is not None:
                    print(">> Checking block service...")
                    result = self._blockservice.lookup_number(number)
                    if result["spam"]:
                        reason = "{} with score {}".format(result["reason"], result["score"])
                        if self.config["DEBUG"]:
                            print(">>> {}".format(reason))
                        self.blacklist_caller(callerid, reason)
                        return True, reason

                print("Caller has been screened")
                return False, "Not found"

        finally:
            sys.stdout.flush()

    def whitelist_caller(self, callerid, reason):
        self._whitelist.add_caller(callerid, reason)

    def blacklist_caller(self, callerid, reason):
        self._blacklist.add_caller(callerid, reason)

    def __init__(self, db, config):
        self._db = db
        self.config = config
        if self.config["DEBUG"]:
            print("Initializing CallScreener")

        self._blacklist = Blacklist(db, config)
        self._whitelist = Whitelist(db, config)

        bs = config["BLOCK_SERVICE"].upper()
        if bs == "NOMOROBO":
            # Set blocking threshold to 1 to filter nuisance calls
            self._blockservice = NomoroboService(config["BLOCK_SERVICE_THRESHOLD"])
        elif bs == "SHOULDIANSWER":
            self._blockservice = ShouldIAnswer(config["BLOCK_SERVICE_THRESHOLD"])
        else:
            self._blockservice = None

        # Load number and name patterns into config vars
        try:
            with open(self.config["CALLERID_PATTERNS_FILE"], "r") as file:
                self.config["CALLERID_PATTERNS"] = yaml.safe_load(file)
        except FileNotFoundError:
            print("Callerid patterns file not found")
            # Load dummy patterns
            self.config["CALLERID_PATTERNS"] = {'blocknames': {}, 'blocknumbers': {},
                                                'permitnames': {}, 'permitnumbers': {}}
        except yaml.YAMLError as e:
            print("Error loading callerid patterns file")
            if hasattr(e, 'problem_mark'):
                mark = e.problem_mark
                print("Error parsing Yaml file at line {}, column {}.".format(mark.line + 1, mark.column + 1))
            sys.exit(1)

        if self.config["DEBUG"]:
            print("CallScreener initialized")
