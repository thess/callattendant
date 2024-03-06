#!/usr/bin/python
# -*- coding: UTF-8 -*-
#
# file: modem.py
#
# Copyright 2018-2020 Bruce Schubert <bruce@emxsys.com>
# Rewrite for Python3 and handling of DLE escapes
#   by: Ted Hess <thess@kitschensync.net>, June 2022
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# ==============================================================================
# This code was inspired by and contains code snippets from Pradeep Singh:
# https://iotbytes.wordpress.com/incoming-call-details-logger-with-raspberry-pi/
# https://github.com/pradeesi/Incoming_Call_Detail_Logger
# ==============================================================================

import atexit
import os
import re
import serial
import subprocess
import threading
import time
import wave

from datetime import datetime
from pprint import pprint

# ACSII codes
DLE_CODE = chr(16)      # Data Link Escape (DLE) code
ETX_CODE = chr(3)       # End Transmission (ETX) code
CR_CODE = chr(13)       # Carraige return
LF_CODE = chr(10)       # Line feed

# Supported modem product codes returned by ATI0
USR_5637_PRODUCT_CODE = '5601'
CONEXANT_PRODUCT_CODE = '56000'

#  Modem AT commands:
#  See http://support.usr.com/support/5637/5637-ug/ref_data.html
RESET = "ATZ"
RESET_PROFILE = "ATZ0"
GET_MODEM_PRODUCT_CODE = "ATI0"
GET_MODEM_SETTINGS = "AT&V"
GET_MODEM_FIRMWARE_ID = "ATI3"
GET_MODEM_PATCH_LEVEL_CONEXANT = "AT-PV"
DISABLE_ECHO_COMMANDS = "ATE0"
ENABLE_ECHO_COMMANDS = "ATE1"
ENABLE_FORMATTED_CID = "AT+VCID=1"
ENABLE_FORMATTED_CID_CONEXANT = "AT-SCID=1;+VCID=1;-STE=3"
ENABLE_VERBOSE_CODES = "ATV1"
DISABLE_SILENCE_DETECTION = "AT+VSD=128,0"
DISABLE_SILENCE_DETECTION_CONEXANT = "AT+VSD=0,0"
ENABLE_SILENCE_DETECTION_5_SECS = "AT+VSD=128,50"
ENABLE_SILENCE_DETECTION_5_SECS_CONEXANT = "AT+VSD=0,50"
ENABLE_SILENCE_DETECTION_10_SECS = "AT+VSD=128,100"
ENABLE_SILENCE_DETECTION_10_SECS_CONEXANT = "AT+VSD=0,100"
ENTER_VOICE_MODE = "AT+FCLASS=8"
ENTER_VOICE_RECIEVE_DATA_STATE = "AT+VRX"
ENTER_VOICE_TRANSMIT_DATA_STATE = "AT+VTX"
SEND_VOICE_TONE_BEEP = "AT+VTS=[900,900,120]"   # 1.2 second beep
GET_VOICE_COMPRESSION_SETTING = "AT+VSM?"
GET_VOICE_COMPRESSION_OPTIONS = "AT+VSM=?"
SET_VOICE_COMPRESSION = "AT+VSM=128,8000"             # USR 5637: 128 = 8-bit linear, 8.0 kHz
SET_VOICE_COMPRESSION_CONEXANT = "AT+VSM=1,8000,0,0"  # Zoom 3095:  1 = 8-bit unsigned pcm, 8.0 kHz
TELEPHONE_ANSWERING_DEVICE_OFF_HOOK = "AT+VLS=1"  # TAD (DCE) off-hook, connected to telco
TELEPHONE_ANSWERING_DEVICE_ON_HOOK = "AT+VLS=0"   # TAD (DCE) on-hook
GO_OFF_HOOK = "ATH1"
GO_ON_HOOK = "ATH0"
TERMINATE_CALL = "ATH"


# Modem DLE shielded codes - DCE to DTE modem data
DLE_BYTE_CODE = DLE_CODE.encode()

