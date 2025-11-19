This Python project was developed on macOS using PyCharm.
It is compatible with Windows, macOS, and Linux, provided the setup steps below are followed carefully.

1. Python Installation
Make sure you have Python 3.9 or higher installed.
	•	Windows: https://www.python.org/downloads/windows/
(During installation, check the box “Add Python to PATH”)
	•	macOS: Python is usually preinstalled, but you can get the latest version at https://www.python.org/downloads/mac-osx/

2. PyCharm Installation
Download and install PyCharm Community Edition (free):
https://www.jetbrains.com/pycharm/download/

3. Opening the Project
	1	Unzip the project folder you download on Moodle.
	2	Open PyCharm.
	3	Select File > Open... and choose the project folder.

4. Creating a Virtual Environment
When PyCharm opens the project, it may suggest creating a virtual environment (venv).
	•	Accept the option “Create a new virtual environment.”
	•	Keep the default location and click OK.
If not prompted, you can create it manually under:
File > Settings > Project > Python Interpreter > Add Interpreter > New Virtual Environment

5. Installing Dependencies
In the PyCharm terminal (bottom panel), type:
pip install -r requirements.txt

This will install all the required Python libraries for the project.

6. Downloading trail source data
Copy the French hiking shapefile (`hiking_foot_routes_lineLine.*`) into the dedicated
`adaptive_quiz_system/data/source/` folder. Ensure the `.shp`, `.shx`, `.dbf`, and `.prj`
files all sit in that directory before running `python backend/init_db.py`.

6. File Encoding (to avoid text errors)
This project uses UTF-8 encoding to support accented characters (é, è, à, ç, etc.).
On macOS:
No action needed (UTF-8 is the default).
On Windows:
If you see an error such as
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe9 in position ...
follow these steps:
	1	In PyCharm, go to: File > Settings > Editor > File Encodings
	2	Set the following options to UTF-8:
	◦	Global Encoding
	◦	Project Encoding
	◦	Default encoding for properties files
	3	Check the box “Transparent native-to-ascii conversion”
	4	Click Apply, then OK.

7. Running the Program
The Flask app now lives in the `app/` package and is started via `run.py`. After installing the
dependencies and generating the SQLite databases (`python backend/init_db.py`), you can launch
the experience from PyCharm or the terminal with:

```
python run.py
```

The personalised demo is available at `http://127.0.0.1:5000/` by default.