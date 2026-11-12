export type Language = 'uz' | 'en';

export const translations = {
  uz: {
    appTitle: "Conduit",
    appSubtitle: "AI Agentlar Boshqaruv Tizimi",
    phaseBadge: "FAZA 4: SCULPTOR VA ILOVA ADAPTERLARI",
    statusConnected: "Ulangan",
    statusConnecting: "Ulanmoqda...",
    statusDisconnected: "Uzilgan",
    killAll: "Hammasini to'xtatish",
    killAllConfirm: "Barcha faol subagent jarayonlarini to'xtatmoqchimisiz?",
    allTasksTerminated: "Barcha vazifalar to'xtatildi",
    executionTime: "Ijro vaqti",
    currentStepLabel: "Joriy qadam",
    evidenceVerified: "Dalil tekshirildi (PASS)",
    evidenceRejected: "Dalilsiz PASS rad etiladi",
    filterLogs: "Loglarni filtrlash...",
    
    // Sidebar
    subagentsTitle: "Subagentlar",
    subagentsDesc: "Modular ishchi agentlar",
    statusActive: "Faol",
    statusLater: "Keyinroq",
    targetAgent: "Ijrochi subagent",
    autoRoute: "Avtomatik (Manager hal qiladi)",
    workspaceLabel: "Ish joyi",
    
    // Apps
    appsTitle: "Integratsiyalangan Ilovalar",
    appsDesc: "Desktop va API qatlamlari holati",
    appReady: "Tayyor",
    appRunning: "Ishlamoqda",
    appNotInstalled: "O'rnatilmagan",

    // Task Input
    taskInputTitle: "Vazifa berish",
    taskInputPlaceholder: "Subagentga topshiriq bering (masalan: 'Google'dan Conduit AI haqida ma'lumot top' yoki 'workspaces fayllarini o'chir')...",
    sendButton: "Boshlash",
    enterHint: "Yuborish uchun Enter yoki Ctrl+Enter",
    quickSuggestions: "Tezkor namunalar:",
    suggestScoutGoogle: "Scout: Google'dan Conduit AI loyihasini qidir va skrinshot ol",
    suggestInspectorAudit: "Inspector: Faza 2 xavfsizlik perimetri va izolatsiyasini sinovdan o'tkaz",
    suggestDangerDelete: "Scout: Test fayllarini o'chirish (Tasdiq dialogini sinash)",

    // Timeline
    timelineTitle: "Vazifa Jarayoni (Timeline)",
    noActiveTask: "Hozircha hech qanday vazifa yuritilmayapti. Yuqoridagi maydondan vazifa bering.",
    stepPlanner: "Rejalashtiruvchi (Planner)",
    stepDoer: "Ijrochi (Doer)",
    stepChecker: "Tekshiruvchi (Checker)",
    evidence: "Yakuniy Dalil",
    unverified: "Tasdiqlanmagan",
    
    // Live Panel
    livePanelTitle: "Jonli Ko'rish Paneli",
    screenshotTitle: "Jonli Skrinshot",
    noScreenshot: "Hozircha skrinshot olinmadi",
    logsTitle: "Loglar Oqimi",
    noLogs: "Loglar mavjud emas",
    zoomScreenshot: "Kattalashtirish",
    close: "Yopish",

    // Statuses
    idle: "Kutish (Idle)",
    working: "Ishlamoqda",
    pass: "PASS (Tasdiqlandi)",
    fail: "FAIL (Xato)",
    needsApproval: "Tasdiq kutilmoqda",

    // Approvals
    approvalTitle: "Xavfli Amal Tasdig'i Talab Qilinadi",
    approvalDesc: "Subagent xavfsizlik chegarasiga tegishli amalni bajarish uchun ruxsat so'ramoqda.",
    approveBtn: "Tasdiqlash (Ruxsat berish)",
    rejectBtn: "Rad etish (To'xtatish)",
    pendingApprovalsBadge: "ta tasdiq kutilmoqda",

    // Command palette
    cmdTitle: "Buyruqlar Paneli",
    cmdSearch: "Subagent qidirish, buyruq berish...",
    cmdNavigate: "Subagentga o'tish",
    cmdKillAll: "Barcha vazifalarni to'xtatish",
    cmdChangeLang: "Tilni o'zgartirish",
    cmdNoResults: "Hech narsa topilmadi",
  },
  en: {
    appTitle: "Conduit",
    appSubtitle: "AI Agents Orchestration System",
    phaseBadge: "PHASE 4: SCULPTOR & APPLICATION ADAPTERS",
    statusConnected: "Connected",
    statusConnecting: "Connecting...",
    statusDisconnected: "Disconnected",
    killAll: "Kill All",
    killAllConfirm: "Are you sure you want to kill all running subagent processes?",
    allTasksTerminated: "All tasks terminated",
    executionTime: "Execution time",
    currentStepLabel: "Current step",
    evidenceVerified: "Evidence verified (PASS)",
    evidenceRejected: "PASS without evidence rejected",
    filterLogs: "Filter logs...",
    
    // Sidebar
    subagentsTitle: "Subagents",
    subagentsDesc: "Modular worker agents",
    statusActive: "Active",
    statusLater: "Later",
    targetAgent: "Target Subagent",
    autoRoute: "Automatic (Routed by Manager)",
    workspaceLabel: "Workspace",
    
    // Apps
    appsTitle: "Integrated Applications",
    appsDesc: "Desktop and API application runtime states",
    appReady: "Ready",
    appRunning: "Running",
    appNotInstalled: "Not Installed",

    // Task Input
    taskInputTitle: "Dispatch Task",
    taskInputPlaceholder: "Instruct a subagent (e.g. 'Search for Conduit AI on Google' or 'Delete workspace temporary files')...",
    sendButton: "Dispatch",
    enterHint: "Press Enter or Ctrl+Enter to submit",
    quickSuggestions: "Quick Presets:",
    suggestScoutGoogle: "Scout: Search Conduit AI on Google and capture screenshot",
    suggestInspectorAudit: "Inspector: Run Phase 2 security perimeter and isolation audit",
    suggestDangerDelete: "Scout: Delete temporary files (Test approval dialog)",

    // Timeline
    timelineTitle: "Task Timeline",
    noActiveTask: "No active task running. Dispatch a new task above.",
    stepPlanner: "Planner",
    stepDoer: "Doer",
    stepChecker: "Checker",
    evidence: "Verified Evidence",
    unverified: "Unverified",
    
    // Live Panel
    livePanelTitle: "Live Monitoring Panel",
    screenshotTitle: "Live Screenshot Preview",
    noScreenshot: "No screenshot captured yet",
    logsTitle: "Live Log Stream",
    noLogs: "No logs recorded yet",
    zoomScreenshot: "Zoom Screenshot",
    close: "Close",

    // Statuses
    idle: "Idle",
    working: "Working",
    pass: "PASS",
    fail: "FAIL",
    needsApproval: "Needs Approval",

    // Approvals
    approvalTitle: "Dangerous Action Approval Required",
    approvalDesc: "Subagent is requesting permission for an action that crosses security thresholds.",
    approveBtn: "Approve & Execute",
    rejectBtn: "Reject & Abort",
    pendingApprovalsBadge: "approvals pending",

    // Command palette
    cmdTitle: "Command Palette",
    cmdSearch: "Search subagent, run task...",
    cmdNavigate: "Jump to Subagent",
    cmdKillAll: "Kill All Tasks",
    cmdChangeLang: "Switch Language",
    cmdNoResults: "No matching commands found",
  }
};
