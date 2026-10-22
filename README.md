# ASR English — paket model lokal

Model: Whisper base.en fine-tuned FLEURS en_us + AMI ihm. CT2 int8 CPU.
Gate CT2 otomatis: False. Target kualitas offline tercapai: False.
Lihat reports/final_test_metrics.csv dan package_status.json. Jika gate gagal, ini paket diagnostic.
Benchmark laptop, peninjauan transkrip, pengukuran streaming, dan CS domain belum otomatis terbukti.

## Windows PowerShell (Python 3.11 atau 3.12 disarankan untuk deployment)
Di folder hasil ekstraksi:
```
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe transcribe_benchmark.py
.\.venv\Scripts\python.exe transcribe_benchmark.py "C:\path\question.wav"
```
Benchmark menulis laptop_benchmark.json: warm CPU RTF < 0.5 adalah target, >= 1 belum secepat audio.
Referensi contoh validation ada di validation_samples/references.json. Contoh ini bukan CS test baru.
Linux/macOS: python3 -m venv .venv, lalu gunakan .venv/bin/python untuk perintah Python.
Jika sounddevice mengeluhkan PortAudio, pasang dependensi PortAudio OS tersebut dan cek izin mikrofon.

## WhisperLive dan pertanyaan mikrofon
Install Git dahulu. Sumber WhisperLive dipin ke commit f26bdd5294ace7d31020ca00e04e7b14c2b7d954:
```
.\.venv\Scripts\python.exe -m pip install -r requirements_live.txt
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip freeze > requirements_resolved.txt
.\.venv\Scripts\python.exe start_server.py
```
Terminal kedua, folder yang sama:
```
.\.venv\Scripts\python.exe live_questions.py
```
Tunggu ready/listening. Bicara, beri jeda singkat setelah kata terakhir, lalu Enter untuk Kirim.
Tidak ada timer 45 detik; server memiliki batas koneksi eksplisit 3600 detik. Setelah Kirim, flush ditunggu 30 detik.
Pertanyaan selanjutnya memakai koneksi baru, model server dipertahankan. Untuk VAD yang melewatkan suara pelan,
uji `live_questions.py --no-vad` dan tinjau WAV/hasilnya; perubahan ini bukan hasil evaluasi model baru.

Partial bersifat sementara; committed adalah segmen; final_turn adalah satu pertanyaan lengkap.
final_turn hanya diterbitkan sekali saat flush selesai dan teks tidak kosong. Jika incomplete, tidak diteruskan ke NLU.
live_sessions menyimpan audio dan event; periksa bahwa kata terakhir tidak hilang, hening tidak menjadi pertanyaan,
pengulangan ucapan tetap ada, dan giliran panjang tidak tercampur. Script ini menulis payload; endpoint NLU teman belum diisi.
Ukur median partial setelah onset speech dan p95 final setelah Kirim dari replay/rekaman: target 2 detik dan 3 detik.
Satu contoh saja belum cukup menghitung p95. Server/klien dan hardware mikrofon harus diuji di laptop.
