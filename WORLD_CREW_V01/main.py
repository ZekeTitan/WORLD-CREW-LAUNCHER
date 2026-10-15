"""WORLD CREW - Launcher for authorized Tenkaichi3Decomp releases."""
import json, os, sys, shutil, subprocess, threading, tempfile, urllib.request, zipfile, re, webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import datetime

VERSION='0.1.0'
DISCORD='https://discord.gg/sznrZU6dT5'
PORT_API='https://api.github.com/repos/z3xox/Tenkaichi3Decomp/releases/latest'
OWN_API='https://api.github.com/repos/ZekeTitan/WORLD-CREW-LAUNCHER/releases/latest'
OWN_RELEASES='https://github.com/ZekeTitan/WORLD-CREW-LAUNCHER/releases/latest'
BASE=Path(getattr(sys,'_MEIPASS',Path(__file__).parent))
DATA=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'WorldCrew'
DATA.mkdir(parents=True,exist_ok=True)
CONFIG=DATA/'config.json'
LOG=DATA/'worldcrew.log'
DEFAULT_PORT=DATA/'WorldCrewRuntime'/'Tenkaichi3Decomp'

def read_config():
    try: return json.loads(CONFIG.read_text(encoding='utf-8'))
    except (ValueError,OSError): return {}

class App:
    def __init__(self,root):
        self.root=root; self.cfg=read_config(); self.busy=False
        root.title('WORLD CREW | Launcher creado por Zeke')
        root.geometry('1280x720'); root.minsize(900,520); root.configure(bg='#10071b')
        self.canvas=tk.Canvas(root,highlightthickness=0,bg='#10071b'); self.canvas.pack(fill='both',expand=True)
        self.bg=tk.PhotoImage(file=str(BASE/'assets'/'launcher.png'))
        self.bg_ref=None; self.controls=[]
        self.status=tk.StringVar(value='Preparando WORLD CREW...')
        self.canvas.bind('<Configure>',self.draw)
        self.log('Iniciando WORLD CREW v'+VERSION)
        root.after(350,lambda:self.thread(self.check_on_start))

    def save(self): CONFIG.write_text(json.dumps(self.cfg,indent=2,ensure_ascii=False),encoding='utf-8')
    def log(self,msg):
        line=f'[{datetime.now():%H:%M:%S}] {msg}'
        with LOG.open('a',encoding='utf-8') as f: f.write(line+'\n')
        self.root.after(0,lambda:self.status.set(msg))

    def draw(self,event=None):
        w=self.canvas.winfo_width(); h=self.canvas.winfo_height()
        if w<10 or h<10:return
        from PIL import Image, ImageTk
        if not hasattr(self,'original'):self.original=Image.open(BASE/'assets'/'launcher.png').convert('RGB')
        self.bg_ref=ImageTk.PhotoImage(self.original.resize((w,h),Image.Resampling.LANCZOS))
        self.canvas.delete('all'); self.canvas.create_image(0,0,anchor='nw',image=self.bg_ref)
        # Interactive transparent hotspots over approved visual design.
        for x,y,ww,hh,cmd in [
            (0.76,0.018,.20,.075,self.open_discord), # blue-haired profile
            (.24,.44,.20,.10,self.play),
            (.18,.57,.18,.16,self.play),
            (.40,.57,.15,.16,self.add_game),
            (.04,.76,.27,.08,self.open_discord),
            (.06,.87,.26,.105,self.choose_iso),
            (.36,.87,.26,.105,self.open_port),
            (.68,.87,.28,.105,self.update_port),
            (.01,.14,.14,.045,self.show_log),
            (.01,.20,.14,.045,self.show_log),
            (.01,.26,.14,.045,self.update_port),
            (.01,.33,.14,.045,self.settings),
            (.01,.39,.14,.045,self.open_discord),
        ]:
            # Hover/click region; invisible in normal mode.
            r=self.canvas.create_rectangle(x*w,y*h,(x+ww)*w,(y+hh)*h,outline='',fill='')
            self.canvas.tag_bind(r,'<Button-1>',lambda e,fn=cmd:fn())
            self.canvas.tag_bind(r,'<Enter>',lambda e:self.canvas.config(cursor='hand2'))
            self.canvas.tag_bind(r,'<Leave>',lambda e:self.canvas.config(cursor=''))
        self.canvas.create_rectangle(0,h-23,w,h,fill='#11071d',outline='')
        self.canvas.create_text(12,h-12,anchor='w',text=self.status.get()[:145],fill='#e5baff',font=('Segoe UI',9))
        # Fixed explicit console entry point, regardless of background lettering.
        self.canvas.create_text(w-15,h-12,anchor='e',text='REGISTRO DEL SISTEMA ↗',fill='#e5baff',font=('Segoe UI',9,'bold'),tags='logs')
        self.canvas.tag_bind('logs','<Button-1>',lambda e:self.show_log())

    def thread(self,fn):
        if self.busy:return
        self.busy=True
        def runner():
            try:fn()
            except Exception as exc:self.log('ERROR: '+str(exc));self.root.after(0,lambda:messagebox.showerror('WORLD CREW',str(exc)))
            finally:self.busy=False
        threading.Thread(target=runner,daemon=True).start()

    def api(self,url):
        req=urllib.request.Request(url,headers={'User-Agent':'WorldCrewLauncher/'+VERSION,'Accept':'application/vnd.github+json'})
        with urllib.request.urlopen(req,timeout=25) as response:return json.load(response)

    def port_path(self):return Path(self.cfg.get('port_path',str(DEFAULT_PORT)))
    def exe(self):return self.port_path()/'Tenkaichi3Decomp.exe'
    def choose_iso(self):
        p=filedialog.askopenfilename(title='Selecciona tu ISO original de BT3',filetypes=[('Imagen de disco','*.iso'),('Todos','*.*')])
        if p:self.cfg['iso_path']=p;self.save();self.log('ISO seleccionada: '+Path(p).name)

    def open_discord(self):webbrowser.open(DISCORD);self.log('Abriendo servidor Discord')
    def open_port(self):
        p=self.port_path();p.mkdir(parents=True,exist_ok=True)
        if os.name=='nt':os.startfile(str(p))
        else:messagebox.showinfo('PORT LOCAL',str(p))
        self.log('Carpeta local: '+str(p))

    def show_log(self):
        top=tk.Toplevel(self.root);top.title('WORLD CREW — Registro del sistema');top.geometry('850x450');top.configure(bg='#120920')
        text=tk.Text(top,bg='#120920',fg='#d9baff',insertbackground='white',font=('Consolas',10),wrap='word');text.pack(fill='both',expand=True,padx=10,pady=10)
        text.insert('1.0',LOG.read_text(encoding='utf-8')[-60000:] if LOG.exists() else 'Sin eventos');text.config(state='disabled');text.see('end')

    def settings(self):
        if messagebox.askyesno('PORT LOCAL','¿Quieres seleccionar una carpeta de instalación existente?'):
            p=filedialog.askdirectory(title='Carpeta de Tenkaichi3Decomp')
            if p:self.cfg['port_path']=p;self.save();self.log('Port local configurado')

    def add_game(self):
        p=filedialog.askopenfilename(title='Selecciona el ejecutable de otro juego',filetypes=[('Ejecutables','*.exe')])
        if p:
            games=self.cfg.setdefault('other_games',[])
            if p not in games:games.append(p);self.save()
            self.log('Juego agregado: '+Path(p).name)
            messagebox.showinfo('Biblioteca','Juego registrado. Se añadirá a la biblioteca visual en una futura versión.')

    def play(self):
        if not self.exe().exists():
            if messagebox.askyesno('WORLD CREW','No se encontró el port. ¿Descargarlo desde GitHub?'):self.update_port()
            return
        if not (self.port_path()/'gamedata').exists():
            iso=self.cfg.get('iso_path','')
            if not iso or not Path(iso).is_file():
                self.choose_iso();iso=self.cfg.get('iso_path','')
            setup=self.port_path()/'Tenkaichi3Decomp-setup.exe'
            if not iso or not setup.exists():
                messagebox.showinfo('WORLD CREW','Selecciona una ISO y comprueba que el setup esté instalado.');return
            if messagebox.askyesno('Preparar juego','¿Abrir el instalador oficial con tu ISO local?'):
                subprocess.Popen([str(setup)],cwd=str(self.port_path()));self.log('Abriendo instalador oficial del port')
            return
        subprocess.Popen([str(self.exe())],cwd=str(self.port_path()))
        self.log('Juego iniciado')

    def check_on_start(self):
        self.log('Buscando instalación de Tenkaichi3Decomp...')
        if self.exe().exists():self.log('Port encontrado: '+str(self.port_path()))
        else:self.log('Port no instalado en WORLD CREW')
        try:
            release=self.api(PORT_API);tag=release.get('tag_name','desconocida')
            self.log('Última versión oficial del port: '+tag)
            if not self.exe().exists():
                self.root.after(0,lambda: self.offer_install(tag))
        except Exception as e:self.log('No se pudo consultar el port: '+str(e))
        try:
            own=self.api(OWN_API);tag=own.get('tag_name','')
            if tag and tag.lstrip('v')!=VERSION:self.root.after(0,lambda: self.offer_launcher_update(tag))
        except Exception:self.log('Aún no hay una release de WORLD CREW publicada o no hay conexión')

    def offer_install(self,tag):
        if messagebox.askyesno('Instalar Tenkaichi3Decomp',f'¿Descargar e instalar el port oficial {tag} en WORLD CREW?\n\nLa ISO se seleccionará después desde tu PC.'):
            self.update_port()

    def offer_launcher_update(self,tag):
        if messagebox.askyesno('Actualización WORLD CREW',f'Hay una nueva versión de WORLD CREW: {tag}.\n¿Abrir la descarga oficial?'):
            webbrowser.open(OWN_RELEASES)

    def update_port(self):self.thread(self.install_port)

    def install_port(self):
        release=self.api(PORT_API)
        tag=release.get('tag_name','')
        assets=release.get('assets',[])
        candidates=[a for a in assets if re.search(r'windows.*x64.*\.zip$|win.*64.*\.zip$',a.get('name',''),re.I)]
        if not candidates:raise RuntimeError('No se encontró un ZIP Windows x64 en la última release oficial.')
        asset=candidates[0];url=asset['browser_download_url'];name=asset['name']
        if not url.startswith('https://github.com/z3xox/Tenkaichi3Decomp/releases/download/'):
            raise RuntimeError('Origen de descarga inesperado.')
        self.log('Descargando '+name+' ('+tag+')...')
        with tempfile.TemporaryDirectory(prefix='worldcrew-') as tmp:
            zpath=Path(tmp)/'release.zip'
            req=urllib.request.Request(url,headers={'User-Agent':'WorldCrewLauncher/'+VERSION})
            with urllib.request.urlopen(req,timeout=45) as response,zpath.open('wb') as out:
                total=0
                while True:
                    block=response.read(1024*1024)
                    if not block:break
                    total+=len(block)
                    if total>700*1024*1024:raise RuntimeError('Archivo demasiado grande para una release del port.')
                    out.write(block)
            self.log('Descarga completada; verificando archivo ZIP...')
            stage=Path(tmp)/'stage';stage.mkdir()
            with zipfile.ZipFile(zpath) as z:
                entries=z.infolist()
                if sum(i.file_size for i in entries)>1200*1024*1024:raise RuntimeError('ZIP excede el límite de tamaño.')
                for i in entries:
                    rel=Path(i.filename.replace('\\','/'))
                    if rel.is_absolute() or '..' in rel.parts or ':' in i.filename:raise RuntimeError('Ruta insegura en ZIP')
                    # Only files/dirs, no symlinks.
                    if (i.external_attr>>16)&0o170000==0o120000:raise RuntimeError('ZIP contiene enlaces no permitidos')
                z.extractall(stage)
            roots=list(stage.rglob('Tenkaichi3Decomp.exe'))
            if not roots:raise RuntimeError('El ZIP no contiene Tenkaichi3Decomp.exe')
            source=roots[0].parent
            target=self.port_path();target.mkdir(parents=True,exist_ok=True)
            # Preserve game data, saves, and personal settings. Do not touch unrelated folders.
            protected={'gamedata','savedata','saves','textures','mods','bt3_settings.txt'}
            for item in source.iterdir():
                if item.name.lower() in protected and (target/item.name).exists():continue
                dest=target/item.name
                if item.is_dir():shutil.copytree(item,dest,dirs_exist_ok=True)
                else:shutil.copy2(item,dest)
            self.cfg['port_version']=tag;self.save()
            self.log('Port instalado/actualizado a '+tag+' en '+str(target))
            self.root.after(0,lambda:messagebox.showinfo('WORLD CREW','Port actualizado a '+tag+' correctamente.\nSelecciona tu ISO y pulsa JUGAR.'))

if __name__=='__main__':
    root=tk.Tk();app=App(root);root.mainloop()
