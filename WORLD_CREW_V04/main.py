"""WORLD CREW v0.2 — interactive launcher for user-supplied ISO and official port."""
import json, os, sys, re, shutil, subprocess, threading, tempfile, urllib.request, zipfile, webbrowser, queue, hashlib, time, math
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

VERSION='0.4.0'
DISCORD='https://discord.gg/sznrZU6dT5'
PORT_API='https://api.github.com/repos/z3xox/Tenkaichi3Decomp/releases/latest'
OWN_API='https://api.github.com/repos/ZekeTitan/WORLD-CREW-LAUNCHER/releases/latest'
BASE=Path(getattr(sys,'_MEIPASS',Path(__file__).resolve().parent))
DATA=Path(os.environ.get('LOCALAPPDATA',str(Path.home()))) / 'WorldCrew'
DATA.mkdir(parents=True,exist_ok=True)
CONFIG=DATA/'config.json'; LOG=DATA/'worldcrew.log'; DEFAULT_PORT=DATA/'WorldCrewRuntime'/'Tenkaichi3Decomp'
BG='#10091c'; PANEL='#20112e'; PANEL2='#2b173c'; PINK='#ff37d0'; CYAN='#51e9ff'; FG='#f9e9ff'; MUTED='#c8acd5'

def load_config():
    try:return json.loads(CONFIG.read_text(encoding='utf-8'))
    except (OSError,ValueError):return {}

