import base64
import copy
import ctypes
import http.server
import json
import mimetypes
import mmap
import os
import secrets
import shutil
import socket
import string
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import uuid
import winreg
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

APP_VERSION = "6.2.1"

BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
DATA_FILE = BASE_DIR / "accounts.json"
BACKUP_FILE = BASE_DIR / "accounts.bak.json"
SESSIONS_DIR = BASE_DIR / "sessions"
TRASH_DIR = BASE_DIR / "trash"
BANNERS_DIR = BASE_DIR / "banners"
CONFIGS_DIR = BASE_DIR / "config_profiles"
PLUGINS_DIR = BASE_DIR / "plugins"
VAULT_FILE = BASE_DIR / "vault.enc"

for _d in (SESSIONS_DIR, TRASH_DIR, BANNERS_DIR, CONFIGS_DIR, PLUGINS_DIR):
    _d.mkdir(exist_ok=True)

LOCAL_APPDATA = Path(os.environ.get("LOCALAPPDATA", ""))
PROGRAM_DATA = Path(os.environ.get("PROGRAMDATA", "C:\\ProgramData"))
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

EPIC_CACHE_IGNORE = shutil.ignore_patterns(
    "Cache", "Code Cache", "GPUCache", "DawnCache", "DawnGraphiteCache",
    "DawnWebGPUCache", "GrShaderCache", "ShaderCache", "Service Worker",
    "*.log", "LOCK", "lockfile",
)

MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".avif": "image/avif",
}

DEFAULT_HUD_SETTINGS = {
    "orientation": "horizontal",
    "position": "top-left",
    "opacity": 0.92,
    "image": "",
    "show_image": True,
    "img_size": 42,
    "img_free": False,
    "img_x": 40,
    "img_y": 90,
    "img_opacity": 0.95,
    "show_fps": True,
    "show_clock": True,
    "show_timer": True,
    "show_cpu": True,
    "show_ram": True,
    "show_gpu": True,
    "show_media": True,
}

CORE_PLATFORMS = {
    "epic": {
        "id": "epic", "name": "Epic Games", "subtitle": "Fortnite • Rocket League",
        "processes": ["EpicGamesLauncher.exe", "EpicWebHelper.exe"], "builtin": True,
    },
    "riot": {
        "id": "riot", "name": "Riot Games", "subtitle": "Valorant • League of Legends",
        "processes": [
            "RiotClientServices.exe", "RiotClientUx.exe", "RiotClientCrashHandler.exe",
            "LeagueClient.exe", "LeagueClientUx.exe", "VALORANT-Win64-Shipping.exe",
        ],
        "builtin": True,
    },
    "steam": {
        "id": "steam", "name": "Steam", "subtitle": "Bibliothèque & Registre",
        "processes": ["steam.exe", "steamwebhelper.exe"], "builtin": True,
    },
}

DEFAULT_PLUGINS = {
    "battlenet.json": {
        "id": "battlenet", "name": "Battle.net", "subtitle": "Overwatch • Call of Duty",
        "processes": ["Battle.net.exe", "Agent.exe"],
        "session_path": "%APPDATA%\\Battle.net\\Battle.net.config",
        "default_exe": "C:\\Program Files (x86)\\Battle.net\\Battle.net Launcher.exe",
    },
    "ubisoft.json": {
        "id": "ubisoft", "name": "Ubisoft Connect", "subtitle": "Rainbow Six • Assassin's Creed",
        "processes": ["upc.exe", "UplayWebCore.exe"],
        "session_path": "%LOCALAPPDATA%\\Ubisoft Game Launcher\\users.dat",
        "default_exe": "C:\\Program Files (x86)\\Ubisoft\\Ubisoft Game Launcher\\upc.exe",
    },
    "ea.json": {
        "id": "ea", "name": "EA App", "subtitle": "Apex Legends • EA FC",
        "processes": ["EADesktop.exe", "EABackgroundService.exe"],
        "session_path": "%LOCALAPPDATA%\\Electronic Arts\\EA Desktop\\user_settings.ini",
        "default_exe": "C:\\Program Files\\Electronic Arts\\EA Desktop\\EA Desktop\\EADesktop.exe",
    },
    "minecraft.json": {
        "id": "minecraft", "name": "Minecraft", "subtitle": "Launcher Officiel",
        "processes": ["Minecraft.exe", "MinecraftLauncher.exe"],
        "session_path": "%APPDATA%\\.minecraft\\launcher_accounts_microsoft_store.json",
        "default_exe": "C:\\XboxGames\\Minecraft Launcher\\Content\\Minecraft.exe",
    },
}


# === SERVEUR LOCAL POUR BANNIÈRES & IMAGES HUD ===
class LocalAssetServer:
    def __init__(self, directory: Path):
        self.directory = directory
        self.port = 0
        self._server = None
        self._start()

    def _start(self):
        root_dir = self.directory

        class AssetHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def do_GET(self):
                raw_name = self.path.split("?", 1)[0].lstrip("/")
                fname = Path(urllib.parse.unquote(raw_name)).name
                fpath = root_dir / fname
                if not fname or not fpath.exists() or not fpath.is_file():
                    self.send_error(404)
                    return
                mime = MIME_MAP.get(fpath.suffix.lower()) or mimetypes.guess_type(str(fpath))[0] or "application/octet-stream"
                try:
                    data = fpath.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(data)
                except Exception:
                    pass

        self._server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), AssetHandler)
        self.port = self._server.server_address[1]
        threading.Thread(target=self._server.serve_forever, daemon=True).start()

    def url_for(self, filename: str) -> str:
        safe = urllib.parse.quote(Path(filename).name)
        return f"http://127.0.0.1:{self.port}/{safe}?v={int(time.time() * 1000)}"

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server.server_close()


# === COMPTEUR FPS RÉEL (RTSS + WINDOWS DXGI ETW + FRÉQUENCE ÉCRAN) ===
class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_ulong),
        ("Data2", ctypes.c_ushort),
        ("Data3", ctypes.c_ushort),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class _EVENT_TRACE_PROPERTIES(ctypes.Structure):
    _fields_ = [
        ("WnodeBufferSize", ctypes.c_ulong),
        ("WnodeProviderId", ctypes.c_ulong),
        ("WnodeHistoricalContext", ctypes.c_uint64),
        ("WnodeTimeStamp", ctypes.c_int64),
        ("WnodeGuid", _GUID),
        ("WnodeClientContext", ctypes.c_ulong),
        ("WnodeFlags", ctypes.c_ulong),
        ("BufferSize", ctypes.c_ulong),
        ("MinimumBuffers", ctypes.c_ulong),
        ("MaximumBuffers", ctypes.c_ulong),
        ("MaximumFileSize", ctypes.c_ulong),
        ("LogFileMode", ctypes.c_ulong),
        ("FlushTimer", ctypes.c_ulong),
        ("EnableFlags", ctypes.c_ulong),
        ("AgeLimit", ctypes.c_long),
        ("NumberOfBuffers", ctypes.c_ulong),
        ("FreeBuffers", ctypes.c_ulong),
        ("EventsLost", ctypes.c_ulong),
        ("BuffersWritten", ctypes.c_ulong),
        ("LogBuffersLost", ctypes.c_ulong),
        ("RealTimeBuffersLost", ctypes.c_ulong),
        ("LoggerThreadId", ctypes.c_void_p),
        ("LogFileNameOffset", ctypes.c_ulong),
        ("LoggerNameOffset", ctypes.c_ulong),
    ]


class _TRACE_LOGFILEW(ctypes.Structure):
    _fields_ = [
        ("LogFileName", ctypes.c_wchar_p),
        ("LoggerName", ctypes.c_wchar_p),
        ("CurrentTime", ctypes.c_int64),
        ("BuffersRead", ctypes.c_ulong),
        ("ProcessTraceMode", ctypes.c_ulong),
        ("CurrentEvent", ctypes.c_byte * 128),
        ("LogfileHeader", ctypes.c_byte * 280),
        ("BufferCallback", ctypes.c_void_p),
        ("BufferSize", ctypes.c_ulong),
        ("Filled", ctypes.c_ulong),
        ("EventsLost", ctypes.c_ulong),
        ("EventRecordCallback", ctypes.c_void_p),
        ("IsKernelTrace", ctypes.c_ulong),
        ("Context", ctypes.c_void_p),
    ]


def _get_monitor_hz() -> int:
    try:
        hdc = ctypes.windll.user32.GetDC(0)
        hz = ctypes.windll.gdi32.GetDeviceCaps(hdc, 116)
        ctypes.windll.user32.ReleaseDC(0, hdc)
        return hz if hz > 1 else 60
    except Exception:
        return 60


