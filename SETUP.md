# Local startup

## 1. Install prerequisites

Install Python 3.11 or newer, including `pip` and `venv`.

On Debian/Ubuntu, if `venv` is missing:

```bash
sudo apt install python3-venv
```

## 2. Open the project directory

```bash
cd /path/to/amrit
```

## 3. Create a virtual environment

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use `.\.venv\Scripts\python.exe` instead of `python` in the following commands.

## 4. Install dependencies

```bash
python -m pip install --only-binary=:all: -r requirements.txt
```

## 5. Start

```bash
python app.py
```

## 6. Open

Visit **http://127.0.0.1:5000**.

Use the same hostname each time.

## 7. Stop and restart

Press `Ctrl+C` to stop.

To restart, activate the virtual environment and run:

```bash
python app.py
```

## Optional: use another port

macOS/Linux:

```bash
PORT=5001 python app.py
```

Windows PowerShell:

```powershell
$env:PORT = "5001"
python app.py
```

Open **http://127.0.0.1:5001**.

## Optional: use a different data directory

macOS/Linux:

```bash
RELAY_DATA_DIR=/absolute/path/to/relay-data python app.py
```

Windows PowerShell:

```powershell
$env:RELAY_DATA_DIR = "C:\absolute\path\to\relay-data"
python app.py
```
