#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
#  mqttindicators.py
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


import time
import threading

import paho.mqtt.client as mqtt

# Client singleton
mqtt_client = None

class MQTTIndicatorClient(object):
    """
    Class for controlling the MQTT client.
    """
    def __init__(self, host, port=1883, topic_prefix='callattendant', username=None, password=None):
        global mqtt_client
        if mqtt_client is None:
            # No need to re-init
            mqtt_client = self

            self.server = host
            self.port = port
            self.username = username
            self.password = password
            # Create client root name
            self.topic_prefix = topic_prefix + "/"

    def publish(self, topic, message):
        """
        Publish a message to a topic.
        """
        client = mqtt.Client()
        if self.username is not None:
            client.username_pw_set(self.username, self.password)
        client.connect(self.server, self.port)
        ts = time.strftime(" (%Y-%m-%d %H:%M:%S)", time.localtime())
        client.publish(self.topic_prefix + topic, str(message) + ts, retain=True)
        client.disconnect()


class MQTTIndicator(object):
    """
    Class for controlling an MQTT LED topic
    """
    def __init__(self, topic, init_state='OFF'):
        self.topic = topic
        if mqtt_client is None:
            raise Exception("MQTT client not initialized")
        self.mqtt_client = mqtt_client
        if init_state is not None:
            self.mqtt_client.publish(self.topic, init_state)
        self.blink_timer = None

    def turn_on(self):
        print("{} LED turned on".format(self.topic))
        if self.blink_timer is not None:
            self.blink_timer.cancel()
            self.blink_timer = None
        self.mqtt_client.publish(self.topic, "ON")

    def turn_off(self):
        print("{} LED turned off".format(self.topic))
        if self.blink_timer is not None:
            self.blink_timer.cancel()
            self.blink_timer = None
        self.mqtt_client.publish(self.topic, "OFF")

    def blink(self, max_times=10):
        # Just say we're blinking
        if max_times is None:
            print("{} LED blinking".format(self.topic))
            max_times = 0
        else:
            print("{} LED blinking: {} times".format(self.topic, max_times))
        self.mqtt_client.publish(self.topic, "BLINK {}".format(max_times))
        if max_times > 0 and self.blink_timer is None:
            self.blink_timer = threading.Timer(0.7 * max_times, self.turn_off)
            self.blink_timer.start()

    def pulse(self, max_times=10):
        if max_times is None:
            print("{} LED pulsing".format(self.topic))
            max_times = 0
        else:
            print("{} LED pulsing: {} times".format(self.topic, max_times))
        self.mqtt_client.publish(self.topic, "PULSE {}".format(max_times))
        if max_times > 0 and self.blink_timer is None:
            self.blink_timer = threading.Timer(2.0 * max_times, self.turn_off)
            self.blink_timer.start()

    def close(self):
        if self.blink_timer is not None:
            self.blink_timer.cancel()
            self.blink_timer = None
        self.mqtt_client.publish(self.topic, "CLOSED")

class MQTTRingIndicator(MQTTIndicator):
    """
    Class for controlling the MQTT ring indicator.
    """
    def __init__(self):
        super().__init__("RING")

    def ring(self):
        super().blink()


class MQTTMessageIndicator(MQTTIndicator):
    """
    The message indicator activated when the voice messaging features are used.
    """
    def __init__(self):
        super().__init__('Messages', None)

    def blink(self):
        super().blink(max_times=None)   # None = forever

    def pulse(self):
        super().pulse(max_times=None)   # None = forever


class MQTTMessageCountIndicator(MQTTIndicator):
    """
    The message count indicator displays the number of unplayed messages in the system.
    """
    def __init__(self):
        super().__init__('MessageCount', None)
        self.dp = False
        self.count = 0

    @property
    def display(self):
        return self.count

    @display.setter
    def display(self, value):
        self.count = value
        print("{} indicator set to {}".format(self.topic, self.count))
        self.mqtt_client.publish(self.topic, value)

    @property
    def decimal_point(self):
        return self.dp

    @decimal_point.setter
    def decimal_point(self, value):
        self.dp = value