def _read_rtss_fps() -> int:
    try:
        mm = mmap.mmap(-1, 4096, tagname="RTSSSharedMemoryV2", access=mmap.ACCESS_READ)
        sig, ver, app_size, app_off, osd_size, osd_off, osd_slots, app_slots = struct.unpack_from("<IIIIIIII", mm, 0)
        if sig != 0x52545353:
            mm.close()
            return 0
        best_fps = 0
        now_ms = ctypes.windll.kernel32.GetTickCount()
        for i in range(min(app_slots, 32)):
            base = app_off + i * app_size
            if base + 280 > 4096:
                break
            pid = struct.unpack_from("<I", mm, base)[0]
            if pid == 0:
                continue
            t0, t1, frames = struct.unpack_from("<III", mm, base + 264)
            if t1 > t0 and (now_ms - t1) < 2500 and frames > 0:
                fps = int(round((frames * 1000.0) / (t1 - t0)))
                if fps > best_fps:
                    best_fps = fps
        mm.close()
        return best_fps
    except Exception:
        return 0


class DwmFpsMeter:
    def __init__(self):
        self._etw_frames = 0
        self._last_t = time.perf_counter()
        self._etw_active = False
        self._start_dxgi_etw()

    def _start_dxgi_etw(self):
        try:
            advapi = ctypes.windll.advapi32
            session_name = "venUsDxgiFpsTrace"
            name_bytes = (session_name + "\x00").encode("utf-16-le")
            buf_size = ctypes.sizeof(_EVENT_TRACE_PROPERTIES) + len(name_bytes) + 64
            buf = ctypes.create_string_buffer(buf_size)
            props = ctypes.cast(buf, ctypes.POINTER(_EVENT_TRACE_PROPERTIES)).contents
            props.WnodeBufferSize = buf_size
            props.WnodeFlags = 0x00020000
            props.WnodeClientContext = 1
            props.LogFileMode = 0x00000100
            props.LoggerNameOffset = ctypes.sizeof(_EVENT_TRACE_PROPERTIES)

            advapi.ControlTraceW(0, session_name, buf, 1)

            handle = ctypes.c_uint64(0)
            if advapi.StartTraceW(ctypes.byref(handle), session_name, buf) != 0:
                return

            dxgi_guid = _GUID(0xCA11C036, 0x0102, 0x4A2D, (ctypes.c_ubyte * 8)(0xA6, 0xAD, 0xF0, 0x3C, 0xFE, 0xD5, 0xD3, 0xC9))
            advapi.EnableTraceEx2(handle, ctypes.byref(dxgi_guid), 1, 4, 0, 0, 0, None)
            self._etw_active = True

            EVENT_CB = ctypes.WINFUNCTYPE(None, ctypes.c_void_p)
            def on_event(_record):
                self._etw_frames += 1
            self._cb_ref = EVENT_CB(on_event)

            def trace_worker():
                log = _TRACE_LOGFILEW()
                log.LoggerName = session_name
                log.ProcessTraceMode = 0x10000100
                log.EventRecordCallback = ctypes.cast(self._cb_ref, ctypes.c_void_p)
                th = advapi.OpenTraceW(ctypes.byref(log))
                if th != ctypes.c_uint64(-1).value:
                    advapi.ProcessTrace(ctypes.byref(th), 1, None, None)

            threading.Thread(target=trace_worker, daemon=True).start()
        except Exception:
            self._etw_active = False

    def sample(self) -> int:
        rtss = _read_rtss_fps()
        if rtss > 0:
            return rtss

        now = time.perf_counter()
        dt = now - self._last_t
        if self._etw_active and dt > 0.1:
            frames = self._etw_frames
            self._etw_frames = 0
            self._last_t = now
            fps = int(round(frames / dt))
            if fps > 5:
                return min(999, fps)

        return _get_monitor_hz()


def trim_windows_working_sets() -> int:
    if not psutil:
        return 0
    trimmed = 0
    my_pid = os.getpid()
    protected = {
        "system", "registry", "smss.exe", "csrss.exe", "wininit.exe", "services.exe",
        "lsass.exe", "svchost.exe", "dwm.exe", "audiodg.exe", "msmpeng.exe", "vgc.exe", "vgtray.exe",
    }
    try:
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        for proc in psutil.process_iter(["pid", "name"]):
            pid = proc.info.get("pid", 0)
            name = (proc.info.get("name") or "").lower()
            if pid <= 4 or pid == my_pid or name in protected:
                continue
            handle = kernel32.OpenProcess(0x0500, False, pid)
            if handle:
                try:
                    if psapi.EmptyWorkingSet(handle):
                        trimmed += 1
                finally:
                    kernel32.CloseHandle(handle)
    except Exception:
        pass
    return trimmed


def clean_temp_files_safe() -> int:
    removed_bytes = 0
    temp_dir = Path(tempfile.gettempdir())
    if not temp_dir.exists():
        return 0
    for item in list(temp_dir.iterdir()):
        try:
            if item.is_file():
                sz = item.stat().st_size
                item.unlink()
                removed_bytes += sz
        except Exception:
            pass
    return int(removed_bytes / (1024 * 1024))


def ensure_default_plugins():
    if not list(PLUGINS_DIR.glob("*.json")):
        for fname, content in DEFAULT_PLUGINS.items():
            (PLUGINS_DIR / fname).write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")


def load_all_platforms():
    ensure_default_plugins()
    platforms = copy.deepcopy(CORE_PLATFORMS)
    for pf in sorted(PLUGINS_DIR.glob("*.json")):
        try:
            cfg = json.loads(pf.read_text(encoding="utf-8"))
            pid = cfg.get("id", pf.stem).strip().lower()
            if pid and pid not in CORE_PLATFORMS:
                cfg["id"] = pid
                cfg["builtin"] = False
                cfg["plugin_file"] = pf.name
                platforms[pid] = cfg
        except Exception:
            pass
    return platforms


def get_epic_saved_dir():
    return LOCAL_APPDATA / "EpicGamesLauncher" / "Saved"


def get_epic_webcaches():
    saved = get_epic_saved_dir()
    return [p for p in saved.glob("webcache*") if p.is_dir()] if saved.exists() else []


def get_session_path(plat_id, platforms):
    if plat_id == "epic":
        config_dir = get_epic_saved_dir() / "Config"
        for p in (config_dir / "WindowsEditor" / "GameUserSettings.ini", config_dir / "Windows" / "GameUserSettings.ini"):
            if p.exists():
                return p
        if config_dir.exists():
            for p in config_dir.rglob("GameUserSettings.ini"):
                return p
        return config_dir / "WindowsEditor" / "GameUserSettings.ini"
    if plat_id == "riot":
        return LOCAL_APPDATA / "Riot Games" / "Riot Client" / "Data" / "RiotGamesPrivateSettings.yaml"
    if plat_id == "steam":
        return None
    raw = platforms.get(plat_id, {}).get("session_path", "")
    return Path(os.path.expandvars(raw)) if raw else None