def api(url):
    request=urllib.request.Request(url,headers={'User-Agent':'WorldCrew/'+VERSION,'Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(request,timeout=25) as response:return json.load(response)

class Launcher:
    def __init__(self,root):
        self.root=root;self.cfg=load_config();self.events=queue.Queue();self.busy=False;self.current='Inicio';self.latest=None
        self.status=tk.StringVar(value='WORLD CREW listo');self.progress=tk.DoubleVar(value=0);self.download_detail=tk.StringVar(value='Esperando descarga...');self.animation_frame=0;self.hero_label=None;self.hero_images=[];self.scroll_canvas=None
        root.title('WORLD CREW — Game Launcher');root.geometry('1280x800');root.minsize(1000,650);root.configure(bg=BG)
        self.images={};self.build_shell();self.navigate('Inicio')
        root.after(100,self.process_events);root.after(60,self.animate_logo)
        self.log('WORLD CREW v'+VERSION+' iniciado. Buscando instalación configurada.')
        self.run_task(self.check_versions)

    def log(self,text):
        line=f'[{datetime.now():%H:%M:%S}] {text}'
        with LOG.open('a',encoding='utf-8') as f:f.write(line+'\n')
        self.events.put(('status',text));self.events.put(('log',line))

    def process_events(self):
        try:
            while True:
                typ,val=self.events.get_nowait()
                if typ=='status':self.status.set(val)
                elif typ=='progress':self.progress.set(val)
                elif typ=='detail':self.download_detail.set(val)
                elif typ=='log' and hasattr(self,'log_box') and self.log_box.winfo_exists():
                    self.log_box.configure(state='normal');self.log_box.insert('end',val+'\n');self.log_box.see('end');self.log_box.configure(state='disabled')
                elif typ=='done':self.busy=False;self.refresh_current()
                elif typ=='info':messagebox.showinfo('WORLD CREW',val)
                elif typ=='error':messagebox.showerror('WORLD CREW',val)
        except queue.Empty:pass
        self.root.after(100,self.process_events)

    def animate_logo(self):
        # Gentle oscillation, limited to the decorative header; no external images or network requests.
        try:
            if self.hero_label is not None and self.hero_label.winfo_exists():
                self.animation_frame += 1
                self.hero_label.configure(image=self.hero_images[(self.animation_frame//2)%len(self.hero_images)]) if self.hero_images else None
        except tk.TclError:
            pass
        self.root.after(60,self.animate_logo)

    def run_task(self,fn):
        if self.busy:messagebox.showinfo('WORLD CREW','Ya hay una operación en curso.');return
        self.busy=True
        def worker():
            try:fn()
            except Exception as e:self.log('ERROR: '+str(e));self.events.put(('error',str(e)))
            finally:self.events.put(('done',None))
        threading.Thread(target=worker,daemon=True).start()

    def save(self):CONFIG.write_text(json.dumps(self.cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    def port(self):return Path(self.cfg.get('port_path',str(DEFAULT_PORT)))
    def exe(self):return self.port()/'Tenkaichi3Decomp.exe'

    def build_shell(self):
        self.sidebar=tk.Frame(self.root,bg='#170a25',width=205);self.sidebar.pack(side='left',fill='y');self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar,text='WORLD\nCREW',font=('Segoe UI',26,'bold'),fg=PINK,bg='#170a25',justify='center').pack(pady=(24,2))
        tk.Label(self.sidebar,text='GAME LAUNCHER',font=('Segoe UI',10,'bold'),fg=FG,bg='#170a25').pack(pady=(0,25))
        self.nav_buttons={}
        for title,ico in [('Inicio','⌂'),('Biblioteca','▣'),('Descargas','↓'),('Actualizaciones','↻'),('Ajustes','⚙'),('Soporte','?')]:
            b=tk.Button(self.sidebar,text=f'{ico}   {title.upper()}',font=('Segoe UI',11,'bold'),fg=FG,bg='#170a25',activebackground=PANEL2,activeforeground=PINK,bd=0,anchor='w',padx=20,pady=15,cursor='hand2',command=lambda t=title:self.navigate(t));b.pack(fill='x',padx=8,pady=2);self.nav_buttons[title]=b
        tk.Label(self.sidebar,text='WORLD CREW\nLauncher creado por Zeke\n© 2026',fg=MUTED,bg='#170a25',font=('Segoe UI',10),justify='left').pack(side='bottom',anchor='w',padx=17,pady=24)
        self.right=tk.Frame(self.root,bg=BG);self.right.pack(side='right',fill='both',expand=True)
        self.top=tk.Frame(self.right,bg='#170a25',height=48);self.top.pack(fill='x');self.top.pack_propagate(False)
        tk.Label(self.top,text='WORLD CREW',font=('Segoe UI',14,'bold'),bg='#170a25',fg=FG).pack(side='left',padx=22)
        tk.Button(self.top,text='🔵  Zeke  ● En línea  ↗ Discord',command=self.discord,bg='#261438',fg=CYAN,bd=0,font=('Segoe UI',10,'bold'),cursor='hand2').pack(side='right',padx=18,pady=7)
        self.viewport=tk.Frame(self.right,bg=BG);self.viewport.pack(fill='both',expand=True)
        self.scroll_canvas=tk.Canvas(self.viewport,bg=BG,highlightthickness=0)
        scrollbar=tk.Scrollbar(self.viewport,orient='vertical',command=self.scroll_canvas.yview)
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right',fill='y');self.scroll_canvas.pack(side='left',fill='both',expand=True)
        self.main=tk.Frame(self.scroll_canvas,bg=BG)
        self.scroll_window=self.scroll_canvas.create_window((0,0),window=self.main,anchor='nw')
        self.main.bind('<Configure>',lambda e:self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox('all')))
        self.scroll_canvas.bind('<Configure>',lambda e:self.scroll_canvas.itemconfigure(self.scroll_window,width=e.width))
        self.root.bind_all('<MouseWheel>',self.scroll_wheel)

        self.footer=tk.Frame(self.right,bg='#140b20',height=30);self.footer.pack(fill='x');self.footer.pack_propagate(False)
        tk.Label(self.footer,textvariable=self.status,bg='#140b20',fg=MUTED,anchor='w').pack(side='left',fill='x',expand=True,padx=12)
        tk.Button(self.footer,text='REGISTRO DEL SISTEMA ↗',command=lambda:self.navigate('Registro'),bg='#140b20',fg=CYAN,bd=0,cursor='hand2').pack(side='right',padx=10)

    def scroll_wheel(self,event):
        if self.scroll_canvas:self.scroll_canvas.yview_scroll(-int(event.delta/120),'units')
    def clear(self):
        if self.scroll_canvas:self.scroll_canvas.yview_moveto(0)

        for c in self.main.winfo_children():c.destroy()
        self.log_box=None
    def refresh_current(self):
        if self.current in ('Descargas','Actualizaciones','Ajustes','Biblioteca'):self.navigate(self.current)
    def navigate(self,page):
        self.current=page;self.clear()
        for t,b in self.nav_buttons.items():b.config(bg='#512063' if t==page else '#170a25',fg=CYAN if t==page else FG)
        getattr(self,'page_'+{'Inicio':'home','Biblioteca':'library','Descargas':'downloads','Actualizaciones':'updates','Ajustes':'settings','Soporte':'support','Registro':'logs'}[page])()

    def title(self,title,subtitle=''):
        tk.Label(self.main,text=title,font=('Segoe UI',25,'bold'),bg=BG,fg=FG).pack(anchor='w',padx=24,pady=(19,2))
        if subtitle:tk.Label(self.main,text=subtitle,font=('Segoe UI',11),bg=BG,fg=MUTED).pack(anchor='w',padx=25,pady=(0,15))
    def panel(self,parent=None):
        p=tk.Frame(parent or self.main,bg=PANEL,highlightbackground='#75348b',highlightthickness=1);return p
    def label(self,parent,text,color=FG,size=11,bold=False):
        w=tk.Label(parent,text=text,bg=PANEL,fg=color,font=('Segoe UI',size,'bold' if bold else 'normal'),anchor='w',justify='left',wraplength=660);w.pack(fill='x',padx=15,pady=5);return w
    def button(self,parent,text,command,primary=False):
        b=tk.Button(parent,text=text,command=command,bg=PINK if primary else '#402451',fg='#170a25' if primary else FG,activebackground='#fd8aea',bd=0,padx=12,pady=10,font=('Segoe UI',10,'bold'),cursor='hand2');b.pack(fill='x',padx=14,pady=(6,12));return b

    def page_home(self):
        hero=self.panel();hero.pack(fill='x',padx=18,pady=(14,8))
        # Decorative header image only: all controls are native interactive widgets.
        img=Image.open(BASE/'assets'/'launcher.png').convert('RGB');w,h=img.size
        img=img.crop((int(w*.16),0,w,int(h*.47)));img.thumbnail((1030,270))
        self.hero_images=[]
        for i in range(24):
            from PIL import ImageEnhance
            phase=math.sin(2*math.pi*i/24)
            frame=Image.new('RGB',(1040,282),PANEL)
            glow=ImageEnhance.Brightness(img).enhance(1.05+0.18*(phase+1)/2)
            frame.paste(glow,(int((1040-img.width)/2+12*phase),int((282-img.height)/2)))
            self.hero_images.append(ImageTk.PhotoImage(frame))
        self.hero_label=tk.Label(hero,image=self.hero_images[0],bg=PANEL);self.hero_label.pack(fill='x',padx=3,pady=3)
        self.title('MIS JUEGOS','Selecciona un juego para comenzar')
        row=tk.Frame(self.main,bg=BG);row.pack(fill='x',padx=20)
        card=self.panel(row);card.pack(side='left',fill='both',expand=True,padx=4)
        cover=Image.open(BASE/'assets'/'bt3.png');cover.thumbnail((150,130));self.images['bt3']=ImageTk.PhotoImage(cover)
        tk.Label(card,image=self.images['bt3'],bg=PANEL).pack(side='left',padx=14,pady=10)
        inner=tk.Frame(card,bg=PANEL);inner.pack(side='left',fill='both',expand=True)
        self.label(inner,'DRAGON BALL Z BUDOKAI TENKAICHI 3',CYAN,12,True)
        self.label(inner,'Tenkaichi3Decomp • Port para Windows',MUTED,10)
        self.button(inner,'▶  JUGAR AHORA',self.play,True)
        self.button(inner,'VER EN BIBLIOTECA',lambda:self.navigate('Biblioteca'))
        tools=tk.Frame(self.main,bg=BG);tools.pack(fill='x',padx=19,pady=(12,4))
        for heading,desc,btn,cmd in [('ISO','Selecciona tu archivo .ISO','SELECCIONAR ISO',self.choose_iso),('PORT LOCAL','Abre la carpeta del port','ABRIR CARPETA',self.open_port),('Actualizar deComp','Descarga e instala la última versión del port','ACTUALIZAR',self.confirm_update)]:
            box=self.panel(tools);box.pack(side='left',fill='both',expand=True,padx=4)
            self.label(box,heading,CYAN,12,True);self.label(box,desc,MUTED,9);self.button(box,btn,cmd,heading=='Actualizar deComp')
        community=self.panel();community.pack(fill='x',padx=23,pady=(15,30))
        self.label(community,'✦  ÚNETE A NUESTRO DISCORD  ✦',PINK,18,True)
        self.label(community,'Comunidad WORLD CREW • Novedades, ayuda y próximos juegos',CYAN,11)
        self.button(community,'ENTRAR AL DISCORD  ↗',self.discord,True)

    def page_library(self):
        self.title('BIBLIOTECA','Todos tus juegos en WORLD CREW')
        card=self.panel();card.pack(fill='x',padx=24,pady=8)
        self.label(card,'DRAGON BALL Z BUDOKAI TENKAICHI 3',CYAN,16,True)
        self.label(card,'Port: '+('Instalado' if self.exe().exists() else 'No instalado'),MUTED)
        self.button(card,'▶ JUGAR',self.play,True)
        self.button(card,'INSTALAR / ACTUALIZAR PORT',self.confirm_update)
        for p in self.cfg.get('other_games',[]):
            item=self.panel();item.pack(fill='x',padx=24,pady=5)
            self.label(item,Path(p).stem,CYAN,12,True)
            self.button(item,'▶ EJECUTAR',lambda path=p:self.launch_external(path))
        self.button(self.main,'+ AGREGAR JUEGO DESDE MI PC',self.add_game)

    def page_downloads(self):
        self.title('DESCARGAS','Instalación y progreso de los archivos oficiales')
        p=self.panel();p.pack(fill='x',padx=24,pady=10)
        self.label(p,'Tenkaichi3Decomp',CYAN,15,True)
        self.label(p,'Destino: '+str(self.port()),MUTED,10)
        ttk.Progressbar(p,variable=self.progress,maximum=100).pack(fill='x',padx=15,pady=10)
        tk.Label(p,textvariable=self.download_detail,bg=PANEL,fg=CYAN,font=('Segoe UI',10)).pack(anchor='w',padx=15,pady=(0,8))
        self.label(p,'El progreso se actualiza mientras se descarga el port.',MUTED,10)
        self.button(p,'DESCARGAR / ACTUALIZAR',self.confirm_update,True)
        self.button(self.main,'VER REGISTRO DEL SISTEMA',lambda:self.navigate('Registro'))

    def page_updates(self):
        self.title('ACTUALIZACIONES','Comprobación de versiones del port y de WORLD CREW')
        p=self.panel();p.pack(fill='x',padx=24,pady=8)
        self.label(p,'Tenkaichi3Decomp',CYAN,15,True)
        self.label(p,'Versión instalada: '+self.cfg.get('port_version','Sin registrar'),MUTED)
        self.label(p,'Versión oficial detectada: '+(self.latest or 'Aún no consultada'),MUTED)
        self.button(p,'ACTUALIZAR deComp',self.confirm_update,True)
        q=self.panel();q.pack(fill='x',padx=24,pady=8)
        self.label(q,'WORLD CREW v'+VERSION,CYAN,15,True)
        self.label(q,'Las versiones nuevas del launcher se publicarán en GitHub Releases.',MUTED)
        self.button(q,'COMPROBAR ACTUALIZACIONES',lambda:self.run_task(self.check_versions))
        self.button(q,'ABRIR RELEASES DE WORLD CREW',lambda:webbrowser.open('https://github.com/ZekeTitan/WORLD-CREW-LAUNCHER/releases'))

    def page_settings(self):
        self.title('AJUSTES','Personaliza las rutas y los juegos instalados')
        p=self.panel();p.pack(fill='x',padx=24,pady=10)
        self.label(p,'ISO actual: '+self.cfg.get('iso_path','No seleccionada'),MUTED,10)
        self.button(p,'SELECCIONAR ISO',self.choose_iso,True)
        self.label(p,'PORT LOCAL: '+str(self.port()),MUTED,10)
        self.button(p,'ELEGIR CARPETA DEL PORT',self.choose_port)
        self.button(p,'ABRIR CARPETA DEL PORT',self.open_port)
        self.button(p,'ABRIR CARPETA DE REGISTROS',lambda:os.startfile(str(DATA)) if os.name=='nt' else None)

    def page_support(self):
        self.title('SOPORTE','Ayuda, comunidad y diagnóstico')
        p=self.panel();p.pack(fill='x',padx=24,pady=10)
        self.label(p,'Comunidad oficial de WORLD CREW',CYAN,16,True)
        self.label(p,'Discord: '+DISCORD,MUTED)
        self.button(p,'ENTRAR AL SERVIDOR DE DISCORD',self.discord,True)
        self.button(p,'VER REGISTRO DE ERRORES',lambda:self.navigate('Registro'))
        self.label(p,'Si una descarga falla, abre Registro del sistema para ver el motivo.',MUTED,10)

    def page_logs(self):
        self.title('REGISTRO DEL SISTEMA','Operaciones de WORLD CREW; no inspecciona archivos personales')
        p=self.panel();p.pack(fill='both',expand=True,padx=24,pady=10)
        self.log_box=tk.Text(p,bg='#0b0715',fg=CYAN,insertbackground=FG,font=('Consolas',10),wrap='word',bd=0)
        self.log_box.pack(fill='both',expand=True,padx=10,pady=10)
        if LOG.exists():self.log_box.insert('1.0',LOG.read_text(encoding='utf-8')[-70000:])
        self.log_box.configure(state='disabled');self.log_box.see('end')

    def discord(self):webbrowser.open(DISCORD);self.log('Abriendo Discord')
    def choose_iso(self):
        p=filedialog.askopenfilename(title='Selecciona tu ISO local',filetypes=[('ISO','*.iso')])
        if p:self.cfg['iso_path']=p;self.save();self.log('ISO seleccionada: '+Path(p).name);self.refresh_current()
    def choose_port(self):
        p=filedialog.askdirectory(title='Selecciona la carpeta del port')
        if p:self.cfg['port_path']=p;self.save();self.log('Carpeta del port configurada: '+p);self.refresh_current()
    def open_port(self):
        p=self.port();p.mkdir(parents=True,exist_ok=True)
        if os.name=='nt':os.startfile(str(p))
        else:messagebox.showinfo('PORT LOCAL',str(p))
        self.log('Abriendo PORT LOCAL: '+str(p))
    def add_game(self):
        p=filedialog.askopenfilename(title='Selecciona el EXE del juego',filetypes=[('Ejecutable Windows','*.exe')])
        if p:
            games=self.cfg.setdefault('other_games',[])
            if p not in games:games.append(p);self.save()
            self.log('Juego agregado: '+Path(p).name);self.navigate('Biblioteca')
    def launch_external(self,p):
        if not Path(p).is_file():messagebox.showerror('WORLD CREW','No se encontró ese ejecutable.');return
        subprocess.Popen([p],cwd=str(Path(p).parent));self.log('Juego iniciado: '+Path(p).name)
    def play(self):
        target=self.port(); exe=self.exe()
        if not exe.is_file():
            if messagebox.askyesno('WORLD CREW','Falta el port. ¿Descargar la versión oficial?'):self.confirm_update()
            return
        if not (target/'gamedata').is_dir():
            messagebox.showwarning('Faltan datos del juego','No existe la carpeta gamedata en el port.\n\nPrepara los datos con tu propia ISO siguiendo las instrucciones oficiales. No se puede iniciar hasta completar la preparación.')
            self.log('No se inicia: falta gamedata en '+str(target));return
        self.log('Iniciando juego desde '+str(target))
        try:
            # Ejecutar desde la carpeta del port; no mover ni copiar solo el EXE.
            process=subprocess.Popen([str(exe)],cwd=str(target),stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            self.log('Proceso iniciado PID '+str(process.pid))
            def monitor():
                try:
                    result=process.wait()
                    self.log('El juego terminó con código '+str(result))
                    if result:self.events.put(('error','El juego terminó con error '+str(result)+'; revisa el registro y comprueba los archivos del port.'))
                except Exception as exc:self.log('Error supervisando el juego: '+str(exc))
            threading.Thread(target=monitor,daemon=True).start()
        except OSError as exc:
            self.log('Error iniciando el juego: '+str(exc));messagebox.showerror('No se pudo iniciar',str(exc))

    def check_versions(self):
        self.log('Buscando el port en la ruta configurada: '+str(self.port()))
        self.log('Port detectado' if self.exe().exists() else 'Port no encontrado en la ruta configurada')
        try:
            release=api(PORT_API);self.latest=release.get('tag_name','desconocida');self.log('Versión oficial de deComp: '+self.latest)
            if not self.exe().exists():self.events.put(('info','No se detectó el port. Puedes instalarlo desde Descargas o Actualizaciones.'))
        except Exception as e:self.log('No se pudo consultar deComp: '+str(e))
        try:
            release=api(OWN_API);tag=release.get('tag_name','')
            if tag and tag.lstrip('v')!=VERSION:self.log('Nueva versión de WORLD CREW disponible: '+tag)
        except Exception:self.log('No hay release de WORLD CREW disponible o falló la conexión')

    def confirm_update(self):
        if not messagebox.askyesno('Actualizar deComp','¿Descargar e instalar la última versión oficial de Tenkaichi3Decomp?\n\nSe conservarán las carpetas de datos protegidas y la ISO local.'):return
        self.navigate('Descargas');self.progress.set(0);self.run_task(self.install_port)

    def install_port(self):
        release=api(PORT_API);tag=release.get('tag_name','')
        assets=release.get('assets',[])
        candidates=[a for a in assets if re.search(r'(windows.*x64|win.*64).*\.zip$',a.get('name',''),re.I)]
        if not candidates:raise RuntimeError('La última release no incluye un ZIP Windows x64 reconocible. Revisa GitHub antes de instalar.')
        asset=candidates[0];url=asset.get('browser_download_url','');name=asset['name']
        if not url.startswith('https://github.com/z3xox/Tenkaichi3Decomp/releases/download/'):
            raise RuntimeError('El enlace de descarga no corresponde al repositorio oficial.')
        self.log('Descargando '+name+' ('+tag+')');self.events.put(('detail','Conectando con GitHub...'))
        with tempfile.TemporaryDirectory(prefix='worldcrew-') as tmp:
            archive=Path(tmp)/'release.zip';req=urllib.request.Request(url,headers={'User-Agent':'WorldCrew/'+VERSION})
            with urllib.request.urlopen(req,timeout=50) as response,archive.open('wb') as out:
                size=int(response.headers.get('Content-Length','0') or '0');total=0;started=time.monotonic();last_update=0;last_log_step=-1
                while True:
                    chunk=response.read(1024*512)
                    if not chunk:break
                    total+=len(chunk)
                    if total>900*1024*1024:raise RuntimeError('La descarga supera el límite permitido.')
                    out.write(chunk)
                    now=time.monotonic()
                    if now-last_update>=0.25:
                        speed=(total/1048576)/max(now-started,0.1)
                        pct=total/size*100 if size else 0
                        amount=f'{total/1048576:.1f} / {size/1048576:.1f} MB' if size else f'{total/1048576:.1f} MB'
                        self.events.put(('detail',f'Descargando {name} • {amount} • {speed:.1f} MB/s'+(f' • {pct:.0f}%' if size else '')))
                        if size:self.events.put(('progress',min(85,pct*.85)))
                        step=int(pct//10) if size else int(total//(20*1048576))
                        if step>last_log_step:self.log('Descarga: '+(f'{pct:.0f}%' if size else amount));last_log_step=step
                        last_update=now
            self.events.put(('progress',88));self.events.put(('detail','Descarga completa. Verificando el archivo ZIP...'));self.log('Descarga completada. Verificando el ZIP.')
            stage=Path(tmp)/'stage';stage.mkdir()
            with zipfile.ZipFile(archive) as z:
                entries=z.infolist()
                if sum(i.file_size for i in entries)>1500*1024*1024:raise RuntimeError('ZIP demasiado grande.')
                for i in entries:
                    rel=Path(i.filename.replace('\\','/'))
                    if rel.is_absolute() or '..' in rel.parts or ':' in i.filename:raise RuntimeError('Ruta insegura dentro del ZIP.')
                    if ((i.external_attr>>16)&0o170000)==0o120000:raise RuntimeError('El ZIP contiene enlaces simbólicos.')
                self.events.put(('progress',91));self.events.put(('detail','Extrayendo archivos del port...'));self.log('Extrayendo archivos oficiales...');z.extractall(stage)
            matches=list(stage.rglob('Tenkaichi3Decomp.exe'))
            if not matches:raise RuntimeError('No se encontró el ejecutable oficial en el ZIP.')
            source=matches[0].parent;target=self.port();target.mkdir(parents=True,exist_ok=True);self.events.put(('progress',96));self.events.put(('detail','Instalando archivos y conservando datos locales...'));self.log('Instalando port en '+str(target))
            protected={'gamedata','savedata','saves','textures','mods','bt3_settings.txt'}
            # Eliminar versiones antiguas solo de archivos distribuidos por el release,
            # sin borrar archivos personales o datos preparados por el usuario.
            for item in source.iterdir():
                dest=target/item.name
                if item.name.lower() in protected and dest.exists():continue
                if item.is_dir():shutil.copytree(item,dest,dirs_exist_ok=True)
                else:shutil.copy2(item,dest)
            self.cfg['port_version']=tag;self.save();self.events.put(('progress',100))
            self.events.put(('detail','Instalación terminada • '+tag));self.log('Port instalado/actualizado a '+tag);self.events.put(('info','Port actualizado correctamente a '+tag))

if __name__=='__main__':
    root=tk.Tk();Launcher(root);root.mainloop()
