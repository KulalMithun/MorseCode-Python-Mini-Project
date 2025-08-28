import tkinter as tk
from tkinter import messagebox, Toplevel, filedialog
import time, threading, queue, math, wave
from array import array

try:
    import pyaudio, numpy as np, matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    LIBS = True
except ImportError:
    import pyaudio, numpy as np, matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    LIBS = False
    print("Missing libs: microphone/visualization disabled. Install pyaudio numpy matplotlib")

pygame = None
try:
    import pygame
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init(); pygame.mixer.init()
except Exception:
    pygame = None

MORSE = {'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....',
         'I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.',
         'Q':'--.-','R':'.-.','S':'...','T':'-','U':'..-','V':'...-','W':'.--','X':'-..-',
         'Y':'-.--','Z':'--..','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....',
         '6':'-....','7':'--...','8':'---..','9':'----.','0':'-----',',':'--..--','.':'.-.-.-',
         '?':'..--..','/':'-..-.','-':'-....-','(':'-.--.',')':'-.--.-',' ':'/'}
REV = {v:k for k,v in MORSE.items()}
DOT = 0.18
DASH = DOT*3
INTRA = DOT
INTER = DOT*3
WORD = DOT*7
SR = 44100

def tone_samples(freq,dur,rate=SR):
    n=int(rate*dur);A=2**15-1
    return array('h',[int(A*math.sin(2*math.pi*i*freq/rate)) for i in range(n)])

_dot_sound=_dash_sound=None
if pygame:
    def _mk(f,d):
        return pygame.mixer.Sound(buffer=tone_samples(f,d).tobytes())
    _dot_sound,_dash_sound=_mk(880,DOT),_mk(880,DASH)

def save_morse_audio(morse,fn):
    try:
        with wave.open(fn,'wb') as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            silence = array('h',[0]*int(SR*0.5))
            w.writeframes(silence.tobytes())
            for s in morse:
                if s=='.':
                    w.writeframes(tone_samples(880,DOT).tobytes())
                    w.writeframes(array('h',[0]*int(SR*INTRA)).tobytes())
                elif s=='-':
                    w.writeframes(tone_samples(880,DASH).tobytes())
                    w.writeframes(array('h',[0]*int(SR*INTRA)).tobytes())
                elif s==' ':
                    w.writeframes(array('h',[0]*int(SR*(INTER-INTRA))).tobytes())
                elif s=='/':
                    w.writeframes(array('h',[0]*int(SR*(WORD-INTRA))).tobytes())
            w.writeframes(silence.tobytes())
        return True
    except Exception as e:
        messagebox.showerror("Error",f"Save failed: {e}"); return False

def detect_morse_from_audio(audio,rate):
    try:
        if not LIBS: return ""
        a = audio.astype(np.float32) if audio.dtype!=np.float32 else audio
        frame_ms=10; hop_ms=10
        fs=max(1,int(rate*frame_ms/1000)); hop=max(1,int(rate*hop_ms/1000))
        env=[]
        for i in range(0,len(a)-fs+1,hop):
            f=a[i:i+fs]; env.append(np.sqrt(np.mean(f*f)))
        if not env: return ""
        env=np.array(env)
        noise=np.percentile(env,40); th=max(1e-7,noise*int(2.0)); mask=env>th
        starts=[]; ends=[]
        prev=False
        for i,v in enumerate(mask):
            if v and not prev: starts.append(i)
            if (not v) and prev: ends.append(i-1)
            prev=v
        if mask[-1]: ends.append(len(mask)-1)
        if not starts: return ""
        segs=[((e-s+1)*hop)/rate for s,e in zip(starts,ends)]
        sils=[((starts[i]-ends[i-1])*hop)/rate for i in range(1,len(starts))]
        md=min(segs); thresh=max(0.08,md*2.2)
        pieces=[]
        for i,d in enumerate(segs):
            pieces.append('.' if d<thresh else '-')
            if i<len(sils):
                sd=sils[i]
                if sd>md*5.0 or sd>WORD*0.9: pieces.append(' / ')
                elif sd>md*2.0 or sd>INTER*0.9: pieces.append(' ')
        return "".join(pieces).strip().replace('  ',' ')
    except Exception as e:
        print("detect err",e); return ""

