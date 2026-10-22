"""Continuous live microphone transcription for the packaged fine-tuned Whisper model.

Run start_server.py in another terminal before running this client.
The WhisperLive server, not this file, loads ct2_model/.
"""

import argparse
import queue
import sys
import threading
from datetime import datetime
from pathlib import Path

import sounddevice as sd
from whisper_live.client import StreamingTranscriptionClient

SAMPLE_RATE = 16_000
BLOCK_SIZE = 1_600  # 100 ms chunks; sent to the server as they arrive


class LiveConsole:
    """Replace provisional text in-place; print finalized segments once."""

    def __init__(self):
        self.lock = threading.Lock()
        self.partial = ""
        self.finished = []

    def _clear_line(self):
        if self.partial:
            sys.stdout.write("\r\033[2K")
            self.partial = ""

    def on_partial(self, text, _segments):
        text = text.strip()
        with self.lock:
            if text == self.partial:
                return
            self._clear_line()
            if text:
                self.partial = text
                sys.stdout.write(f"... {text}")
            sys.stdout.flush()

    def on_committed(self, text, segments):
        text = text.strip()
        with self.lock:
            self._clear_line()
            if text:
                self.finished.append(text)
                sys.stdout.write(f"✓ {text}\n")
                sys.stdout.flush()

    def message(self, text):
        with self.lock:
            self._clear_line()
            print(text, flush=True)

    def save(self):
        with self.lock:
            self._clear_line()
            output = " ".join(self.finished).strip()
        if not output:
            self.message("No finalized transcript to save.")
            return
        output_dir = Path(__file__).resolve().parent / "live_sessions"
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"continuous_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        output_path = output_dir / filename
        output_path.write_text(output + "\n", encoding="utf-8")
        self.message(f"Transcript saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Continuous WhisperLive microphone transcription")
    parser.add_argument("--list-devices", action="store_true", help="List microphone devices and exit")
    parser.add_argument("--device", type=int, default=None, help="Input device ID from --list-devices")
    parser.add_argument("--no-vad", action="store_true", help="Disable voice activity detection")
    args = parser.parse_args()

    if args.list_devices:
        print(sd.query_devices())
        return

    output = LiveConsole()
    audio_queue = queue.Queue(maxsize=120)  # Up to 12 seconds of 100-ms chunks
    stop = threading.Event()
    failures = queue.Queue()

    def audio_callback(indata, frames, time_info, status):
        if status:
            failures.put(f"Microphone warning: {status}")
        try:
            audio_queue.put_nowait(bytes(indata))
        except queue.Full:
            failures.put("Audio buffer overflow: the system cannot stream fast enough")
            stop.set()

    def server_error(exc):
        failures.put(f"WhisperLive connection error: {exc}")
        stop.set()

    client = StreamingTranscriptionClient(
        "127.0.0.1", 9090,
        lang="en",
        model="base.en",  # The server overrides this with ct2_model/
        use_vad=not args.no_vad,
        ready_timeout=60,
        on_partial_transcript=output.on_partial,
        on_committed_transcript=output.on_committed,
        on_error=server_error,
    )

    connected = False
    try:
        output.message("Connecting to local WhisperLive server at 127.0.0.1:9090...")
        client.connect()
        connected = True
        output.message("LIVE microphone ON. Speak English; text updates while you speak.")
        output.message("Press Ctrl+C ONLY when you want to stop and save the transcript.\n")
        with sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            device=args.device,
            channels=1,
            dtype="int16",
            callback=audio_callback,
        ):
            while not stop.is_set():
                if not client._client.recording:
                    failures.put("The server closed the session (server limit: 60 minutes).")
                    break
                try:
                    chunk = audio_queue.get(timeout=0.2)
                except queue.Empty:
                    continue
                client.send(chunk, pcm_format="int16")
    except KeyboardInterrupt:
        output.message("\nStopping the microphone. Finalizing the last words...")
    except Exception as exc:
        output.message(f"\nDeployment error: {type(exc).__name__}: {exc}")
    finally:
        if connected:
            try:
                client.close(timeout=30)  # END_OF_AUDIO flush: don't drop final words
            except Exception as exc:
                output.message(f"Could not finalize cleanly: {exc}")
        else:
            try:
                client._client.close_websocket()
            except Exception:
                pass
        output.save()
        while not failures.empty():
            output.message("Notice: " + failures.get_nowait())


if __name__ == "__main__":
    main()
