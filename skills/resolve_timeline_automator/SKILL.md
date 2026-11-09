---
name: resolve_timeline_automator
description: DaVinci Resolve studio editing engine, cut list execution, timeline assembly and color grading
version: 1.0.0
license: MIT
author: Post Tools Collective & Pedro Labonia
---

# DaVinci Resolve Timeline & Export Automator Asbob Qo'llanmasi (SKILL)

## Tavsif
DaVinci Resolve studio editing engine, cut list execution, timeline assembly and color grading

## Mavjud Buyruqlar
- `assemble_timeline`
- `export_render`
- `apply_lut`
- `self_test`

## Kirish Parametrlari (Inputs)
- **`project_name`** (`str`): project_name parametri
- **`clips`** (`list`): clips parametri
- **`output_file`** (`str`): output_file parametri
- **`resolution`** (`str`): resolution parametri

## Chiqish Formati (Outputs)
- **`status`** (`str`): status javob qiymati
- **`export_path`** (`str`): export_path javob qiymati
- **`timeline_id`** (`str`): timeline_id javob qiymati

## Foydalanish Qoidalari
1. Asbobni ishlatishdan oldin kiruvchi parametrlar schema bo'yicha tekshiriladi.
2. Og'ir render yoki montaj buyruqlari fonda mustaqil PID bilan bajariladi.
3. Barcha amallar Inspector tomonidan tekshirilishi uchun chiqish fayli va log yaratilishi shart.
