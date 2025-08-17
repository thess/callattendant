#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  messenger.py
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

import os
import sys
import threading
import time
from messaging.message import Message
from screening.whitelist import Whitelist

import smtplib, ssl
from email.mime.audio import MIMEAudio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import socket

class VoiceMail:

    def __init__(self, db, config, modem):
        """
        Initialize the database tables for voice messages.
        """
        if config["DEBUG"]:
            print("Initializing VoiceMail")

        self.db = db
        self.config = config
        self.modem = modem

        # Create a message event shared with the Message class used to monitor changes
        self.message_event = threading.Event()
        self.config["MESSAGE_EVENT"] = self.message_event

        # Initialize the message indicators (LEDs)
        status_indicators = self.config["STATUS_INDICATORS"]
        if status_indicators == "GPIO":
            from hardware.indicators import MessageIndicator, MessageCountIndicator, \
                    GPIO_MESSAGE, GPIO_MESSAGE_COUNT_PINS, GPIO_MESSAGE_COUNT_KWARGS

            self.message_indicator = MessageIndicator(
                    self.config.get("GPIO_LED_MESSAGE_PIN", GPIO_MESSAGE),
                    self.config.get("GPIO_LED_MESSAGE_BRIGHTNESS", 100))
            pins = self.config.get("GPIO_LED_MESSAGE_COUNT_PINS", GPIO_MESSAGE_COUNT_PINS)
            kwargs = self.config.get("GPIO_LED_MESSAGE_COUNT_KWARGS", GPIO_MESSAGE_COUNT_KWARGS)
            self.message_count_indicator = MessageCountIndicator(*pins, **kwargs)
        elif status_indicators == "NULL":
            from hardware.nullgpio import MessageIndicator, MessageCountIndicator
            self.message_indicator = MessageIndicator()
            self.message_count_indicator = MessageCountIndicator()
        elif status_indicators == "MQTT":
            from hardware.mqttindicators import MQTTMessageIndicator, MQTTMessageCountIndicator
            self.message_indicator = MQTTMessageIndicator()
            self.message_count_indicator = MQTTMessageCountIndicator()

        # Create the Message object used to interface with the DB
        self.messages = Message(db, config)
        self.whitelist = Whitelist(db, config)

        # Start the thread that monitors the message events and updates the indicators
        self._stop_flag = False
        self._thread = threading.Thread(target=self._event_handler)
        self._thread.name = "voice_mail_event_handler"
        self._thread.start()

        # Pulse the indicator if an unplayed msg is waiting
        self.message_event.set()

        if self.config["DEBUG"]:
            print("VoiceMail initialized")

    def stop(self):
        """
        Stops the voice mail thread and releases hardware resources.
        """
        # Signal thread to stop and wait for it to finish
        self._stop_flag = True
        self.message_event.set()
        self._thread.join()
        # Release hardware resources
        self.message_indicator.close()
        self.message_count_indicator.close()

    def _event_handler(self):
        """
        Thread function that updates the message indicators upon a message event.
        """
        while True:
            # Get the number of unread messages
            if self.message_event.wait():
                if self.config["DEBUG"]:
                    print("Message Event triggered")
                if self._stop_flag:
                    break
                self.reset_message_indicator()
                self.message_event.clear()
                sys.stdout.flush()

    def voice_messaging_menu(self, call_no, caller):
        """
        Respond to the screening choices.
        """
        # Build some common paths
        voice_mail = self.config.get_namespace("VOICE_MAIL_")
        voice_mail_callback_file = voice_mail['callback_file']
        invalid_response_file = voice_mail['invalid_response_file']
        goodbye_file = voice_mail['goodbye_file']

        # Indicate the user is in the menu
        self.message_indicator.blink()

        tries = 0
        wait_secs = 8   # Candidate for configuration
        while tries < 3:
            success, digit = self.modem.wait_for_keypress(wait_secs)
            if not success:
                break
            print(">>Caller pressed: {}".format(digit))
            if digit == '1':
                self.record_message(call_no, caller, self.config["VOICE_MAIL_LEAVE_MESSAGE_FILE"])
                break
            elif digit == '0':
                # Save caller to whitelist
                self.whitelist.add_caller(caller, "Caller pressed 0")
                self.modem.play_audio(voice_mail_callback_file)
                self.modem.play_audio(goodbye_file)
                break
            elif digit == '#':
                self.modem.play_audio(goodbye_file)
                break
            else:
                # Try again--up to a limit
                self.modem.play_audio(invalid_response_file)
                tries += 1
        # Out of menu - update message indicator
        self.message_event.set()

    def record_message(self, call_no, caller, msg_file=None, detect_silence=True):
        """
        Records a message.
        """
        # Build the filename used for a potential message
        path = self.config["VOICE_MAIL_MESSAGE_FOLDER"]
        filepath = os.path.join(path, "{}_{}_{}_{}.wav".format(
            call_no,
            caller["NMBR"],
            caller["NAME"].replace('_', '-').replace('/', '-'),
            time.strftime("%m%d%y_%H%M")))

        # Play instructions to caller
        if msg_file:
            success, retval = self.modem.play_audio(msg_file)
            if not success or (retval in ('off-hook', 'hang-up')):
                return False, None

        # Show recording in progress
        self.message_indicator.turn_on()

        # Record the message
        retval = None
        if self.modem.record_audio(filepath, detect_silence):
            # Save to Message table (message.add will update the indicator)
            msg_no = self.messages.add(call_no, filepath)

            # Send an e-mail notification
            if self.config["EMAIL_ENABLE"]:
                self.__send_email(caller, filepath)

            # Return the messageID on success
            retval = msg_no

        return retval

    def __send_email(self, caller, filepath):
        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(self.config["EMAIL_SERVER"], self.config["EMAIL_PORT"], context=context) as server:
                server.login(self.config["EMAIL_SERVER_USERNAME"], self.config["EMAIL_SERVER_PASSWORD"])
                message = MIMEMultipart()
                message['From'] = self.config["EMAIL_FROM"]
                message['To'] = self.config["EMAIL_TO"]
                message['Subject'] = f'Voicemail message received from: {caller["NMBR"]}'
                message['Date'] = time.strftime("%a, %d %b %Y %T %z (%Z)")
                body = MIMEText(f'Caller {caller["NMBR"]}, {caller["NAME"]} left a message.\n' +
                                f'Listen to message at http://{socket.gethostname()}:{self.config["PORT"]}/messages\n')
                message.attach(body)
                if self.config["EMAIL_WAVE_ATTACHMENT"]:
                    with open(filepath, 'rb') as wavefile:
                        att = MIMEAudio(wavefile.read(), 'wave')
                        att.add_header('Content-Disposition', f'attachment;filename="{os.path.basename(filepath)}"')
                        message.attach(att)
                server.sendmail(self.config["EMAIL_FROM"], self.config["EMAIL_TO"], message.as_string())
                print("Email notification sent to {}".format(self.config["EMAIL_TO"]))
        except Exception as e:
            print("Error sending email: {}".format(e))

    def delete_message(self, msg_no):
        """
        Removes the message record and associated wav file.
        """
        # Remove  message and file (message.delete will update the indicator)
        return self.messages.delete(msg_no)

    def reset_message_indicator(self):
        unplayed_count = self.messages.get_unplayed_count()
        if self.config["DEBUG"]:
            print("Resetting Message Indicator to show {} unplayed messages".format(unplayed_count))
        if unplayed_count > 0:
            self.message_indicator.pulse()
            if self.config["STATUS_INDICATORS"] == "GPIO":
                if unplayed_count < 10:
                    self.message_count_indicator.display = unplayed_count
                    self.message_count_indicator.decimal_point = False
                else:
                    self.message_count_indicator.display = 9
                    self.message_count_indicator.decimal_point = True
            else:
                # Display actual count if not restricted by single digit
                self.message_count_indicator.display = unplayed_count
        else:
            self.message_indicator.turn_off()
            self.message_count_indicator.display = 0
            self.message_count_indicator.decimal_point = False
