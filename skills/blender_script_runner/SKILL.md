---
name: blender_script_runner
description: Headless Blender 3D execution engine, procedural mesh builder and cycles/eevee renderer
version: 1.0.0
license: Apache-2.0
author: Blender Studio & Open Source Community
---

# Blender Script & Scene Runner Asbob Qo'llanmasi (SKILL)

## Tavsif
Headless Blender 3D execution engine, procedural mesh builder and cycles/eevee renderer

## Mavjud Buyruqlar
- `render_scene`
- `execute_script`
- `inspect_scene`
- `self_test`

## Kirish Parametrlari (Inputs)
- **`script_path`** (`str`): script_path parametri
- **`scene_file`** (`str`): scene_file parametri
- **`output_image`** (`str`): output_image parametri
- **`samples`** (`int`): samples parametri

## Chiqish Formati (Outputs)
- **`status`** (`str`): status javob qiymati
- **`render_file`** (`str`): render_file javob qiymati
- **`log`** (`str`): log javob qiymati

## Foydalanish Qoidalari
1. Asbobni ishlatishdan oldin kiruvchi parametrlar schema bo'yicha tekshiriladi.
2. Og'ir render yoki montaj buyruqlari fonda mustaqil PID bilan bajariladi.
3. Barcha amallar Inspector tomonidan tekshirilishi uchun chiqish fayli va log yaratilishi shart.
