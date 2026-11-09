"""
Conduit Buyruq Protokoli (Pydantic asosida).

Agentlar o'rtasida erkin suhbat yo'q, faqat qat'iy tuzilmali buyruq va hisobotlar almashiladi.
- Command: Miya -> Subagent {id, to, task, expected_evidence}
- Report: Subagent -> Miya {id, from_agent, status (PASS/FAIL/BLOCKED), evidence, notes}
- Dalilsiz PASS qabul qilinmaydi.
"""

from typing import Optional, Literal, Tuple, Dict, Any
from pydantic import BaseModel, Field, ValidationError

class Command(BaseModel):
    id: str = Field(..., description="Buyruqning noyob identifikatori")
    to: str = Field(..., min_length=2, description="Qabul qiluvchi subagent nomi")
    task: str = Field(..., min_length=3, description="Bajarilishi kerak bo'lgan aniq vazifa")
    expected_evidence: str = Field(..., min_length=2, description="Kutilayotgan dalil turi (screenshot, audit, logs)")

class Report(BaseModel):
    id: str = Field(..., description="Buyruqqa mos keluvchi hisobot identifikatori")
    from_agent: str = Field(..., min_length=2, description="Hisobot beruvchi subagent")
    status: Literal["PASS", "FAIL", "BLOCKED"] = Field(..., description="Ijro natijasi")
    evidence: str = Field(..., description="Haqiqiy dalil (fayl yo'li, audit natijasi, hash)")
    notes: str = Field(default="", description="Qo'shimcha izoh yoki xatolik sababi")
    screenshot_url: Optional[str] = Field(default=None, description="Agar skrinshot olingan bo'lsa veb ko'rish URL")

def validate_command(raw_data: Dict[str, Any]) -> Tuple[Optional[Command], Optional[str]]:
    """Buyruq formatini qat'iy tekshiradi."""
    try:
        cmd = Command(**raw_data)
        return cmd, None
    except ValidationError as e:
        return None, f"Noto'g'ri buyruq formati: {e.errors()}"
    except Exception as e:
        return None, f"Buyruq xatoligi: {str(e)}"

def validate_report(raw_data: Dict[str, Any]) -> Tuple[Optional[Report], Optional[str]]:
    """
    Hisobot formatini va dalil mavjudligini tekshiradi.
    Dalilsiz PASS qat'iyan qabul qilinmaydi!
    """
    try:
        rep = Report(**raw_data)
        
        # Dalilsiz PASS tekshiruvi
        if rep.status == "PASS":
            ev = rep.evidence.strip()
            if not ev or ev.lower() in ["yo'q", "none", "null", "dalil yo'q", "n/a", ""]:
                return None, "QOIDABUZARLIK: Dalilsiz (skrinshot yo'li yoki audit natijasisiz) PASS qabul qilinmaydi!"
            
            # Agar screenshot kutilsa, rasm mavjudligi yoki /static/ yoki check_goal tasdig'i bo'lishi kerak
            valid_indicators = [".png", ".jpg", ".jpeg", "pass", "ok", "tasdiq", "audit", "valid", "screenshot"]
            if not any(ind in ev.lower() for ind in valid_indicators):
                return None, "QOIDABUZARLIK: PASS hisoboti uchun yaroqli dalil (fayl yo'li yoki tasdiq) topilmadi!"
                
        return rep, None
    except ValidationError as e:
        return None, f"Noto'g'ri hisobot formati: {e.errors()}"
    except Exception as e:
        return None, f"Hisobot xatoligi: {str(e)}"
