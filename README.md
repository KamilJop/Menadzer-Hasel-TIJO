# Local Password Manager

<p align="center">
  <img src="ui/resources/icons/app_icon.svg" alt="Local Password Manager Logo" width="80" height="80" />
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="https://riverbankcomputing.com/software/pyqt/"><img src="https://img.shields.io/badge/PyQt6-GUI-41CD52?style=flat-square&logo=qt&logoColor=white" alt="PyQt6"></a>
  <a href="https://github.com/pwh-p2p/argon2-cffi"><img src="https://img.shields.io/badge/Argon2id-KDF-E53935?style=flat-square" alt="Argon2id"></a>
  <a href="https://cryptography.io/"><img src="https://img.shields.io/badge/AES--256--GCM-AEAD-1E88E5?style=flat-square" alt="AES-256-GCM"></a>
  <a href="https://docs.pytest.org/"><img src="https://img.shields.io/badge/Pytest-Testing-0A9EDC?style=flat-square&logo=pytest&logoColor=white" alt="Pytest"></a>
  <a href="https://pyinstaller.org/"><img src="https://img.shields.io/badge/PyInstaller-Executable%20Build-FF6F00?style=flat-square" alt="PyInstaller"></a>
  <a href="https://microsoft.com/windows"><img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=flat-square&logo=windows&logoColor=white" alt="Platform: Windows"></a>
  <img src="https://img.shields.io/badge/Release-Standalone%20.exe-2E7D32?style=flat-square" alt="Standalone .exe">
</p>

---

## Project Overview

A desktop password manager developed for the university course **Software Testing and Quality Assurance**. All credentials are encrypted and stored locally on the user's machine without any external servers or cloud dependencies.

### Encryption Flow

1. **Key Derivation:** The user's password and a random salt are processed through **Argon2id** to derive an encryption key.
2. **Encryption:** Vault data is encrypted.
3. **Storage:** The encrypted file is saved locally.
4. **Decryption:** Entering the password decrypts and validates the vault. Incorrect passwords or corrupted files fail decryption immediately.

---

## Features

- **Password Authentication:** Vault access protected by Argon2id.
- **Category Management:** Organize entries by category with search and filtering.
- **Password Strength Validator:** Real-time entropy calculation and weak pattern detection.
- **Password Generator:** Random password generator.
- **Export and Import:** Encrypted JSON backup and plaintext JSON export.
- **Desktop UI:** Interface built with PyQt6.

---

## Standalone Release (.exe)

A precompiled, standalone Windows executable (`PasswordManager.exe`) is provided in the **[Releases](../../releases)** section. It requires no Python installation or external dependencies.

### Running the Executable

1. Download `PasswordManager.exe` from the latest release (or use the one in `dist/PasswordManager.exe`).
2. Place the executable in your desired working directory.
3. Double-click `PasswordManager.exe` to run the application.


---

## Running from Source

### Prerequisites

- **Python 3.10+** (tested with Python 3.10 through 3.14)
- **pip** package manager

### 1. Clone the Repository

```powershell
git clone https://github.com/KamilJop/Menad-er-Hase-.git
cd Menad-er-Hase-
```

### 2. Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the Application

```powershell
python main.py
```
or using

```powershell
python -m ui.app
```

---

## Compiling to Standalone Executable (.exe)

The project includes a ready-to-use PyInstaller specification file (`PasswordManager.spec`) that packages the Python runtime, PyQt6 binaries, cryptographic extensions, stylesheets, and icons into a single `.exe` file.

### 1. Install Build Dependencies

```powershell
pip install -r requirements-dev.txt
```

### 2. Build with PyInstaller

Run the build command using the specification file:

```powershell
pyinstaller --clean --noconfirm PasswordManager.spec
```

### 3. Output Location

The generated executable will be placed in:

```text
dist/PasswordManager.exe
```

This executable is self-contained and can be distributed and executed on Windows machines without Python installed.

---

## Testing

The project was developed following testability and clean code standards. Pure business logic in `core/` is decoupled from the GUI, enabling automated headless unit and integration testing.

### Run Test Suite

```powershell
pytest
```

### Run Tests with Coverage Report

```powershell
pytest --cov=core --cov=storage --cov-report=term-missing
```

### Run a Specific Test Module

```powershell
pytest tests/unit/test_crypto.py -v
```

---

## Project Structure

```text
TIJO/
├── core/                           # Business & cryptographic domain logic (Pure Python)
│   ├── crypto.py                   # Argon2id KDF & AES-256-GCM engine
│   ├── models.py                   # Data models (Entry, Category, VaultPayload)
│   ├── validator.py                # Password entropy & rule evaluation
│   ├── generator.py                # Cryptographically secure password generator
│   └── exceptions.py               # Custom domain exceptions
│
├── storage/                        # Persistence & export layer
│   ├── interfaces.py               # Repository and exporter interfaces
│   ├── repository.py               # Vault persistence with atomic file writes
│   └── exporter.py                 # Encrypted & Plaintext JSON export/import
│
├── ui/                             # PyQt6 desktop user interface
│   ├── app.py                      # Application bootstrap & entry point
│   ├── state.py                    # Session state manager
│   ├── views/                      # Main window, login screen, and dialogs
│   ├── widgets/                    # Custom UI components
│   ├── services/                   # Clipboard and asset services
│   └── resources/                  # Stylesheets and icons
│
├── tests/                          # Automated test suite
│   ├── unit/                       # Unit tests (crypto, validator, generator, repository)
│   └── integration/                # Integration tests (vault workflow, export/import)
│
├── PasswordManager.spec            # PyInstaller build specification
├── requirements.txt                # Runtime dependencies
├── requirements-dev.txt            # Development & build dependencies
└── main.py                         # Application entry point
```

---

## License

This project is licensed under the MIT License.
