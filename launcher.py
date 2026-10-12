import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import json
import shutil
import threading
import subprocess
from datetime import datetime

import minecraft_launcher_lib
from minecraft_launcher_lib import utils

BASE = Path.home() / "CreeperLauncher"
GAME = BASE / "minecraft"
MODS = BASE / "mods"
CONFIG = BASE / "config.json"
STATS = BASE / "launcher_stats.json"

for folder in (BASE, GAME, MODS):
    folder.mkdir(parents=True, exist_ok=True)

defaults = {
    "version": "1.21.4",
    "loader": "Vanilla",
    "ram": 4
}

try:
    settings = json.loads(CONFIG.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    settings = defaults.copy()

root = tk.Tk()
root.title("Creeper Launcher")
root.geometry("720x570")
# Tema Creeper: negro y verde oscuro
BG = "#090B0A"
PANEL = "#111713"
INPUT = "#1A241D"
GREEN = "#1F5B35"
GREEN_HOVER = "#2B7545"
TEXT = "#E8F2EA"
MUTED = "#A8B8AC"
BORDER = "#294333"

root.configure(bg=BG)

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "TFrame",
    background=BG
)
style.configure(
    "TLabel",
    background=BG,
    foreground=TEXT,
    font=("Segoe UI", 10)
)
style.configure(
    "TButton",
    background=GREEN,
    foreground=TEXT,
    padding=(12, 8),
    borderwidth=0,
    font=("Segoe UI", 10, "bold")
)
style.map(
    "TButton",
    background=[("active", GREEN_HOVER), ("pressed", GREEN_HOVER)],
    foreground=[("disabled", MUTED)]
)
style.configure(
    "TLabelframe",
    background=BG,
    foreground="#6CCB83",
    bordercolor=BORDER,
    relief="solid",
    borderwidth=1
)
style.configure(
    "TLabelframe.Label",
    background=BG,
    foreground="#6CCB83",
    font=("Segoe UI", 10, "bold")
)
style.configure(
    "TEntry",
    fieldbackground=INPUT,
    foreground=TEXT,
    insertcolor=TEXT,
    bordercolor=BORDER,
    lightcolor=BORDER,
    darkcolor=BORDER,
    padding=5
)
style.configure(
    "TCombobox",
    fieldbackground=INPUT,
    background=GREEN,
    foreground=TEXT,
    arrowcolor=TEXT,
    bordercolor=BORDER,
    lightcolor=BORDER,
    darkcolor=BORDER,
    padding=5
)
style.map(
    "TCombobox",
    fieldbackground=[("readonly", INPUT)],
    foreground=[("readonly", TEXT)],
    selectbackground=[("readonly", GREEN)],
    selectforeground=[("readonly", TEXT)],
    background=[("active", GREEN_HOVER)]
)
style.configure(
    "Vertical.TScrollbar",
    background=GREEN,
    troughcolor=BG,
    arrowcolor=TEXT,
    bordercolor=BG
)

version = tk.StringVar(value=settings.get("version", "1.21.4"))
version_category = tk.StringVar(value="Release")
loader = tk.StringVar(value=settings.get("loader", "Vanilla"))
ram = tk.StringVar(value=str(settings.get("ram", 4)))
status = tk.StringVar(value="Listo")

# CREEPER_PROGRESS_PATCH_V2
progress_text = tk.StringVar(value="Listo")
progress_value = tk.DoubleVar(value=0)
progress_count = tk.StringVar(value="")


def save():
    settings.update({
        "version": version.get().strip(),
        "loader": loader.get(),
        "ram": int(ram.get())
    })
    CONFIG.write_text(
        json.dumps(settings, indent=4),
        encoding="utf-8"
    )

def task(fn):
    def run():
        try:
            fn()
        except Exception as exc:
            msg = str(exc)
            root.after(0, lambda: messagebox.showerror("Error", msg))
            root.after(0, lambda: status.set("Error"))
    threading.Thread(target=run, daemon=True).start()

