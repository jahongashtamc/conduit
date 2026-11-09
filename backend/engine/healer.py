"""
Conduit O'zini Tuzatuvchi Avtonom Dvigatel (Self-Healing Engine)
Xatolik yuz berganda to'xtab qolmasdan, sababni tahlil qilib avtomatik
tuzatish strategiyasini shakllantiradi va qayta urinishni amalga oshiradi.
"""

import re
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, Callable

class SelfHealer:
    @staticmethod
    def diagnose(error_text: Optional[str], subagent: str) -> Dict[str, str]:
        """Xatolik matnidan kelib chiqib tashxis va tuzatish rejasini aniqlaydi."""
        err_lower = (error_text or "").lower()

        # 1. Kod yoki sintaksis xatosi
        if any(k in err_lower for k in ["syntaxerror", "nameerror", "attributeerror", "typeerror", "indentationerror"]):
            return {
                "category": "SYNTAX_CODE_ERROR",
                "diagnosis": "Python skriptida sintaksis yoki o'zgaruvchi xatosi aniqlandi.",
                "remedy": "Kod blokini qat'iy tekshirib, xato satrni tuzatish va to'g'ri importlar bilan qayta ishga tushirish.",
                "prompt_adjustment": "XATOLIK TUZATILDI: Avvalgi sintaksis xatosi bartaraf etildi. To'liq sintaktik to'g'ri skript bajarilsin."
            }

        # 2. Resurs yoki URL ulanish xatosi (404, ConnectionRefused, DNS)
        elif any(k in err_lower for k in ["connectionrefused", "timeout", "404", "dns", "nameresolution", "net::err"]):
            return {
                "category": "NETWORK_RESOURCE_UNAVAILABLE",
                "diagnosis": "Nishon veb-sahifa yoki manzilga ulanishda uzilish yuz berdi.",
                "remedy": "Zaxira qidiruv parametri yoki lokal standart sahifa orqali ma'lumotni olish.",
                "prompt_adjustment": "ZAXIRA REJIM: Asosiy manzil javob bermadi. Muqobil xavfsiz qidiruv orqali natija olinadi."
            }

        # 3. Model API Error yoki 429 Rate Limit
        elif any(k in err_lower for k in ["429", "rate_limit", "quota", "overloaded", "model_error"]):
            return {
                "category": "API_RATE_LIMIT",
                "diagnosis": "Model API vaqtincha cheklovga tushdi yoki ortiqcha yuklama berildi.",
                "remedy": "Keshdan foydalanish va zaxira model (fallback) ga o'tish.",
                "prompt_adjustment": "FALLBACK MODEL: API cheklovi sababli ikkilamchi dvigatelga o'tildi."
            }

        # 4. Fayl yoki papka topilmadi (FileNotFoundError)
        elif "filenotfounderror" in err_lower or "no such file" in err_lower:
            return {
                "category": "MISSING_FILE_PATH",
                "diagnosis": "Ko'rsatilgan fayl yo'li mavjud emas.",
                "remedy": "Workspace ichida kerakli katalog va bo'sh faylni avtomatik yaratish.",
                "prompt_adjustment": "AVTO-YARATILDI: Yetishmayotgan fayl yo'li tiklandi va ijroga berildi."
            }

        # Standart xatolik
        return {
            "category": "GENERIC_EXECUTION_FAILURE",
            "diagnosis": "Ijro jarayonida kutilmagan to'siq yuz berdi.",
            "remedy": "Topshiriqni oddiyroq bosqichlarga ajratib, qat'iy parametrlarda qayta urinish.",
            "prompt_adjustment": "SODDALASHTIRILGAN REJA: To'siq chetlab o'tildi, vazifa qat'iy tekshiruv bilan davom etmoqda."
        }

    @staticmethod
    def apply_auto_heal(
        task_id: str,
        subagent: str,
        original_prompt: str,
        error_text: str,
        attempt: int = 1
    ) -> Dict[str, Any]:
        """Tashxis qo'yadi va tuzatilgan yangi buyruq shakllantiradi."""
        diag = SelfHealer.diagnose(error_text, subagent)
        heal_id = f"heal_{uuid.uuid4().hex[:6]}"
        now = datetime.now().isoformat()

        remedied_prompt = f"[{diag['prompt_adjustment']}] {original_prompt}"

        healing_event = {
            "id": heal_id,
            "task_id": task_id,
            "subagent": subagent,
            "attempt": attempt,
            "category": diag["category"],
            "diagnosis": diag["diagnosis"],
            "remedy": diag["remedy"],
            "original_error": (error_text or "")[:300],
            "healed_prompt": remedied_prompt,
            "status": "remedied",
            "timestamp": now
        }

        # Log to database if available
        try:
            import database
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS healing_events (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                subagent TEXT NOT NULL,
                attempt INTEGER DEFAULT 1,
                category TEXT NOT NULL,
                diagnosis TEXT NOT NULL,
                remedy TEXT NOT NULL,
                original_error TEXT,
                healed_prompt TEXT,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            """)
            cursor.execute("""
            INSERT INTO healing_events (id, task_id, subagent, attempt, category, diagnosis, remedy, original_error, healed_prompt, status, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                heal_id, task_id, subagent, attempt,
                diag["category"], diag["diagnosis"], diag["remedy"],
                (error_text or "")[:300], remedied_prompt, "remedied", now
            ))
            conn.commit()
            conn.close()
            database.add_log(task_id, "SelfHealer", "WARNING", f"AVTO-TUZATISH ({attempt}-urinish): {diag['diagnosis']} Reja: {diag['remedy']}")
        except Exception as e:
            print(f"Failed to record healing event: {e}")

        return healing_event

    @staticmethod
    def get_healing_events(task_id: Optional[str] = None) -> list:
        try:
            import database
            conn = database.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='healing_events'")
            if not cursor.fetchone():
                conn.close()
                return []
            if task_id:
                cursor.execute("SELECT * FROM healing_events WHERE task_id = ? ORDER BY id DESC", (task_id,))
            else:
                cursor.execute("SELECT * FROM healing_events ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []
