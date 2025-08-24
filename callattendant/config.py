#!/usr/bin/env python
#
# file: config.py
#
# ==============================================================================
# This file is an elided version of the Flask project's config module:
# https://github.com/pallets/flask/blob/master/src/flask/config.py
# ==============================================================================

import errno
import os
import types

from shutil import copyfile
from tempfile import gettempdir
from werkzeug.utils import import_string

# This default configuration (used when a configuration file is not provided)
# will record messages from blocked (denied) callers, and will simply pass permitted
# and screened callers through to the home phone.
#
default_config = {
    "VERSION": '2.3.0',

    "DEBUG": False,
    "TESTING": False,

    "HOST": "0.0.0.0",
    "PORT": 5000,

    "MODEM_DEVICE": "",
    "OPTIONAL_MODEM_INIT": "",

    "ENABLE_CALLERID_VALIDATION": True,
    "DATABASE": "callattendant.db",

    "NOTIFICATIONS_FOLDER": "notifications",
    "SCREENING_MODE": ("whitelist", "blacklist"),

    "PHONE_DISPLAY_SEPARATOR": "-",
    "PHONE_DISPLAY_FORMAT": "###-###-####",

    "BLOCK_ENABLED": True,
    "BLOCK_SERVICE": "",
    "NOMOROBO_USERNAME": "",
    "NOMOROBO_PASSWORD": "",

    "BLOCK_SERVICE_THRESHOLD": 2,

    "CALLERID_PATTERNS_FILE": 'cid_patterns.yaml',

    "PERMIT_NEXT_CALL_FLAG": 'permitnextcall.flag',

    "BLOCKED_ACTIONS": ("answer", "greeting", "voice_mail"),
    "BLOCKED_GREETING_FILE": "blocked_greeting.wav",
    "BLOCKED_RINGS_BEFORE_ANSWER": 0,

    "SCREENED_ACTIONS": ("answer", "greeting", "record_message"),
    "SCREENED_GREETING_FILE": "screener_greeting.wav",
    "SCREENED_RINGS_BEFORE_ANSWER": 0,

    "PERMITTED_ACTIONS": ("ignore",),
    "PERMITTED_GREETING_FILE": "general_greeting.wav",
    "PERMITTED_RINGS_BEFORE_ANSWER": 0,

    "VOICE_MAIL_GOODBYE_FILE": "goodbye.wav",
    "VOICE_MAIL_INVALID_RESPONSE_FILE": "invalid_response.wav",
    "VOICE_MAIL_LEAVE_MESSAGE_FILE": "please_leave_message.wav",
    "VOICE_MAIL_CALLBACK_FILE": "thankyou_callback.wav",
    "VOICE_MAIL_MESSAGE_FOLDER": "messages",
    "VOICE_MAIL_RECORD_TIME": 120,

    "EMAIL_SERVER": "SMTP server",
    "EMAIL_PORT": 465,
    "EMAIL_SERVER_USERNAME": 'user name to log into the SMTP server',
    "EMAIL_SERVER_PASSWORD": 'password to log into the SMTP server',
    "EMAIL_FROM": 'e-mail address to appear in the "From:" header',
    "EMAIL_TO": 'e-mail address to send the voicemail notification to',
    "EMAIL_WAVE_ATTACHMENT": False,

    "STATUS_INDICATORS": "NULL",

    "GPIO_LED_RING_PIN": 14,
    "GPIO_LED_RING_BRIGHTNESS": 100,
    "GPIO_LED_APPROVED_PIN": 15,
    "GPIO_LED_APPROVED_BRIGHTNESS": 100,
    "GPIO_LED_BLOCKED_PIN": 17,
    "GPIO_LED_BLOCKED_BRIGHTNESS": 100,
    "GPIO_LED_MESSAGE_PIN": 4,
    "GPIO_LED_MESSAGE_BRIGHTNESS": 100,
    "GPIO_LED_MESSAGE_COUNT_PINS": (8, 7, 27, 23, 10, 11, 9, 18),
    "GPIO_LED_MESSAGE_COUNT_KWARGS": {"active_high": True},

    "MQTT_BROKER": "localhost",
    "MQTT_PORT": 1883,
    "MQTT_TOPIC_PREFIX": "callattendant",
    "MQTT_USERNAME": None,
    "MQTT_PASSWORD": None,
    "MQTT_TIME_FORMAT": "UNIX",
    "MQTT_CALLERID_FORMAT": "RAW",
    "MQTT_INDICATOR_TYPE": "STATE",
}

