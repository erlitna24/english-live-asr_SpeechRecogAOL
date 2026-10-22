# Deployment guide: FLEURS + AMI fine-tuned Whisper (continuous microphone)

## Stack

Local VS Code + Python 3.11 + WhisperLive (pinned by `requirements_live.txt`) + Faster-Whisper/CTranslate2 + `ct2_model/` (your fine-tuned `base.en` INT8 model).

This is a **local live-ASR prototype**, not a deployed public website. Mic audio streams in 100 ms chunks; partial captions appear before speech stops. Accuracy and latency must still be tested on your own hardware. WhisperLive is **nearly-live/chunk-based**, not instantaneous word-by-word recognition.

## Before running

Unzip the whole project into a directory and open *that directory* in VS Code. Preserve the `ct2_model/` folder, `start_server.py`, `requirements.txt`, `requirements_live.txt`, and `live_transcribe.py`. `model.bin` is already in `ct2_model/`. Training checkpoints and datasets are not needed for inference.

Prerequisites: Python **3.11**, Git, microphone permission. Mac: Homebrew and PortAudio (`brew install python@3.11 git portaudio`). Windows: install Python 3.11 and Git (ensure they are accessible from terminal).

## A. macOS (Apple Silicon / Intel)

From the VS Code terminal **inside the unzipped project directory**:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements_live.txt
.venv/bin/python -m pip install -r requirements.txt
```

Run the server in **Terminal 1**:

```bash
.venv/bin/python start_server.py
```

Leave it running. Open a **second VS Code terminal** in the same folder. Run the live microphone client:

```bash
.venv/bin/python live_transcribe.py
```

Speak continuously. Partial text (`...`) is updated in place and committed text (`✓`) is printed when finalized. **You do not press Enter between sentences.** Use `Ctrl+C` only when finished, and the committed transcript will be saved under `live_sessions/`.

If macOS asks for Microphone access, allow VS Code/Terminal in **System Settings > Privacy & Security > Microphone**. You may need to restart VS Code after granting access.

## B. Windows PowerShell

From the VS Code terminal inside the unzipped project directory:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements_live.txt
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Run server in **Terminal 1**:

```powershell
.\.venv\Scripts\python.exe start_server.py
```

Open **Terminal 2** in the same directory, and run:

```powershell
.\.venv\Scripts\python.exe live_transcribe.py
```

No PowerShell script activation is required. Grant microphone permissions under Windows Settings > Privacy & security > Microphone if necessary.

## Troubleshooting

1. `ModuleNotFoundError`: ensure you use `.venv/bin/python` (macOS) or `.\.venv\Scripts\python.exe` (Windows) and both requirements installs succeeded.
2. `git not found`: install Git, reopen VS Code's terminal, rerun `pip install -r requirements_live.txt`.
3. `PortAudio` error on macOS: `brew install portaudio`; rerun `pip install -r requirements.txt` if needed.
4. `Invalid input device` / no microphone: run the commands below to list devices and choose an input ID:

   macOS: `.venv/bin/python live_transcribe.py --list-devices`

   Windows: `.\.venv\Scripts\python.exe live_transcribe.py --list-devices`

   Then add `--device 2` to the client command, substituting the **actual** microphone index from your own output.
5. Connection refused on port `9090`: start `start_server.py` first and keep it running. If the server prints a Python error, resolve that error before running the client.
6. No captions: check physical microphone input, microphone permissions, server output, then try `live_transcribe.py --no-vad` as a diagnostic. Model quality or latency may also be an issue.
7. Slow inference: the server is configured for **CPU INT8**, including on Macs with an Apple GPU. Test actual delay on the target laptop; stream speed is not guaranteed.
8. Sessions have a **60-minute limit** because the existing server sets `max_connection_time=3600`. Restart client before the limit if necessary.

## Evidence and qualification

- `ct2_model/model.bin` SHA-256 matches `ct2_model/export_complete.json`.
- `package_status.json` marks CT2 quality gate **failed** (AMI CTranslate2 WER drift > allowed 1 pp); `quality_decision.json` marks the offline quality target **not met**. The model can be tested locally but should not yet be presented as a validated/production-ready deployment.
- `transcribe_benchmark.py` can be run separately to measure file-level inference performance. Live microphone latency requires additional measurements during the stream.
- `live_questions.py` was kept unchanged for question-by-question workflows. `live_transcribe.py` is the **continuous** transcript client.