DCE_ANSWER_TONE = chr(97)          # <DLE>-a
DCE_BUSY_TONE = chr(98)            # <DLE>-b
DCE_FAX_CALLING_TONE = chr(99)     # <DLE>-c
DCE_DIAL_TONE = chr(100)           # <DLE>-d
DCE_DATA_CALLING_TONE = chr(101)   # <DLE>-e
DCE_LINE_REVERSAL = chr(108)       # <DLE>-l
DCE_PHONE_ON_HOOK = chr(104)       # <DLE>-h
DCE_PHONE_OFF_HOOK = chr(72)       # <DLE>-H
DCE_PHONE_OFF_HOOK2 = chr(80)      # <DLE>-P (Conexant)
DCE_PHONE_OFF_HOOK3 = chr(112)     # <DLE>-p (Conexant)
DCE_QUIET_DETECTED = chr(113)      # <DLE>-q (Conexant)
DCE_RING = chr(82)                 # <DLE>-R
DCE_SILENCE_DETECTED = chr(115)    # <DLE>-s
DCE_TX_BUFFER_UNDERRUN = chr(117)  # <DLE>-u
DCE_END_VOICE_DATA_TX = chr(3)     # <DLE><ETX>

# System DLE shielded codes (single DLE) - DTE to DCE commands (used by USR 5637 modem)
DTE_RAISE_VOLUME = (chr(16) + chr(117))           # <DLE>-u
DTE_LOWER_VOLUME = (chr(16) + chr(100))           # <DLE>-d
DTE_END_VOICE_DATA_RX = (chr(16) + chr(33))       # <DLE>-!
DTE_END_VOICE_DATA_RX2 = (chr(16) + chr(94))      # <DLE>-^ Zoom
DTE_END_VOICE_DATA_TX = (chr(16) + chr(3))        # <DLE><ETX>
DTE_CLEAR_TRANSMIT_BUFFER = (chr(16) + chr(24))   # <DLE><CAN>

# Empty line (just CR/LF)
CRLF = (chr(13) + chr(10))

TEST_DATA = [
    b"RING", b"DATE=0801", b"TIME=1801", b"NMBR=8055554567", b"NAME=Test1 - Permitted",
    b"RING", b"RING", b"RING", b"RING",
    b"RING", b"DATE=0802", b"TIME=1802", b"NMBR=5551234567", b"NAME=Test2 - Spammer",
    b"RING", b"DATE=0803", b"TIME=1803", b"NMBR=3605554567", b"NAME=Test3 - Blocked",
    b"RING", b"DATE=0804", b"TIME=1804", b"NMBR=8005554567", b"NAME=V123456789012345",
    b"RING", b"DATE = 0805", b"TIME = 1805", b"NMBR = 8055554567", b"NAME = Test5 - Permitted",
    b"RING", b"NMBR = 1234567890", b""
]


