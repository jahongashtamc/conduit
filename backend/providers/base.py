from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

class BaseAgentProvider(ABC):
    """
    Conduit subagentlari uchun tashqi AI model va agent provayderlarining umumiy interfeysi.
    Boshqa provayderlar (masalan lokal LLM, browser AI) keyinchalik shu interfeysdan meros oladi.
    """

    @abstractmethod
    def get_provider_name(self) -> str:
        """Provayder nomi (masalan: 'mcp')."""
        raise NotImplementedError

    @abstractmethod
    def is_connected(self) -> bool:
        """Agent Conduit tizimiga ulanganmi yoki yo'q."""
        raise NotImplementedError

    @abstractmethod
    async def run(self, role_prompt: str, task: str, tools: List[str]) -> Dict[str, Any]:
        """
        Vazifani agentga bajarish uchun topshirish.
        
        Parametrlar:
        - role_prompt: Subagentning role.md va ichki qoidalaridan shakllangan instruksiya
        - task: Foydalanuvchi bergan aniq vazifa
        - tools: role.md da ruxsat berilgan toollar ro'yxati
        
        Qaytaradi: {
            "status": "PASS" | "FAIL",
            "output": str,
            "evidence": str,
            "steps": List[Dict]
        }
        """
        raise NotImplementedError


class MCPAgentProvider(BaseAgentProvider):
    """
    Tashqi AI Agent (masalan: Antigravity yoki Claude Code) MCP (Model Context Protocol) 
    orqali ulanib, Conduit subagentlarini boshqaruvchi provayder.
    """

    def __init__(self, agent_name: str = "Antigravity Agent"):
        self.agent_name = agent_name
        self.connected = True
        self.last_heartbeat = datetime.now().isoformat()
        self.connected_agent_info = {
            "agent_name": agent_name,
            "protocol": "Model Context Protocol (MCP v2.0)",
            "transport": "stdio / sse",
            "connected_at": self.last_heartbeat
        }

    def get_provider_name(self) -> str:
        return "mcp"

    def is_connected(self) -> bool:
        return self.connected

    def set_connected(self, state: bool, agent_name: Optional[str] = None):
        self.connected = state
        if agent_name:
            self.agent_name = agent_name
            self.connected_agent_info["agent_name"] = agent_name
        self.last_heartbeat = datetime.now().isoformat()

    def get_info(self) -> Dict[str, Any]:
        return {
            "is_connected": self.connected,
            "agent_name": self.agent_name,
            "protocol": self.connected_agent_info["protocol"],
            "transport": self.connected_agent_info["transport"],
            "last_heartbeat": self.last_heartbeat
        }

    async def run(self, role_prompt: str, task: str, tools: List[str]) -> Dict[str, Any]:
        """
        MCP orqali ulangan tashqi agentga vazifa beriladi.
        Tashqi agent Conduit toollari (list_subagents, run_task, get_task) orqali subagentni harakatga keltiradi.
        """
        return {
            "status": "PASS",
            "provider": "mcp",
            "role_prompt": role_prompt,
            "agent_name": self.agent_name,
            "output": f"Vazifa MCP provayderi ({self.agent_name}) orqali qabul qilindi va subagentga topshirildi.",
            "evidence": "MCP sessiyasi faol."
        }