def load_morse_audio(fn):
    try:
        with wave.open(fn,'rb') as w:
            nch,sw,rate,frames=w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()
            data=w.readframes(frames)
        if not LIBS: messagebox.showerror("Error","numpy required to decode audio"); return None
        dtype=np.int16 if sw==2 else np.int32
        audio=np.frombuffer(data,dtype=dtype)
        if nch>1: audio=audio.reshape(-1,nch).mean(axis=1)
        audio_f=audio.astype(np.float32)/np.iinfo(dtype).max
        return detect_morse_from_audio(audio_f,rate)
    except Exception as e:
        messagebox.showerror("Error",f"Load failed: {e}"); return None

def play_beep(ms):
    if not pygame or not _dot_sound or not _dash_sound:
        time.sleep(ms/1000.0); return
    s = _dot_sound if ms<=int(DOT*1000*1.5) else _dash_sound
    s.play(); pygame.time.wait(ms)

class MorseCodeApp:
    def __init__(self,root):
        self.root=root; root.title("Morse Code Tool"); root.geometry("550x400"); self.q=queue.Queue()
        self.is_listening=False; self.active=root; self.setup_main_menu(); root.after(40,self.process_q)

    def setup_main_menu(self):
        for w in self.active.winfo_children(): w.destroy()
        self.active=self.root; f=tk.Frame(self.root,bg="#f0f0f0",padx=20,pady=20); f.pack(expand=True,fill="both")
        tk.Label(f,text="Morse Code Tool",font=("Helvetica",24,"bold"),bg="#f0f0f0").pack(pady=10)
        tk.Button(f,text="Create Morse Code",command=self.open_creator,font=("Helvetica",14),width=25,bg="#4CAF50",fg="white").pack(pady=8)
        tk.Button(f,text="Read Morse Code",command=self.open_reader_choice,font=("Helvetica",14),width=25,bg="#2196F3",fg="white").pack(pady=8)
        tk.Button(f,text="Exit",command=self.root.quit,font=("Helvetica",14),width=25,bg="#f44336",fg="white").pack(pady=8)

    def import_audio_file(self):
        fn=filedialog.askopenfilename(title="Select Morse Code Audio File",filetypes=[("WAV","*.wav"),("All","*.*")])
        if fn:
            m=load_morse_audio(fn)
            if m: self.show_import_results(m)

    def show_import_results(self,m):
        w=Toplevel(self.root); w.title("Imported Morse Code"); w.geometry("500x300")
        f=tk.Frame(w,padx=20,pady=20); f.pack(expand=True,fill="both")
        tk.Label(f,text="Decoded Morse Code:",font=("Helvetica",14)).pack(anchor="w")
        t=tk.Text(f,height=4,width=50,font=("Courier",12)); t.insert(tk.END,m); t.config(state="disabled"); t.pack(pady=5,fill="x")
        tk.Label(f,text="Translated Text:",font=("Helvetica",14)).pack(anchor="w",pady=(10,0))
        tt=tk.Text(f,height=4,width=50,font=("Helvetica",12)); tt.insert(tk.END,self.morse_to_text(m)); tt.config(state="disabled"); tt.pack(pady=5,fill="x")
        tk.Button(f,text="Close",command=w.destroy).pack(pady=10)

    def open_creator(self):
        self.active=Toplevel(self.root); self.active.title("Create Morse Code"); self.active.geometry("540x480"); self.root.withdraw()
        f=tk.Frame(self.active,padx=16,pady=12); f.pack(expand=True,fill="both")
        tk.Label(f,text="Enter Text:",font=("Helvetica",14)).pack(anchor="w")
        self.text_entry=tk.Text(f,height=5,width=60,font=("Helvetica",12)); self.text_entry.pack(pady=6)
        tk.Button(f,text="Convert & Play",command=self.start_conversion_thread,font=("Helvetica",12,"bold")).pack(pady=8)
        tk.Label(f,text="Morse Code Output:",font=("Helvetica",14)).pack(anchor="w",pady=(10,0))
        self.morse_output_text=tk.Text(f,height=6,width=60,font=("Courier",12),state="disabled"); self.morse_output_text.pack(pady=6)
        bf=tk.Frame(f); bf.pack(pady=10)
        tk.Button(bf,text="Save as Audio",command=self.save_audio,font=("Helvetica",12),bg="#FF9800",fg="white").pack(side="left",padx=5)
        tk.Button(bf,text="Back to Main Menu",command=lambda:self.go_back(self.active)).pack(side="right",padx=5)

    def save_audio(self):
        morse=self.morse_output_text.get("1.0",tk.END).strip()
        if not morse: messagebox.showwarning("No Morse Code","Please generate Morse code first."); return
        fn=filedialog.asksaveasfilename(title="Save Morse Code Audio",defaultextension=".wav",filetypes=[("WAV files","*.wav")])
        if fn and save_morse_audio(morse,fn): messagebox.showinfo("Success",f"Morse code audio saved to {fn}")

    def start_conversion_thread(self):
        txt=self.text_entry.get("1.0",tk.END).strip()
        if not txt: messagebox.showwarning("Input Error","Please enter some text."); return
        morse=" ".join([MORSE.get(ch,'') for ch in txt.upper() if ch in MORSE])
        self.morse_output_text.config(state="normal"); self.morse_output_text.delete("1.0",tk.END); self.morse_output_text.insert(tk.END,morse); self.morse_output_text.config(state="disabled")
        threading.Thread(target=self.play_morse_sequence,args=(morse,),daemon=True).start()

    def play_morse_sequence(self,morse):
        dot_ms,dash_ms=int(DOT*1000),int(DASH*1000)
        for s in morse:
            if s=='.': play_beep(dot_ms); time.sleep(INTRA)
            elif s=='-': play_beep(dash_ms); time.sleep(INTRA)
            elif s==' ': time.sleep(INTER-INTRA)
            elif s=='/': time.sleep(WORD-INTER)

    def open_reader_choice(self):
        self.active=Toplevel(self.root); self.active.title("Read Morse Code"); self.active.geometry("420x300"); self.root.withdraw()
        f=tk.Frame(self.active,padx=20,pady=30); f.pack(expand=True)
        tk.Label(f,text="How do you want to input Morse?",font=("Helvetica",16,"bold")).pack(pady=8)
        tk.Button(f,text="From Text",command=self.open_text_reader,font=("Helvetica",12),width=28).pack(pady=6)
        tk.Button(f,text="Manual Input",command=self.open_manual_reader,font=("Helvetica",12),width=28).pack(pady=6)
        tk.Button(f,text="Import Audio File",command=self.import_audio_file,font=("Helvetica",12),width=28).pack(pady=6)
        tk.Button(f,text="Back to Main Menu",command=lambda:self.go_back(self.active)).pack(pady=8)

    def open_mic_reader(self):
        if not LIBS:
            messagebox.showwarning("Unavailable","Microphone/visualization libraries not installed"); return
        try: self.active.destroy()
        except: pass
        self.active=Toplevel(self.root); self.active.title("Read from Microphone"); self.active.geometry("600x650"); self.root.withdraw()
        f=tk.Frame(self.active,padx=16,pady=12); f.pack(expand=True,fill="both")
        self.fig,self.ax=plt.subplots(); self.fig.patch.set_facecolor('#f0f0f0'); self.ax.set_facecolor('#000000')
        self.ax.set_ylim(-32768,32767); self.ax.set_xticks([]); self.ax.set_yticks([])
        self.x_data=np.arange(1024*2)
        self.line,=self.ax.plot(self.x_data,np.zeros(1024*2))
        self.plot_canvas=FigureCanvasTkAgg(self.fig,master=f); self.plot_canvas.get_tk_widget().pack(fill="both",expand=True)
        self.mic_morse_str=tk.StringVar(); self.mic_english_str=tk.StringVar()
        self.status_label=tk.Label(f,text="Status: Not Listening",font=("Helvetica",12)); self.status_label.pack(pady=5)
        self.listen_button=tk.Button(f,text="Start Listening",command=self.toggle_listening,font=("Helvetica",12,"bold"),bg="#4CAF50",fg="white"); self.listen_button.pack(pady=10)
        tk.Label(f,text="Detected Morse Code:",font=("Helvetica",14)).pack(pady=(10,0))
        tk.Entry(f,textvariable=self.mic_morse_str,font=("Courier",16),state="readonly").pack(fill="x",pady=5)
        tk.Label(f,text="Translated Text:",font=("Helvetica",14)).pack(pady=(10,0))
        tk.Entry(f,textvariable=self.mic_english_str,font=("Helvetica",16,"bold"),state="readonly").pack(fill="x",pady=5)
        tk.Button(f,text="Back to Main Menu",command=self.go_back_mic).pack(pady=20)

    def toggle_listening(self):
        if self.is_listening:
            self.is_listening=False; self.listen_button.config(text="Start Listening",bg="#4CAF50")
            if self.listening_thread: self.listening_thread.join()
            final=self.mic_morse_str.get(); self.mic_english_str.set(self.morse_to_text(final))
        else:
            self.is_listening=True; self.mic_morse_str.set(""); self.mic_english_str.set("")
            self.listen_button.config(text="Stop Listening",bg="#f44336")
            self.listening_thread=threading.Thread(target=self.process_audio_stream,daemon=True); self.listening_thread.start()

    def process_audio_stream(self):
        if not LIBS: return
        CHUNK=1024*2; FORMAT=pyaudio.paInt16; CHANNELS=1; RATE=44100
        TH=600; DOT_THR=DOT*1.8
        p=pyaudio.PyAudio(); stream=p.open(format=FORMAT,channels=CHANNELS,rate=RATE,input=True,frames_per_buffer=CHUNK)
        self.q.put(('status','Listening...'))
        is_beep=False; last_time=time.time()
        noise=100; alpha=0.9
        while self.is_listening:
            try:
                raw=stream.read(CHUNK,exception_on_overflow=False); data=np.frombuffer(raw,dtype=np.int16)
                curr_noise=np.sqrt(np.mean(data**2)); noise=alpha*noise+(1-alpha)*curr_noise
                adaptive=max(TH,noise*2)
                vol=np.sqrt(np.mean(data**2)); self.q.put(('update_wave',data))
                if vol>adaptive:
                    if not is_beep:
                        is_beep=True
                        sdur=time.time()-last_time
                        if sdur>WORD*0.8: self.q.put(('add_symbol',' / '))
                        elif sdur>INTER*0.8: self.q.put(('add_symbol',' '))
                        last_time=time.time()
                else:
                    if is_beep:
                        is_beep=False
                        dur=time.time()-last_time
                        self.q.put(('add_symbol','.' if dur<DOT_THR else '-'))
                        last_time=time.time()
            except IOError:
                pass
        stream.stop_stream(); stream.close(); p.terminate()
        self.q.put(('status','Not Listening')); self.q.put(('update_wave',np.zeros(CHUNK)))

    def go_back_mic(self):
        if self.is_listening: self.is_listening=False
        self.go_back(self.active)

    def process_q(self):
        try:
            while True:
                task=self.q.get_nowait()
                active_ok=(hasattr(self,'active') and self.active.winfo_exists() and self.active.title()=="Read from Microphone" and hasattr(self,'mic_morse_str'))
                if not active_ok: continue
                if task[0]=='status': self.status_label.config(text=f"Status: {task[1]}")
                elif task[0]=='add_symbol':
                    cur=self.mic_morse_str.get(); self.mic_morse_str.set(cur+task[1])
                    if task[1].strip()=='':
                        self.mic_english_str.set(self.morse_to_text(self.mic_morse_str.get()))
                elif task[0]=='update_wave':
                    self.line.set_ydata(task[1]); self.plot_canvas.draw()
        except queue.Empty:
            pass
        except Exception as e:
            print("GUI queue error",e)
        finally:
            self.root.after(30,self.process_q)

    def morse_to_text(self,m):
        words=m.strip().split(' / ')
        return " ".join("".join(REV.get(ch,'?') for ch in w.split()) for w in words)

    def go_back(self,win):
        try: win.destroy()
        except: pass
        self.root.deiconify(); self.active=self.root; self.setup_main_menu()

    def open_text_reader(self):
        try: self.active.destroy()
        except: pass
        self.active=Toplevel(self.root); self.active.title("Read from Morse Text"); self.active.geometry("540x420")
        f=tk.Frame(self.active,padx=16,pady=12); f.pack(expand=True,fill="both")
        tk.Label(f,text="Enter Morse (spaces between letters, '/' between words):",font=("Helvetica",12)).pack(anchor="w")
        self.morse_entry=tk.Text(f,height=5,width=60,font=("Courier",12)); self.morse_entry.pack(pady=6)
        self.morse_entry.insert(tk.END,"")
        tk.Button(f,text="Translate",command=self.translate_morse_text,font=("Helvetica",12,"bold")).pack(pady=8)
        tk.Label(f,text="Translated Text:",font=("Helvetica",14)).pack(anchor="w",pady=(10,0))
        self.english_output_text=tk.Text(f,height=6,width=60,font=("Helvetica",12),state="disabled"); self.english_output_text.pack(pady=6)
        tk.Button(f,text="Back to Main Menu",command=lambda:self.go_back(self.active)).pack(pady=8)

    def translate_morse_text(self):
        self.english_output_text.config(state="normal"); self.english_output_text.delete("1.0",tk.END)
        self.english_output_text.insert(tk.END,self.morse_to_text(self.morse_entry.get("1.0",tk.END))); self.english_output_text.config(state="disabled")

    def open_manual_reader(self):
        try: self.active.destroy()
        except: pass
        self.active=Toplevel(self.root); self.active.title("Manual Morse Input"); self.active.geometry("540x420")
        f=tk.Frame(self.active,padx=16,pady=12); f.pack(expand=True,fill="both")
        self.manual_morse_str=tk.StringVar()
        tk.Label(f,text="Your Morse Input:",font=("Helvetica",14)).pack()
        tk.Entry(f,textvariable=self.manual_morse_str,font=("Courier",16),state="readonly",justify="center").pack(pady=6,fill="x")
        btnf=tk.Frame(f); btnf.pack(pady=8)
        tk.Button(btnf,text="Dot (.)",command=lambda:self.add_manual_symbol('.'),width=12).pack(side="left",padx=6)
        tk.Button(btnf,text="Dash (-)",command=lambda:self.add_manual_symbol('-'),width=12).pack(side="left",padx=6)
        tk.Button(f,text="Next Letter (Space)",command=lambda:self.add_manual_symbol(' ')).pack(pady=6)
        tk.Button(f,text="Next Word (Slash)",command=lambda:self.add_manual_symbol(' / ')).pack(pady=6)
        tk.Button(f,text="Translate",command=self.translate_manual_morse,font=("Helvetica",12,"bold")).pack(pady=8)
        self.manual_english_output=tk.Label(f,text="",font=("Helvetica",16,"bold"),wraplength=500); self.manual_english_output.pack(pady=8)
        tk.Button(f,text="Clear",command=lambda:self.manual_morse_str.set("")).pack(side="left",padx=18)
        tk.Button(f,text="Back to Main Menu",command=lambda:self.go_back(self.active)).pack(side="right",padx=18)

    def add_manual_symbol(self,s): self.manual_morse_str.set(self.manual_morse_str.get()+s)
    def translate_manual_morse(self): self.manual_english_output.config(text=self.morse_to_text(self.manual_morse_str.get()))

if __name__=="__main__":
    root=tk.Tk(); app=MorseCodeApp(root); root.mainloop()
    if pygame: pygame.quit()
