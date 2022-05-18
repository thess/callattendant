#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
#  indicators.py
#
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

class DummyLED(object):
    def turn_on(self):
        pass

    def blink(self, max_times=10):
        # blink in a separate thread
        print("Blinking: {} times".format(max_times))

    def pulse(self, max_times=10):
        print("Pulsing: {} times".format(max_times))

    def turn_off(self):
        pass

    def close(self):
        pass

    def __init__(self):
        pass

class ApprovedIndicator(DummyLED):
    """
    The approved indicator activated when a call from a permitted number is received.
    """
    def __init__(self):
        super().__init__()


class BlockedIndicator(DummyLED):
    """
    The blocked indicator activated when a call from a blocked number is received.
    """
    def __init__(self):
        super().__init__()

class RingIndicator(DummyLED):
    """
    The ring indicator, activated when an incoming call is being received.
    """
    def __init__(self):
        super().__init__()

    def ring(self):
        self.blink()
        print("{RING LED BLINKING}")

class MessageIndicator(DummyLED):
    """
    The message indicator activated when the voice messaging features are used.
    """

    def __init__(self):
        super().__init__()

    def turn_off(self):
        print("{MSG LED OFF}")
        super().turn_off()

    def turn_on(self):
        print("{MSG LED ON}")
        super().turn_on()

    def blink(self):
        print("{MSG LED Blinking}")
        super().blink(max_times=None)   # None = forever

    def pulse(self):
        print("{MSG LED Pulsing}")
        super().pulse(max_times=None)   # None = forever

class MessageCountIndicator(object):
    """
    The message count indicator displays the number of unplayed messages in the system.
    """
    def __init__(self):
        pass

    def display(self, char):
        self.val = char
        print("Display: {}".format(char))

    @property
    def decimal_point(self):
        return self.dp

    @decimal_point.setter
    def decimal_point(self, value):
        self.dp = value

    def close(self):
        pass
