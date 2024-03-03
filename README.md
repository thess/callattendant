# Call Attendant

The Call Attendant (__callattendant__) is an auto attendant with an integrated call blocker and 
voice messaging system running on a Raspberry Pi or equivalent. It stops annoying robocalls and spammers from interrupting your life. Let the Call Attendant intercept and block robocallers and telemarketers.

The __callattendant__ provides for configurable phone number formats, and support for regular-expressions to specify blocked and permitted names and numbers in addtion to flexible and editable blocked-number and permitted-number lists.

_If you're at all interested in this project, please provide some feedback by giving it a
[star](https://github.com/thess/callattendant/stargazers), get involved
by filing [issues](https://github.com/thess/callattendant/issues) and/or submitting 
[pull requests](https://github.com/thess/callattendant/pulls).
Thanks!_

#### Useful Links from Original Repo

- [Legacy Web Page](https://emxsys.github.io/callattendant/)
- [Legacy Wiki](https://github.com/emxsys/callattendant/wiki)

#### Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)

### Project History

The **callattendant** project was developed and excellent documentation produced by Bruce Schubert as [emxsys](https://github.com/emxsys). This fork is based on the merging of the orginal base and the features of a couple of other forks. Most notably [galacticstudios](https://github.com/galacticstudios)/**[callattendant](https://github.com/galacticstudios/callattendant)** for their contributions:

* Ability to store and edit regular-expression lists for blocked and permitted names and numbers.
* Option to send email notification of messages including optionally attaching the .wav file.
* Addition of "Permit Next Call" button to enable/disable automatically allowing the next incoming call or handle it normally (screened, blocked, etc.)

#### New and/or updated in this fork

*  CallerID patterns are now in a single file (YAML).
*  Status indicators can be GPIO, MQTT or NULL (for none).
*  Works with both USR and Conexant based modems.
*  Automatic whitelist for caller pressing '0' when being screened.
*  Add import and export functions for permit and block lists.
*  eMail and MQTT config added to __app.cfg__.
*  Notifications folder location added to __app.cfg__.
*  Upgrade to Python3 strings vs. bytes in modem handling.
*  Better detection of modem notifications and keypad handling.
*  Remove unnecessary threading and events.


## Overview

The Call Attendant (__callattendant__) is a python-based, automated call attendant that runs on any system supporting Python 3, a network interface and a USB fax/voice modem attached. Some minimum hardware requirements and tested modems are listed below.

#### How it works

The system is connected to your home phone system in parallel with your phone
handset(s). When an incoming call is received, the call goes to both your phone and the
__callattendant__. During the period of the first ring the __callattendant__ analyzes the caller ID,
and based on your configuration, determines if the call should be blocked or allowed. Blocked calls
can be simply hung up on (optional message), or routed to the voice message system. Calls that are allowed will simply ring your home phone like normal. Calls can be sent to the integrated voice mail system if you choose. The __callattendant__'s filtering mechanisms include an online lookup service, a permitted number list, a blocked number list and pattern matching on the caller's number and/or name.

#### Features include:

- A call blocker that intercepts robocallers and blocked numbers at or before the first ring
- Permitted numbers pass straight through to the local phone system for normal call ringing and answering
- [Optional] Visual indicators to show whether the incoming call is from a permitted, blocked, or unknown number
- Call details, permitted numbers, and blocked numbers are available in a web-based user interface
- Calls can be handled by a voice messaging system that optioanlly requires human interaction,
  e.g, "Press 1 to leave a message"

You can review call history, voice messages, permitted and blocked numbers, and performing caller
management through the Call Attendant's web interface. Here is an example of the home page with metrics and a convienient list of recent calls. For a complete description see the
[User Guide](https://github.com/thess/callattendant/wiki/User-Guide).

##### _Screenshots of the home page as seen on an IPad Pro and a Pixel 2 phone_

![Dashboard-Responsive](https://github.com/thess/callattendant/blob/fmsentry/docs/dashboard-responsive.png)

### Documentation

The project wiki on GitHub contains the documentation for the Call Attendant:

- See the [Wiki Home](https://github.com/thess/callattendant/wiki/Home) for complete
  installation, configuration, and operation instructions.
- See the [User Guide](https://github.com/thess/callattendant/wiki/User-Guide) section for the
  web interface instructions.
- The [Developer Guide](https://github.com/thess/callattendant/wiki/Developer-Guide) section
  describes the software architecture and software development plan, and shows you how to setup
  your software development environment.
- The [Advanced](https://github.com/thess/callattendant/wiki/Advanced) section addresses more
  complex setups and situations. For instance, _Running as a Service_.

### Hardware Requirements

The __callattendant__ uses the following hardware:

- Computer system cabable of running Python3.
- Network access for software installation and optional call screener service.
- USB port for external modem.
- A 56K V.92 Data + Fax modem compatible with the **U.S. Robotics USR5637** or any device using a **Conexant CX930xx** modem have been proven effective.
- [Optional] A GPIO based indicator board or an MQTT server.

**Note:** Dell Conexant modems such as RD02-D400 are not compatible with the __callattendant__ without a firmware patch.
A patch may be applied by adding a modem init string in the config file OPTIONAL_MODEM_INIT.
Multiple commands may be specified by separating them with a semicolon. For example: `AT!4886=00;AT!4892=FF`

ref: https://en.wikipedia.org/wiki/Network_Caller_ID (Note G)
```
CallerID can be reenabled in any CX93001-based modem by one of the following:
AT!4886=00 for Bell FSK countries
AT!4886=01 for V23 FSK (Japan)
AT!4886=02 for ETSI FSK (France, Italy, Spain)
AT!4886=03 for SIN227 (UK)
AT!4886=05 for ETSI DTMF
Sometimes additionally AT!4892=FF may be required.`
```

---

## Software setup

The installation requires Python3.5 or later.

### Setup a Virtual Environment

The following instructions create and activate a virtual environment named _venv_ within the
current folder:

```bash
# Install virtualenv - if not installed
$ sudo apt install virtualenv

# Create the virtual environment
$ virtualenv venv --python=python3

# Activate it
$ source venv/bin/activate
```

Now you're operating with a virtual Python. To check, issue the `which` command and ensure the
output points to your virtual environment; and also check the Python version:

```bash
$ which python
.../venv/bin/python

$ python --version
Python 3.9.2
```

Installation of the __callattendant__ software will be placed within the virtual environment folder (under `lib/python3.x/site-packages` to be exact). The virtual environment, when activated, alters your _PATH_ so that the system looks for python and its packages within this folder hierarchy.

### Install the Software

The software is available on [Github](https://github.com/thess/callattendant/releases).
Install and update using `pip` or from source:

```bash
# For a first time installation of lxml 5.x, you may need to install
#   the development dependencies libxml2 and libxslt.
# Note: You only have to do this once

$ sudo apt install libxml2-dev libxslt-dev

# Option 1: Using pip
$ source venv/bin/activate
$ pip3 install "callattendant@git+https://github.com/thess/callattendant"

# Option 2: From source (download source tarball from github or clone repository)
$ cd <download directory>
$ source <virtualenv-location>/venv/bin/activate
$ python3 setup.py install

```
---

### Operation

The __callattendant__ package includes a `callattendant` command to start the system. Run this command
the first time with the `--create-folder` option to create the initial data and files in the default
data folder: `~/.callattendant`. This is a hidden folder off the root of your home directory. You
can override this location with the `--data-path` option.

```
Usage: callattendant --config [FILE] --data-path [FOLDER]
Options:
-c, --config [FILE]       load a python configuration file
-d, --data-path [FOLDER]  path to data and configuration files
-f, --create-folder       create the data-path folder if it does not exist
-h, --help                displays this help text
```

```bash
# Creating the default data folder with the default configuration
$ callattendant --create-folder

# Using the default configuration
$ callattendant

# Using a customized config file in an alternate, existing location
$ callattendant --config myapp.cfg --data-path /var/lib/callattendant
```

You should see output of the form:

```
Command line options:
  --config=app.cfg
  --data-path=None
  --create-folder=False
Initializing Modem
Opening serial port
Looking for modem on /dev/ttyACM0
******* Conextant-based modem detected **********
Serial port opened on /dev/ttyACM0
Modem initialized
{MSG LED OFF}
Starting the Flask webapp
Running the Flask server
Waiting for call...
 * Serving Flask app "userinterface.webapp" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
```

Make a few calls to yourself to test the service. The standard output will show the progress of the calls. Then navigate to `http://localhost:5000` in a web browser to checkout the web interface.

Press `ctrl-c` to shutdown the system

---

### Web Interface

#### URL: `http://localhost:5000` or `http://<hostname or FQDN>:5000

To view the web interface, simply point your web browser to port `5000` on your system running Callattendant. For example, in your browser, you can use:

```
http://localhost:5000/
```

See the [User Guide](https://github.com/thess/callattendant/wiki/User-Guide) for more information.

---

### Configuration

The Call Attendant's behavior can be controlled by a configuration file. To override the default
configuration, open the  the `~/.callattenant/app.cfg` and edit its contents.

```bash
nano ~/.callattendant/app.cfg
```

Then specify the configuration file and path on the command line, e.g.:

```
callattendant --config app.cfg
```

See the [Configuration](https://github.com/thess/callattendant/wiki/Home#configuration)
section in the project's wiki for more information.

---
