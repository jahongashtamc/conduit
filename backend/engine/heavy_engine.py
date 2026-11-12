r"""
Conduit Heavy Engine (OG'IR ISH REJIMI: 3 GB - 12 GB+)
Ishlab chiqarish darajasidagi og'ir hisoblash va media montaj quvuri:
- HeavyDiskGuard: kiruvchi hajm x 2.5 + zaxira <= bo'sh joy qoidasi (BLOCKED agar yetmasa)
- Oqimli ma'lumot almashinuvi (Chunked Streaming, xotira sarfi < 150 MB)
- Uzoq ish (Detached Persistent Jobs, SQLite PID va checkpoint)
- Progress kuzatuvi (ffmpeg -progress, Blender Fra: loglari) va Stall timeout
- Checkpoint va Resume (tayyor kadrlar va segmentlarni qaytadan ishlamaslik)
- Resurs nazoratchisi (Og'ir vazifa = 1 ta, pause, resume, cancel)
- Engil dalil: ffprobe metadata, sampled/streaming hash, 3-5 kadr prevyu
- Windows Long Path (\\?\) va File Lock himoyasi
"""

import os
import json
import time
import shutil
import hashlib
import sqlite3
import psutil
import subprocess
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Callable

# Windows uzun yo'llar (260+ belgi) xavfsizligi
def normalize_win_path(path: str) -> str:
    abs_path = os.path.abspath(path)
    if os.name == "nt" and not abs_path.startswith("\\\\?\\") and len(abs_path) > 240:
        return "\\\\?\\" + abs_path
    return abs_path

# FFmpeg binarisini aniqlash
def get_ffmpeg_binary() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        # Global fallback
        return shutil.which("ffmpeg") or "ffmpeg"

class DiskBudgetExceededError(Exception):
    pass

class HeavyDiskGuard:
    """
    Og'ir vazifalar oldidan diskdagi bo'sh joyni qat'iy nazorat qilish:
    kiruvchi fayllar hajmi x 2.5 + 1GB zaxira <= nishon diskdagi bo'sh joy.
    """
    @staticmethod
    def evaluate_storage_budget(
        input_bytes: int,
        target_dir: str,
        factor: float = 2.5,
        safety_buffer_bytes: int = 1024 * 1024 * 1024 # 1.0 GB
    ) -> Dict[str, Any]:
        norm_dir = normalize_win_path(target_dir)
        os.makedirs(norm_dir, exist_ok=True)
        usage = shutil.disk_usage(norm_dir)
        free_bytes = usage.free
        required_bytes = int(input_bytes * factor) + safety_buffer_bytes

        drive_letter = os.path.splitdrive(os.path.abspath(target_dir))[0] or "C:"
        req_gb = required_bytes / (1024 * 1024 * 1024)
        free_gb = free_bytes / (1024 * 1024 * 1024)

        if free_bytes < required_bytes:
            reason = f"BLOCKED: Kerak: {req_gb:.1f} GB, bo'sh: {free_gb:.1f} GB, disk: {drive_letter}"
            return {
                "allowed": False,
                "status": "BLOCKED",
                "reason": reason,
                "required_gb": req_gb,
                "free_gb": free_gb,
                "drive": drive_letter
            }

        return {
            "allowed": True,
            "status": "APPROVED",
            "reason": f"Diskda yetarli joy mavjud ({free_gb:.1f} GB bo'sh, {req_gb:.1f} GB talab etiladi)",
            "required_gb": req_gb,
            "free_gb": free_gb,
            "drive": drive_letter
        }

    @staticmethod
    def enforce_storage_budget(input_bytes: int, target_dir: str, factor: float = 2.5):
        eval_res = HeavyDiskGuard.evaluate_storage_budget(input_bytes, target_dir, factor)
        if not eval_res["allowed"]:
            raise DiskBudgetExceededError(eval_res["reason"])
        return eval_res