def close_processes(process_list, fast=False):
    closed = 0
    if not process_list:
        return 0
    if not fast:
        for proc in process_list:
            subprocess.run(["taskkill", "/IM", proc], creationflags=CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1.8)
    for proc in process_list:
        res = subprocess.run(["taskkill", "/F", "/IM", proc], creationflags=CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            closed += 1
    time.sleep(0.4 if fast else 0.8)
    return closed


def detect_exe_path(plat_id, platforms):
    if plat_id == "steam":
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                exe, _ = winreg.QueryValueEx(key, "SteamExe")
                if Path(exe).exists():
                    return str(Path(exe))
        except OSError:
            pass
        default = Path(r"C:\Program Files (x86)\Steam\steam.exe")
        return str(default) if default.exists() else ""
    if plat_id == "riot":
        installs_file = PROGRAM_DATA / "Riot Games" / "RiotClientInstalls.json"
        if installs_file.exists():
            try:
                data = json.loads(installs_file.read_text(encoding="utf-8"))
                for key in ("rc_live", "rc_default", "rc_beta"):
                    if key in data and Path(data[key]).exists():
                        return data[key]
            except Exception:
                pass
        default = Path(r"C:\Riot Games\Riot Client\RiotClientServices.exe")
        return str(default) if default.exists() else ""
    if plat_id == "epic":
        for p in (
            Path(r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe"),
            Path(r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe"),
            Path(r"C:\Program Files\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe"),
        ):
            if p.exists():
                return str(p)
        return ""
    default_exe = platforms.get(plat_id, {}).get("default_exe", "")
    if default_exe and Path(os.path.expandvars(default_exe)).exists():
        return str(Path(os.path.expandvars(default_exe)))
    return ""


def send_vk(vk_code):
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, 0, 0)
        user32.keybd_event(vk_code, 0, 2, 0)
        return True
    except Exception:
        return False


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def query_gpu_metrics():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=temperature.gpu,utilization.gpu,name", "--format=csv,noheader,nounits"],
            creationflags=CREATE_NO_WINDOW, timeout=1.2, text=True,
        ).strip()
        parts = [p.strip() for p in out.split(",")]
        return {"temp": int(parts[0]), "util": int(parts[1]), "name": parts[2] if len(parts) > 2 else "NVIDIA GPU"}
    except Exception:
        return {"temp": None, "util": None, "name": "GPU"}


def get_spotify_track():
    titles = []
    try:
        user32 = ctypes.windll.user32
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def cb(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buf = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buf, length + 1)
                    t = buf.value
                    if " - " in t and not any(b in t for b in ("Visual Studio", "Chrome", "Edge", "Firefox", "venUs")):
                        pid = ctypes.c_ulong()
                        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                        if psutil:
                            try:
                                if "spotify" in psutil.Process(pid.value).name().lower():
                                    titles.append(t)
                            except Exception:
                                pass
            return True

        user32.EnumWindows(EnumWindowsProc(cb), 0)
    except Exception:
        pass
    return titles[0] if titles else ""


def get_top_memory_processes(limit=10):
    if not psutil:
        return []
    grouped = {}
    for p in psutil.process_iter(["name", "memory_info"]):
        try:
            name, mem = p.info.get("name"), p.info.get("memory_info")
            if not name or not mem:
                continue
            key = name.lower()
            if key not in grouped:
                grouped[key] = {"name": name, "mb": 0.0, "count": 0}
            grouped[key]["mb"] += mem.rss / (1024 * 1024)
            grouped[key]["count"] += 1
        except Exception:
            pass
    ranked = sorted(grouped.values(), key=lambda x: x["mb"], reverse=True)[:limit]
    for item in ranked:
        item["mb"] = int(round(item["mb"]))
    return ranked


class TelemetryMonitor:
    def __init__(self):
        self._fps = DwmFpsMeter()
        self.snapshot = {
            "cpu": 0, "ram_pct": 0, "ram_used_gb": 0.0, "ram_total_gb": 0.0, "ram_free_gb": 0.0,
            "gpu_temp": None, "gpu_util": None, "gpu_name": "GPU", "fps": 0, "track": "",
            "clock": time.strftime("%H:%M"), "top_procs": [],
        }
        self._stop = False
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        tick = 0
        if psutil:
            psutil.cpu_percent(interval=None)
        while not self._stop:
            try:
                self.snapshot["cpu"] = int(round(psutil.cpu_percent(interval=None))) if psutil else 0
                self.snapshot["fps"] = self._fps.sample()
                if psutil:
                    vm = psutil.virtual_memory()
                    self.snapshot["ram_pct"] = int(round(vm.percent))
                    self.snapshot["ram_used_gb"] = round(vm.used / (1024 ** 3), 1)
                    self.snapshot["ram_total_gb"] = round(vm.total / (1024 ** 3), 1)
                    self.snapshot["ram_free_gb"] = round(vm.available / (1024 ** 3), 1)
                self.snapshot["clock"] = time.strftime("%H:%M")
                if tick % 2 == 0:
                    gpu = query_gpu_metrics()
                    self.snapshot["gpu_temp"] = gpu["temp"]
                    self.snapshot["gpu_util"] = gpu["util"]
                    self.snapshot["gpu_name"] = gpu["name"]
                    self.snapshot["track"] = get_spotify_track()
                if tick % 3 == 0:
                    self.snapshot["top_procs"] = get_top_memory_processes(10)
                tick += 1
            except Exception:
                pass
            time.sleep(1.5)

    def stop(self):
        self._stop = True


class EncryptedVault:
    def __init__(self, path: Path):
        self.path = path
        self._fernet = None
        self._salt = None
        self._entries = []

    @property
    def exists(self):
        return self.path.exists()

    @property
    def unlocked(self):
        return self._fernet is not None

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
        return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))

    def unlock_or_create(self, password: str):
        if not HAS_CRYPTO:
            return {"ok": False, "message": "Installe cryptography : py -m pip install cryptography"}
        if len(password or "") < 4:
            return {"ok": False, "message": "Mot de passe maître trop court (4 caractères min)."}
        if not self.path.exists():
            salt = os.urandom(16)
            self._fernet = Fernet(self._derive_key(password, salt))
            self._entries = []
            self._save_with_salt(salt)
            return {"ok": True, "created": True, "entries": self._entries}
        raw = self.path.read_bytes()
        if len(raw) < 17:
            return {"ok": False, "message": "Fichier vault.enc corrompu."}
        salt, token = raw[:16], raw[16:]
        f = Fernet(self._derive_key(password, salt))
        try:
            self._entries = json.loads(f.decrypt(token).decode("utf-8"))
            self._fernet, self._salt = f, salt
            return {"ok": True, "entries": self._entries}
        except InvalidToken:
            return {"ok": False, "message": "Mot de passe maître incorrect."}

    def _save_with_salt(self, salt: bytes):
        self._salt = salt
        self.path.write_bytes(salt + self._fernet.encrypt(json.dumps(self._entries, ensure_ascii=False).encode("utf-8")))

    def lock(self):
        self._fernet = None
        self._entries = []

    def add_entry(self, title, category, username, secret, notes):
        if not self.unlocked:
            return {"ok": False, "message": "Coffre verrouillé."}
        if not (title or "").strip():
            return {"ok": False, "message": "Titre requis."}
        self._entries.append({
            "id": uuid.uuid4().hex[:8], "title": title.strip(), "category": category or "Mot de passe",
            "username": (username or "").strip(), "secret": secret or "", "notes": (notes or "").strip(),
        })
        self._save_with_salt(self._salt)
        return {"ok": True, "entries": self._entries}

    def delete_entry(self, entry_id):
        if not self.unlocked:
            return {"ok": False, "message": "Coffre verrouillé."}
        self._entries = [e for e in self._entries if e["id"] != entry_id]
        self._save_with_salt(self._salt)
        return {"ok": True, "entries": self._entries}


DECK_HTML = """<!DOCTYPE html>
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>venUs Deck</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
  body{font-family:-apple-system,Segoe UI,sans-serif;background:linear-gradient(155deg,#181a1f,#030304);color:#fff;padding:24px 18px 40px;min-height:100vh}
  header{display:flex;justify-content:space-between;align-items:center;margin-bottom:22px;padding-bottom:14px;border-bottom:1px solid rgba(255,255,255,.1)}
  h1{font-size:20px;font-weight:600} h1 span{color:#a1a1aa;font-weight:400;margin-left:6px;font-size:11px;letter-spacing:.2em;text-transform:uppercase}
  .sec{font-family:monospace;font-size:10px;text-transform:uppercase;letter-spacing:.18em;color:#71717a;margin:20px 0 10px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:10px}
  button{background:linear-gradient(165deg,rgba(255,255,255,.1),rgba(255,255,255,.03));border:1px solid rgba(255,255,255,.15);border-radius:16px;color:#fff;padding:18px 14px;font-size:13px;font-weight:600;cursor:pointer;display:flex;flex-direction:column;gap:5px;text-align:left}
  .tag{font-family:monospace;font-size:10px;color:#a1a1aa;font-weight:400}
  .prime{background:#fff;color:#050506;border-color:#fff} .prime .tag{color:#52525b}
  #toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#14161a;border:1px solid rgba(255,255,255,.25);padding:10px 18px;border-radius:12px;font-size:12px;opacity:0;transition:opacity .25s}
  #toast.show{opacity:1}
</style></head><body>
  <header><h1>venUs<span>silver</span></h1></header>
  <div class="sec">Système</div>
  <div class="grid">
    <button class="prime" onclick="act('boost_max')">BOOST MAX<span class="tag">Safe RAM</span></button>
    <button onclick="act('game_mode')">Game Mode<span class="tag">Boost + HUD</span></button>
    <button onclick="act('toggle_overlay')">HUD Overlay<span class="tag">ON / OFF</span></button>
  </div>
  <div class="sec">Média</div>
  <div class="grid">
    <button onclick="act('media_play')">Play / Pause<span class="tag">Spotify</span></button>
    <button onclick="act('media_prev')">Précédent<span class="tag">Piste</span></button>
    <button onclick="act('media_next')">Suivant<span class="tag">Piste</span></button>
    <button onclick="act('media_mute')">Mute<span class="tag">Audio</span></button>
  </div>
  <div class="sec">Comptes</div><div class="grid" id="acc-grid"></div><div id="toast"></div>
<script>
  function toast(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2400);}
  async function act(name,p={}){const r=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:name,...p})});const d=await r.json();toast(d.message||'OK');}
  fetch('/api/accounts').then(r=>r.json()).then(d=>{document.getElementById('acc-grid').innerHTML=d.accounts.map(a=>`<button onclick="act('launch',{plat:'${a.plat}',id:'${a.id}'})">${a.label}<span class="tag">${a.plat_name}</span></button>`).join('');});
</script></body></html>"""