class Modem(object):
    """
    This class is responsible for serial communications between the
    Raspberry Pi and a voice/data/fax modem.
    """

    def __init__(self, config):
        """
        Constructs a modem object for serial communications.
            :param config:
                application configuration dict
        """
        print("Initializing Modem")
        self.config = config
        self.is_open = False
        self.model = None   # Model is set to USR, CONEXANT or UNKNOWN by _detect_modem

        # Thread synchronization objects
        self._stop_flag = False
        self._lock = threading.RLock()
        self._thread = None

        # Ring notifications
        status_indicators = self.config["STATUS_INDICATORS"]
        if status_indicators == "GPIO":
            from hardware.indicators import RingIndicator
            self.ring_indicator = RingIndicator(
                self.config.get("GPIO_LED_RING_PIN"),
                self.config.get("GPIO_LED_RING_BRIGHTNESS", 100))
        elif status_indicators == "NULL":
            from hardware.nullgpio import RingIndicator
            self.ring_indicator = RingIndicator()
        elif status_indicators == "MQTT":
            from hardware.mqttindicators import MQTTRingIndicator
            self.ring_indicator = MQTTRingIndicator()

        self.ring_event = threading.Event()

        # Initialize the serial port attached to the physical modem
        self._serial = serial.Serial()
        self.is_open = self._open_serial_port()
        # Automatically close the serial port at program termination
        atexit.register(self._close_serial_port)

        print("Modem {}".format("initialized" if self.is_open else "initialization failed!"))

    def start(self, handle_caller):
        """
        Starts the thread that processes incoming data.
            :param handle_caller:
                A callback function that takes a caller dict object.
            :return:
                True if modem was started successfully
        """
        if self.is_open:
            self._thread = threading.Thread(
                target=self._call_handler,
                kwargs={'handle_caller': handle_caller})
            self._thread.name = "modem_call_handler"
            self._thread.start()
            return True
        else:
            print("Error: Starting the modem call handling thread failed; the serial port is not open")
            return False

    def stop(self):
        """
        Stops the modem thread and releases hardware resources.
        """
        self._stop_flag = True
        # Wake up the thread if it is sleeping
        self._serial.cancel_read()
        if self._thread:
            self._thread.join()
        self.ring_indicator.close()
        self._close_serial_port()

    def _call_handler(self, handle_caller):
        """
        Thread function that processes the incoming modem data.
            :param handle_caller:
                A callback function that takes a caller dict object.
        """
        # Common constants
        RING = "RING"
        DATE = "DATE"
        TIME = "TIME"
        NAME = "NAME"
        NMBR = "NMBR"

        # Testing variables
        debugging = self.config["DEBUG"]
        testing = self.config["TESTING"]
        test_index = 0
        logfile = None

        # Handle incoming calls
        try:
            # This loop reads incoming data from the serial port and
            # posts the caller data to the handle_caller function
            call_record = {}
            while not self._stop_flag:
                modem_data = b''

                # Read from the modem
                with self._lock:
                    # Using a shorter timeout here (vs 3 secs) to improve performance
                    # with detecting partial caller ID scenarios
                    save_timeout = self._serial.timeout
                    self._serial.timeout = 0.5
                    # Wait/read a line of data from the serial port with the configured timeout.
                    # FYI: The verbose-form result codes are preceded and terminated by the
                    # sequence <CR><LF>. The numeric-form is also terminated by <CR> but it
                    # has no preceding sequence.
                    modem_data = self._serial.readline().decode("utf-8", "ignore").strip()
                    self._serial.timeout = save_timeout

                # Some telcos do not supply all the caller info fields.
                # If the modem timed out (empty modem data) or another RING occured,
                # then look for and handle a partial set of caller info.
                if (modem_data == '') or (RING in modem_data):
                    # NMBR is required for processing a partial CID
                    if call_record.get('NMBR'):
                        now = datetime.now()
                        if not call_record.get('DATE'):
                            call_record['DATE'] = now.strftime("%m%d")
                        if not call_record.get('TIME'):
                            call_record['TIME'] = now.strftime("%H%M")
                        if not call_record.get('NAME'):
                            call_record['NAME'] = "Unknown"
                    else:
                        # Othewise, throw away any partial data without a number
                        # that was received between RINGs/timeouts.
                        # Note: in UK and other regions that do not supply a NAME,
                        # you could set the default name here, for example:
                        #   call_record{"NAME": "Unknown"}
                        call_record = {}

                # Process the modem data
                if modem_data != '':
                    # Some debugging/dev tasks here
                    if debugging:
                        print(modem_data)
                        self._serial.flush()

                    # Process the modem data
                    if RING in modem_data:
                        self.ring()
                    elif DATE in modem_data:
                        items = modem_data.split('=')
                        call_record['DATE'] = items[1].strip()
                    elif TIME in modem_data:
                        items = modem_data.split('=')
                        call_record['TIME'] = items[1].strip()
                    elif NAME in modem_data:
                        items = modem_data.split('=')
                        call_record['NAME'] = items[1].strip()
                    elif NMBR in modem_data:
                        items = modem_data.split('=')
                        call_record['NMBR'] = items[1].strip()

                # Test for a complete set of caller ID data
                # https://stackoverflow.com/questions/1285911/how-do-i-check-that-multiple-keys-are-in-a-dict-in-a-single-pass
                if all(k in call_record for k in ("DATE", "TIME", "NAME", "NMBR")):
                    # Already handled first RING (don't count twice)
                    self.ring_event.clear()
                    # Queue caller for screening
                    print("> Queueing call {} for processing".format(call_record["NMBR"]))
                    handle_caller(call_record)
                    # Note: in UK and regions that do not supply a NAME,
                    # you could set the default name here, for example:
                    #   call_record{"NAME": "Unknown"}
                    call_record = {}

                # Yield to other threads
                time.sleep(0.0001)

        finally:
            print("Modem thread exiting")

    def pick_up(self):
        """
        Go "off hook". Called by the application object (callattendant.py)
        to set the lock and perform a batch of operations before hanging up.
        The hang_up() function must be called to release the lock.

        note:: hang_up() MUST be called by the same thread to release the lock
            :return:
                True if successful
        """
        print("> Going off hook...")
        self._serial.cancel_read()
        self._lock.acquire()
        if self.config["DEBUG"]:
            print(">>> Lock acquired in pick-up()")
        try:
            if not self._send(ENTER_VOICE_MODE):
                raise RuntimeError("Failed to put modem into voice mode.")

            if not self._send(DISABLE_SILENCE_DETECTION):
                raise RuntimeError("Failed to disable silence detection.")

            if not self._send(TELEPHONE_ANSWERING_DEVICE_OFF_HOOK):
                raise RuntimeError("Unable put modem into telephone answering device mode.")

        except Exception as e:
            pprint("Error in pick_up: {}".format(e))
            # Only release the lock if we failed to go off-hook
            self._lock.release()
            print(">>> Lock released in pick-up()")
            return False

        return True

    def hang_up(self):
        """
        Hang up on an active call, i.e., go "on hook". Called by the
        application object after finishing a batch of modem operations
        to terminate the call and release the lock aquired by pick_up().
        note:: Assumes pick-up() has been called previously to acquire
            the lock
            :return:
                True if successful
        """
        print("> Going on hook...")
        try:
            self._serial.cancel_read()

            # Prevent any pending data from corrupting the next call
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()

            if not self._send(GO_ON_HOOK):
                raise RuntimeError("Failed to hang up the call.")
            # ~ if not self._send(RESET):
                # ~ raise RuntimeError("Failed to reset the modem.")

        except Exception as e:
            print("**Error: hang_up() failed")
            pprint(e)
            return False

        finally:
            # Release the lock acquired by pick_up()
            self._lock.release()
            if self.config["DEBUG"]:
                print(">>> Lock released in hang-up()")

        return True

    def play_audio(self, audio_file_name):
        """
        Play the given audio file.
            :param audio_file_name:
                a wav file with 8-bit linear compression recored at 8.0 kHz sampling rate
            :return:
                True if successful
        """
        debugging = self.config["DEBUG"]
        if debugging:
            print("> Playing {}...".format(audio_file_name))

        return_data = None
        self._serial.cancel_read()
        with self._lock:

            # Setup modem for transmitting audio data
            if not self._send(ENTER_VOICE_MODE):
                print("* Error: Failed to put modem into voice mode.")
                return False, None
            if not self._send(SET_VOICE_COMPRESSION):
                print("* Error: Failed to set compression method and sampling rate specifications.")
                return False, None
            if not self._send(TELEPHONE_ANSWERING_DEVICE_OFF_HOOK):
                print("* Error: Unable put modem into telephone answering device mode.")
                return False, None

            # wait before we speak
            time.sleep(1.0)
            # Play Audio File
            with wave.open(audio_file_name, 'rb') as wavefile:
                chunk = 1024
                data = wavefile.readframes(chunk)
                if len(data) > 0:
                    if not self._send(ENTER_VOICE_TRANSMIT_DATA_STATE, "CONNECT"):
                        print("* Error: Unable put modem into voice data transmit state.")
                        return False, None
                # pump out message
                while data != b'':
                    self._serial.write(data)
                    data = wavefile.readframes(chunk)
                    # Check for DCE notifications
                    if self._serial.in_waiting > 1:
                        modem_data = self._serial.read(self._serial.in_waiting).decode("utf-8", "ignore").strip()
                        if debugging:
                            print(">> play_audio input: {}".format(
                                  "".join(map(lambda x: '<DLE>' if x == DLE_CODE else
                                                        '<ETX>' if x == ETX_CODE else x, modem_data))))
                        if modem_data != '':
                            if modem_data[0] == DLE_CODE:
                                if (modem_data[1] == DCE_PHONE_OFF_HOOK) or \
                                        (modem_data[1] == DCE_PHONE_OFF_HOOK2) or \
                                        (modem_data[1] == DCE_PHONE_OFF_HOOK3):
                                    print(">> Local phone off-hook - abort playback")
                                    return_data = 'off-hook'
                                    break
                                if modem_data[1] == DCE_TX_BUFFER_UNDERRUN:
                                    print(">> Underrun -- ignoring")
                                    continue
                                if modem_data[1] == '/':
                                    # Search for ~ and extract the digits
                                    if (modem_data.find('~') != -1):
                                        modem_data = modem_data.replace(DLE_CODE, "")
                                        digit_list = re.findall('/(.+?)~', modem_data)
                                        if len(digit_list) > 0:
                                            print(">> Terminate playback")
                                            # Return only the first digit found
                                            return_data = digit_list[0][0]
                                            break

                                print(">> DCE Notification: <DLE>{}".format(modem_data[1]))

                self._send(DTE_END_VOICE_DATA_TX)

        return True, return_data

    def record_audio(self, audio_file_name, detect_silence=True):
        """
        Records audio from the model to the given audio file.
            :param audio_file_name:
                the wav file to be created with the recorded audio;
                recorded with 8-bit linear compression at 8.0 kHz sampling rate
            :return:
                True if a message was saved.
        """
        if self.config["DEBUG"]:
            print("> Recording {}...".format(audio_file_name))

        self._serial.cancel_read()
        with self._lock:
            try:
                if not self._send(ENTER_VOICE_MODE):
                    raise RuntimeError("Failed to put modem into voice mode.")

                if not self._send(SET_VOICE_COMPRESSION):
                    raise RuntimeError("Failed to set compression method and sampling rate specifications.")

                if not self._send(DISABLE_SILENCE_DETECTION):
                    raise RuntimeError("Failed to disable silence detection.")

                if not self._send(TELEPHONE_ANSWERING_DEVICE_OFF_HOOK):
                    raise RuntimeError("Unable put modem (TAD) off hook.")

                if not self._send(SEND_VOICE_TONE_BEEP):
                    raise RuntimeError("Failed to play 1.2 second beep.")

                if not self._send(ENTER_VOICE_RECIEVE_DATA_STATE, "CONNECT"):
                    raise RuntimeError("Error: Unable put modem into voice receive mode.")

            except RuntimeError as error:
                print("Modem initialization error: ", error)
                return False

            # Record Audio File
            start_time = datetime.now()
            record_timeout = self.config["VOICE_MAIL_RECORD_TIME"]
            CHUNK = 1024
            audio_frames = 0
            # Define the range of amplitude values that are to be considered silence.
            # In the 8-bit audio data, silence is \0x7f or \0x80 (127.5 rounded up or down)
            threshold = 1
            min_silence = 127 - threshold
            max_silence = 128 + threshold
            silent_frame_count = 0
            success = True
            try:
                with wave.open(audio_file_name, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(1)
                    wf.setframerate(8000)
                    wf.setcomptype('NONE', 'Not compressed')

                    while True:
                        # Read audio data from the Modem
                        audio_data = self._serial.read(CHUNK)

                        # Scan the audio data for DLE codes from modem
                        idx = audio_data.find(DLE_BYTE_CODE)
                        if (idx != -1) and (idx < len(audio_data) - 1):
                            # Found a DLE code, check for specific escapes
                            escaped_code = chr(audio_data[idx + 1])
                            if escaped_code == DCE_END_VOICE_DATA_TX:
                                # <DLE><ETX> is in the stream
                                print(">> <DLE><ETX> Char Recieved... Stop recording.")
                                break
                            if (escaped_code == DCE_PHONE_OFF_HOOK) or \
                                    (escaped_code == DCE_PHONE_OFF_HOOK2) or \
                                    (escaped_code == DCE_PHONE_OFF_HOOK3):
                                # <DLE>H or <DLE>P is in the stream
                                print(">> Local phone off hook... Stop recording")
                                break
                            if escaped_code == DCE_BUSY_TONE:
                                print(">> Busy Tone... Stop recording.")
                                break
                            if escaped_code == DCE_DIAL_TONE:
                                print(">> Dial Tone... Stop recording.")
                                break
                            if escaped_code == '/':
                                # Search for ~ and extract the digits
                                idx2 = audio_data.find(b'~', idx + 2)
                                if idx2 != -1:
                                    digit_data = audio_data[idx + 2:idx2].decode().replace(DLE_CODE, '')
                                    print(">> Keypad data received: {}".format(digit_data))
                                    break

                        # Test for silence
                        if detect_silence:
                            if len(audio_data) == sum(1 for x in audio_data if min_silence <= x <= max_silence):
                                # Increment number of contiguous silent frames
                                silent_frame_count += 1
                            else:
                                silent_frame_count = 0
                            # At 8KHz sample rate, 5 secs is ~40K bytes
                            if silent_frame_count > 40:  # 40 frames is ~5 secs
                                # TODO: Consider trimming silent tail from audio data.
                                print(">> Silent frames detected... Stop recording.")
                                break

                        # Timeout
                        if ((datetime.now() - start_time).seconds) > record_timeout:
                            print(">> Stop recording: max time limit reached.")
                            break

                        # Add Audio Data to output file
                        wf.writeframes(audio_data)
                        audio_frames += 1

                    # Save the file if there is audio
                    if audio_frames > silent_frame_count:
                        print(">> Saving audio file.")
                    else:
                        print(">> Removing silent audio.")
                        wf.close()
                        os.remove(audio_file_name)
                        success = False

                print(">> Recording stopped after {} seconds.".format((datetime.now() - start_time).seconds))

            except Exception as e:
                print(">> Error in record_audio: ", e)
                success = False
            finally:
                # Clear input buffer before sending commands else its
                # contents may be interpreted as the cmd's return code
                self._serial.reset_input_buffer()

                # Send End of Recieve Data state by passing "<DLE>!"
                # USR-5637 note: The command returns <DLE><ETX>
                if not self._send(DTE_END_VOICE_DATA_RX, DLE_CODE + ETX_CODE):
                    print("* Error: Unable to signal end of data receive state")
                # OK indicates return to command mode
                retval, response = self._read_response("OK", 5)
                if not retval:
                    print("* Error: Unable to return to command mode")

        return success

    def wait_for_keypress(self, wait_time_secs=15):
        """
        Waits n seconds for a key-press.
            :params wait_time_secs:
                the number of seconds to wait for a keypress
            :return:
                success (bool), key-press value (str)
        """
        print("> Waiting for key-press...")

        debugging = self.config["DEBUG"]

        self._serial.cancel_read()
        with self._lock:
            try:
                # Initialize modem
                if not self._send(ENTER_VOICE_MODE):
                    raise RuntimeError("Failed to put modem into voice mode.")

                if not self._send(ENABLE_SILENCE_DETECTION_10_SECS):
                    raise RuntimeError("Failed to enable silence detection.")

                if not self._send(TELEPHONE_ANSWERING_DEVICE_OFF_HOOK):
                    raise RuntimeError("Unable put modem into Telephone Answering Device mode.")

                # Wait for keypress
                start_time = datetime.now()
                modem_data = ''
                while wait_time_secs > (datetime.now() - start_time).seconds:
                    # Read 1 byte from the Modem
                    modem_char = self._serial.read().decode("utf-8", "ignore")
                    if modem_char == '':
                        continue
                    modem_data += modem_char
                    if debugging and len(modem_data) > 1:
                        print(">> Keypress Data: {}".format(
                              "".join(map(lambda x: '<DLE>' if x == DLE_CODE else
                                                    '<ETX>' if x == ETX_CODE else x, modem_data))))

                    if ((DLE_CODE + DCE_PHONE_OFF_HOOK) in modem_data) or \
                            ((DLE_CODE + DCE_PHONE_OFF_HOOK2) in modem_data) or \
                            ((DLE_CODE + DCE_PHONE_OFF_HOOK3) in modem_data):
                        raise RuntimeError("Local phone off hook... Aborting.")

                    if (DLE_CODE + DCE_RING) in modem_data:
                        raise RuntimeError("Ring detected... Aborting.")

                    if (DLE_CODE + DCE_BUSY_TONE) in modem_data:
                        raise RuntimeError("Busy Tone... Aborting.")

                    if (DLE_CODE + DCE_SILENCE_DETECTED) in modem_data:
                        raise RuntimeError("Silence Detected... Aborting.")

                    if (DLE_CODE + DCE_END_VOICE_DATA_TX) in modem_data:
                        raise RuntimeError("<DLE><ETX> Recieved... Aborting.")

                    # Parse DTMF Digits, if found in the stream
                    if (DLE_CODE + '/') in modem_data:
                        # Search for ~ and extract the digits
                        if modem_data.find('~') != -1:
                            modem_data = modem_data.replace(DLE_CODE, "")
                            digit_list = re.findall('/(.+?)~', modem_data)
                            if len(digit_list) > 0:
                                # Return only the first digit found
                                return True, digit_list[0][0]
                            modem_data = ''
                        continue

                print("Timeout limit exceeded: {}".format(wait_time_secs))
                raise RuntimeError("Timeout - wait time limit reached.")

            except RuntimeError as e:
                print("Exiting wait_for_keypress({}): {}".format(wait_time_secs, e))

        return False, ''

    def ring(self):
        """
        Activate the ring indicator
        """
        # Notify other threads that a ring occurred
        self.ring_event.set()
        # Visual notification (LED)
        self.ring_indicator.ring()

    def _send(self, command, expected_response="OK", response_timeout=5):
        """
        Sends a command string (e.g., AT command) to the modem.
            :param command:
                the command string to send
            :param expected_response:
                the expected response to the command, e.g. "OK"
            :param response_timeout:
                number of seconds to wait for the command to respond
            :return:
                True: if the command response matches the expected_response;
        """
        success, result = self._send_and_read(command, expected_response, response_timeout)
        return success

    def _send_and_read(self, command, expected_response="OK", response_timeout=5):
        """
        Sends a command string (e.g., AT command) to the modem and reads the result
            :param command:
                the command string to send
            :param expected_response:
                the expected response to the command, e.g. "OK"
            :param response_timeout:
                number of seconds to wait for the command to respond
            :return:
                True: if the command response matches the expected_response;
                plus the result preceding the command response, if any.
        """
        with self._lock:
            try:
                if self.config["DEBUG"]:
                    print("_send_and_read('{}','{}',{})".format(command, expected_response, response_timeout))

                self._serial.write((command + '\r').encode())
                self._serial.flush()
                # Get the execution status plus any preceeding result(s) from the modem
                success, result = self._read_response(expected_response, response_timeout)
                return (success, result)
            except Exception as e:
                print("Error in _send_and_read('{}','{}',{}): {}".format(command, expected_response, response_timeout, e))
            return False, None

    def _read_response(self, expected_response, response_timeout_secs):
        """
        Handles the command response code from the modem.
        Called by _send() and operates within the _send method's lock context.
            :param expected_response:
                the expected response, e.g. "OK"
            :param response_timeout_secs:
                number of seconds to wait for the command to respond
            :return: (boolean, result)
                True if the response matches the expected_response, else False if
                an ERROR is returned or if it times out; result contains any line(s)
                preceeding the command response.
        """
        start_time = datetime.now()
        try:
            response = ''
            while True:
                modem_data = self._serial.readline().decode("utf-8", "ignore")
                if modem_data != '':
                    response += modem_data
                    if self.config["DEBUG"]:
                        pprint(modem_data)
                    if expected_response is None:
                        return (True, None)

                    elif expected_response in response:
                        return (True, response)

                    elif "ERROR" in response:
                        if self.config["DEBUG"]:
                            print(">>> _read_response returned ERROR")
                        return (False, response)

                if (datetime.now() - start_time).seconds > response_timeout_secs:
                    if self.config["DEBUG"]:
                        print(">>> _read_response('{}',{}) timed out".format(expected_response, response_timeout_secs))
                    return (False, response)

        except Exception as e:
            print("Error in _read_response('{}',{}): {}".format(expected_response, response_timeout_secs, e))
        return (False, None)

    def _open_serial_port(self):
        """
        Detects and opens the first serial port that is attached to a voice modem.
            :return:
                True if a modem was successfuly detected and initialized, else False
        """
        print("Opening serial port")
        if self.is_open:
            return True

        if self.config["MODEM_DEVICE"] != "":
            com_ports_list = self.config["MODEM_DEVICE"].split(",")
        else:
            # List all the Serial COM Ports on device
            proc = subprocess.Popen(['ls /dev/tty[A-Za-z]*'], shell=True, stdout=subprocess.PIPE)
            com_ports = proc.communicate()[0].decode("utf-8", "ignore")
            com_ports_list = com_ports.split('\n')

        # Find the right port associated with the Voice Modem
        success = True
        for com_port in com_ports_list:
            if 'tty' in com_port:
                # Try to open the COM Port and execute AT Command
                try:
                    # Initialize the serial port and attempt to open
                    self._init_serial_port(com_port)
                    self._serial.open()
                except Exception as e:
                    print("Warning: _open_serial_port failed: {}, {}".format(self._serial.port, e))
                    success = False
                else:
                    # Detect the modem model
                    if self._detect_modem():
                        print("Serial port opened on {}".format(self._serial.port))
                        # Exit the loop after preparing the modem for use
                        success = self._init_modem()
                        break
                    else:
                        if self.config["DEBUG"]:
                            print("Failed to detect a compatible modem on {}".format(self._serial.port))
                        if self._serial.is_open:
                            self._serial.close()
                        # Loop to next com port
        return success

    def _close_serial_port(self):
        """
        Closes the serial port attached to the modem.
        """
        try:
            if self._serial.is_open:
                print("-> Closing modem serial port")
                self._serial.close()
                self.is_open = False
        except Exception as e:
            print("Error: _close_serial_port failed: {}".format(e))

    def _init_serial_port(self, com_port):
        """
        Initializes the given serial port for communications with a modem.
            Called by open_serial_port.
            :param com_port:
                The OS com port
        """
        self._serial.port = com_port
        self._serial.baudrate = 57600                   # bps
        self._serial.bytesize = serial.EIGHTBITS        # number of bits per bytes
        self._serial.parity = serial.PARITY_NONE        # set parity check: no parity
        self._serial.stopbits = serial.STOPBITS_ONE     # number of stop bits
        self._serial.timeout = 3                        # timeout for read
        self._serial.writeTimeout = 3                   # timeout for write
        self._serial.xonxoff = False                    # disable software flow control
        self._serial.rtscts = False                     # disable hardware (RTS/CTS) flow control
        self._serial.dsrdtr = False                     # disable hardware (DSR/DTR) flow control

    def _detect_modem(self):
        """
        Auto-detects the existance of a modem on the serial port, and sets model property.
            :return: True if successful, else False
        """
        print("Looking for modem on {}".format(self._serial.port))

        global SET_VOICE_COMPRESSION, DISABLE_SILENCE_DETECTION, \
            ENABLE_SILENCE_DETECTION_5_SECS, ENABLE_SILENCE_DETECTION_10_SECS, \
            DTE_RAISE_VOLUME, DTE_LOWER_VOLUME, DTE_END_VOICE_DATA_TX, \
            DTE_END_VOICE_DATA_RX, DTE_CLEAR_TRANSMIT_BUFFER, \
            ENABLE_FORMATTED_CID

        # Test if connected to a modem using basic AT command.
        self._serial.reset_input_buffer()
        if not self._send("AT"):
            return False

        # Attempt to identify the modem
        (success, result) = self._send_and_read(GET_MODEM_PRODUCT_CODE)

        if success:
            # Query firmware ID
            self._send_and_read(GET_MODEM_FIRMWARE_ID)
            if USR_5637_PRODUCT_CODE in result:
                print("*** US Robotics modem detected ***")
                self.model = "USR"

            elif CONEXANT_PRODUCT_CODE in result:
                self.model = "CONEXANT"
                # Define the settings for the Zoom3905 where they differ from the USR5637
                SET_VOICE_COMPRESSION = SET_VOICE_COMPRESSION_CONEXANT
                DISABLE_SILENCE_DETECTION = DISABLE_SILENCE_DETECTION_CONEXANT
                ENABLE_SILENCE_DETECTION_5_SECS = ENABLE_SILENCE_DETECTION_5_SECS_CONEXANT
                ENABLE_SILENCE_DETECTION_10_SECS = ENABLE_SILENCE_DETECTION_10_SECS_CONEXANT
                ENABLE_FORMATTED_CID = ENABLE_FORMATTED_CID_CONEXANT
                # Query firmware patch level
                self._send_and_read(GET_MODEM_PATCH_LEVEL_CONEXANT)
                print("*** Conextant modem detected ***")
            else:
                print("******* Unknown modem detected **********")
                # We'll try to use the modem with the predefined USR AT commands if it supports VOICE mode.
                if self._send(ENTER_VOICE_MODE):
                    self.model = "UNKNOWN"
                    # Use the default settings (used by the USR 5637 modem)
                else:
                    print("Error: Failed detect a compatible modem")
                    self.modem = None
                    success = False

        return success

    def _init_modem(self):
        """
        Initializes/configures the modem device in preparation for call attendant tasks.
            :return:
                True if successful, otherwise False
        """
        if self.config["DEBUG"]:
            print("Initializing modem settings")
        try:
            if not self._send(RESET):
                print("Error: Unable reset to factory default")
            if self.config["OPTIONAL_MODEM_INIT"]:
                self._send(self.config["OPTIONAL_MODEM_INIT"])
            if not self._send(ENABLE_VERBOSE_CODES):
                print("Error: Unable set response in verbose form")
            if not self._send(DISABLE_ECHO_COMMANDS):
                print("Error: Failed to disable local echo mode")
            if not self._send(ENABLE_FORMATTED_CID):
                print("Error: Failed to enable formatted caller report.")

            # Save these settings to a profile
            if not self._send("AT&W0"):
                print("Error: Failed to store profile.")

            # Output the modem settings to the log
            self._send(GET_MODEM_SETTINGS)

        except Exception as e:
            print("Error: _init_modem failed: {}".format(e))
            return False
        return True
