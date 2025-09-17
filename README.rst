IGv4 Test App
=============

GUI application (Tkinter) used on the assembly line for testing IGv4 hardware.

This document explains how to run the app from source (Windows and Linux), how to build a standalone executable with PyInstaller, and how to run the provided binary (Bin).
 The Bin is available only for RPi and was tested on Raspberry Pi 4 Model B.

Requirements
------------

- Python 3 (3.8 or newer recommended)
- Git
- On Windows: PowerShell (for the commands below)
- On Raspberry Pi / Linux: desktop session or X server (Tkinter GUI requires a display)

Quick repository setup
----------------------

Clone the repository and enter the project folder::

    git clone https://github.com/myaccount/myproject.git
    cd myproject



Using the provided Bin binary (RPi only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A prebuilt Bin file is available for RPi and tested on Raspberry Pi 4 Model B. Steps:

1. Go to the Bin folder.
2. Extract the contents of the provided .zip file.
3. Make the binary executable if required::
       chmod +x IGv4_test_app_<version>  # replace <version> with the actual version
4. Add MAC_addr.xlsx to root of Bin folder (next to the binary) to use a custom MAC address list.
5. Give the binary permission to access USB devices (required for ptouch-print to print labels)::

       sudo chmod -R 777 /dev/bus/usb/
6. Run the binary::
       ./IGv4_test_app_<version>         # or run the produced executable file name


Running from source
-------------------

Windows (PowerShell)
~~~~~~~~~~~~~~~~~~~~

Open PowerShell and go to the project folder (the folder containing app).

Create a virtual environment::

    python -m venv venv

If PowerShell blocks script execution when you try to activate, run this once in the same session::

    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

Activate the virtual environment::

    .\venv\Scripts\Activate.ps1

Upgrade pip (optional but recommended) and install dependencies::

    python -m pip install --upgrade pip
    pip install -r app\requirements.txt

Run the app::

    python app\app_gui.py

Note: If your system uses python3 instead of python, replace accordingly.

Windows (CMD)
~~~~~~~~~~~~~

If you prefer the classic Command Prompt::

    python -m venv venv
    venv\Scripts\activate
    python -m pip install --upgrade pip
    pip install -r app\requirements.txt
    python app\app_gui.py

Linux / Raspberry Pi (tested on RPi 4 Model B)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create and activate a venv::

    python3 -m venv venv
    source venv/bin/activate

Upgrade pip and install dependencies::

    python3 -m pip install --upgrade pip
    pip install -r app/requirements.txt

Run the app::

    python3 app/app_gui.py

Make sure you are on the Pi desktop or have X11 forwarding enabled, because the GUI needs a display.

Build a standalone executable with PyInstaller
----------------------------------------------

Notes before building:

- The project uses a Res folder for resources. PyInstaller needs those files included with ``--add-data``
- On Linux and macOS the ``--add-data`` source and destination are separated with a colon ``:``
- On Windows the separator is a semicolon ``;``
- The example names the build using the value of ``app/_version.py`` which defines ``__version__``

Install PyInstaller::

    pip install pyinstaller

Obtain version number

Bash / Linux / macOS::

    VERSION=$(python3 -c "from app._version import __version__; print(__version__)")

Windows PowerShell::

    $VERSION = python -c "from app._version import __version__; print(__version__)"

Run PyInstaller from project root

Linux / Raspberry Pi example (one-folder build)::

    pyinstaller --clean app/app_gui.py -n "IGv4_test_app_$VERSION" --add-data "Res/*:Res"

Windows PowerShell example (one-folder build)::

    pyinstaller --clean app/app_gui.py -n "IGv4_test_app_$VERSION" --add-data "Res/*;Res"

Notes:

- If you want a single-file executable, add ``-F`` (one-file mode). Example::

    pyinstaller --clean -F app/app_gui.py -n "IGv4_test_app_$VERSION" --add-data "Res/*:Res"

- One-file builds extract at runtime and can cause a delay at startup. For GUI apps with many resources, a one-folder build is often more predictable.
- After the build finishes the built app will be under ``dist/IGv4_test_app_<version>/`` and the executable will be inside that folder.

Running the binary
------------------

From your locally-built distribution (dist)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Linux / RPi::

    cd dist/IGv4_test_app_<version>/
    chmod +x IGv4_test_app_<version>  # if required
    ./IGv4_test_app_<version>         # or run the produced executable file name

Windows:

Open PowerShell or CMD and run the .exe inside ``dist\IGv4_test_app_<version>``.
Repository layout (expected)
----------------------------

::

    myproject/
    ├─ app/
    │  ├─ app_gui.py
    │  ├─ _version.py
    │  └─ requirements.txt
    ├─ Res/          # resources used by the GUI (icons, data files, etc)
    ├─ Bin/          # optional: prebuilt RPi binary (provided)
    └─ README.rst

Adjust commands if your repo structure differs.
