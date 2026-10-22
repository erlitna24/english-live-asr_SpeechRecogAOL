import os
# CPU int8 sesuai target, termasuk laptop yang kebetulan memiliki GPU.
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
from whisper_live.server import TranscriptionServer
base=Path(__file__).resolve().parent
model=base/'ct2_model'
if not (model/'model.bin').is_file():
    raise SystemExit('Model custom tidak ditemukan; ekstrak paket lengkap.')
TranscriptionServer().run('127.0.0.1',port=9090,backend='faster_whisper',
    faster_whisper_custom_model_path=str(model),single_model=True,max_clients=1,max_connection_time=3600)
