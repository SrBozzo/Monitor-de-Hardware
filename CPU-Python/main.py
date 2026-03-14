import customtkinter as ctk
import psutil
import platform
import math
import threading
import subprocess
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import webbrowser

# Importa as bibliotecas do Windows
try:
    import wmi
    import pythoncom
    has_wmi = True
except ImportError:
    has_wmi = False

# Configuração do tema principal
ctk.set_appearance_mode("Dark")  
ctk.set_default_color_theme("blue")  

def format_size(size_bytes):
    if size_bytes == 0: return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def get_color_by_percent(percent):
    if percent < 60: return "#2FA572"
    elif percent < 85: return "#E0A800"
    else: return "#DC3545"

class MonitorHardwareApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Monitor de Hardware - Python Edition")
        self.geometry("1000x750")

        # Tenta carregar o ícone personalizado (precisa estar na mesma pasta do main.py)
        try:
            self.iconbitmap("logo.ico")
        except:
            pass

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==========================================================
        # 🧠 BASE DE DADOS EM TEMPO REAL
        # ==========================================================
        self.hw_data = {
            "uptime": "",
            "cpu_pct": 0, "cpu_freq": 0, "cpu_temp": "N/A", "cpu_cores": [],
            "ram_pct": 0, "ram_used": 0, "ram_total": 0,
            "gpu_ok": False, "gpu_nome": "", "gpu_uso": 0, "gpu_temp": "N/A", "vram_usada": 0, "vram_total": 0, "gpu_freq": 0, "gpu_power": 0, "gpu_fan": 0,
            "net_down": 0, "net_up": 0,
            "discos": {},
            "top_procs": []
        }
        
        self.running = True
        threading.Thread(target=self.motor_de_dados_em_segundo_plano, daemon=True).start()

        self.tela_atual = ""
        self.ui_elements = {} 
        self.overlay_ativo = False
        self.overlay_window = None

        # --- Menu Lateral ---
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        # A linha 10 vai expandir, empurrando os botões de Exportar e GitHub para o fundo
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Meu PC Info", font=ctk.CTkFont(size=22, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 20))

        self.btn_overlay = ctk.CTkButton(self.sidebar_frame, text="🎮 Overlay Gamer", command=self.toggle_overlay, fg_color="#D35400", hover_color="#A04000")
        self.btn_overlay.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")

        botoes = [
            ("Dashboard Geral", self.build_dashboard),
            ("Processador (CPU)", self.build_cpu),
            ("Memória RAM", self.build_ram),
            ("Placa de Vídeo (GPU)", self.build_gpu),
            ("Armazenamento", self.build_armazenamento),
            ("Placa Mãe & Sistema", self.build_sistema),
            ("Periféricos & Áudio", self.build_perifericos),
            ("Drivers Instalados", self.build_drivers)
        ]

        for i, (texto, comando) in enumerate(botoes):
            btn = ctk.CTkButton(self.sidebar_frame, text=texto, command=comando, anchor="w")
            btn.grid(row=i+2, column=0, padx=20, pady=5, sticky="ew")
            
        btn_exportar = ctk.CTkButton(self.sidebar_frame, text="📄 Exportar Relatório", command=self.exportar_relatorio, fg_color="#2FA572", hover_color="#248058")
        btn_exportar.grid(row=11, column=0, padx=20, pady=(20, 10), sticky="ew")

        btn_github = ctk.CTkButton(self.sidebar_frame, text="💻 Criado por SrBozzo", command=self.abrir_github, fg_color="#1E1E1E", hover_color="#333333")
        btn_github.grid(row=12, column=0, padx=20, pady=(0, 20), sticky="ew")

        # --- Área Principal ---
        self.main_frame = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.build_dashboard()
        self.update_loop() 

    # =========================================================================
    # AÇÕES DOS BOTÕES ESPECIAIS
    # =========================================================================
    def abrir_github(self):
        webbrowser.open("https://github.com/SrBozzo")

    def exportar_relatorio(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Documento de Texto", "*.txt")])
        if not filepath: return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=== RELATÓRIO DE HARDWARE ===\n")
                f.write(f"Data: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"CPU: {platform.processor()}\n")
                f.write(f"RAM: {format_size(psutil.virtual_memory().total)}\n")
            messagebox.showinfo("Sucesso", "Relatório guardado!")
        except Exception as e: messagebox.showerror("Erro", str(e))

    # =========================================================================
    # 🚀 MOTOR DE DADOS EM SEGUNDO PLANO
    # =========================================================================
    def motor_de_dados_em_segundo_plano(self):
        last_net = psutil.net_io_counters()
        last_disk = psutil.disk_io_counters(perdisk=True)
        last_time = time.time()

        while self.running:
            try:
                curr_time = time.time()
                time_diff = curr_time - last_time if (curr_time - last_time) > 0 else 1.0

                # 1. Uptime
                uptime_seg = curr_time - psutil.boot_time()
                self.hw_data["uptime"] = f"Tempo Ligado: {int(uptime_seg // 3600)}h {int((uptime_seg % 3600) // 60)}m"

                # 2. CPU
                self.hw_data["cpu_pct"] = psutil.cpu_percent()
                self.hw_data["cpu_cores"] = psutil.cpu_percent(percpu=True)
                freq = psutil.cpu_freq()
                self.hw_data["cpu_freq"] = freq.current if freq else 0
                
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    if 'coretemp' in temps: self.hw_data["cpu_temp"] = f"{temps['coretemp'][0].current:.0f}°C"

                # 3. RAM
                mem = psutil.virtual_memory()
                self.hw_data["ram_pct"] = mem.percent
                self.hw_data["ram_used"] = mem.used
                self.hw_data["ram_total"] = mem.total

                # 4. GPU (NVIDIA)
                try:
                    cmd = "nvidia-smi --query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total,clocks.gr,power.draw,fan.speed --format=csv,noheader,nounits"
                    res = subprocess.check_output(cmd, text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip().split(', ')
                    self.hw_data["gpu_ok"] = True
                    self.hw_data["gpu_nome"] = res[0]
                    self.hw_data["gpu_uso"] = float(res[1])
                    self.hw_data["gpu_temp"] = f"{res[2]}°C"
                    self.hw_data["vram_usada"] = float(res[3]) / 1024
                    self.hw_data["vram_total"] = float(res[4]) / 1024
                    self.hw_data["gpu_freq"] = float(res[5])
                    self.hw_data["gpu_power"] = res[6]
                    self.hw_data["gpu_fan"] = res[7]
                except:
                    self.hw_data["gpu_ok"] = False

                # 5. Top Processos
                procs = []
                for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
                    if p.info['name'] and p.info['cpu_percent'] is not None: procs.append(p.info)
                self.hw_data["top_procs"] = sorted(procs, key=lambda p: p['cpu_percent'], reverse=True)[:5]

                # 6. Rede
                curr_net = psutil.net_io_counters()
                self.hw_data["net_down"] = (curr_net.bytes_recv - last_net.bytes_recv) / time_diff
                self.hw_data["net_up"] = (curr_net.bytes_sent - last_net.bytes_sent) / time_diff
                last_net = curr_net

                # 7. Discos IO & Espaço
                curr_disk = psutil.disk_io_counters(perdisk=True)
                for p in psutil.disk_partitions():
                    if 'cdrom' in p.opts or p.fstype == '': continue
                    letter = p.device.replace('\\', '').replace(':', '')
                    try:
                        uso = psutil.disk_usage(p.mountpoint).percent
                        read_s, write_s = 0, 0
                        for io_name, io_data in curr_disk.items():
                            if letter in io_name or io_name in letter:
                                if io_name in last_disk:
                                    read_s = (io_data.read_bytes - last_disk[io_name].read_bytes) / time_diff
                                    write_s = (io_data.write_bytes - last_disk[io_name].write_bytes) / time_diff
                                break
                        self.hw_data["discos"][letter] = {"uso": uso, "read": read_s, "write": write_s}
                    except: pass
                last_disk = curr_disk

                last_time = curr_time
                time.sleep(1) 
            except Exception as e:
                time.sleep(1)

    # =========================================================================
    # OVERLAY GAMER (COM BORDA PRETA)
    # =========================================================================
    def toggle_overlay(self):
        if self.overlay_ativo and self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_ativo = False
            self.btn_overlay.configure(text="🎮 Overlay Gamer")
        else:
            self.overlay_window = ctk.CTkToplevel(self)
            self.overlay_window.title("Overlay Gamer")
            self.overlay_window.geometry("250x120+20+20") 
            self.overlay_window.overrideredirect(True) 
            self.overlay_window.attributes("-topmost", True) 
            
            TRANSPARENT_COLOR = "#000001"
            if platform.system() == "Windows":
                self.overlay_window.config(bg=TRANSPARENT_COLOR)
                self.overlay_window.attributes("-transparentcolor", TRANSPARENT_COLOR)
            
            self.ov_canvas = tk.Canvas(self.overlay_window, bg=TRANSPARENT_COLOR, highlightthickness=0)
            self.ov_canvas.pack(fill="both", expand=True)

            font_ov = ("Consolas", 18, "bold")
            color_text = "#FFB000" 
            
            self.ov_texts = {}
            
            def criar_texto_com_borda(nome, y_pos):
                items_borda = []
                espessura = 2 
                for dx in range(-espessura, espessura + 1):
                    for dy in range(-espessura, espessura + 1):
                        if dx != 0 or dy != 0:
                            items_borda.append(self.ov_canvas.create_text(10 + dx, y_pos + dy, text="", font=font_ov, fill="black", anchor="w"))
                
                item_principal = self.ov_canvas.create_text(10, y_pos, text="", font=font_ov, fill=color_text, anchor="w")
                self.ov_texts[nome] = {"borda": items_borda, "principal": item_principal}

            criar_texto_com_borda("gpu", 20)
            criar_texto_com_borda("vram", 45)
            criar_texto_com_borda("cpu", 70)
            criar_texto_com_borda("ram", 95)

            self.overlay_ativo = True
            self.btn_overlay.configure(text="❌ Fechar Overlay")

    def atualizar_texto_overlay(self, nome, novo_texto):
        if nome in self.ov_texts:
            for item in self.ov_texts[nome]["borda"]:
                self.ov_canvas.itemconfig(item, text=novo_texto)
            self.ov_canvas.itemconfig(self.ov_texts[nome]["principal"], text=novo_texto)

    # =========================================================================
    # FUNÇÕES DE GESTÃO DO ECRÃ
    # =========================================================================
    def limpar_tela(self, titulo):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.ui_elements = {} 
        
        lbl_titulo = ctk.CTkLabel(self.main_frame, text=titulo, font=ctk.CTkFont(size=28, weight="bold"))
        lbl_titulo.grid(row=0, column=0, pady=(10, 20), sticky="w")
        return 1 

    def criar_separador(self, row):
        sep = ctk.CTkFrame(self.main_frame, height=2, fg_color="#333333")
        sep.grid(row=row, column=0, sticky="ew", pady=15)

    def mostrar_texto_estatico(self, texto, row, key_name="texto_estatico"):
        txt = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(size=14), wrap="word")
        txt.grid(row=row, column=0, sticky="nsew", pady=(0, 20))
        self.main_frame.grid_rowconfigure(row, weight=1)
        
        def ajustar_altura(event=None):
            try:
                if txt.winfo_exists():
                    nova_altura = self.winfo_height() - 150
                    if nova_altura > 100: txt.configure(height=nova_altura)
            except: pass
            
        ajustar_altura()
        self.bind("<Configure>", ajustar_altura)
        txt.insert("0.0", texto)
        txt.configure(state="disabled")
        self.ui_elements[key_name] = txt

    # =========================================================================
    # CONSTRUTORES DE ECRÃ (BUILDERS)
    # =========================================================================
    def build_dashboard(self):
        self.tela_atual = "dashboard"
        row = self.limpar_tela("Dashboard Geral (Tempo Real)")

        self.ui_elements['dash_uptime'] = ctk.CTkLabel(self.main_frame, text="Tempo Ligado: A carregar...", font=ctk.CTkFont(size=14))
        self.ui_elements['dash_uptime'].grid(row=row, column=0, sticky="w"); row+=1
        self.criar_separador(row); row+=1

        ctk.CTkLabel(self.main_frame, text="🔥 Top Processos", font=ctk.CTkFont(size=18, weight="bold")).grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['dash_procs'] = []
        for i in range(5):
            lbl = ctk.CTkLabel(self.main_frame, text=f"{i+1}. ...", font=ctk.CTkFont(size=14))
            lbl.grid(row=row, column=0, sticky="w"); row+=1
            self.ui_elements['dash_procs'].append(lbl)
        self.criar_separador(row); row+=1

        ctk.CTkLabel(self.main_frame, text="⚙️ Processador (CPU)", font=ctk.CTkFont(size=18, weight="bold")).grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['dash_cpu_stats'] = ctk.CTkLabel(self.main_frame, text="A carregar...", font=ctk.CTkFont(size=14))
        self.ui_elements['dash_cpu_stats'].grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['dash_cpu_bar'] = ctk.CTkProgressBar(self.main_frame, height=15)
        self.ui_elements['dash_cpu_bar'].grid(row=row, column=0, pady=(5, 5), sticky="ew"); row+=1
        self.ui_elements['dash_cpu_bar'].set(0)
        self.criar_separador(row); row+=1

        ctk.CTkLabel(self.main_frame, text="🧠 Memória RAM", font=ctk.CTkFont(size=18, weight="bold")).grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['dash_ram_stats'] = ctk.CTkLabel(self.main_frame, text="A carregar...", font=ctk.CTkFont(size=14))
        self.ui_elements['dash_ram_stats'].grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['dash_ram_bar'] = ctk.CTkProgressBar(self.main_frame, height=15)
        self.ui_elements['dash_ram_bar'].grid(row=row, column=0, pady=(5, 5), sticky="ew"); row+=1
        self.ui_elements['dash_ram_bar'].set(0)
        self.criar_separador(row); row+=1

        ctk.CTkLabel(self.main_frame, text="🎮 Placa de Vídeo (GPU)", font=ctk.CTkFont(size=18, weight="bold")).grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['dash_gpu_stats'] = ctk.CTkLabel(self.main_frame, text="A carregar...", font=ctk.CTkFont(size=14))
        self.ui_elements['dash_gpu_stats'].grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['dash_gpu_bar'] = ctk.CTkProgressBar(self.main_frame, height=15)
        self.ui_elements['dash_gpu_bar'].grid(row=row, column=0, pady=(5, 5), sticky="ew"); row+=1
        self.ui_elements['dash_gpu_bar'].set(0)
        
        self.ui_elements['dash_vram_stats'] = ctk.CTkLabel(self.main_frame, text="VRAM Usada: ...", font=ctk.CTkFont(size=14))
        self.ui_elements['dash_vram_stats'].grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['dash_vram_bar'] = ctk.CTkProgressBar(self.main_frame, height=10)
        self.ui_elements['dash_vram_bar'].grid(row=row, column=0, pady=(0, 5), sticky="ew"); row+=1
        self.ui_elements['dash_vram_bar'].set(0)
        self.criar_separador(row); row+=1

        ctk.CTkLabel(self.main_frame, text="💾 Armazenamento (Discos)", font=ctk.CTkFont(size=18, weight="bold")).grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['dash_discos'] = {}
        for p in psutil.disk_partitions():
            if 'cdrom' in p.opts or p.fstype == '': continue 
            nome = p.device
            ctk.CTkLabel(self.main_frame, text=f"Disco {nome}", font=ctk.CTkFont(size=15, weight="bold")).grid(row=row, column=0, sticky="w", pady=(10, 0)); row+=1
            lbl_stats = ctk.CTkLabel(self.main_frame, text="A carregar...", font=ctk.CTkFont(size=14))
            lbl_stats.grid(row=row, column=0, sticky="w"); row+=1
            bar = ctk.CTkProgressBar(self.main_frame, height=15)
            bar.grid(row=row, column=0, pady=(0, 5), sticky="ew"); row+=1
            bar.set(0)
            drive_letter = nome.replace('\\', '').replace(':', '')
            self.ui_elements['dash_discos'][drive_letter] = {"lbl": lbl_stats, "bar": bar}
        self.criar_separador(row); row+=1

        ctk.CTkLabel(self.main_frame, text="🌐 Internet (Rede)", font=ctk.CTkFont(size=18, weight="bold")).grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['dash_net_down'] = ctk.CTkLabel(self.main_frame, text="⬇️ Download: ...", text_color="#2FA572")
        self.ui_elements['dash_net_down'].grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['dash_net_up'] = ctk.CTkLabel(self.main_frame, text="⬆️ Upload: ...", text_color="#3498DB")
        self.ui_elements['dash_net_up'].grid(row=row, column=0, sticky="w"); row+=1

    def build_cpu(self):
        self.tela_atual = "cpu"
        row = self.limpar_tela("Processador (CPU) - Detalhado")

        lbl_estatico = ctk.CTkLabel(self.main_frame, text="A buscar informações do fabricante...", justify="left")
        lbl_estatico.grid(row=row, column=0, sticky="w", pady=(0, 15)); row+=1

        def buscar_wmi_cpu():
            if not has_wmi: return
            try:
                pythoncom.CoInitialize()
                cpu = wmi.WMI().Win32_Processor()[0]
                info = f"🏭 Fabricante: {cpu.Manufacturer}  |  🏷️ Modelo: {cpu.Name}\n"
                info += f"🔌 Socket: {cpu.SocketDesignation}  |  🏗️ Arquitetura: {cpu.Architecture} bits\n"
                info += f"📦 Cache L2: {cpu.L2CacheSize} KB  |  📦 Cache L3: {cpu.L3CacheSize} KB"
                self.after(0, lambda: lbl_estatico.configure(text=info) if lbl_estatico.winfo_exists() else None)
            except: pass
            finally: pythoncom.CoUninitialize()
        threading.Thread(target=buscar_wmi_cpu).start()

        self.ui_elements['cpu_global_lbl'] = ctk.CTkLabel(self.main_frame, text="Uso Global: 0% | Freq: 0 MHz", font=ctk.CTkFont(size=16, weight="bold"))
        self.ui_elements['cpu_global_lbl'].grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['cpu_global_bar'] = ctk.CTkProgressBar(self.main_frame, height=20)
        self.ui_elements['cpu_global_bar'].grid(row=row, column=0, pady=(5, 15), sticky="ew"); row+=1

        self.criar_separador(row); row+=1

        ctk.CTkLabel(self.main_frame, text="Uso por Núcleo (Threads):", font=ctk.CTkFont(size=16, weight="bold")).grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['cores'] = []
        for i in range(psutil.cpu_count(logical=True)):
            lbl = ctk.CTkLabel(self.main_frame, text=f"Core {i}: 0%", font=ctk.CTkFont(size=12))
            lbl.grid(row=row, column=0, sticky="w")
            bar = ctk.CTkProgressBar(self.main_frame, height=10)
            bar.grid(row=row+1, column=0, pady=(0, 10), sticky="ew")
            bar.set(0)
            self.ui_elements['cores'].append((lbl, bar))
            row += 2

    def build_ram(self):
        self.tela_atual = "ram"
        row = self.limpar_tela("Memória RAM - Detalhado")

        lbl_estatico = ctk.CTkLabel(self.main_frame, text="A analisar pentes de memória...", justify="left")
        lbl_estatico.grid(row=row, column=0, sticky="w", pady=(0, 15)); row+=1

        def buscar_wmi_ram():
            if not has_wmi: return
            try:
                pythoncom.CoInitialize()
                memorias = wmi.WMI().Win32_PhysicalMemory()
                info = ""
                for i, mem in enumerate(memorias):
                    cap_gb = int(mem.Capacity) / (1024**3)
                    info += f"Slot {i+1}: {cap_gb:.0f}GB | Freq: {mem.Speed} MHz | Fab: {mem.Manufacturer}\n"
                self.after(0, lambda: lbl_estatico.configure(text=info if info else "Dados não disponíveis.") if lbl_estatico.winfo_exists() else None)
            except: pass
            finally: pythoncom.CoUninitialize()
        threading.Thread(target=buscar_wmi_ram).start()

        self.ui_elements['ram_lbl'] = ctk.CTkLabel(self.main_frame, text="Uso: 0%", font=ctk.CTkFont(size=16, weight="bold"))
        self.ui_elements['ram_lbl'].grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['ram_bar'] = ctk.CTkProgressBar(self.main_frame, height=25)
        self.ui_elements['ram_bar'].grid(row=row, column=0, pady=(5, 15), sticky="ew"); row+=1

    def build_gpu(self):
        self.tela_atual = "gpu"
        row = self.limpar_tela("Placa de Vídeo (GPU) - Detalhado")

        lbl_aviso = ctk.CTkLabel(self.main_frame, text="Sensores avançados nativos para placas NVIDIA.", text_color="#A0A0A0")
        lbl_aviso.grid(row=row, column=0, sticky="w", pady=(0, 10)); row+=1

        self.ui_elements['gpu_info'] = ctk.CTkLabel(self.main_frame, text="A carregar...", font=ctk.CTkFont(size=16, weight="bold"), justify="left")
        self.ui_elements['gpu_info'].grid(row=row, column=0, sticky="w"); row+=1
        
        self.ui_elements['gpu_uso_lbl'] = ctk.CTkLabel(self.main_frame, text="Carga: 0%")
        self.ui_elements['gpu_uso_lbl'].grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['gpu_uso_bar'] = ctk.CTkProgressBar(self.main_frame, height=15)
        self.ui_elements['gpu_uso_bar'].grid(row=row, column=0, pady=(0, 15), sticky="ew"); row+=1

        self.ui_elements['gpu_vram_lbl'] = ctk.CTkLabel(self.main_frame, text="VRAM: 0 GB")
        self.ui_elements['gpu_vram_lbl'].grid(row=row, column=0, sticky="w"); row+=1
        self.ui_elements['gpu_vram_bar'] = ctk.CTkProgressBar(self.main_frame, height=15)
        self.ui_elements['gpu_vram_bar'].grid(row=row, column=0, pady=(0, 15), sticky="ew"); row+=1

    def build_armazenamento(self):
        self.tela_atual = "armazenamento"
        row = self.limpar_tela("Armazenamento (Discos) - Detalhado")

        self.ui_elements['discos'] = {}
        for p in psutil.disk_partitions():
            if 'cdrom' in p.opts or p.fstype == '': continue 
            nome = p.device
            ctk.CTkLabel(self.main_frame, text=f"💽 Disco {nome} ({p.fstype}) - Ponto: {p.mountpoint}", font=ctk.CTkFont(size=16, weight="bold")).grid(row=row, column=0, sticky="w", pady=(10,0)); row+=1
            
            lbl_espaco = ctk.CTkLabel(self.main_frame, text="A calcular...")
            lbl_espaco.grid(row=row, column=0, sticky="w"); row+=1
            bar_espaco = ctk.CTkProgressBar(self.main_frame, height=10)
            bar_espaco.grid(row=row, column=0, pady=(0, 5), sticky="ew"); row+=1
            
            lbl_io = ctk.CTkLabel(self.main_frame, text="Leitura: 0 KB/s")
            lbl_io.grid(row=row, column=0, sticky="w"); row+=1
            
            drive_letter = nome.replace('\\', '').replace(':', '')
            self.ui_elements['discos'][drive_letter] = {"lbl_espaco": lbl_espaco, "bar_espaco": bar_espaco, "lbl_io": lbl_io}
            self.criar_separador(row); row+=1

    def build_sistema(self):
        self.tela_atual = "estatico"
        row = self.limpar_tela("Placa Mãe & Sistema (Dados Estáticos)")
        self.mostrar_texto_estatico("Aguarde, a extrair toda a arquitetura do PC...\n(A interface não irá bloquear!)", row, "txt_sys")
        
        def buscar_sys():
            info = f"=== SISTEMA OPERATIVO ===\nSistema: {platform.system()} {platform.release()} ({platform.version()})\nArquitetura: {platform.machine()}\n\n"
            if has_wmi:
                try:
                    pythoncom.CoInitialize()
                    b = wmi.WMI().Win32_BaseBoard()[0]
                    bios = wmi.WMI().Win32_BIOS()[0]
                    info += f"=== PLACA MÃE ===\nFabricante: {b.Manufacturer}\nModelo: {b.Product}\nVersão: {b.Version}\n\n"
                    info += f"=== BIOS ===\nFabricante: {bios.Manufacturer}\nVersão: {bios.SMBIOSBIOSVersion}\n"
                except: pass
                finally: pythoncom.CoUninitialize()
            
            def atualizar():
                if 'txt_sys' in self.ui_elements and self.ui_elements['txt_sys'].winfo_exists():
                    self.ui_elements['txt_sys'].configure(state="normal")
                    self.ui_elements['txt_sys'].delete("0.0", "end")
                    self.ui_elements['txt_sys'].insert("0.0", info)
                    self.ui_elements['txt_sys'].configure(state="disabled")
            self.after(0, atualizar)
        threading.Thread(target=buscar_sys).start()

    def build_perifericos(self):
        self.tela_atual = "estatico"
        row = self.limpar_tela("Periféricos e Áudio Conectados")
        self.mostrar_texto_estatico("A mapear dispositivos...", row, "txt_peri")
        
        def buscar_peri():
            info = ""
            if has_wmi:
                try:
                    pythoncom.CoInitialize()
                    c = wmi.WMI()
                    info += "⌨️ TECLADOS:\n" + "".join([f"  • {k.Description or k.Name}\n" for k in c.Win32_Keyboard()]) + "\n"
                    info += "🖱️ RATOS:\n" + "".join([f"  • {m.Name}\n" for m in c.Win32_PointingDevice()]) + "\n"
                    info += "🖥️ MONITORES:\n" + "".join([f"  • {mon.Caption or mon.Name}\n" for mon in c.Win32_DesktopMonitor()]) + "\n"
                    info += "🔊 ÁUDIO:\n" + "".join([f"  • {a.Name}\n" for a in c.Win32_SoundDevice()]) + "\n"
                except: info = "Erro ao efetuar a procura."
                finally: pythoncom.CoUninitialize()
                
            def atualizar():
                if 'txt_peri' in self.ui_elements and self.ui_elements['txt_peri'].winfo_exists():
                    self.ui_elements['txt_peri'].configure(state="normal")
                    self.ui_elements['txt_peri'].delete("0.0", "end")
                    self.ui_elements['txt_peri'].insert("0.0", info)
                    self.ui_elements['txt_peri'].configure(state="disabled")
            self.after(0, atualizar)
        threading.Thread(target=buscar_peri).start()

    def build_drivers(self):
        self.tela_atual = "estatico"
        row = self.limpar_tela("Drivers Instalados no Kernel")
        self.mostrar_texto_estatico("A varrer registo do Windows (Pode demorar 15s)...", row, "txt_drivers")
        
        def buscar_drivers():
            info = ""
            if has_wmi:
                try:
                    pythoncom.CoInitialize()
                    categorias = {}
                    for d in wmi.WMI().Win32_PnPSignedDriver():
                        if d.DeviceName and d.DeviceClass:
                            c = d.DeviceClass.upper()
                            if c not in categorias: categorias[c] = []
                            categorias[c].append(f"  • {d.DeviceName}")
                    for classe in sorted(categorias.keys()):
                        info += f"=== {classe} ===\n" + "\n".join(categorias[classe]) + "\n\n"
                except: pass
                finally: pythoncom.CoUninitialize()
                
            def atualizar():
                if 'txt_drivers' in self.ui_elements and self.ui_elements['txt_drivers'].winfo_exists():
                    self.ui_elements['txt_drivers'].configure(state="normal")
                    self.ui_elements['txt_drivers'].delete("0.0", "end")
                    self.ui_elements['txt_drivers'].insert("0.0", info)
                    self.ui_elements['txt_drivers'].configure(state="disabled")
            self.after(0, atualizar)
        threading.Thread(target=buscar_drivers).start()

    # =========================================================================
    # 👁️ O LEITOR DA TELA (ATUALIZAÇÃO GERAL)
    # =========================================================================
    def update_loop(self):
        data = self.hw_data

        # --- ATUALIZA O OVERLAY GAMER ---
        if self.overlay_ativo and self.overlay_window and self.overlay_window.winfo_exists():
            if data["gpu_ok"]:
                self.atualizar_texto_overlay("gpu", f"GPU  {data['gpu_uso']:3.0f}%  {data['gpu_temp']}")
                v_pct = (data['vram_usada']/data['vram_total'])*100 if data['vram_total'] > 0 else 0
                self.atualizar_texto_overlay("vram", f"MEM  {data['vram_usada']:4.1f}GB  {v_pct:3.0f}%")
            self.atualizar_texto_overlay("cpu", f"CPU  {data['cpu_pct']:3.0f}%  {data['cpu_temp']}")
            self.atualizar_texto_overlay("ram", f"RAM  {data['ram_used']/(1024**3):4.1f}GB  {data['ram_pct']:3.0f}%")

        # --- ATUALIZA DASHBOARD ---
        if self.tela_atual == "dashboard":
            if 'dash_uptime' in self.ui_elements: self.ui_elements['dash_uptime'].configure(text=data["uptime"])
            
            if 'dash_procs' in self.ui_elements:
                for i, proc in enumerate(data["top_procs"]):
                    if i < len(self.ui_elements['dash_procs']):
                        self.ui_elements['dash_procs'][i].configure(text=f"{i+1}. {proc['name']} - CPU: {proc['cpu_percent']:.1f}% | RAM: {(proc['memory_percent'] or 0):.1f}%")

            if 'dash_cpu_stats' in self.ui_elements:
                self.ui_elements['dash_cpu_stats'].configure(text=f"Uso: {data['cpu_pct']}% | Freq: {data['cpu_freq']:.0f} MHz | Temp: {data['cpu_temp']}")
                self.ui_elements['dash_cpu_bar'].set(data['cpu_pct']/100)
                self.ui_elements['dash_cpu_bar'].configure(progress_color=get_color_by_percent(data['cpu_pct']))

            if 'dash_ram_stats' in self.ui_elements:
                self.ui_elements['dash_ram_stats'].configure(text=f"Uso: {data['ram_pct']}% | Usado: {format_size(data['ram_used'])} / Total: {format_size(data['ram_total'])}")
                self.ui_elements['dash_ram_bar'].set(data['ram_pct']/100)
                self.ui_elements['dash_ram_bar'].configure(progress_color=get_color_by_percent(data['ram_pct']))

            if 'dash_gpu_stats' in self.ui_elements and data["gpu_ok"]:
                self.ui_elements['dash_gpu_stats'].configure(text=f"Uso GPU: {data['gpu_uso']}% | Temp: {data['gpu_temp']}")
                self.ui_elements['dash_gpu_bar'].set(data['gpu_uso'] / 100)
                self.ui_elements['dash_gpu_bar'].configure(progress_color=get_color_by_percent(data['gpu_uso']))

                v_pct = (data['vram_usada'] / data['vram_total']) * 100 if data['vram_total'] > 0 else 0
                self.ui_elements['dash_vram_stats'].configure(text=f"VRAM Usada: {data['vram_usada']:.2f} GB ({v_pct:.1f}%)")
                self.ui_elements['dash_vram_bar'].set(v_pct / 100)
                self.ui_elements['dash_vram_bar'].configure(progress_color=get_color_by_percent(v_pct))

            if 'dash_discos' in self.ui_elements:
                for letter, info in self.ui_elements['dash_discos'].items():
                    if letter in data["discos"]:
                        d_info = data["discos"][letter]
                        info["bar"].set(d_info["uso"]/100)
                        info["bar"].configure(progress_color=get_color_by_percent(d_info["uso"]))
                        info["lbl"].configure(text=f"Uso de Espaço: {d_info['uso']}% | Leitura: {format_size(d_info['read'])}/s | Gravação: {format_size(d_info['write'])}/s")

            if 'dash_net_down' in self.ui_elements:
                self.ui_elements['dash_net_down'].configure(text=f"⬇️ Download: {format_size(data['net_down'])}/s")
                self.ui_elements['dash_net_up'].configure(text=f"⬆️ Upload: {format_size(data['net_up'])}/s")

        # --- ATUALIZA CPU DETALHE ---
        elif self.tela_atual == "cpu":
            if 'cpu_global_lbl' in self.ui_elements:
                self.ui_elements['cpu_global_lbl'].configure(text=f"Uso Global: {data['cpu_pct']}% | Freq Atual: {data['cpu_freq']:.0f} MHz")
                self.ui_elements['cpu_global_bar'].set(data['cpu_pct']/100)
                self.ui_elements['cpu_global_bar'].configure(progress_color=get_color_by_percent(data['cpu_pct']))
                
                for i, pct in enumerate(data['cpu_cores']):
                    if i < len(self.ui_elements['cores']):
                        lbl, bar = self.ui_elements['cores'][i]
                        lbl.configure(text=f"Core {i}: {pct}%")
                        bar.set(pct/100)
                        bar.configure(progress_color=get_color_by_percent(pct))

        # --- ATUALIZA RAM DETALHE ---
        elif self.tela_atual == "ram":
            if 'ram_lbl' in self.ui_elements:
                self.ui_elements['ram_lbl'].configure(text=f"Uso: {data['ram_pct']}% | Usado: {format_size(data['ram_used'])} / Total: {format_size(data['ram_total'])}")
                self.ui_elements['ram_bar'].set(data['ram_pct']/100)
                self.ui_elements['ram_bar'].configure(progress_color=get_color_by_percent(data['ram_pct']))

        # --- ATUALIZA GPU DETALHE ---
        elif self.tela_atual == "gpu" and data["gpu_ok"]:
            if 'gpu_info' in self.ui_elements:
                v_pct = (data['vram_usada'] / data['vram_total']) * 100 if data['vram_total'] > 0 else 0
                self.ui_elements['gpu_info'].configure(text=f"Nome: {data['gpu_nome']}\nTemperatura: {data['gpu_temp']}  |  Energia: {data['gpu_power']} W  |  Ventoinha: {data['gpu_fan']}%\nClock: {data['gpu_freq']} MHz")
                self.ui_elements['gpu_uso_lbl'].configure(text=f"Carga: {data['gpu_uso']}%")
                self.ui_elements['gpu_uso_bar'].set(data['gpu_uso']/100)
                self.ui_elements['gpu_uso_bar'].configure(progress_color=get_color_by_percent(data['gpu_uso']))
                self.ui_elements['gpu_vram_lbl'].configure(text=f"VRAM: {data['vram_usada']:.2f} GB / {data['vram_total']:.2f} GB ({v_pct:.1f}%)")
                self.ui_elements['gpu_vram_bar'].set(v_pct/100)
                self.ui_elements['gpu_vram_bar'].configure(progress_color=get_color_by_percent(v_pct))

        # --- ATUALIZA DISCOS DETALHE ---
        elif self.tela_atual == "armazenamento":
            if 'discos' in self.ui_elements:
                for letter, info in self.ui_elements['discos'].items():
                    if letter in data["discos"]:
                        d_info = data["discos"][letter]
                        info["lbl_espaco"].configure(text=f"Espaço Usado: {d_info['uso']}%")
                        info["bar_espaco"].set(d_info['uso']/100)
                        info["bar_espaco"].configure(progress_color=get_color_by_percent(d_info['uso']))
                        info["lbl_io"].configure(text=f"Leitura: {format_size(d_info['read'])}/s | Gravação: {format_size(d_info['write'])}/s")

        self.after(1000, self.update_loop)

if __name__ == "__main__":
    app = MonitorHardwareApp()
    app.mainloop()