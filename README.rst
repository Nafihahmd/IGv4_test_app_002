# IGv4 Test App

GUI application (Tkinter) used on the assembly line for testing IGv4 hardware.

This document explains how to run the app from source (Windows and Linux), how to build a standalone executable with PyInstaller, and how to run the provided binary (Bin) on Raspberry Pi 4 Model B. The `Bin` is available only for RPi and was tested on Raspberry Pi 4 Model B.

## Requirements

* Python 3 (3.8 or newer recommended)
* Git
* On Windows: PowerShell (for the commands below)
* On Raspberry Pi / Linux: desktop session or X server (Tkinter GUI requires a display)

## Quick repository setup

Clone the repository and enter the project folder:

\::

git clone [https://github.com/Nafihahmd/IGv4_test_app_002.git](https://github.com/Nafihahmd/IGv4_test_app_002.git)
cd IGv4_test_app_002

## Running from source

Windows (PowerShell)
^^^^^^^^^^^^^^^^^^^^^

1. Open PowerShell and go to the project folder (the folder containing `app`).

2. Create a virtual environment::

   python -m venv venv

3. If PowerShell blocks script execution when you try to activate, run this once in the same session::

   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

4. Activate the virtual environment::

   .\venv\Scripts\Activate.ps1

5. Upgrade pip (optional but recommended) and install dependencies::

   python -m pip install --upgrade pip
   pip install -r app\requirements.txt

6. Run the app::

   python app\app\_gui.py

Note: If your system uses `python3` instead of `python`, replace accordingly.

Windows (CMD)
^^^^^^^^^^^^^

If you prefer the classic Command Prompt:

\::

python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r app\requirements.txt
python app\app\_gui.py

Linux / Raspberry Pi (tested on RPi 4 Model B)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Create and activate a venv::

   python3 -m venv venv
   source venv/bin/activate

2. Upgrade pip and install dependencies::

   python3 -m pip install --upgrade pip
   pip install -r app/requirements.txt

3. Run the app::

   python3 app/app\_gui.py

Make sure you are on the Pi desktop or have X11 forwarding enabled, because the GUI needs a display.

## Build a standalone executable with PyInstaller

Notes before building:

* The project uses a `Res` folder for resources. PyInstaller needs those files included with `--add-data`.
* On Linux and macOS the `--add-data` source and destination are separated with a colon `:`.
* On Windows the separator is a semicolon `;`.
* The example names the build using the value of `app/_version.py` which defines `__version__`.

1. Install PyInstaller::

   pip install pyinstaller

2. Obtain version number

   * Bash / Linux / macOS::

     VERSION=\$(python3 -c "from app.\_version import **version**; print(**version**)")

   * Windows PowerShell::

     \$VERSION = python -c "from app.\_version import **version**; print(**version**)"

3. Run PyInstaller from project root

   * Linux / Raspberry Pi example (one-folder build)::

     pyinstaller --clean app/app\_gui.py -n "IGv4\_test\_app\_\$VERSION" --add-data "Res/\*:Res"

   * Windows PowerShell example (one-folder build)::

     pyinstaller --clean app/app\_gui.py -n "IGv4\_test\_app\_\$VERSION" --add-data "Res/\*;Res"

   Notes:

   * If you want a single-file executable, add `-F` (one-file mode). Example::

     pyinstaller --clean -F app/app\_gui.py -n "IGv4\_test\_app\_\$VERSION" --add-data "Res/\*:Res"

   * One-file builds extract at runtime and can cause a delay at startup. For GUI apps with many resources, a one-folder build is often more predictable.

After the build finishes the built app will be under `dist/IGv4_test_app_<version>/` and the executable will be inside that folder.

## Running the binary

From your locally-built distribution (`dist`)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Linux / RPi::

\::

cd dist/IGv4\_test\_app\_<version>/
chmod +x IGv4\_test\_app\_<version>   # if required
./IGv4\_test\_app\_<version>          # or run the produced executable file name

Windows::

Open PowerShell or CMD and run the `.exe` inside `dist\IGv4_test_app_<version>\`.

Using the provided Bin binary (RPi only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You mentioned a prebuilt `Bin` file is available for RPi and tested on Raspberry Pi 4 Model B. Typical steps:

1. Copy the `Bin` folder to the Pi (via `scp`, USB, or similar).
2. On the Pi, in the folder containing the binary::

   cd Bin
   chmod +x IGv4\_test\_app\_<version>   # if not executable
   ./IGv4\_test\_app\_<version>

If the binary is a folder with resources, run the launcher inside that folder (for example `./run.sh` or the executable produced by PyInstaller). If the binary expects to be launched from a certain working directory to find `Res/`, run it from that folder.

Important RPi notes

* The Bin executable was only tested on Raspberry Pi 4 Model B. Other Pi models or ARM boards may not be compatible.
* Ensure the Pi has a desktop session or an X server available when launching the GUI.
* If you see errors about missing libraries, install missing system packages. If the executable still reports missing Tk libraries, try installing system Tk: for Debian/Ubuntu/Raspbian::

  sudo apt update
  sudo apt install python3-tk

## Troubleshooting tips

* If `pip install -r app/requirements.txt` fails, inspect the error messages and install any missing OS-level packages. On Debian/Ubuntu/Raspbian use `sudo apt-get update` and install dev packages needed by wheels.
* If activation fails on Windows PowerShell, ensure script execution for the session is allowed (see the `Set-ExecutionPolicy` command above).
* If the GUI does not open on Linux/RPi, check you are running inside a graphical session and the `DISPLAY` environment variable is set.
* If PyInstaller misses resource files, verify paths passed to `--add-data` and ensure the `Res` folder contains required files.
* If the executable fails with missing shared library errors on Linux, inspect the error and install the appropriate system package.

## Repository layout (expected)

\::

IGv4_test_app_002/
├─ app/
│  ├─ app\_gui.py
│  ├─ \_version.py
│  └─ requirements.txt
├─ Res/                # resources used by the GUI (icons, data files, etc)
├─ Bin/                # optional: prebuilt RPi binary (provided)
└─ README.rst

Adjust commands if your repo structure differs.

## Reporting issues

If you run into problems building or running the app, please open an issue in the GitHub repo and include:

* platform (Windows / Raspberry Pi 4 Model B / other)
* Python version (`python --version`)
* full error output or traceback
* steps you followed

