# Time Capsule

**Every version remembered. Less space wasted.**

Time Capsule is a local-first, educational version-history app for UTF-8 text files. It stores an initial compressed baseline, then stores compressed reversible deltas for later snapshots. It includes a timeline, diff viewer, recovery, SHA-256 integrity checks, storage metrics, and portable JSON capsule export/import.

## Features

- Create multiple local capsules for different files/projects.
- Save labelled snapshots from an editor or upload a supported UTF-8 text file.
- Store first snapshot as a zlib-compressed baseline and later versions as zlib-compressed deltas.
- Reconstruct older versions and verify each reconstruction with SHA-256.
- Compare two versions with a unified diff.
- Download reconstructed versions and export/import complete capsule archives.
- Compare delta storage against independently zlib-compressed full copies.

## Requirements

- Windows 10/11, macOS, or Linux
- Python 3.10 or newer (Python 3.11 recommended)
- Internet access the first time you install Streamlit

## Quick start on Windows

1. Download and extract `time-capsule.zip` to a folder you can write to.
2. Install Python 3.11 from <https://www.python.org/downloads/> if it is not already installed. During setup on Windows, enable **Add Python to PATH**.
3. Open the extracted `time-capsule` folder.
4. Double-click `run_windows.bat`. The script creates a virtual environment, installs dependencies, and launches the app.
5. A browser tab should open at `http://localhost:8501`. If it does not, copy that address into your browser.
6. Keep the terminal window open while using the app. Close it to stop the app.

### Manual setup (Windows PowerShell)

From the project folder:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

If PowerShell blocks activation, you can skip activation and run the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

## How to use the app

1. **Create a capsule:** in the left sidebar, open “New capsule”, enter a project name and tracked filename (for example `my_script.py`), then click “Create capsule”.
2. **Create version 1:** type or paste text into the editor, or upload a UTF-8 text file. Enter a snapshot label such as `Initial working version` and click **Save snapshot**.
3. **Make a change:** edit the text, add a label such as `Added input validation`, and save another snapshot. Repeat as needed.
4. **Inspect history:** each saved snapshot appears in the Version timeline. Click **Load into editor** to load a historical version; save it as a new snapshot if you want to branch/continue from it. Loading a version does not delete later versions.
5. **Compare:** after at least two snapshots exist, choose two versions in the Compare versions section to see a unified diff and download either version.
6. **Check storage:** the top metrics compare stored baseline/delta payloads with independently compressed full copies. Results vary with how much the content changes; negative savings are possible and are reported honestly.
7. **Back up:** click **Export capsule archive**. Store the downloaded JSON file somewhere safe. To restore it later, use “Import a capsule archive (.json)” in the sidebar.
8. **Verify integrity:** each reconstructed version is checked against its stored SHA-256 hash. If payload data is corrupted, reconstruction will fail with an integrity error.

## Demo flow for a presentation

1. Create a capsule called `Demo Python Project`, filename `example.py`.
2. Paste the contents of `demo_files/example_v1.py`; save as `Initial version`.
3. Change the file using `demo_files/example_v2.py`; save as `Added validation`.
4. Save a third version with one more small edit.
5. Show the timeline, compare v1 and v2, and discuss storage metrics.
6. Export the capsule, import it, and load an older version to demonstrate portability.

## Tests

The project includes unit tests for delta round-trips, Unicode, line endings, malformed deltas, version reconstruction, and archive validation.

```bash
python -m unittest discover -s tests -v
```

## Technical design

- **Delta generation:** `difflib.SequenceMatcher` generates edit operations. `src/delta_engine.py` converts these to a reversible operation stream.
- **Compression:** `zlib` compresses the baseline and each delta.
- **Persistence:** each capsule is saved as JSON in `.time_capsule_data/` beside the app. Payload bytes are Base64 encoded within the JSON document.
- **Integrity:** SHA-256 is calculated on the exact UTF-8 text of every snapshot.
- **Interface:** Streamlit.

## Scope and limitations

- This MVP tracks one UTF-8 text file per capsule; it is not a full Git replacement.
- Binary files, images, folders, cloud sync, multi-user collaboration, and encryption are not implemented.
- Delta compression is not guaranteed to save space for every input. The app reports actual measured storage values.
- This is a local educational tool. Keep exported backups of important files; deleting the project folder also deletes its local capsule data.
- The storage metrics measure compressed payload sizes, not all JSON metadata, filesystem overhead, or browser cache.

## Project structure

```text
time-capsule/
├── app.py
├── src/
│   ├── delta_engine.py
│   ├── compression.py
│   ├── integrity.py
│   └── version_manager.py
├── tests/
├── demo_files/
├── requirements.txt
├── run_windows.bat
└── README.md
```
