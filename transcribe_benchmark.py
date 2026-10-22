import argparse, json, math, time
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('audio', nargs='?', help='Audio yang akan ditranskripsi; kosong = benchmark contoh paket')
    parser.add_argument('--model', default=str(Path(__file__).parent/'ct2_model'))
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--repeat', type=int, default=3)
    args = parser.parse_args()
    if args.repeat < 1 or args.threads < 1:
        parser.error('repeat dan threads harus >= 1')
    paths = [Path(args.audio)] if args.audio else sorted((Path(__file__).parent/'validation_samples').glob('*.wav'))
    if not paths:
        parser.error('Tidak ada audio benchmark.')
    model = WhisperModel(args.model, device='cpu', compute_type='int8', cpu_threads=args.threads,
                        local_files_only=True)
    records = []
    for path in paths:
        waveform, rate = sf.read(path, dtype='float32', always_2d=True)
        waveform = waveform.mean(axis=1)
        if rate != 16000:
            factor = math.gcd(rate,16000)
            waveform = resample_poly(waveform,16000//factor,rate//factor).astype('float32')
        if not len(waveform) or not np.isfinite(waveform).all():
            raise ValueError('Audio invalid: '+str(path))
        def transcribe():
            segments,_ = model.transcribe(waveform, language='en', beam_size=3, temperature=0.0,
                    condition_on_previous_text=False, without_timestamps=True, vad_filter=False,
                    compression_ratio_threshold=None, log_prob_threshold=None, no_speech_threshold=None,
                    max_new_tokens=440)
            return ' '.join(s.text.strip() for s in segments).strip()
        transcribe()  # warm-up
        elapsed = []
        for _ in range(args.repeat):
            start=time.perf_counter(); text=transcribe(); elapsed.append(time.perf_counter()-start)
        duration=len(waveform)/16000
        records.append({'audio':path.name,'duration_s':duration,'prediction':text,
                        'median_inference_s':float(np.median(elapsed)),
                        'median_rtf':float(np.median(elapsed))/duration})
    report={'device':'cpu','compute_type':'int8','threads':args.threads,'records':records,
            'throughput_rtf':sum(r['median_inference_s'] for r in records)/sum(r['duration_s'] for r in records),
            'note':'Offline inference-only warm RTF; tidak mengukur latensi streaming.'}
    (Path(__file__).parent/'laptop_benchmark.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