class StreamDeckServer:
    def __init__(self, backend):
        self._backend = backend
        self.server = None
        self.port = 8765
        self.running = False

    def start(self):
        if self.running:
            return {"ok": True, "url": f"http://{get_local_ip()}:{self.port}", "running": True}
        backend = self._backend

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def _send_json(self, obj, code=200):
                body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/api/accounts":
                    items = [
                        {"plat": pid, "plat_name": meta["name"], "id": a["id"], "label": a["label"]}
                        for pid, meta in backend._platforms.items()
                        for a in backend._data["accounts"].get(pid, [])
                    ]
                    self._send_json({"accounts": items})
                else:
                    body = DECK_HTML.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

            def do_POST(self):
                if self.path == "/api/action":
                    payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8") or "{}")
                    self._send_json(backend.run_macro(payload.get("action", ""), payload))
                else:
                    self._send_json({"ok": False}, 404)

        try:
            self.server = http.server.ThreadingHTTPServer(("0.0.0.0", self.port), Handler)
            self.running = True
            threading.Thread(target=self.server.serve_forever, daemon=True).start()
            return {"ok": True, "url": f"http://{get_local_ip()}:{self.port}", "running": True}
        except OSError as e:
            return {"ok": False, "message": f"Port {self.port} occupé : {e}", "running": False}

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        self.running = False
        return {"ok": True, "running": False}