CID_PATTERNS_DEFAULT_STRING = b"blocknames: {}\nblocknumbers: {}\n" \
                              b"permitnames: {}\npermitnumbers: {}\n"

class ConfigAttribute:
    """
    Makes an attribute forward to the config
    """

    def __init__(self, name, get_converter=None):
        self.__name__ = name
        self.get_converter = get_converter

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        rv = obj.config[self.__name__]
        if self.get_converter is not None:
            rv = self.get_converter(rv)
        return rv

    def __set__(self, obj, value):
        obj.config[self.__name__] = value


class Config(dict):
    """
    Config objects works exactly like a dict but provides ways to fill it
    from files or special dictionaries. You can fill the config from a
    config file, e.g., app.config.from_pyfile('yourconfig.cfg')
    Only uppercase keys are added to the config.  This makes it possible to use
    lowercase values in the config file for temporary values that are not added
    to the config or to define the config keys in the same file that implements
    the application.
    """

    def __init__(self, root_path=None, data_path=None, defaults=None):
        """
        Constructor.
            :param root_path:
                Path to the top-level package.
                If None, will use the path to this file, assumed to be in the top package
            :param data_path:
                Path to the data folder.
                The application database and message files are stored here.
                If None, will use the tmp folder - used in unit tests
            :param defaults:
                The default configuration values
        """
        dict.__init__(self, defaults or default_config)
        if root_path:
            self.root_path = root_path
        else:
            # This file must be in the top-level package
            self.root_path = os.path.dirname(os.path.realpath(__file__))
        if data_path:
            self.data_path = data_path
        else:
            # Use the tmp folder
            self.data_path = gettempdir()
        self["ROOT_PATH"] = self.root_path
        self["DATA_PATH"] = self.data_path

    def default_notification(self, wav_name):
        """
        Checks for default notification file and optionally copies from installed source.
            :param name:
                The message name (wave file)
            :return:
                True if file OK, else False
        """
        filepath = self[wav_name]
        if not os.path.exists(filepath):
            # Copy the default notification file to the notifications folder from install resources
            print("* {} not found: {}".format(wav_name, filepath))
            print("**  Copying default file to {}".format(filepath))
            try:
                copyfile(os.path.join(self.root_path, "resources", default_config[wav_name]), filepath)
            except Exception as e:
                print("* Could not copy default {}: {}".format(wav_name, e))
                return False
        return True

    def normalize_paths(self):
        """
        Normalizes the file based setting will absolute paths built from the
        root_path and data_path values passed in the contstructor.
        """
        # rootpath = self.root_path
        datapath = self.data_path
        if not datapath:
            return

        self["DB_FILE"] = os.path.normpath(os.path.join(datapath, self["DATABASE"]))

        wavpath = os.path.join(datapath, self["NOTIFICATIONS_FOLDER"])
        self["NOTIFICATIONS_FOLDER"] = os.path.normpath(wavpath)
        self["BLOCKED_GREETING_FILE"] = os.path.normpath(os.path.join(wavpath, self["BLOCKED_GREETING_FILE"]))
        self["SCREENED_GREETING_FILE"] = os.path.normpath(os.path.join(wavpath, self["SCREENED_GREETING_FILE"]))
        self["PERMITTED_GREETING_FILE"] = os.path.normpath(os.path.join(wavpath, self["PERMITTED_GREETING_FILE"]))

        self["VOICE_MAIL_GOODBYE_FILE"] = os.path.normpath(os.path.join(wavpath, self["VOICE_MAIL_GOODBYE_FILE"]))
        self["VOICE_MAIL_LEAVE_MESSAGE_FILE"] = os.path.normpath(os.path.join(wavpath, self["VOICE_MAIL_LEAVE_MESSAGE_FILE"]))
        self["VOICE_MAIL_INVALID_RESPONSE_FILE"] = os.path.normpath(os.path.join(wavpath, self["VOICE_MAIL_INVALID_RESPONSE_FILE"]))
        self["VOICE_MAIL_CALLBACK_FILE"] = os.path.normpath(os.path.join(wavpath, self["VOICE_MAIL_CALLBACK_FILE"]))

        self["CALLERID_PATTERNS_FILE"] = os.path.normpath(os.path.join(datapath, self["CALLERID_PATTERNS_FILE"]))

        self["PERMIT_NEXT_CALL_FLAG"] = os.path.normpath(os.path.join(datapath, self["PERMIT_NEXT_CALL_FLAG"]))

        self["VOICE_MAIL_MESSAGE_FOLDER"] = os.path.normpath(os.path.join(datapath, self["VOICE_MAIL_MESSAGE_FOLDER"]))

    def validate(self):
        """
        Validates the settings.
            :return:
                True if the settings are permissible.
        """
        success = True

        if not isinstance(self["DEBUG"], bool):
            print("* DEBUG should be a bool: {}".format(type(self["DEBUG"])))
            success = False
        if not isinstance(self["TESTING"], bool):
            print("* TESTING should be bool: {}".format(type(self["TESTING"])))
            success = False
        if not isinstance(self["BLOCK_ENABLED"], bool):
            print("* BLOCK_ENABLED should be a bool: {}".format(type(self["BLOCK_ENABLED"])))
            success = False
        if self["BLOCK_SERVICE"] not in ("", "NOMOROBO", "SHOULDIANSWER"):
            print("* BLOCK_SERVICE is invalid: {}".format(self["BLOCK_SERVICE"]))
            success = False
        if self["BLOCK_SERVICE"] == "NOMOROBO":
            if "NOMOROBO_USERNAME" not in self or len(self["NOMOROBO_USERNAME"]) == 0:
                print("* NOMOROBO_USERNAME is required for NOMOROBO BLOCK_SERVICE")
                success = False
            if "NOMOROBO_PASSWORD" not in self or len(self["NOMOROBO_PASSWORD"]) == 0:
                print("* NOMOROBO_PASSWORD is required for NOMOROBO BLOCK_SERVICE")
                success = False
        if (not isinstance(self["BLOCK_SERVICE_THRESHOLD"], int) or
                (self["BLOCK_SERVICE_THRESHOLD"] != 1 and self["BLOCK_SERVICE_THRESHOLD"] != 2)):
            print("* BLOCK_SERVICE_THRESHOLD should be 1 or 2: {}".format(self["BLOCK_SERVICE_THRESHOLD"]))
            success = False

        for mode in self["SCREENING_MODE"]:
            if mode not in ("whitelist", "blacklist"):
                print("* SCREENING_MODE option is invalid: {}".format(mode))
                success = False

        if not self._validate_actions("BLOCKED_ACTIONS"):
            success = False
        if not self._validate_actions("SCREENED_ACTIONS"):
            success = False
        if not self._validate_actions("PERMITTED_ACTIONS"):
            success = False

        if self["STATUS_INDICATORS"] not in ("NULL", "GPIO", "MQTT"):
            print("* STATUS_INDICATORS is invalid: {}".format(self["STATUS_INDICATORS"]))
            success = False

        if self["STATUS_INDICATORS"] == "MQTT":
            if self["MQTT_CALLERID_FORMAT"] not in ("RAW", "DISPLAY"):
                print("* MQTT_CALLERID_FORMAT is invalid: {}".format(self["MQTT_CALLERID_FORMAT"]))
                success = False
            if self["MQTT_TIME_FORMAT"] not in ("UNIX", "ISO"):
                print("* MQTT_TIME_FORMAT is invalid: {}".format(self["MQTT_TIME_FORMAT"]))
                success = False
            if self["MQTT_INDICATOR_TYPE"] not in ("STATE", "EVENT"):
                print("* MQTT_INDICATOR_TYPE is invalid: {}".format(self["MQTT_INDICATOR_TYPE"]))
                success = False

        if not isinstance(self["BLOCKED_RINGS_BEFORE_ANSWER"], int):
            print("* BLOCKED_RINGS_BEFORE_ANSWER should be an integer: {}".format(type(self["BLOCKED_RINGS_BEFORE_ANSWER"])))
            success = False
        if not isinstance(self["SCREENED_RINGS_BEFORE_ANSWER"], int):
            print("* SCREENED_RINGS_BEFORE_ANSWER should be an integer: {}".format(type(self["SCREENED_RINGS_BEFORE_ANSWER"])))
            success = False
        if not isinstance(self["PERMITTED_RINGS_BEFORE_ANSWER"], int):
            print("* PERMITTED_RINGS_BEFORE_ANSWER should be an integer: {}".format(type(self["PERMITTED_RINGS_BEFORE_ANSWER"])))
            success = False

        filepath = self["CALLERID_PATTERNS_FILE"]
        if not os.path.exists(filepath):
            print("* CALLERID_PATTERNS_FILE does not exist: {}".format(filepath))
            print("**  Creating default empty file")
            try:
                with open(filepath, 'wb') as cidf:
                    cidf.write(CID_PATTERNS_DEFAULT_STRING)
            except Exception as e:
                print("* Could not create default CALLERID_PATTERNS_FILE: {}".format(e))
                success = False

        # Check for default notification files and copy from installed resources if not found
        if not self.default_notification("BLOCKED_GREETING_FILE"):
            success = False
        if not self.default_notification("SCREENED_GREETING_FILE"):
            success = False
        if not self.default_notification("PERMITTED_GREETING_FILE"):
            success = False
        if not self.default_notification("VOICE_MAIL_GOODBYE_FILE"):
            success = False
        if not self.default_notification("VOICE_MAIL_LEAVE_MESSAGE_FILE"):
            success = False
        if not self.default_notification("VOICE_MAIL_INVALID_RESPONSE_FILE"):
            success = False
        if not self.default_notification("VOICE_MAIL_CALLBACK_FILE"):
            success = False

        filepath = self["VOICE_MAIL_MESSAGE_FOLDER"]
        if not os.path.exists(filepath):
            print("* VOICE_MAIL_MESSAGE_FOLDER not found: {}".format(filepath))
            success = False

        # Warnings
        if not self["PHONE_DISPLAY_SEPARATOR"] in self["PHONE_DISPLAY_FORMAT"]:
            print("* WARNING: PHONE_DISPLAY_SEPARATOR not used in PHONE_DISPLAY_FORMAT: '{}'".format(self["PHONE_DISPLAY_SEPARATOR"]))

        return success

    def _validate_actions(self, key):
        """
        :param key:
            String: "BLOCKED_ACTIONS", "SCREENED_ACTIONS" or "PERMITTED_ACTIONS"
        """
        if not isinstance(self[key], tuple):
            print("* {} must be a tuple, not {}".format(key, type(self[key])))
            return False

        for action in self[key]:
            if action not in ("answer", "ignore", "greeting", "record_message", "voice_mail"):
                print("* {} option is invalid: {}".format(key, action))
                return False

        if not any(a in self[key] for a in ("answer", "ignore")):
            print("* {} must include either 'answer' or 'ignore'".format(key))
            return False

        if all(a in self[key] for a in ("answer", "ignore")):
            print("* {} cannot include both 'answer' and 'ignore'".format(key))
            return False

        if all(a in self[key] for a in ("record_message", "voice_mail")):
            print("* {} cannot include both 'record_message' and 'voice_mail'".format(key))
            return False

        # WARNINGS: they print only; they do not fail validation.
        if "ignore" in self[key]:
            if any(a in self[key] for a in ("greeting", "record_message", "voice_mail")):
                print("* WARNING: {} contains actions in addition to 'ignore'. They will not be used.".format(key))

        return True

    def pretty_print(self):
        """
        Pretty print the given configuration dict object.
        """
        print("[Configuration]")
        keys = sorted(self.keys())
        for key in keys:
            # Hide sensitive values
            if (key == "EMAIL_SERVER_PASSWORD") | (key == "MQTT_PASSWORD") | (key == "NOMOROBO_PASSWORD"):
                print("  {} = {}".format(key, "********"))
            else:
                print("  {} = {}".format(key, self[key]))

    def from_pyfile(self, filename, silent=False):
        """Updates the values in the config from a Python file.
            :param filename:
                The filename of the config.  This can either be an
                absolute filename or a filename relative to the data path.
            :param silent:
                set to ``True`` if you want silent failure for missing files.
        """
        filename = os.path.join(self.data_path, filename)
        d = types.ModuleType("config")
        d.__file__ = filename
        try:
            with open(filename, mode="rb") as config_file:
                exec(compile(config_file.read(), filename, "exec"), d.__dict__)
        except OSError as e:
            if silent and e.errno in (errno.ENOENT, errno.EISDIR, errno.ENOTDIR):
                return False
            e.strerror = "Unable to load configuration file ({})".format(e.strerror)
            raise
        self.from_object(d)
        return True

    def from_object(self, obj):
        """
        Updates the values from the given object.  An object can be of one
        of the following two types:
        -   a string: in this case the object with that name will be imported
        -   an actual object reference: that object is used directly
        Objects are usually either modules or classes. :meth:`from_object`
        loads only the uppercase attributes of the module/class. A ``dict``
        object will not work with :meth:`from_object` because the keys of a
        ``dict`` are not attributes of the ``dict`` class.
        Example of module-based configuration::
            app.config.from_object('yourapplication.default_config')
            from yourapplication import default_config
            app.config.from_object(default_config)
        Nothing is done to the object before loading. If the object is a
        class and has ``@property`` attributes, it needs to be
        instantiated before being passed to this method.
        You should not use this function to load the actual configuration but
        rather configuration defaults.  The actual config should be loaded
        with :meth:`from_pyfile` and ideally from a location not within the
        package because the package might be installed system wide.
        See :ref:`config-dev-prod` for an example of class-based configuration
        using :meth:`from_object`.
            :param obj:
                an import name or object
        """
        if isinstance(obj, str):
            obj = import_string(obj)
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)

    def get_namespace(self, namespace, lowercase=True, trim_namespace=True):
        """
        Returns a dictionary containing a subset of configuration options
        that match the specified namespace/prefix. Example usage::
            app.config['IMAGE_STORE_TYPE'] = 'fs'
            app.config['IMAGE_STORE_PATH'] = '/var/app/images'
            app.config['IMAGE_STORE_BASE_URL'] = 'http://img.website.com'
            image_store_config = app.config.get_namespace('IMAGE_STORE_')
        The resulting dictionary `image_store_config` would look like::
            {
                'type': 'fs',
                'path': '/var/app/images',
                'base_url': 'http://img.website.com'
            }
        This is often useful when configuration options map directly to
        keyword arguments in functions or class constructors.

        :param namespace:
            a configuration namespace
        :param lowercase:
            a flag indicating if the keys of the resulting
            dictionary should be lowercase
        :param trim_namespace:
            a flag indicating if the keys of the resulting
            dictionary should not include the namespace
        """
        rv = {}
        for k, v in self.items():
            if not k.startswith(namespace):
                continue
            if trim_namespace:
                key = k[len(namespace):]
            else:
                key = k
            if lowercase:
                key = key.lower()
            rv[key] = v
        return rv

    def __repr__(self):
        # return f"<{type(self).__name__} {dict.__repr__(self)}>"
        return '<{} {}>'.format(type(self).__name__, dict.__repr__(self))
