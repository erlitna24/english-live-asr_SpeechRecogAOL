import argparse, json, queue, threading, time, uuid, wave
from pathlib import Path
import sounddevice as sd
from whisper_live.client import StreamingTranscriptionClient, Client

class VerifiedFlushClient(StreamingTranscriptionClient):
    # Pinned WhisperLive close() tidak mengembalikan status timeout; adapter mencatatnya sebelum forced close.
    def flush(self, timeout=30):
        if self._closed or not self._client.recording:
            return False
        self._closed=True
        try:
            self._client.send_packet_to_server(Client.END_OF_AUDIO.encode('utf-8'))
            deadline=time.monotonic()+timeout
            while self._client.recording and time.monotonic()<deadline:
                time.sleep(.05)
            return not self._client.recording
        finally:
            self._client.close_websocket()

def make_turn(client_factory, audio_capture, folder, session_id, turn_id, use_vad=True):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    errors=[]; committed={}; pending=[None]; lock=threading.Lock(); stop=threading.Event()
    state={'closing':False,'unexpected_close':False,'capture_start':None,'first_partial_s':None}
    origin=time.perf_counter(); count=[0]; events=[]
    def log(event, **fields):
        record={'event':event,'elapsed_s':time.perf_counter()-origin,**fields}
        with lock: events.append(record)
        print(json.dumps(record,ensure_ascii=False),flush=True)
    def partial(text,segments):
        with lock:
            pending[0]=dict(segments[-1]) if segments else None
            if text and state['first_partial_s'] is None:
                state['first_partial_s']=time.perf_counter()-origin
        log('partial',text=text)
    def commit(text,segments):
        with lock:
            for seg in segments:
                key=(float(seg['start']),float(seg['end']))
                committed[key]=dict(seg)  # timeline identity; actual repeated text at later times is retained
                if pending[0] and float(seg['start'])<=float(pending[0]['start'])+.05 and float(seg['end'])>=float(pending[0]['end'])-.05:
                    pending[0]=None
        log('committed',text=text)
    def error(exc):
        errors.append(str(exc));stop.set();log('error',message=str(exc))
    def closed():
        if not state['closing']:
            state['unexpected_close']=True;stop.set()
        log('closed')
    client=client_factory(host='127.0.0.1',port=9090,lang='en',model='base.en',use_vad=use_vad,
        ready_timeout=60,on_session_started=lambda:log('ready'),on_partial_transcript=partial,
        on_committed_transcript=commit,on_error=error,on_close=closed)
    try:
        client.connect();state['capture_start']=time.perf_counter()-origin
        log('listening')
        try:
            audio_capture(client,stop,count,folder/'audio.wav',errors)
        except Exception as exc:
            errors.append(type(exc).__name__+': '+str(exc))
        state['closing']=True;log('finalizing');submitted=time.perf_counter()
        flushed=client.flush(timeout=30)
        with lock:
            complete=flushed and not errors and not state['unexpected_close'] and pending[0] is None
            text=' '.join(s['text'].strip() for _,s in sorted(committed.items())).strip()
        # final_turn emitted once per call, only when flush is complete and text exists.
        payload={'event':'final_turn' if complete and text else 'incomplete' if not complete else 'empty_turn',
                 'session_id':session_id,'turn_id':turn_id,'language':'en','text':text,
                 'is_complete':complete,'completion_reason':'manual_submit' if complete else 'flush_or_connection_failed',
                 'audio_duration_s':count[0]/16000,'asr_model_id':'fleurs_ami_base_en_v1',
                 'final_after_submit_s':time.perf_counter()-submitted}
        log(payload['event'],**{k:v for k,v in payload.items() if k!='event'})
        result={'payload':payload,'errors':errors,'events':events,
                'capture_start_s':state['capture_start'],'first_partial_s':state['first_partial_s'],
                'note':'Partial timing starts at capture; speech-onset latency requires inspection of saved audio.'}
        (folder/'turn.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
        return complete
    finally:
        if not client._closed:
            client.close(timeout=5)

def capture(client,stop,count,path,errors):
    chunks=queue.Queue(maxsize=100)
    def callback(data,frames,timing,status):
        if status: errors.append(str(status));stop.set()
        try: chunks.put_nowait(bytes(data))
        except queue.Full: errors.append('audio_queue_overflow');stop.set()
    threading.Thread(target=lambda:(input('Bicara, lalu Enter untuk Kirim pertanyaan: '),stop.set()),daemon=True).start()
    with wave.open(str(path),'wb') as audio:
        audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(16000)
        stream=sd.RawInputStream(samplerate=16000,channels=1,dtype='int16',blocksize=3200,callback=callback)
        stream.start()
        try:
            while not stop.is_set():
                try: data=chunks.get(timeout=.1)
                except queue.Empty: continue
                audio.writeframesraw(data);count[0]+=len(data)//2;client.send(data,pcm_format='int16')
        finally:
            stream.stop();stream.close()
        while not chunks.empty():
            data=chunks.get_nowait();audio.writeframesraw(data);count[0]+=len(data)//2
            client.send(data,pcm_format='int16')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--no-vad',action='store_true');args=parser.parse_args()
    session_id=uuid.uuid4().hex
    while True:
        turn_id=uuid.uuid4().hex
        folder=Path(__file__).parent/'live_sessions'/session_id/turn_id
        make_turn(VerifiedFlushClient,capture,folder,session_id,turn_id,use_vad=not args.no_vad)
        if input('Enter = pertanyaan baru (koneksi baru); ketik q = selesai: ').strip().lower()=='q':break

if __name__=='__main__':main()