# === HUD OVERLAY SANS FOND BLANC + COINS ARRONDIS WIN11 ===
# === HUD OVERLAY AUTO-AJUSTÉ + INVISIBLE BARRE DES TÂCHES ===
def run_overlay_hud():
    import webview

    hud_cfg = dict(DEFAULT_HUD_SETTINGS)
    if DATA_FILE.exists():
        try:
            loaded = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            hud_cfg.update(loaded.get("settings", {}).get("hud", {}))
        except Exception:
            pass

    vertical = hud_cfg.get("orientation") == "vertical"
    opacity = max(0.35, min(1.0, float(hud_cfg.get("opacity", 0.92))))
    position = hud_cfg.get("position", "top-left")
    img_size = max(24, min(360, int(hud_cfg.get("img_size", 42))))
    img_free = bool(hud_cfg.get("img_free", False))

    img_rel = hud_cfg.get("image", "")
    img_path = (BASE_DIR / img_rel) if img_rel else None
    img_data_url = ""
    if img_path and img_path.exists():
        try:
            mime = MIME_MAP.get(img_path.suffix.lower(), "image/png")
            img_data_url = f"data:{mime};base64,{base64.b64encode(img_path.read_bytes()).decode('ascii')}"
        except Exception:
            pass

    fps_meter = DwmFpsMeter()
    t0 = time.time()
    cache = {"gpu": "N/A", "track": "—", "tick": 0}
    last_size = {"w": 0, "h": 0}
    hud_win = None
    free_win = None
    user32 = ctypes.windll.user32

    class HudBridge:
        def get_metrics(self):
            hh, rem = divmod(int(time.time() - t0), 3600)
            mm, ss = divmod(rem, 60)
            fval = fps_meter.sample()
            cpu = f"{int(psutil.cpu_percent())}%" if psutil else "--%"
            ram = f"{int(psutil.virtual_memory().percent)}%" if psutil else "--%"
            if cache["tick"] % 3 == 0:
                g = query_gpu_metrics()
                cache["gpu"] = f"{g['temp']}°C" if g["temp"] is not None else "N/A"
                tr = get_spotify_track()
                cache["track"] = (tr[:24] + "…") if len(tr) > 24 else (tr or "—")
            cache["tick"] += 1
            return {
                "fps": f"{fval} FPS" if fval > 0 else "-- FPS",
                "clock": time.strftime("%H:%M"),
                "timer": f"{hh:02d}:{mm:02d}:{ss:02d}",
                "cpu": cpu,
                "ram": ram,
                "gpu": cache["gpu"],
                "media": cache["track"],
            }

        def fit_window(self, w, h):
            if not hud_win:
                return
            nw, nh = max(120, int(w)), max(38, int(h))
            if abs(nw - last_size["w"]) > 2 or abs(nh - last_size["h"]) > 2:
                last_size["w"], last_size["h"] = nw, nh
                hud_win.resize(nw, nh)

        def close_hud(self):
            if free_win:
                try:
                    free_win.destroy()
                except Exception:
                    pass
            if hud_win:
                hud_win.destroy()

        def save_free_pos(self):
            if not free_win:
                return
            try:
                if DATA_FILE.exists():
                    d = json.loads(DATA_FILE.read_text(encoding="utf-8"))
                    d.setdefault("settings", {}).setdefault("hud", {})["img_x"] = int(free_win.x)
                    d["settings"]["hud"]["img_y"] = int(free_win.y)
                    DATA_FILE.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception:
                pass

    blocks = []
    if hud_cfg.get("show_image", True) and not img_free:
        if img_data_url:
            sz = min(28, img_size)
            blocks.append(f'<img src="{img_data_url}" style="width:{sz}px;height:{sz}px;border-radius:6px;object-fit:cover;flex-shrink:0;" />')
        else:
            blocks.append('<div class="brand"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5"><path d="M4 5l8 14L20 5"/></svg><span>venUs</span></div>')

    if hud_cfg.get("show_fps", True):
        blocks.append('<span class="fps" id="m-fps">-- FPS</span>')
    if hud_cfg.get("show_clock", True):
        blocks.append('<span class="val" id="m-clock">--:--</span>')
    if hud_cfg.get("show_timer", True):
        blocks.append('<span class="val" id="m-timer">00:00:00</span>')
    if hud_cfg.get("show_cpu", True):
        blocks.append('<div class="kv"><span class="k">CPU</span><span class="v" id="m-cpu">--%</span></div>')
    if hud_cfg.get("show_ram", True):
        blocks.append('<div class="kv"><span class="k">RAM</span><span class="v" id="m-ram">--%</span></div>')
    if hud_cfg.get("show_gpu", True):
        blocks.append('<div class="kv"><span class="k">GPU</span><span class="v" id="m-gpu">--</span></div>')
    if hud_cfg.get("show_media", True):
        blocks.append('<div class="kv"><span class="k">♪</span><span class="v" id="m-media">—</span></div>')

    hud_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><style>
  *{{box-sizing:border-box;margin:0;padding:0;user-select:none}}
  html,body{{background:#0a0b0e;overflow:hidden;font-family:'Cascadia Code','Consolas',monospace}}
  .pill{{
    display:inline-flex;align-items:center;gap:14px;padding:10px 15px;
    background:#0a0b0e;border:1px solid rgba(255,255,255,0.16);border-top-color:rgba(255,255,255,0.3);
    border-radius:8px;color:#e5e7eb;font-size:12px;white-space:nowrap;
  }}
  .pill.vertical{{flex-direction:column;align-items:flex-start;gap:8px;padding:12px 15px;min-width:150px}}
  .brand{{display:flex;align-items:center;gap:6px;font-family:'Segoe UI',sans-serif;font-weight:700;color:#fff;font-size:13px}}
  .fps{{color:#34d399;font-weight:700}}
  .val{{color:#f4f5f7}}
  .kv{{display:flex;align-items:baseline;gap:5px}}
  .k{{font-size:10px;color:#8e95a2}}
  .v{{color:#f4f5f7;font-weight:600}}
  .close{{color:#71717a;cursor:pointer;font-size:12px;padding-left:4px}}
  .close:hover{{color:#fff}}
</style></head><body>
  <div id="pill" class="pill {'vertical' if vertical else ''} pywebview-drag-region">
    {''.join(blocks)}
    <span class="close" onclick="window.pywebview.api.close_hud()">✕</span>
  </div>
<script>
  function syncSize(){{
    const p=document.getElementById('pill');
    if(!p) return;
    const r=p.getBoundingClientRect();
    window.pywebview.api.fit_window(Math.ceil(r.width), Math.ceil(r.height));
  }}
  async function tick(){{
    try{{
      const d=await window.pywebview.api.get_metrics();
      for(const k of ['fps','clock','timer','cpu','ram','gpu','media']){{
        const el=document.getElementById('m-'+k);
        if(el) el.textContent=d[k];
      }}
      syncSize();
    }}catch{{}}
  }}
  window.addEventListener('pywebviewready',()=>{{tick();setInterval(tick,1000);}});
</script></body></html>"""

    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    ww, wh = (165, 220) if vertical else (520, 42)
    margin = 20
    pos_map = {
        "top-left": (margin, margin),
        "top-right": (max(margin, sw - ww - margin), margin),
        "bottom-left": (margin, max(margin, sh - wh - 64)),
        "bottom-right": (max(margin, sw - ww - margin), max(margin, sh - wh - 64)),
    }
    px, py = pos_map.get(position, (margin, margin))

    bridge = HudBridge()
    hud_win = webview.create_window(
        "venUs HUD",
        html=hud_html,
        js_api=bridge,
        x=px,
        y=py,
        width=ww,
        height=wh,
        min_size=(10, 10),
        frameless=True,
        on_top=True,
        background_color="#0a0b0e",
        easy_drag=True,
    )

    def apply_win_style():
        time.sleep(0.35)
        for title, alpha in (("venUs HUD", opacity), ("venUs HUD Image", float(hud_cfg.get("img_opacity", 0.95)))):
            try:
                hwnd = user32.FindWindowW(None, title)
                if hwnd:
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(ctypes.c_int(2)), 4)
                    ex = user32.GetWindowLongW(hwnd, -20)
                    # Layered (opacité) + ToolWindow (masque de la barre des tâches)
                    user32.SetWindowLongW(hwnd, -20, (ex | 0x00080000 | 0x00000080) & ~0x00040000)
                    user32.SetLayeredWindowAttributes(hwnd, 0, int(max(0.2, min(1.0, alpha)) * 255), 0x02)
            except Exception:
                pass

    if hud_cfg.get("show_image", True) and img_free and img_data_url:
        free_html = f"""<!DOCTYPE html><html><head><style>
          *{{margin:0;padding:0;user-select:none}}
          html,body{{width:100%;height:100%;background:#0a0b0e;overflow:hidden}}
          img{{width:100%;height:100%;object-fit:contain;display:block}}
        </style></head><body class="pywebview-drag-region" onmouseup="window.pywebview.api.save_free_pos()">
          <img src="{img_data_url}" />
        </body></html>"""
        free_win = webview.create_window(
            "venUs HUD Image",
            html=free_html,
            js_api=bridge,
            x=int(hud_cfg.get("img_x", 40)),
            y=int(hud_cfg.get("img_y", 90)),
            width=img_size,
            height=img_size,
            frameless=True,
            on_top=True,
            background_color="#0a0b0e",
            easy_drag=True,
        )

    webview.start(apply_win_style)


# === API PRINCIPALE VENUS v6.2.1 ===
class VenusTitaniumAPI:
    def __init__(self, get_window_fn):
        self._get_window = get_window_fn
        self._is_maximized = False
        self._platforms = load_all_platforms()
        self._data = self._load_data()
        self._vault = EncryptedVault(VAULT_FILE)
        self._deck = StreamDeckServer(self)
        self._assets = LocalAssetServer(BANNERS_DIR)
        self._telemetry = TelemetryMonitor()
        self._overlay_proc = None
        self._game_mode = False
        self._last_boost = {"freed_mb": 0, "trimmed": 0, "temp_mb": 0, "at": ""}

    def _load_data(self):
        default_data = {
            "paths": {pid: detect_exe_path(pid, self._platforms) for pid in self._platforms},
            "accounts": {pid: [] for pid in self._platforms},
            "trash": [],
            "settings": {
                "sound": True, "ram_boost_enabled": True, "ram_deep_trim": True, "ram_high_power": True,
                "ram_kill_list": ["chrome.exe", "msedge.exe", "opera.exe"],
                "github_repo": "", "hud": copy.deepcopy(DEFAULT_HUD_SETTINGS),
            },
            "config_profiles": [], "file_configs": [],
        }
        src_file = DATA_FILE if DATA_FILE.exists() else (BACKUP_FILE if BACKUP_FILE.exists() else None)
        if src_file:
            try:
                loaded = json.loads(src_file.read_text(encoding="utf-8"))
                default_data["paths"].update(loaded.get("paths", {}))
                for pid, accs in loaded.get("accounts", {}).items():
                    default_data["accounts"][pid] = accs
                default_data["trash"] = loaded.get("trash", [])
                loaded_st = loaded.get("settings", {})
                loaded_hud = loaded_st.pop("hud", {}) if isinstance(loaded_st, dict) else {}
                default_data["settings"].update(loaded_st)
                default_data["settings"]["hud"].update(loaded_hud)
                default_data["config_profiles"] = loaded.get("config_profiles", [])
                default_data["file_configs"] = loaded.get("file_configs", [])
            except Exception:
                pass
        for pid in self._platforms:
            default_data["accounts"].setdefault(pid, [])
            default_data["paths"].setdefault(pid, detect_exe_path(pid, self._platforms))
        return default_data

    def _save_data(self):
        if DATA_FILE.exists():
            try:
                shutil.copy2(DATA_FILE, BACKUP_FILE)
            except Exception:
                pass
        DATA_FILE.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _resolve_banner_url(self, value: str) -> str:
        if not value:
            return ""
        if value.startswith(("http://", "https://", "data:")):
            return value
        p = BASE_DIR / value
        if p.exists():
            return self._assets.url_for(p.name)
        p2 = BANNERS_DIR / Path(value).name
        if p2.exists():
            return self._assets.url_for(p2.name)
        return ""

    def _client_state(self):
        view = copy.deepcopy(self._data)
        for pid in list(view["accounts"].keys()):
            for acc in view["accounts"][pid]:
                acc["banner_src"] = self._resolve_banner_url(acc.get("banner", ""))
                acc.setdefault("playtime_sec", 0)
                acc.setdefault("rank", "")
                acc.setdefault("game_exe", "")
                acc.setdefault("launch_args", "")
                acc.setdefault("favorite", False)
        view["platforms"] = list(self._platforms.values())
        view["hud_image_src"] = self._resolve_banner_url(view["settings"]["hud"].get("image", ""))
        view["app_version"] = APP_VERSION
        view["vault_exists"] = self._vault.exists
        view["vault_unlocked"] = self._vault.unlocked
        view["deck_running"] = self._deck.running
        view["deck_url"] = f"http://{get_local_ip()}:{self._deck.port}"
        view["overlay_running"] = self._overlay_proc is not None and self._overlay_proc.poll() is None
        view["game_mode"] = self._game_mode
        view["last_boost"] = dict(self._last_boost)
        return view

    def get_state(self):
        return self._client_state()

    def get_telemetry(self):
        snap = dict(self._telemetry.snapshot)
        snap["overlay_running"] = self._overlay_proc is not None and self._overlay_proc.poll() is None
        snap["last_boost"] = dict(self._last_boost)
        return snap

    def win_minimize(self):
        w = self._get_window()
        if w:
            w.minimize()

    def win_toggle_maximize(self):
        w = self._get_window()
        if not w:
            return
        if self._is_maximized:
            w.restore()
            self._is_maximized = False
        else:
            w.maximize()
            self._is_maximized = True
        return {"maximized": self._is_maximized}

    def win_close(self):
        self._telemetry.stop()
        self._deck.stop()
        self._assets.stop()
        if self._overlay_proc and self._overlay_proc.poll() is None:
            self._overlay_proc.terminate()
        w = self._get_window()
        if w:
            w.destroy()

    def save_settings(self, updates):
        self._data["settings"].update(updates or {})
        self._save_data()
        return {"ok": True, "state": self._client_state()}

    def _open_file_dialog(self, file_types):
        import webview
        w = self._get_window()
        if not w:
            return None
        dtype = getattr(getattr(webview, "FileDialog", None), "OPEN", getattr(webview, "OPEN_DIALOG", 10))
        res = w.create_file_dialog(dtype, allow_multiple=False, file_types=file_types)
        return res[0] if res and len(res) > 0 else None

    def run_boost_max(self, also_close_targets=False):
        before_mb = int(psutil.virtual_memory().used / (1024 * 1024)) if psutil else 0
        closed = 0
        if also_close_targets:
            kill_list = self._data["settings"].get("ram_kill_list", [])
            if kill_list:
                closed = close_processes(kill_list, fast=True)
        t1 = trim_windows_working_sets()
        time.sleep(0.25)
        t2 = trim_windows_working_sets()
        trimmed = max(t1, t2)
        temp_mb = clean_temp_files_safe()
        if self._data["settings"].get("ram_high_power", True):
            subprocess.run(["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"], creationflags=CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.35)
        after_mb = int(psutil.virtual_memory().used / (1024 * 1024)) if psutil else before_mb
        freed_mb = max(0, before_mb - after_mb)
        self._last_boost = {"freed_mb": freed_mb, "trimmed": trimmed, "temp_mb": temp_mb, "at": time.strftime("%H:%M:%S")}
        freed_txt = f"{freed_mb / 1024:.2f} Go" if freed_mb >= 1024 else f"{freed_mb} Mo"
        extra = f" • {temp_mb} Mo temp" if temp_mb > 0 else ""
        if closed > 0:
            extra += f" • {closed} app(s) fermée(s)"
        return {"ok": True, "message": f"BOOST MAX : {freed_txt} libérés ({trimmed} processus optimisés{extra}).", "state": self._client_state()}

    def kill_single_process(self, proc_name):
        if not proc_name:
            return {"ok": False, "message": "Invalide."}
        close_processes([proc_name], fast=True)
        return {"ok": True, "message": f"{proc_name} fermé."}

    def toggle_proc_in_boost_list(self, proc_name):
        proc_name = (proc_name or "").strip()
        if not proc_name:
            return {"ok": False, "message": "Invalide."}
        lst = self._data["settings"].setdefault("ram_kill_list", [])
        if proc_name.lower() in [x.lower() for x in lst]:
            self._data["settings"]["ram_kill_list"] = [x for x in lst if x.lower() != proc_name.lower()]
            msg = f"{proc_name} retiré."
        else:
            lst.append(proc_name)
            msg = f"{proc_name} ajouté."
        self._save_data()
        return {"ok": True, "message": msg, "state": self._client_state()}

    def save_hud_settings(self, hud_updates):
        self._data["settings"]["hud"].update(hud_updates or {})
        self._save_data()
        if self._overlay_proc and self._overlay_proc.poll() is None:
            self._overlay_proc.terminate()
            self._overlay_proc = None
            self._start_overlay_proc()
        return {"ok": True, "message": "HUD mis à jour.", "state": self._client_state()}

    def pick_hud_image(self):
        path = self._open_file_dialog(("Images (*.png;*.jpg;*.jpeg;*.webp;*.gif;*.bmp)", "Tous les fichiers (*.*)"))
        if not path:
            return {"ok": False, "cancelled": True}
        src = Path(path)
        if not src.exists():
            return {"ok": False, "message": "Image introuvable."}
        old = self._data["settings"]["hud"].get("image", "")
        if old:
            (BASE_DIR / old).unlink(missing_ok=True)
        dest_name = f"hud_img_{uuid.uuid4().hex[:6]}.png"
        dest = BANNERS_DIR / dest_name
        if HAS_PIL:
            try:
                im = Image.open(src).convert("RGBA")
                im.thumbnail((420, 420))
                im.save(dest, "PNG")
            except Exception:
                dest_name = f"hud_img_{uuid.uuid4().hex[:6]}{src.suffix.lower() or '.png'}"
                shutil.copy2(src, BANNERS_DIR / dest_name)
        else:
            dest_name = f"hud_img_{uuid.uuid4().hex[:6]}{src.suffix.lower() or '.png'}"
            shutil.copy2(src, BANNERS_DIR / dest_name)
        self._data["settings"]["hud"]["image"] = f"banners/{dest_name}"
        self._data["settings"]["hud"]["show_image"] = True
        self._save_data()
        if self._overlay_proc and self._overlay_proc.poll() is None:
            self._overlay_proc.terminate()
            self._overlay_proc = None
            self._start_overlay_proc()
        return {"ok": True, "message": "Image HUD importée.", "state": self._client_state()}

    def clear_hud_image(self):
        old = self._data["settings"]["hud"].get("image", "")
        if old:
            (BASE_DIR / old).unlink(missing_ok=True)
        self._data["settings"]["hud"]["image"] = ""
        self._save_data()
        if self._overlay_proc and self._overlay_proc.poll() is None:
            self._overlay_proc.terminate()
            self._overlay_proc = None
            self._start_overlay_proc()
        return {"ok": True, "message": "Logo venUs restauré.", "state": self._client_state()}

    def _start_overlay_proc(self):
        cmd = [sys.executable, "--overlay"] if getattr(sys, "frozen", False) else [sys.executable, str(BASE_DIR / "venus_app.py"), "--overlay"]
        self._overlay_proc = subprocess.Popen(cmd, creationflags=CREATE_NO_WINDOW)

    def toggle_overlay(self):
        if self._overlay_proc and self._overlay_proc.poll() is None:
            self._overlay_proc.terminate()
            self._overlay_proc = None
            return {"ok": True, "running": False, "message": "HUD désactivé.", "state": self._client_state()}
        try:
            self._start_overlay_proc()
            return {"ok": True, "running": True, "message": "HUD activé (FPS + Image).", "state": self._client_state()}
        except Exception as e:
            return {"ok": False, "message": f"Erreur HUD : {e}"}

    def toggle_game_mode(self):
        self._game_mode = not self._game_mode
        if self._game_mode:
            r = self.run_boost_max(False)
            if self._overlay_proc is None or self._overlay_proc.poll() is not None:
                self._start_overlay_proc()
            return {"ok": True, "active": True, "message": f"Game Mode ON — {r['message']}", "state": self._client_state()}
        if self._overlay_proc and self._overlay_proc.poll() is None:
            self._overlay_proc.terminate()
            self._overlay_proc = None
        return {"ok": True, "active": False, "message": "Game Mode désactivé.", "state": self._client_state()}

    def configure_exe_path(self, plat):
        path = self._open_file_dialog(("Exécutable Windows (*.exe)",))
        if path:
            self._data["paths"][plat] = path
            self._save_data()
            return {"ok": True, "message": "Exécutable enregistré.", "state": self._client_state()}
        return {"ok": False, "cancelled": True}

    def pick_game_exe(self):
        path = self._open_file_dialog(("Exécutable de jeu (*.exe)",))
        return {"ok": bool(path), "path": path or ""}

    def toggle_favorite(self, plat, acc_id):
        acc = next((a for a in self._data["accounts"].get(plat, []) if a["id"] == acc_id), None)
        if not acc:
            return {"ok": False, "message": "Introuvable."}
        acc["favorite"] = not acc.get("favorite", False)
        self._save_data()
        return {"ok": True, "message": "Épinglé au Hub." if acc["favorite"] else "Retiré du Hub.", "state": self._client_state()}

    def add_steam_account(self, label, steam_login, rank="", game_exe="", launch_args=""):
        label, steam_login = (label or "").strip(), (steam_login or "").strip()
        if not label or not steam_login:
            return {"ok": False, "message": "Nom et identifiant Steam requis."}
        self._data["accounts"].setdefault("steam", []).append({
            "id": uuid.uuid4().hex[:8], "label": label, "steam_login": steam_login,
            "rank": (rank or "").strip(), "game_exe": (game_exe or "").strip(),
            "launch_args": (launch_args or "").strip(), "playtime_sec": 0, "favorite": False,
        })
        self._save_data()
        return {"ok": True, "message": f"Compte '{label}' ajouté.", "state": self._client_state()}

    def capture_account(self, plat, label, rank="", game_exe="", launch_args=""):
        label = (label or "").strip()
        if not label:
            return {"ok": False, "message": "Nom requis."}
        meta = self._platforms.get(plat)
        if not meta:
            return {"ok": False, "message": "Plateforme inconnue."}
        try:
            close_processes(meta.get("processes", []))
            src_path = get_session_path(plat, self._platforms)
            if not src_path or not src_path.exists():
                return {"ok": False, "message": f"Session {meta['name']} introuvable. Connecte-toi d'abord."}
            if plat == "epic":
                content = src_path.read_text(encoding="utf-8", errors="ignore")
                if "[RememberMe]" not in content or "Data=" not in content:
                    return {"ok": False, "message": "Case 'Rester connecté' non détectée sur Epic."}
            acc_id = uuid.uuid4().hex[:8]
            dest_dir = SESSIONS_DIR / plat / acc_id
            dest_dir.mkdir(parents=True, exist_ok=True)
            if src_path.is_dir():
                shutil.copytree(src_path, dest_dir / src_path.name, dirs_exist_ok=True)
            else:
                shutil.copy2(src_path, dest_dir / src_path.name)
            if plat == "epic":
                for c in get_epic_webcaches():
                    try:
                        shutil.copytree(c, dest_dir / c.name, ignore=EPIC_CACHE_IGNORE, dirs_exist_ok=True)
                    except Exception:
                        pass
            self._data["accounts"].setdefault(plat, []).append({
                "id": acc_id, "label": label, "rank": (rank or "").strip(),
                "game_exe": (game_exe or "").strip(), "launch_args": (launch_args or "").strip(),
                "playtime_sec": 0, "favorite": False,
            })
            self._save_data()
            return {"ok": True, "message": f"Session '{label}' sécurisée.", "state": self._client_state()}
        except Exception as e:
            return {"ok": False, "message": f"Erreur : {e}"}

    def prepare_new_account(self, plat):
        meta = self._platforms.get(plat)
        exe_path = self._data["paths"].get(plat, "")
        if not exe_path or not Path(exe_path).exists():
            return {"ok": False, "message": f"Configure l'exécutable de {meta['name']}."}
        try:
            close_processes(meta.get("processes", []))
            sp = get_session_path(plat, self._platforms)
            if sp and sp.exists():
                shutil.rmtree(sp, ignore_errors=True) if sp.is_dir() else sp.unlink()
            if plat == "epic":
                for c in get_epic_webcaches():
                    shutil.rmtree(c, ignore_errors=True)
            os.startfile(exe_path)
            return {"ok": True, "message": f"{meta['name']} ouvert. Connecte-toi puis capture ce compte."}
        except Exception as e:
            return {"ok": False, "message": f"Erreur : {e}"}

    def _store_banner_from_path(self, acc, src: Path):
        old = acc.get("banner", "")
        if old and not old.startswith(("http://", "https://")):
            (BASE_DIR / old).unlink(missing_ok=True)
        ext = src.suffix.lower() if src.suffix else ".png"
        dest_name = f"{acc['id']}_{uuid.uuid4().hex[:6]}{ext}"
        shutil.copy2(src, BANNERS_DIR / dest_name)
        acc["banner"] = f"banners/{dest_name}"

    def update_account_meta(self, plat, acc_id, label, rank, game_exe, launch_args, banner_url):
        acc = next((a for a in self._data["accounts"].get(plat, []) if a["id"] == acc_id), None)
        if not acc:
            return {"ok": False, "message": "Introuvable."}
        if (label or "").strip():
            acc["label"] = label.strip()
        acc["rank"] = (rank or "").strip()
        acc["game_exe"] = (game_exe or "").strip()
        acc["launch_args"] = (launch_args or "").strip()
        b = (banner_url or "").strip().strip('"')
        if b.startswith(("http://", "https://")):
            acc["banner"] = b
        elif b and Path(b).exists() and Path(b).is_file():
            self._store_banner_from_path(acc, Path(b))
        self._save_data()
        return {"ok": True, "message": "Profil mis à jour.", "state": self._client_state()}

    def pick_banner_file(self, plat, acc_id):
        acc = next((a for a in self._data["accounts"].get(plat, []) if a["id"] == acc_id), None)
        if not acc:
            return {"ok": False, "message": "Compte introuvable."}
        try:
            path = self._open_file_dialog(("Images (*.png;*.jpg;*.jpeg;*.webp;*.gif;*.bmp)", "Tous les fichiers (*.*)"))
            if not path:
                return {"ok": False, "cancelled": True}
            src = Path(path)
            if not src.exists():
                return {"ok": False, "message": "Fichier image introuvable."}
            self._store_banner_from_path(acc, src)
            self._save_data()
            return {"ok": True, "message": "Bannière appliquée.", "state": self._client_state()}
        except Exception as e:
            return {"ok": False, "message": f"Erreur bannière : {e}"}

    def clear_banner(self, plat, acc_id):
        acc = next((a for a in self._data["accounts"].get(plat, []) if a["id"] == acc_id), None)
        if not acc:
            return {"ok": False, "message": "Introuvable."}
        old = acc.get("banner", "")
        if old and not old.startswith(("http://", "https://")):
            (BASE_DIR / old).unlink(missing_ok=True)
        acc.pop("banner", None)
        self._save_data()
        return {"ok": True, "message": "Bannière retirée.", "state": self._client_state()}

    def delete_account(self, plat, acc_id):
        accs = self._data["accounts"].get(plat, [])
        target = next((a for a in accs if a["id"] == acc_id), None)
        if not target:
            return {"ok": False, "message": "Introuvable."}
        self._data["accounts"][plat] = [a for a in accs if a["id"] != acc_id]
        src_sess = SESSIONS_DIR / plat / acc_id
        if src_sess.exists():
            dst_sess = TRASH_DIR / plat / acc_id
            dst_sess.parent.mkdir(parents=True, exist_ok=True)
            shutil.rmtree(dst_sess, ignore_errors=True)
            shutil.move(str(src_sess), str(dst_sess))
        self._data.setdefault("trash", []).append({"plat": plat, "account": target})
        self._save_data()
        return {"ok": True, "message": f"'{target['label']}' mis à la corbeille (récupérable).", "state": self._client_state()}

    def recover_accounts(self):
        restored = 0
        for item in list(self._data.get("trash", [])):
            plat, acc = item["plat"], item["account"]
            tr_dir = TRASH_DIR / plat / acc["id"]
            if tr_dir.exists():
                dst = SESSIONS_DIR / plat / acc["id"]
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.rmtree(dst, ignore_errors=True)
                shutil.move(str(tr_dir), str(dst))
            if acc["id"] not in {a["id"] for a in self._data["accounts"].get(plat, [])}:
                self._data["accounts"].setdefault(plat, []).append(acc)
                restored += 1
        self._data["trash"] = []

        if BACKUP_FILE.exists():
            try:
                bak = json.loads(BACKUP_FILE.read_text(encoding="utf-8"))
                for plat, accs in bak.get("accounts", {}).items():
                    existing = {a["id"] for a in self._data["accounts"].get(plat, [])}
                    for a in accs:
                        if a["id"] not in existing and (plat == "steam" or (SESSIONS_DIR / plat / a["id"]).exists()):
                            self._data["accounts"].setdefault(plat, []).append(a)
                            restored += 1
            except Exception:
                pass

        for plat_dir in SESSIONS_DIR.iterdir():
            if not plat_dir.is_dir():
                continue
            plat = plat_dir.name
            existing = {a["id"] for a in self._data["accounts"].get(plat, [])}
            for acc_dir in plat_dir.iterdir():
                if acc_dir.is_dir() and acc_dir.name not in existing and any(acc_dir.iterdir()):
                    self._data["accounts"].setdefault(plat, []).append({
                        "id": acc_dir.name, "label": f"Récupéré ({acc_dir.name[:4]})",
                        "rank": "", "game_exe": "", "launch_args": "", "playtime_sec": 0, "favorite": False,
                    })
                    restored += 1

        if restored > 0:
            self._save_data()
            return {"ok": True, "message": f"{restored} compte(s) restauré(s) !", "state": self._client_state()}
        return {"ok": False, "message": "Aucune session orpheline ni sauvegarde trouvée.", "state": self._client_state()}

    def _track_playtime(self, plat, acc_id, watch_names):
        if not psutil:
            return
        found, start = False, time.time()
        for _ in range(15):
            time.sleep(2)
            active = {p.name().lower() for p in psutil.process_iter(["name"]) if p.info.get("name")}
            if any(w.lower() in active for w in watch_names):
                found, start = True, time.time()
                break
        if not found:
            return
        while True:
            time.sleep(10)
            active = {p.name().lower() for p in psutil.process_iter(["name"]) if p.info.get("name")}
            if not any(w.lower() in active for w in watch_names):
                break
        elapsed = int(time.time() - start)
        if elapsed >= 15:
            acc = next((a for a in self._data["accounts"].get(plat, []) if a["id"] == acc_id), None)
            if acc:
                acc["playtime_sec"] = acc.get("playtime_sec", 0) + elapsed
                self._save_data()

    def launch_account(self, plat, acc_id):
        meta = self._platforms.get(plat)
        if not meta:
            return {"ok": False, "message": "Plateforme inconnue."}
        exe_path = self._data["paths"].get(plat, "")
        if not exe_path or not Path(exe_path).exists():
            return {"ok": False, "message": f"Exécutable {meta['name']} introuvable."}
        acc = next((a for a in self._data["accounts"].get(plat, []) if a["id"] == acc_id), None)
        if not acc:
            return {"ok": False, "message": "Compte introuvable."}
        try:
            if self._data["settings"].get("ram_boost_enabled"):
                self.run_boost_max(False)
            close_processes(meta.get("processes", []))
            if plat == "steam":
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", 0, winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, "AutoLoginUser", 0, winreg.REG_SZ, acc["steam_login"])
                    winreg.SetValueEx(key, "RememberPassword", 0, winreg.REG_DWORD, 1)
            else:
                target = get_session_path(plat, self._platforms)
                saved_dir = SESSIONS_DIR / plat / acc["id"]
                saved_item = saved_dir / target.name
                if not saved_item.exists():
                    return {"ok": False, "message": f"Session introuvable pour '{acc['label']}'."}
                if plat == "epic":
                    for c in get_epic_webcaches():
                        shutil.rmtree(c, ignore_errors=True)
                    for sc in saved_dir.glob("webcache*"):
                        if sc.is_dir():
                            shutil.copytree(sc, get_epic_saved_dir() / sc.name, dirs_exist_ok=True)
                target.parent.mkdir(parents=True, exist_ok=True)
                if saved_item.is_dir():
                    shutil.rmtree(target, ignore_errors=True)
                    shutil.copytree(saved_item, target)
                else:
                    shutil.copy2(saved_item, target)

            os.startfile(exe_path)
            watch_procs = list(meta.get("processes", []))
            game_exe, launch_args = (acc.get("game_exe") or "").strip(), (acc.get("launch_args") or "").strip()
            if game_exe:
                def delayed_game():
                    time.sleep(4.5)
                    try:
                        if "://" in game_exe:
                            os.startfile(game_exe)
                        elif Path(game_exe).exists():
                            subprocess.Popen([game_exe] + (launch_args.split() if launch_args else []), cwd=str(Path(game_exe).parent))
                    except Exception:
                        pass
                threading.Thread(target=delayed_game, daemon=True).start()
                if "://" not in game_exe:
                    watch_procs.insert(0, Path(game_exe).name)
            threading.Thread(target=self._track_playtime, args=(plat, acc_id, watch_procs), daemon=True).start()
            return {"ok": True, "message": f"{meta['name']} lancé — {acc['label']}"}
        except Exception as e:
            return {"ok": False, "message": f"Erreur : {e}"}

    def add_config_profile(self, name, game, crosshair, dpi, sens, notes):
        if not (name or "").strip():
            return {"ok": False, "message": "Nom requis."}
        self._data["config_profiles"].append({
            "id": uuid.uuid4().hex[:8], "name": name.strip(), "game": (game or "Valorant").strip(),
            "crosshair": (crosshair or "").strip(), "dpi": (dpi or "").strip(),
            "sens": (sens or "").strip(), "notes": (notes or "").strip(),
        })
        self._save_data()
        return {"ok": True, "message": "Profil sauvegardé.", "state": self._client_state()}

    def delete_config_profile(self, cid):
        self._data["config_profiles"] = [c for c in self._data["config_profiles"] if c["id"] != cid]
        self._save_data()
        return {"ok": True, "state": self._client_state()}

    def snapshot_game_config(self, name, game):
        if not (name or "").strip():
            return {"ok": False, "message": "Nom requis."}
        src = self._open_file_dialog(("Fichiers config (*.ini;*.cfg;*.json;*.yaml;*.txt)", "Tous les fichiers (*.*)"))
        if not src:
            return {"ok": False, "cancelled": True}
        src_p = Path(src)
        fid = uuid.uuid4().hex[:8]
        stored = CONFIGS_DIR / f"{fid}_{src_p.name}"
        shutil.copy2(src_p, stored)
        self._data["file_configs"].append({
            "id": fid, "name": name.strip(), "game": (game or "Jeu").strip(),
            "target_path": str(src_p), "stored_file": stored.name,
        })
        self._save_data()
        return {"ok": True, "message": "Snapshot sauvegardé.", "state": self._client_state()}

    def apply_game_config(self, fid):
        cfg = next((c for c in self._data["file_configs"] if c["id"] == fid), None)
        if not cfg:
            return {"ok": False, "message": "Introuvable."}
        stored, target = CONFIGS_DIR / cfg["stored_file"], Path(cfg["target_path"])
        if not stored.exists():
            return {"ok": False, "message": "Fichier manquant."}
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stored, target)
        return {"ok": True, "message": f"Config '{cfg['name']}' appliquée."}

    def delete_game_config(self, fid):
        cfg = next((c for c in self._data["file_configs"] if c["id"] == fid), None)
        if cfg:
            (CONFIGS_DIR / cfg["stored_file"]).unlink(missing_ok=True)
        self._data["file_configs"] = [c for c in self._data["file_configs"] if c["id"] != fid]
        self._save_data()
        return {"ok": True, "state": self._client_state()}

    def generate_password(self, length=22):
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
        return {"ok": True, "password": "".join(secrets.choice(alphabet) for _ in range(max(12, min(48, int(length)))))}

    def vault_unlock(self, password):
        res = self._vault.unlock_or_create(password)
        res["state"] = self._client_state()
        return res

    def vault_lock(self):
        self._vault.lock()
        return {"ok": True, "state": self._client_state()}

    def vault_add(self, title, category, username, secret, notes):
        return self._vault.add_entry(title, category, username, secret, notes)

    def vault_delete(self, entry_id):
        return self._vault.delete_entry(entry_id)

    def toggle_deck(self):
        res = self._deck.stop() if self._deck.running else self._deck.start()
        res["state"] = self._client_state()
        return res

    def run_macro(self, action, payload=None):
        payload = payload or {}
        if action == "media_play":
            send_vk(0xB3)
            return {"ok": True, "message": "Play / Pause"}
        if action == "media_next":
            send_vk(0xB0)
            return {"ok": True, "message": "Suivant"}
        if action == "media_prev":
            send_vk(0xB1)
            return {"ok": True, "message": "Précédent"}
        if action == "media_mute":
            send_vk(0xAD)
            return {"ok": True, "message": "Mute"}
        if action == "boost_max":
            return self.run_boost_max(False)
        if action == "toggle_overlay":
            return self.toggle_overlay()
        if action == "game_mode":
            return self.toggle_game_mode()
        if action == "launch":
            return self.launch_account(payload.get("plat", ""), payload.get("id", ""))
        return {"ok": False, "message": "Action inconnue."}

    def create_plugin(self, pid, name, subtitle, processes_csv, session_path, default_exe):
        pid = "".join(c for c in (pid or "").lower() if c.isalnum() or c in "_-")
        if not pid or pid in CORE_PLATFORMS:
            return {"ok": False, "message": "ID invalide."}
        cfg = {
            "id": pid, "name": (name or pid).strip(), "subtitle": (subtitle or "Plugin").strip(),
            "processes": [p.strip() for p in (processes_csv or "").split(",") if p.strip()],
            "session_path": (session_path or "").strip(), "default_exe": (default_exe or "").strip(),
        }
        (PLUGINS_DIR / f"{pid}.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        self._platforms = load_all_platforms()
        self._data["accounts"].setdefault(pid, [])
        self._data["paths"].setdefault(pid, detect_exe_path(pid, self._platforms))
        self._save_data()
        return {"ok": True, "message": f"Plugin '{cfg['name']}' ajouté.", "state": self._client_state()}

    def open_plugins_folder(self):
        os.startfile(str(PLUGINS_DIR))
        return {"ok": True}

    def check_updates(self, repo_override=""):
        repo = (repo_override or self._data["settings"].get("github_repo", "")).strip()
        if not repo or "/" not in repo:
            return {"ok": False, "message": "Format : utilisateur/depot"}
        self._data["settings"]["github_repo"] = repo
        self._save_data()
        try:
            req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases/latest", headers={"User-Agent": f"venUs/{APP_VERSION}"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            latest = data.get("tag_name", "").lstrip("v")
            url = data.get("html_url", f"https://github.com/{repo}/releases")
            if latest and latest != APP_VERSION:
                return {"ok": True, "has_update": True, "latest": latest, "url": url, "message": f"v{latest} disponible."}
            return {"ok": True, "has_update": False, "latest": APP_VERSION, "message": f"À jour (v{APP_VERSION})."}
        except Exception as e:
            return {"ok": False, "message": f"Erreur GitHub : {e}"}

    def open_url(self, url):
        if url.startswith(("http://", "https://")):
            os.startfile(url)