def install():
    save()
    ver = version.get().strip()
    kind = loader.get()

    def work():
        root.after(0, lambda: status.set("Instalando Minecraft..."))

        if kind == "Vanilla":
            import time
            started_at = time.monotonic()
            progress_state = {"max": 0, "value": 0}

            def callback_status(message):
                root.after(0, lambda m=str(message): progress_text.set(m))

            def callback_max(maximum):
                try:
                    maximum = max(1, int(maximum))
                except (TypeError, ValueError):
                    maximum = 1
                progress_state["max"] = maximum

                def update_max():
                    install_bar.configure(maximum=maximum)
                    progress_value.set(0)
                    progress_count.set(f"Elementos: 0 / {maximum}")
                root.after(0, update_max)

            def callback_progress(value):
                try:
                    value = max(0, float(value))
                except (TypeError, ValueError):
                    return

                progress_state["value"] = value
                maximum = max(1, progress_state["max"])
                elapsed = max(0.1, time.monotonic() - started_at)
                rate = value / elapsed

                def update_progress():
                    install_bar.configure(mode="determinate")
                    progress_value.set(min(value, maximum))
                    progress_count.set(
                        f"Elementos: {int(value)} / {maximum}  |  "
                        f"Ritmo: {rate:.1f} elementos/s"
                    )
                root.after(0, update_progress)

            callback = {
                "setStatus": callback_status,
                "setProgress": callback_progress,
                "setMax": callback_max,
            }

            root.after(0, lambda: install_bar.stop())
            root.after(0, lambda: install_bar.configure(mode="determinate"))
            root.after(0, lambda: progress_value.set(0))
            root.after(0, lambda: progress_text.set(
                f"Preparando descarga de Minecraft {ver}..."
            ))

            minecraft_launcher_lib.install.install_minecraft_version(
                ver, str(GAME), callback=callback
            )
        else:
            loader_id = {
                "Fabric": "fabric",
                "Forge": "forge",
                "NeoForge": "neoforge",
                "Quilt": "quilt"
            }[kind]

            root.after(0, lambda: progress_value.set(0))
            root.after(0, lambda: progress_text.set(
                f"Instalando {kind} para Minecraft {ver}..."
            ))
            root.after(0, lambda: progress_count.set(
                "El instalador del cargador no proporciona aqui un porcentaje confirmado."
            ))
            root.after(0, lambda: install_bar.configure(mode="indeterminate"))
            root.after(0, lambda: install_bar.start(12))

            api = minecraft_launcher_lib.mod_loader.get_mod_loader(loader_id)
            api.install(ver, str(GAME))

        root.after(0, lambda: status.set("Instalación completada"))
        root.after(
            0,
            lambda: messagebox.showinfo(
                "Creeper Launcher",
                "Minecraft se instaló correctamente."
            )
        )

    if not ver:
        messagebox.showwarning("Versión", "Introduce una versión.")
        return

    task(work)

def refresh():
    disabled_dir = MODS / "disabled"
    disabled_dir.mkdir(parents=True, exist_ok=True)

    mods_list.delete(0, tk.END)

    for file in sorted(MODS.glob("*.jar")):
        mods_list.insert(tk.END, "[ACTIVO] " + file.name)

    for file in sorted(disabled_dir.glob("*.jar")):
        mods_list.insert(tk.END, "[DESACTIVADO] " + file.name)


def import_mods():
    files = filedialog.askopenfilenames(
        title="Importar mods",
        filetypes=[("Mods de Minecraft", "*.jar")]
    )

    if not files:
        return

    MODS.mkdir(parents=True, exist_ok=True)
    disabled_dir = MODS / "disabled"
    disabled_dir.mkdir(parents=True, exist_ok=True)

    imported = 0
    skipped = []

    for item in files:
        source = Path(item)
        target = MODS / source.name

        if source.resolve() == target.resolve():
            continue

        if target.exists():
            skipped.append(source.name)
            continue

        shutil.copy2(source, target)
        imported += 1

    refresh()

    message = "Mods importados: " + str(imported)
    if skipped:
        message += "\nYa existian y no se sobrescribieron:\n"
        message += "\n".join(skipped)

    messagebox.showinfo("Administrador de mods", message)


def toggle_mod():
    selection = mods_list.curselection()
    if not selection:
        messagebox.showwarning(
            "Administrador de mods",
            "Selecciona un mod de la lista."
        )
        return

    label = mods_list.get(selection[0])
    disabled_dir = MODS / "disabled"
    disabled_dir.mkdir(parents=True, exist_ok=True)

    if label.startswith("[ACTIVO] "):
        name = label[len("[ACTIVO] "):]
        source = MODS / name
        target = disabled_dir / name
    elif label.startswith("[DESACTIVADO] "):
        name = label[len("[DESACTIVADO] "):]
        source = disabled_dir / name
        target = MODS / name
    else:
        messagebox.showerror(
            "Administrador de mods",
            "No se pudo identificar el mod seleccionado."
        )
        return

    if not source.is_file():
        messagebox.showerror(
            "Administrador de mods",
            "No se encontro el archivo del mod."
        )
        refresh()
        return

    if target.exists():
        messagebox.showerror(
            "Administrador de mods",
            "Ya existe un archivo con ese nombre en el destino. "
            "No se ha sobrescrito."
        )
        return

    shutil.move(str(source), str(target))
    refresh()


