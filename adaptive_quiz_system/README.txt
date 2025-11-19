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
Locate the main script (usually main.py or app.py)
and click Run in PyCharm (top-right corner).
You can also run it from the terminal with:
python main.py