# Install guide (students & lab PCs)

Follow this **in order**. If a step fails, do not skip ahead — jump to [Troubleshooting](#troubleshooting).

---

## 0. What you need

- A computer with **Windows 10/11**, **macOS**, or **Linux**
- **Python 3.10, 3.11, or 3.12** (3.12 recommended)
- About **1–2 GB** free disk (Cantera + RocketCEA wheels)
- Permission to install Python packages (or use a user install)

Check Python:

```bash
python --version
```

or on Windows:

```bash
py -0
py -3.12 --version
```

If you see 3.9 or older, install a newer Python from [python.org](https://www.python.org/downloads/)  
**Windows tip:** during install, tick **“Add python.exe to PATH”**.

---

## 1. Create a virtual environment (required)

A venv keeps propwrap’s packages separate from the system Python.

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Or use Command Prompt:

```cmd
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` at the start of your prompt.

---

## 2. Install propwrap (recommended: PyPI)

```bash
python -m pip install --upgrade pip
pip install propwrap
```

This installs **propwrap** plus required dependencies:

- rocketcea, **cantera**, pydantic, **matplotlib**, numpy

**First install can take several minutes.** Wait for it to finish.

### From source (if your course clones the repo)

```bash
git clone https://github.com/shanthoshkv/propwrap.git
cd propwrap
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Student pin file (more reproducible lab PCs):

```bash
pip install -r requirements-student.txt
pip install -e .
```

---

## 3. Verify the install

```bash
propwrap run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20
python -c "import cantera, matplotlib, propwrap; print(propwrap.__version__)"
```

You should see Isp, c*, temperatures, etc.

If `propwrap` is not found:

```bash
python -m propwrap.cli run RP-1 LOX --of 2.56 --pc-bar 70 --eps 20
```

Run tests (from a source checkout with `.[dev]`):

```bash
pytest -q
```

---

## 4. Generate your first lab pack

```bash
propwrap homework kerolox --name YourName
```

Opens a folder with `summary.md`, CSVs, plots, and `assumptions.txt`.

---

## Common lab-PC problems

| Symptom | Fix |
|---------|-----|
| `python` not found | Use `py -3.12` on Windows; reinstall Python with PATH |
| Activation policy error | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `pip install` fails on rocketcea | Use Python 3.11/3.12 64-bit; `pip install --upgrade pip` |
| Permission denied | Use venv (don’t install system-wide); or `pip install --user` |
| Corporate proxy | Ask IT for proxy env vars; or install offline wheels |
| Antivirus blocks compile | Prefer **prebuilt wheels** (`pip install --prefer-binary rocketcea cantera`) |

---

## Troubleshooting

### RocketCEA import error

```bash
pip install --prefer-binary --force-reinstall rocketcea
python -c "from rocketcea.cea_obj import CEA_Obj; print(CEA_Obj(oxName='LOX',fuelName='LH2').get_Isp())"
```

Expect a number near **374**.

### Cantera import error

```bash
pip install --prefer-binary cantera
python -c "import cantera; print(cantera.__version__)"
```

### Wrong pressure (tiny Isp or weird results)

- `pc=` means **pascals**  
- For 70 bar use `--pc-bar 70` or `pc_bar=70`  
- Never write `pc=70` unless you really mean 70 Pa

### Still stuck?

1. Confirm `(.venv)` is active  
2. `pip list | findstr rocketcea` (Windows) / `pip list | grep rocketcea`  
3. Read [how_to_use.md](how_to_use.md)  
4. Open a GitHub issue with OS, Python version, and full error text  

---

## Google Colab / locked machines

If you cannot install packages on a lab PC, see **[colab.md](colab.md)** for a cloud notebook path and limitations.

---

## After install — recommended student path

1. [how_to_use.md](how_to_use.md) — learn the API  
2. `propwrap homework kerolox --name You` — get a report  
3. [learning/](learning/) — concepts (units, frozen/shifting, fair trades)  
4. [cheat_sheet.md](cheat_sheet.md) — one-page reference  