def sync_mods():
    destination = GAME / "mods"
    destination.mkdir(parents=True, exist_ok=True)

    disabled_dir = MODS / "disabled"
    disabled_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    conflicts = []

    for file in sorted(MODS.glob("*.jar")):
        target = destination / file.name

        if target.exists():
            try:
                same = file.resolve() == target.resolve()
            except OSError:
                same = False

            if not same:
                conflicts.append(file.name)
                continue

        if not target.exists():
            shutil.copy2(file, target)

        count += 1

    message = (
        "Mods activos comprobados: " + str(count)
        + "\nCarpeta del juego:\n" + str(destination)
    )

    if conflicts:
        message += (
            "\n\nNo se sobrescribieron archivos existentes:\n"
            + "\n".join(conflicts)
        )

    messagebox.showinfo("Sincronizacion de mods", message)


def show_startup_window(process, ver):
    splash = tk.Toplevel(root)
    splash.title("Creeper Launcher - Iniciando")
    splash.configure(bg=BG)
    splash.resizable(False, False)
    splash.transient(root)

    width, height = 390, 175
    x = root.winfo_rootx() + max(0, (root.winfo_width() - width) // 2)
    y = root.winfo_rooty() + max(0, (root.winfo_height() - height) // 2)
    splash.geometry(f"{width}x{height}+{x}+{y}")

    tk.Label(
        splash, text="CREEPER LAUNCHER",
        bg=BG, fg="#6CCB83",
        font=("Segoe UI", 17, "bold")
    ).pack(pady=(18, 4))

    message = tk.StringVar(value=f"Preparando Minecraft {ver}...")
    tk.Label(
        splash, textvariable=message,
        bg=BG, fg=TEXT, font=("Segoe UI", 10)
    ).pack(pady=(0, 12))

    bar = ttk.Progressbar(
        splash, mode="indeterminate",
        style="Creeper.Horizontal.TProgressbar",
        length=330
    )
    bar.pack(padx=20, fill="x")
    bar.start(12)

    tk.Button(
        splash, text="Ocultar",
        command=splash.destroy,
        bg=GREEN, fg=TEXT, activebackground=GREEN_HOVER,
        activeforeground=TEXT, relief="flat",
        padx=12, pady=4
    ).pack(pady=12)

    def check_process():
        try:
            if not splash.winfo_exists():
                return
            code = process.poll()
            if code is not None:
                bar.stop()
                message.set(
                    "El proceso de Minecraft termino."
                    if code == 0 else
                    f"Minecraft termino con codigo {code}."
                )
                splash.after(2500, splash.destroy)
                return
            splash.after(500, check_process)
        except tk.TclError:
            return

    splash.after(500, check_process)


def find_java_for_version(ver, version_json):
    import json
    import os
    import re
    import subprocess
    from pathlib import Path

    required_major = None

    # Los metadatos de la versión tienen prioridad.
    try:
        metadata = json.loads(
            version_json.read_text(encoding="utf-8")
        )
        java_info = metadata.get("javaVersion") or {}
        major = java_info.get("majorVersion")
        if major is not None:
            required_major = int(major)
    except (OSError, ValueError, TypeError, AttributeError):
        pass

    # Reglas alternativas para versiones sin metadatos.
    if required_major is None:
        if ver.startswith("26."):
            required_major = 25
        elif ver.startswith("1.21"):
            required_major = 21
        elif ver.startswith(("1.18", "1.19", "1.20")):
            required_major = 17
        elif ver.startswith("1.17"):
            required_major = 16
        else:
            required_major = 8

    # Buscar runtimes del launcher e instalaciones externas.
    candidates = []
    runtime_dir = GAME / "runtime"

    if runtime_dir.is_dir():
        candidates.extend(runtime_dir.rglob("java.exe"))

    roots = []
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        roots.append(Path(java_home))

    roots.extend([
        Path("C:/Program Files/Eclipse Adoptium"),
        Path("C:/Program Files/Java"),
    ])

    for base in roots:
        if base.is_dir():
            candidates.extend(base.rglob("java.exe"))

    java_by_major = {}

    for java_file in dict.fromkeys(candidates):
        try:
            result = subprocess.run(
                [str(java_file), "-version"],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
                creationflags=getattr(
                    subprocess, "CREATE_NO_WINDOW", 0
                ),
            )

            output = (result.stdout or "") + (result.stderr or "")

            match = re.search(
                r'version\s+"([^"]+)"',
                output,
                re.IGNORECASE,
            )

            if match:
                version_text = match.group(1)
                major = (
                    8 if version_text.startswith("1.8")
                    else int(version_text.split(".")[0])
                )
            else:
                match = re.search(
                    r'openjdk\s+(\d+)',
                    output,
                    re.IGNORECASE,
                )
                if not match:
                    continue
                major = int(match.group(1))

            java_by_major.setdefault(major, java_file)

        except (OSError, ValueError, subprocess.SubprocessError):
            continue

    selected = java_by_major.get(required_major)

    if selected is None:
        available = ", ".join(
            str(number) for number in sorted(java_by_major)
        ) or "ninguno"

        raise FileNotFoundError(
            f"Minecraft {ver} requiere Java {required_major}, "
            f"pero no se encontró un runtime compatible. "
            f"Java detectados: {available}."
        )

    return selected


def _load_stats():
    try:
        data = json.loads((BASE / "launcher_stats.json").read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("sessions"), list):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"sessions": []}


def _save_stats(data):
    target = BASE / "launcher_stats.json"
    temporary = target.with_name("launcher_stats.json.tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    temporary.replace(target)


def _begin_stats_session(ver):
    import time
    import uuid

    session_id = uuid.uuid4().hex
    session = {
        "id": session_id,
        "version": ver,
        "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "ended_at": None,
        "duration_seconds": None,
        "return_code": None
    }
    try:
        data = _load_stats()
        data["sessions"].append(session)
        _save_stats(data)
        return session_id, time.monotonic()
    except OSError:
        return None, None


def _track_stats_session(process, session_id, started):
    import time

    if not session_id:
        return

    def check():
        try:
            code = process.poll()
            if code is None:
                root.after(1000, check)
                return

            data = _load_stats()
            for session in reversed(data["sessions"]):
                if session.get("id") == session_id:
                    session["ended_at"] = datetime.now().astimezone().isoformat(
                        timespec="seconds"
                    )
                    session["duration_seconds"] = max(
                        0, int(time.monotonic() - started)
                    )
                    session["return_code"] = code
                    break
            _save_stats(data)
        except (OSError, tk.TclError):
            return

    root.after(1000, check)


def export_stats_csv():
    import csv

    sessions = _load_stats().get("sessions", [])
    if not sessions:
        messagebox.showinfo(
            "Exportar estad?sticas",
            "Todav?a no hay partidas registradas."
        )
        return

    destination = filedialog.asksaveasfilename(
        parent=root,
        title="Exportar estad?sticas",
        defaultextension=".csv",
        initialfile="creeper_launcher_stats.csv",
        filetypes=[("Archivo CSV", "*.csv")]
    )
    if not destination:
        return

    fields = [
        "version", "started_at", "ended_at",
        "duration_seconds", "return_code"
    ]
    try:
        with open(destination, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fields, delimiter=";")
            writer.writeheader()
            for session in sessions:
                writer.writerow({
                    field: session.get(field, "")
                    for field in fields
                })
        messagebox.showinfo(
            "Exportaci?n completada",
            f"Se exportaron {len(sessions)} partidas.\n{destination}",
            parent=root
        )
    except (OSError, csv.Error) as exc:
        messagebox.showerror("Error al exportar", str(exc), parent=root)


def show_stats_window(_event=None):
    data = _load_stats()
    sessions = data["sessions"]
    completed = [
        s for s in sessions if s.get("duration_seconds") is not None
    ]
    total_seconds = sum(
        int(s.get("duration_seconds") or 0) for s in completed
    )
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60

    window = tk.Toplevel(root)
    window.title("Creeper Launcher - Estad?sticas")
    window.geometry("650x420")
    window.configure(bg=BG)
    window.transient(root)

    tk.Label(
        window,
        text="ESTAD?STICAS DE CREEPER",
        bg=BG,
        fg="#6CCB83",
        font=("Segoe UI", 16, "bold")
    ).pack(anchor="w", padx=16, pady=(14, 6))

    tk.Label(
        window,
        text=(
            f"Partidas registradas: {len(sessions)}    "
            f"Tiempo jugado: {hours} h {minutes} min"
        ),
        bg=BG,
        fg=TEXT,
        font=("Segoe UI", 10)
    ).pack(anchor="w", padx=16, pady=(0, 10))

    panel = ttk.Frame(window, padding=(12, 0, 12, 8))
    panel.pack(fill="both", expand=True)

    columns = ("version", "started", "duration", "result")
    table = ttk.Treeview(
        panel, columns=columns, show="headings", height=12
    )
    table.heading("version", text="Versi?n")
    table.heading("started", text="Inicio")
    table.heading("duration", text="Duraci?n")
    table.heading("result", text="Resultado")
    table.column("version", width=100, anchor="w")
    table.column("started", width=190, anchor="w")
    table.column("duration", width=100, anchor="center")
    table.column("result", width=100, anchor="center")

    scrollbar = ttk.Scrollbar(
        panel, orient="vertical", command=table.yview
    )
    table.configure(yscrollcommand=scrollbar.set)
    table.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    for session in reversed(sessions):
        seconds = session.get("duration_seconds")
        if seconds is None:
            duration = "En curso"
        else:
            minutes_played, secs = divmod(int(seconds), 60)
            duration = f"{minutes_played} min {secs} s"

        code = session.get("return_code")
        result = (
            "En curso" if code is None
            else "C?digo 0" if code == 0
            else f"C?digo {code}"
        )
        table.insert(
            "", "end",
            values=(
                session.get("version", "?"),
                session.get("started_at", "").replace("T", " ")[:19],
                duration,
                result
            )
        )

    ttk.Button(
        window, text="Exportar CSV",
        command=export_stats_csv
    ).pack(pady=(0, 6))

    ttk.Button(
        window, text="Cerrar", command=window.destroy
    ).pack(pady=(0, 12))



def play():
    ver = version.get().strip()

    if not ver:
        messagebox.showwarning("Versión", "Selecciona una versión.")
        return

    version_json = GAME / "versions" / ver / f"{ver}.json"

    if not version_json.is_file():
        messagebox.showwarning(
            "Minecraft no instalado",
            f"Instala primero la versión {ver}."
        )
        return

    try:
        java = find_java_for_version(ver, version_json)

        memory_gb = int(ram.get())
        if not 2 <= memory_gb <= 32:
            raise ValueError("La RAM debe estar entre 2 y 32 GB.")

        options = utils.generate_test_options()
        options["executablePath"] = str(java)
        options["gameDirectory"] = str(GAME)
        options["jvmArguments"] = [
            f"-Xms{min(2, memory_gb)}G",
            f"-Xmx{memory_gb}G"
        ]

        command = minecraft_launcher_lib.command.get_minecraft_command(
            ver, str(GAME), options
        )

        diagnostic_command = [
            "<JAVA>" if i == 0 else arg
            for i, arg in enumerate(command)
        ]

        (BASE / "last_launch_command.txt").write_text(
            "\n".join(diagnostic_command),
            encoding="utf-8"
        )

        process = subprocess.Popen(
            command,
            cwd=str(GAME),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )

        session_id, session_started = _begin_stats_session(ver)
        _track_stats_session(process, session_id, session_started)


        status.set(
            f"Iniciando Minecraft {ver} con Java "
            f"{java} y {memory_gb} GB de RAM..."
        )
        show_startup_window(process, ver)

    except Exception as exc:
        messagebox.showerror("Error al iniciar", str(exc))
        status.set("Error al iniciar")
frame = ttk.Frame(root, padding=22)
frame.pack(fill="both", expand=True)

ttk.Label(
    frame, text="CREEPER LAUNCHER",
    font=("Segoe UI", 23, "bold")
).pack(anchor="w")

ttk.Label(
    frame, text="Tu Minecraft, tus mods, tus reglas."
).pack(anchor="w", pady=(0, 18))

settings_box = ttk.LabelFrame(
    frame, text="Configuración", padding=12
)
settings_box.pack(fill="x")

ttk.Label(settings_box, text="Versión").grid(
    row=0, column=0, sticky="w", padx=6, pady=6
)
ttk.Entry(
    settings_box, textvariable=version, width=18
).grid(row=0, column=1, sticky="w", padx=6, pady=6)

ttk.Label(settings_box, text="Categor?a").grid(
    row=0, column=2, sticky="w", padx=6, pady=6
)

category_box = ttk.Combobox(
    settings_box,
    textvariable=version_category,
    values=["Release", "Snapshot", "Alpha", "Beta"],
    state="readonly",
    width=12
)
category_box.grid(row=0, column=3, sticky="w", padx=6, pady=6)

ttk.Label(settings_box, text="Versiones disponibles").grid(
    row=1, column=0, sticky="w", padx=6, pady=6
)

version_list = ttk.Combobox(
    settings_box,
    state="readonly",
    width=18
)
version_list.grid(row=1, column=1, sticky="w", padx=6, pady=6)

def refresh_versions(*_):
    try:
        all_versions = utils.get_version_list()
        type_map = {
            "Release": "release",
            "Snapshot": "snapshot",
            "Alpha": "old_alpha",
            "Beta": "old_beta"
        }
        wanted = type_map[version_category.get()]
        ids = [item["id"] for item in all_versions
               if item.get("type") == wanted]
        version_list["values"] = ids
        current = version.get().strip()
        if current in ids:
            version_list.set(current)
        elif ids:
            version_list.set(ids[0])
    except Exception as exc:
        messagebox.showerror(
            "Versiones",
            f"No se pudo cargar el cat?logo de versiones.\\n{exc}"
        )

def choose_version(_event=None):
    selected = version_list.get()
    if selected:
        version.set(selected)

version_list.bind("<<ComboboxSelected>>", choose_version)
category_box.bind("<<ComboboxSelected>>", refresh_versions)

ttk.Label(settings_box, text="Cargador").grid(
    row=2, column=0, sticky="w", padx=6, pady=6
)
ttk.Combobox(
    settings_box, textvariable=loader,
    values=["Vanilla", "Fabric", "Forge", "NeoForge", "Quilt"],
    state="readonly", width=15
).grid(row=2, column=1, sticky="w", padx=6, pady=6)

ttk.Label(settings_box, text="RAM (GB)").grid(
    row=3, column=0, sticky="w", padx=6, pady=6
)
ttk.Combobox(
    settings_box, textvariable=ram,
    values=["2", "4", "6", "8", "12", "16"],
    state="readonly", width=15
).grid(row=3, column=1, sticky="w", padx=6, pady=6)

ttk.Button(
    frame, text="Instalar Minecraft",
    command=install
).pack(fill="x", pady=(12, 6))

mods_box = ttk.LabelFrame(
    frame, text="Biblioteca de mods", padding=10
)
mods_box.pack(fill="both", expand=True, pady=6)

mods_list = tk.Listbox(
    mods_box,
    bg=INPUT,
    fg=TEXT,
    selectbackground=GREEN,
    selectforeground="#FFFFFF",
    height=6,
    relief="flat",
    borderwidth=0,
    highlightthickness=1,
    highlightbackground=BORDER,
    highlightcolor=GREEN,
    font=("Consolas", 10)
)
mods_list.pack(fill="both", expand=True, pady=(0, 8))

buttons = ttk.Frame(mods_box)
buttons.pack(fill="x")

ttk.Button(
    buttons, text="Importar .jar",
    command=import_mods
).pack(side="left", padx=(0, 6))

ttk.Button(
    buttons, text="Sincronizar mods",
    command=sync_mods
).pack(side="left")

ttk.Button(
    buttons, text="Activar / desactivar",
    command=toggle_mod
).pack(side="left", padx=(6, 0))

ttk.Button(
    frame, text="JUGAR MINECRAFT",
    command=play
).pack(fill="x", pady=8)

progress_panel = tk.Frame(frame, bg=BG)
progress_panel.pack(fill="x", pady=(0, 5))

ttk.Label(
    progress_panel, textvariable=progress_text
).pack(anchor="w", pady=(0, 3))

style.configure(
    "Creeper.Horizontal.TProgressbar",
    troughcolor=INPUT,
    background=GREEN,
    bordercolor=BORDER,
    lightcolor=GREEN,
    darkcolor=GREEN,
    thickness=10
)

install_bar = ttk.Progressbar(
    progress_panel,
    variable=progress_value,
    maximum=100,
    mode="determinate",
    style="Creeper.Horizontal.TProgressbar"
)
install_bar.pack(fill="x")

ttk.Label(
    progress_panel, textvariable=progress_count
).pack(anchor="w", pady=(2, 0))

ttk.Label(frame, textvariable=status).pack(anchor="w")

root.bind("<F6>", show_stats_window)

refresh_versions()
refresh()
root.mainloop()
