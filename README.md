# English Live ASR — Fine-Tuned Whisper

Continuous English speech-to-text on a local laptop, using a **fine-tuned Whisper base.en** model (FLEURS en_us + AMI IHM), **WhisperLive**, and **Faster-Whisper / CTranslate2 INT8**.

> **Project status:** Local working prototype, **not a production-validated model**. The model quality gates in `package_status.json` did not pass. Live performance and accuracy may vary by microphone and laptop.

## What it does

- Reads English speech continuously from your laptop microphone.
- Displays **provisional/partial captions while you speak**, without pressing Enter between sentences.
- Prints finalized transcript segments and saves the finalized text to `live_sessions/` when you stop with `Ctrl+C`.
- Runs **locally**: each user starts a server and a microphone client on **their own laptop**. No public server or API key is needed.

WhisperLive works in near-real-time audio chunks, not guaranteed word-by-word instantaneous transcription.

## Project files

```text
english-live-asr/
├── ct2_model/              # Fine-tuned Whisper model (including model.bin)
├── start_server.py          # Local WhisperLive WebSocket server: 127.0.0.1:9090
├── live_transcribe.py       # Continuous microphone transcription (MAIN DEMO)
├── live_questions.py        # Alternative: question-by-question mode (requires Enter)
├── transcribe_benchmark.py # Offline audio-file performance test
├── requirements.txt        # Model/audio dependencies
├── requirements_live.txt   # WhisperLive source, pinned commit
├── DEPLOY_LIVE.md          # Detailed installation and troubleshooting
├── reports/                # Evaluation reports
├── validation_samples/     # Packaged validation audio and references
└── package_status.json     # Model quality/status flags
```

**You do not need the FLEURS/AMI training datasets, Google Colab, or a new fine-tuning run** to test live transcription. You do need the complete `ct2_model/` directory.

## Prerequisites

- Python **3.11** (recommended)
- Git, and **Git LFS** to download `ct2_model/model.bin` when cloning from GitHub
- A working microphone and microphone permission for VS Code/Terminal
- Internet access **during the first dependency installation**; transcription itself connects to the local server
- On macOS, [Homebrew](https://brew.sh/) and PortAudio. **Before cloning**, install prerequisites using `brew install python@3.11 git git-lfs portaudio`.
- On Windows, install [Python 3.11](https://www.python.org/downloads/), [Git](https://git-scm.com/downloads/win) and [Git LFS](https://git-lfs.com/) **before cloning**.

**Important dependency fix:** `WhisperLive 0.10.0` from the pinned commit requires `faster-whisper==1.2.0`. Verify that the committed `requirements.txt` uses **1.2.0**, not 1.2.1. The training provenance in `run_config.json` may record older experimental versions and does not control deployment installation.

## 1. Clone the repository

Replace `<REPO_URL>` with the actual HTTPS or SSH URL of this GitHub repository. If this is a private repository, accept the collaborator invitation first.

```bash
git lfs install
git clone <REPO_URL>
cd english-live-asr
git lfs pull
```

The folder name after cloning will match the repository name. Confirm that `ct2_model/model.bin` is a real model file, not an LFS pointer. If necessary, rerun `git lfs pull`.

## 2A. Setup on Windows (PowerShell)

After installing the prerequisites above, open the cloned repository folder in VS Code.

In the VS Code terminal **inside the repository root**:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements_live.txt
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

**Terminal 1 — server:**

```powershell
.\.venv\Scripts\python.exe start_server.py
```

Leave Terminal 1 running. Wait for the log indicating it is listening on `127.0.0.1:9090`.

**Terminal 2 — live microphone:** Open a NEW terminal in the same folder:

```powershell
.\.venv\Scripts\python.exe live_transcribe.py
```

Speak English. Partial captions should update during speech. Stop the microphone client with `Ctrl+C` and then stop the server in Terminal 1 with `Ctrl+C`.

## 2B. Setup on macOS

After installing the Homebrew prerequisites above and cloning the repository, run the following **inside the cloned repository folder** in VS Code:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements_live.txt
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
```

**Terminal 1 — server:**

```bash
.venv/bin/python start_server.py
```

Wait for `server listening on 127.0.0.1:9090`. Keep the terminal open.

**Terminal 2 — live microphone:**

```bash
.venv/bin/python live_transcribe.py
```

Allow microphone access for VS Code/Terminal under **System Settings → Privacy & Security → Microphone** if prompted. Speak continuously, then use `Ctrl+C` to stop. Stop the server separately.

**Note:** The server is configured for CPU inference with the packaged INT8 model, even on Apple Silicon Macs.

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

Output shown above is illustrative; the actual transcript depends on your microphone and speech. Finalized text is saved to `live_sessions/continuous_<timestamp>.txt` when you stop. This directory is intentionally excluded from Git.

## Troubleshooting

| Issue | What to check |
|---|---|
| `[Errno 61] Connection refused` / WebSocket connection error | Start `start_server.py` **first** in Terminal 1. Keep it running while starting Terminal 2. |
| `426 Upgrade Required` in server logs | An ordinary HTTP request contacted the WebSocket endpoint. It does not by itself mean the server failed; test with `live_transcribe.py`. |
| `No module named ...` | Check the virtual environment and install both requirements files with `.venv`'s Python. |
| Pip says `whisper-live requires faster-whisper==1.2.0` | Fix `requirements.txt` to pin `faster-whisper==1.2.0`, reinstall it, then run `python -m pip check` using the virtual environment. |
| `model.bin` missing / very small | Model may not have downloaded via Git LFS. Run `git lfs pull` and check `ct2_model/model.bin`. |
| Microphone permission / no audio input | Enable permission for VS Code/Terminal, check the laptop input device, then list devices as shown below. |
| No captions or incomplete segments | Check input volume and server logs; as a diagnostic, try `--no-vad` (this changes speech segmentation behavior, not model weights). |
| Slow captions | This is CPU INT8 inference. Speed and delay depend on hardware; measure it on the actual laptop. |

Choose a microphone manually if the default is wrong:

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

## Other available modes

- **Continuous live transcription (main demo):** `live_transcribe.py` — no Enter needed between sentences.
- **Question-based transcription:** `live_questions.py` — records a conversational turn and uses **Enter** to submit/finalize each question. See `DEPLOY_LIVE.md` and the original design notes.
- **Offline benchmark:** `transcribe_benchmark.py` — processes included validation examples or a WAV file and measures file-level performance. This is **not** the same as measuring live-streaming latency.

## Model evaluation and limitations

The package contains reports in `reports/` and status in `package_status.json`. They indicate:

- `ct2_gate_passed: false`
- `offline_target_met: false`
- Laptop-level latency, live microphone quality, and generalization to new computer-science speech have **not** been established by these reports.

This is a **working local proof of concept**, not a claim of meeting the final research quality targets. Do not present success at starting the server as proof of ASR accuracy.

## More details

See [`DEPLOY_LIVE.md`](DEPLOY_LIVE.md) for fuller deployment notes and troubleshooting. The Git repository should exclude `.venv/`, `speech_recog_AOL/`, `live_sessions/`, secrets, archives, and other machine-local files. The model binary should be stored through Git LFS so teammates can clone it correctly.
