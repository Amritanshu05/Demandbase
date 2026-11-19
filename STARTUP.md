# Run the project

Requires Python 3.9 or newer with `pip` and `venv`.

## First-time setup

Open a terminal in the project directory and use the commands for your operating system.

### macOS / Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

### Windows — PowerShell or Command Prompt

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install tzdata
.\.venv\Scripts\python.exe app.py
```

If `py` is unavailable but Python is installed, use `python -m venv .venv` for the first command. The Windows commands run the virtual environment's Python directly; no activation or PowerShell execution-policy changes are needed.

Open **http://127.0.0.1:5001** on either operating system.

## Subsequent starts

### macOS / Linux

```sh
.venv/bin/python app.py
```

### Windows — PowerShell or Command Prompt

```powershell
.\.venv\Scripts\python.exe app.py
```

## Use another port

### macOS / Linux

```sh
PORT=5002 .venv/bin/python app.py
```

### Windows PowerShell

```powershell
$env:PORT = "5002"
.\.venv\Scripts\python.exe app.py
```

### Windows Command Prompt

```bat
set PORT=5002
.\.venv\Scripts\python.exe app.py
```

Open **http://127.0.0.1:5002**.

The first start creates `instance/`, the SQLite database, the signing key, and demo data automatically. Existing databases receive the new chat table automatically when the app starts; no reset or manual migration command is needed. No environment file or API keys are required. Stop the server with **Ctrl+C**.
