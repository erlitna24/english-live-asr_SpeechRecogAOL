# English Live ASR — Fine-Tuned Whisper

Continuous English speech-to-text on a local laptop, using a **fine-tuned Whisper base.en** model (FLEURS en_us + AMI IHM), **WhisperLive**, and **Faster-Whisper / CTranslate2 INT8**.

> **Project status:** Local working prototype, **not a production-validated model**. The quality gates in `package_status.json` did not pass (see [Model evaluation and limitations](#model-evaluation-and-limitations)). Live accuracy and latency vary by microphone and laptop.

## What it does

- Reads English speech continuously from your laptop microphone.
- Shows **provisional (partial) captions while you speak**; no Enter key needed between sentences.
- Prints finalized segments and saves the finalized text to `live_sessions/` when you stop with `Ctrl+C`.
- Runs **fully locally**: you start a server and a microphone client on your own laptop. No public server or API key is needed.

WhisperLive works on near-real-time audio chunks (100 ms chunks are streamed to the server), not instantaneous word-by-word recognition.

## Project files

```text
english-live-asr_SpeechRecogAOL/
├── ct2_model/               # Fine-tuned Whisper model (CTranslate2 INT8, model.bin via Git LFS)
├── start_server.py          # Local WhisperLive WebSocket server on 127.0.0.1:9090
├── live_transcribe.py       # Continuous microphone transcription (MAIN DEMO)
├── live_questions.py        # Alternative: question-by-question mode (press Enter per question)
├── transcribe_benchmark.py  # Offline audio-file performance test
├── requirements.txt         # Model/audio dependencies
├── requirements_live.txt    # WhisperLive source, pinned commit
├── run_config.json          # Training provenance (not used for deployment)
├── package_status.json      # Model quality/status flags
├── reports/                 # Evaluation reports
└── validation_samples/      # Packaged validation audio and references
```

You do **not** need the FLEURS/AMI training datasets, Google Colab, or a new fine-tuning run to test live transcription. You do need the complete `ct2_model/` directory.

## Prerequisites

- Python **3.11** (recommended)
- Git and **Git LFS** (needed to download `ct2_model/model.bin`)
- A working microphone, with microphone permission for VS Code / Terminal
- Internet access during the first dependency installation only
- **macOS:** [Homebrew](https://brew.sh/), then `brew install python@3.11 git git-lfs portaudio`
- **Windows:** install [Python 3.11](https://www.python.org/downloads/), [Git](https://git-scm.com/downloads/win) and [Git LFS](https://git-lfs.com/), and make sure `py`, `git` and `git lfs` work in the terminal

Install the prerequisites **before cloning**.

> **Dependency note:** the pinned WhisperLive commit requires `faster-whisper==1.2.0`, which `requirements.txt` already pins. Do not upgrade it. Versions in `run_config.json` describe the training run and do not affect installation.

## 1. Clone the repository

```bash
git lfs install
git clone https://github.com/erlitna24/english-live-asr_SpeechRecogAOL.git
cd english-live-asr_SpeechRecogAOL
git lfs pull
```

Confirm that `ct2_model/model.bin` is the real model (tens of MB or more), not a ~130-byte LFS pointer. If it is tiny, run `git lfs pull` again.

## 2A. Setup on Windows (PowerShell)

Open the cloned folder in VS Code. In the terminal **inside the repository root**:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements_live.txt
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

No PowerShell script activation is required.

**Terminal 1 — server** (leave running; wait until it reports listening on `127.0.0.1:9090`):

```powershell
.\.venv\Scripts\python.exe start_server.py
```

**Terminal 2 — live microphone** (open a NEW terminal in the same folder):

```powershell
.\.venv\Scripts\python.exe live_transcribe.py
```

Speak English. Stop the client with `Ctrl+C`, then stop the server in Terminal 1 with `Ctrl+C`.
If needed, grant access under **Windows Settings → Privacy & security → Microphone**.

## 2B. Setup on macOS (Apple Silicon / Intel)

Inside the cloned repository folder:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements_live.txt
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

**Terminal 1 — server** (keep it open; wait for `server listening on 127.0.0.1:9090`):

```bash
.venv/bin/python start_server.py
```

**Terminal 2 — live microphone:**

```bash
.venv/bin/python live_transcribe.py
```

If prompted, allow microphone access for VS Code / Terminal under **System Settings → Privacy & Security → Microphone**; you may need to restart VS Code afterwards. Use `Ctrl+C` to stop the client, then stop the server separately.

The server runs CPU INT8 inference, even on Macs with an Apple GPU.

## Expected behavior

```text
# Terminal 1 (server)
... server listening on 127.0.0.1:9090

# Terminal 2 (microphone)
Connecting to local WhisperLive server at 127.0.0.1:9090...
LIVE microphone ON. Speak English; text updates while you speak.
... This is a partial transcript
✓ This is a finalized transcript.
```

The output above is illustrative; the actual transcript depends on your microphone and speech. Finalized text is saved to `live_sessions/continuous_<timestamp>.txt` when you stop. That folder is excluded from Git.

## Choosing a microphone

If the default input device is wrong, list devices and pick an ID:

```bash
# macOS
.venv/bin/python live_transcribe.py --list-devices
.venv/bin/python live_transcribe.py --device 2   # replace 2 with YOUR device ID
```

```powershell
# Windows
.\.venv\Scripts\python.exe live_transcribe.py --list-devices
.\.venv\Scripts\python.exe live_transcribe.py --device 2   # replace 2 with YOUR device ID
```

## Troubleshooting

| Issue | What to check |
|---|---|
| `Connection refused` on port `9090` / WebSocket error | Start `start_server.py` **first** and keep it running. If the server printed a Python error, fix that first. |
| `426 Upgrade Required` in server logs | A plain HTTP request hit the WebSocket endpoint. This alone does not mean the server failed; test with `live_transcribe.py`. |
| `ModuleNotFoundError` / `No module named ...` | Use the virtual environment's Python (`.venv/bin/python` or `.\.venv\Scripts\python.exe`) and make sure both requirements files installed successfully. |
| `git not found` while installing `requirements_live.txt` | Install Git, reopen the terminal, and rerun the install. |
| `PortAudio` error on macOS | `brew install portaudio`, then rerun `pip install -r requirements.txt`. |
| Pip says `whisper-live requires faster-whisper==1.2.0` | Do not upgrade faster-whisper. Reinstall with `pip install -r requirements.txt`, then run `python -m pip check`. |
| `model.bin` missing or very small | The model was not downloaded via Git LFS. Run `git lfs pull` and check `ct2_model/model.bin`. |
| `Invalid input device` / no audio input | Check microphone permission and the input device, then use `--list-devices` and `--device` as shown above. |
| No captions or incomplete segments | Check input volume, microphone permission and server logs. As a diagnostic, try `--no-vad` (this changes speech segmentation, not model weights). |
| Slow captions | Inference is CPU INT8; delay depends on your hardware. Measure it on the actual laptop. |
| Session ends after 60 minutes | The server sets `max_connection_time=3600`. Restart the client before the limit if needed. |

## Other modes

- **Continuous live transcription (main demo):** `live_transcribe.py` — no Enter needed between sentences.
- **Question-by-question mode:** `live_questions.py` — records one conversational turn and uses **Enter** to submit each question.
- **Offline benchmark:** `transcribe_benchmark.py` — runs the included validation samples or a WAV file and measures file-level performance. This is **not** the same as live-streaming latency.

## Model evaluation and limitations

Evaluation reports are in `reports/`; status flags are in `package_status.json`. They indicate:

- `ct2_gate_passed: false`
- `offline_target_met: false`
- `fleurs_regression_within_1pp: false`
- Laptop-level latency, live microphone quality, and generalization to new computer-science speech have **not** been established.

The model can be tested locally but should not be presented as validated or production-ready. Successfully starting the server is not evidence of ASR accuracy.

## Repository hygiene

The Git repository excludes `.venv/`, `speech_recog_AOL/`, `live_sessions/`, secrets, archives and other machine-local files (see `.gitignore`). `ct2_model/*.bin` is stored with Git LFS so that clones receive the real model file.

## Acknowledgements

Built with [Whisper](https://github.com/openai/whisper), [WhisperLive](https://github.com/collabora/WhisperLive), [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) and [CTranslate2](https://github.com/OpenNMT/CTranslate2). Fine-tuned on the FLEURS and AMI corpora.