class StreamProcessor:
    """
    Katta fayllar (3-12 GB) bilan ishlashda xotira to'lishining oldini oluvchi
    1-8 MB oqimli (streaming) yordamchi.
    """
    CHUNK_SIZE = 4 * 1024 * 1024 # 4 MB

    @staticmethod
    def copy_file_streamed(src: str, dst: str, progress_callback: Optional[Callable[[int, int, float], None]] = None) -> Dict[str, Any]:
        src_norm = normalize_win_path(src)
        dst_norm = normalize_win_path(dst)
        os.makedirs(os.path.dirname(dst_norm), exist_ok=True)

        total_bytes = os.path.getsize(src_norm)
        copied = 0
        hasher = hashlib.sha256()

        start_time = time.time()
        start_ram = psutil.Process().memory_info().rss / (1024 * 1024)
        peak_ram = start_ram

        with open(src_norm, "rb") as f_in, open(dst_norm, "wb") as f_out:
            while True:
                chunk = f_in.read(StreamProcessor.CHUNK_SIZE)
                if not chunk:
                    break
                f_out.write(chunk)
                hasher.update(chunk)
                copied += len(chunk)

                current_ram = psutil.Process().memory_info().rss / (1024 * 1024)
                if current_ram > peak_ram:
                    peak_ram = current_ram

                if progress_callback and total_bytes > 0:
                    progress_callback(copied, total_bytes, (copied / total_bytes) * 100.0)

        duration = time.time() - start_time
        return {
            "bytes_copied": copied,
            "sha256": hasher.hexdigest(),
            "duration_sec": duration,
            "peak_ram_mb": peak_ram,
            "speed_mb_s": (copied / (1024 * 1024)) / max(duration, 0.001)
        }

    @staticmethod
    def calculate_stream_hash(file_path: str, chunk_size: int = CHUNK_SIZE) -> str:
        norm_fp = normalize_win_path(file_path)
        hasher = hashlib.sha256()
        with open(norm_fp, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def calculate_sampled_hash(file_path: str, sample_size: int = 4 * 1024 * 1024) -> str:
        """
        Katta fayllar (10-12 GB) uchun sekundlar ichida dalil oluvchi barmoq izi:
        boshidan 4MB + o'rtasidan 4MB + oxiridan 4MB.
        """
        norm_fp = normalize_win_path(file_path)
        size = os.path.getsize(norm_fp)
        hasher = hashlib.sha256()

        with open(norm_fp, "rb") as f:
            # 1. Boshidan
            hasher.update(f.read(sample_size))
            # 2. O'rtasidan
            if size > sample_size * 2:
                f.seek(size // 2)
                hasher.update(f.read(sample_size))
            # 3. Oxiridan
            if size > sample_size * 3:
                f.seek(max(0, size - sample_size))
                hasher.update(f.read(sample_size))

        return hasher.hexdigest()


class WindowsSafeFileHandler:
    r"""Windows long paths (\\?\) and file locking (WinError 32) protections."""
    @staticmethod
    def safe_remove(path: str, retries: int = 5, delay: float = 0.5) -> bool:
        norm_path = normalize_win_path(path)
        if not os.path.exists(norm_path):
            return True
        for attempt in range(retries):
            try:
                if os.path.isdir(norm_path):
                    shutil.rmtree(norm_path)
                else:
                    os.remove(norm_path)
                return True
            except PermissionError as e:
                if attempt == retries - 1:
                    raise PermissionError(f"Windows Fayl Qulfi Xatosi: '{path}' boshqa jarayon tomonidan bloklangan. ({e})")
                time.sleep(delay)
            except Exception as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(delay)
        return False

    @staticmethod
    def test_file_lock(path: str) -> Dict[str, Any]:
        norm_path = normalize_win_path(path)
        if not os.path.exists(norm_path):
            return {"locked": False, "exists": False}
        try:
            with open(norm_path, "r+b"):
                pass
            return {"locked": False, "exists": True}
        except PermissionError:
            return {"locked": True, "exists": True, "error": f"Fayl boshqa jarayon tomonidan bloklangan: {path}"}
        except Exception as e:
            return {"locked": False, "exists": True, "error": str(e)}


class ResourceMonitor:
    """RAM, GPU va Disk resurslarini kuzatish va navbatni boshqarish."""
    @staticmethod
    def get_system_metrics(target_dir: str = ".") -> Dict[str, Any]:
        mem = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=0.1)
        usage = shutil.disk_usage(normalize_win_path(target_dir))

        gpu_info = "N/A"
        try:
            # Check nvidia-smi if available
            smi = shutil.which("nvidia-smi")
            if smi:
                res = subprocess.run([smi, "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
                if res.returncode == 0 and res.stdout.strip():
                    gpu_info = res.stdout.strip()
        except Exception:
            pass

        return {
            "ram_used_pct": mem.percent,
            "ram_free_gb": round(mem.available / (1024 ** 3), 2),
            "ram_total_gb": round(mem.total / (1024 ** 3), 2),
            "cpu_percent": cpu_pct,
            "disk_free_gb": round(usage.free / (1024 ** 3), 2),
            "gpu_metrics": gpu_info,
            "healthy": mem.percent < 95.0 and (usage.free / (1024 ** 3)) > 1.0
        }


class LightweightMediaEvidence:
    """
    Katta fayllarni xotiraga yuklamasdan ffprobe metadata, thumbnail va parametrlarini olish.
    """
    @staticmethod
    def get_media_metadata(video_path: str) -> Dict[str, Any]:
        norm_path = normalize_win_path(video_path)
        ffmpeg_bin = get_ffmpeg_binary()

        # ffprobe o'rniga ffmpeg -i orqali tezkor tahlil
        cmd = [ffmpeg_bin, "-hide_banner", "-i", norm_path]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
        output = proc.stderr

        file_size = os.path.getsize(norm_path) if os.path.exists(norm_path) else 0

        # Duration, bitrate, format ajratish
        duration_sec = 0.0
        resolution = "Unknown"
        codec = "Unknown"

        for line in output.split("\n"):
            line = line.strip()
            if "Duration:" in line:
                try:
                    parts = line.split("Duration:")[1].split(",")[0].strip().split(":")
                    duration_sec = float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
                except Exception:
                    pass
            if "Video:" in line:
                try:
                    codec = line.split("Video:")[1].split()[0]
                    # Resolution masalan 1920x1080 yoki 3840x2160
                    for token in line.split(","):
                        token = token.strip()
                        if "x" in token and any(c.isdigit() for c in token):
                            candidate = token.split()[0]
                            if "x" in candidate:
                                resolution = candidate
                except Exception:
                    pass

        return {
            "file_path": video_path,
            "size_bytes": file_size,
            "size_human": f"{file_size / (1024*1024):.2f} MB" if file_size < 1024*1024*1024 else f"{file_size / (1024*1024*1024):.2f} GB",
            "duration_sec": duration_sec,
            "resolution": resolution,
            "video_codec": codec,
            "format_valid": duration_sec > 0 or file_size > 1024
        }

    @staticmethod
    def extract_keyframes(video_path: str, output_dir: str, count: int = 3) -> List[str]:
        """Katta videoni yuklamasdan 3 ta tezkor kadr skrinshotini oladi."""
        norm_in = normalize_win_path(video_path)
        norm_out_dir = normalize_win_path(output_dir)
        os.makedirs(norm_out_dir, exist_ok=True)
        ffmpeg_bin = get_ffmpeg_binary()

        meta = LightweightMediaEvidence.get_media_metadata(video_path)
        duration = meta.get("duration_sec", 10.0)

        generated = []
        timestamps = [duration * 0.1, duration * 0.5, duration * 0.9] if duration > 3 else [0.5, 1.0, 1.5]

        for idx, ts in enumerate(timestamps[:count]):
            thumb_path = os.path.join(norm_out_dir, f"thumb_key_{idx+1}.jpg")
            cmd = [
                ffmpeg_bin, "-y",
                "-ss", str(ts),
                "-i", norm_in,
                "-vframes", "1",
                "-s", "480x270",
                thumb_path
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
                generated.append(thumb_path)

        return generated


class HeavyJobManager:
    """
    Uzoq davom etuvchi jarayonlar boshqaruvi:
    - Bir vaqtda 1 ta og'ir job (Semaphore)
    - Jarayon alohida yashaydi (Detached Process)
    - SQLite'da holat va PID
    - Backend qayta yoqilganda jobni qayta topish va tiklash
    - Pause, Resume, Cancel
    """
    _instance = None

    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.jobs_table_init()
        self.semaphore = asyncio.Semaphore(1)
        self.active_jobs: Dict[str, psutil.Process] = {}

    def get_db_conn(self):
        db_path = os.path.join(self.workspace_root, "backend", "conduit.db")
        return sqlite3.connect(db_path, timeout=30.0)

    def jobs_table_init(self):
        conn = self.get_db_conn()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS heavy_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE NOT NULL,
            task_id TEXT NOT NULL,
            job_type TEXT NOT NULL,
            pid INTEGER,
            status TEXT NOT NULL DEFAULT 'queued',
            progress_pct REAL DEFAULT 0.0,
            current_unit INTEGER DEFAULT 0,
            total_units INTEGER DEFAULT 0,
            checkpoint_json TEXT,
            started_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """)
        conn.commit()
        conn.close()

    def register_job(self, job_id: str, task_id: str, job_type: str, total_units: int = 100) -> Dict[str, Any]:
        conn = self.get_db_conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("DELETE FROM heavy_jobs WHERE job_id = ?", (job_id,))
        cursor.execute("""
        INSERT INTO heavy_jobs (job_id, task_id, job_type, pid, status, progress_pct, current_unit, total_units, checkpoint_json, started_at, updated_at)
        VALUES (?, ?, ?, NULL, 'queued', 0.0, 0, ?, '{}', ?, ?)
        """, (job_id, task_id, job_type, total_units, now, now))
        conn.commit()
        conn.close()
        return {"job_id": job_id, "status": "queued"}

    def update_job_progress(self, job_id: str, pid: Optional[int], status: str, progress_pct: float, current_unit: int = 0, checkpoint_data: Optional[Dict] = None):
        conn = self.get_db_conn()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cp_json = json.dumps(checkpoint_data or {})
        cursor.execute("""
        UPDATE heavy_jobs
        SET pid = COALESCE(?, pid), status = ?, progress_pct = ?, current_unit = ?, checkpoint_json = ?, updated_at = ?
        WHERE job_id = ?
        """, (pid, status, progress_pct, current_unit, cp_json, now, job_id))
        conn.commit()
        conn.close()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        conn = self.get_db_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM heavy_jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            d = dict(row)
            d["checkpoint"] = json.loads(d.get("checkpoint_json") or "{}")
            return d
        return None

    def pause_job(self, job_id: str) -> bool:
        job = self.get_job(job_id)
        if not job or not job.get("pid"):
            return False
        try:
            p = psutil.Process(job["pid"])
            p.suspend()
            self.update_job_progress(job_id, job["pid"], "paused", job["progress_pct"], job["current_unit"])
            return True
        except Exception:
            return False

    def resume_job(self, job_id: str) -> bool:
        job = self.get_job(job_id)
        if not job or not job.get("pid"):
            return False
        try:
            p = psutil.Process(job["pid"])
            p.resume()
            self.update_job_progress(job_id, job["pid"], "running", job["progress_pct"], job["current_unit"])
            return True
        except Exception:
            return False

    def cancel_job(self, job_id: str) -> bool:
        job = self.get_job(job_id)
        if not job or not job.get("pid"):
            return False
        try:
            p = psutil.Process(job["pid"])
            for child in p.children(recursive=True):
                try:
                    child.kill()
                except Exception:
                    pass
            p.kill()
        except Exception:
            pass
        self.update_job_progress(job_id, None, "cancelled", job.get("progress_pct", 0.0), job.get("current_unit", 0))
        return True

    def check_stall(self, job_id: str, timeout_sec: int = 60) -> Tuple[bool, float]:
        """
        N soniya davomida progress yangilanmagan bo'lsa STALLED holatini aniqlaydi.
        """
        job = self.get_job(job_id)
        if not job or job.get("status") not in ("running", "queued"):
            return False, 0.0
        try:
            updated_dt = datetime.fromisoformat(job["updated_at"])
            elapsed = (datetime.now() - updated_dt).total_seconds()
            if elapsed > timeout_sec:
                self.update_job_progress(job_id, job.get("pid"), "stalled", job["progress_pct"], job["current_unit"])
                return True, elapsed
            return False, elapsed
        except Exception:
            return False, 0.0

    def recover_active_jobs(self) -> List[Dict[str, Any]]:
        """Backend qayta yoqilganda ishlab turgan yoki uzilgan joblarni aniqlash va tiklash."""
        conn = self.get_db_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM heavy_jobs WHERE status IN ('running', 'queued', 'paused')")
        rows = cursor.fetchall()
        conn.close()

        recovered = []
        for r in rows:
            job = dict(r)
            pid = job.get("pid")
            if pid and psutil.pid_exists(pid):
                # Jarayon hamon ishlab turibdi!
                recovered.append({"job_id": job["job_id"], "state": "ALIVE_RUNNING", "pid": pid})
            else:
                # Jarayon to'xtab qolgan, oxirgi checkpointdan tiklanadi
                recovered.append({"job_id": job["job_id"], "state": "INTERRUPTED_READY_FOR_RESUME", "last_unit": job["current_unit"]})
        return recovered


class FFmpegResumablePipeline:
    """
    Katta video montaj va kodlashni bo'laklar (segments) bo'yicha checkpoint qilib,
    to'xtab qolsa ham qolgan joyidan davom ettiruvchi barqaror quvur.
    """
    def __init__(self, workspace_dir: str):
        self.workspace_dir = normalize_win_path(workspace_dir)
        self.temp_dir = os.path.join(self.workspace_dir, "cache_temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.ffmpeg_bin = get_ffmpeg_binary()

    def process_resumable_video(
        self,
        job_id: str,
        input_file: str,
        output_file: str,
        segment_duration_sec: int = 2,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """
        Videoni bo'laklab ishlaydi va har bo'lakni checkpointga saqlaydi.
        Agar uzilsa, tayyor bo'laklar qayta ishlanmaydi.
        """
        meta = LightweightMediaEvidence.get_media_metadata(input_file)
        duration = meta.get("duration_sec", 10.0)
        total_segments = max(1, int(duration // segment_duration_sec) + (1 if duration % segment_duration_sec else 0))

        checkpoint_file = os.path.join(self.temp_dir, f"{job_id}_checkpoint.json")
        completed_segments = []

        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, "r") as f:
                    completed_segments = json.load(f).get("completed", [])
            except Exception:
                completed_segments = []

        segment_files = []
        start_ram = psutil.Process().memory_info().rss / (1024 * 1024)
        peak_ram = start_ram

        for seg_idx in range(total_segments):
            seg_out = os.path.join(self.temp_dir, f"{job_id}_seg_{seg_idx:04d}.mp4")
            segment_files.append(seg_out)

            if seg_idx in completed_segments and os.path.exists(seg_out) and os.path.getsize(seg_out) > 0:
                # Bu bo'lak allaqachon tayyor, o'tkazib yuboriladi!
                continue

            ss = seg_idx * segment_duration_sec
            t = min(segment_duration_sec, max(0.1, duration - ss))

            # Segmentni kodlash
            cmd = [
                self.ffmpeg_bin, "-y",
                "-ss", str(ss),
                "-t", str(t),
                "-i", input_file,
                "-c:v", "libx264", "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                seg_out
            ]

            proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if proc.returncode != 0:
                raise RuntimeError(f"FFmpeg segment {seg_idx} kodlashda xatolik!")

            completed_segments.append(seg_idx)
            with open(checkpoint_file, "w") as f:
                json.dump({"completed": completed_segments, "total": total_segments}, f)

            current_ram = psutil.Process().memory_info().rss / (1024 * 1024)
            if current_ram > peak_ram:
                peak_ram = current_ram

            if progress_callback:
                progress_callback((len(completed_segments) / total_segments) * 90.0)

        # Barcha bo'laklarni oxirida lossless birlashtirish (Concat Demuxer)
        concat_list = os.path.join(self.temp_dir, f"{job_id}_concat.txt")
        with open(concat_list, "w") as f:
            for sfp in segment_files:
                f.write(f"file '{sfp.replace(chr(92), '/')}'\n")

        merge_cmd = [
            self.ffmpeg_bin, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            output_file
        ]
        merge_proc = subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if merge_proc.returncode != 0:
            raise RuntimeError("Segmentlarni birlashtirishda xatolik yuz berdi!")

        if progress_callback:
            progress_callback(100.0)

        # Temp bo'laklarni tozalash (faqat workspace temp ichida)
        try:
            if os.path.exists(concat_list):
                os.remove(concat_list)
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)
            for sfp in segment_files:
                if os.path.exists(sfp):
                    os.remove(sfp)
        except Exception:
            pass

        return {
            "success": True,
            "output_file": output_file,
            "total_segments": total_segments,
            "peak_ram_mb": peak_ram,
            "final_size_bytes": os.path.getsize(output_file)
        }
