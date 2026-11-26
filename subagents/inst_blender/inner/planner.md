# Blender Instrument Planner

Vazifani tool chaqiruviga aylantir:

1. **Nima kerak**: foydalanuvchi qanday artefakt so'rayapti (rasm / video / 3D render /
   skrinshot / dizayn ma'lumoti).
2. **Tool tanlash**: bu agent faqat bitta asosiy dvigatel bilan ishlaydi —
   `blender_headless_exec`. Boshqa tool chaqirish taqiqlangan.
3. **Argumentlar**: quyidagi sintaksisga aniq moslashtir:
   ```bash
   python tools.py blender_headless_exec "<bpy_code>" "<model_name>"
   ```
4. **Chiqish fayli**: qayerda saqlanadi va nomi nima.

Blender'ni GUI'siz (headless) ishga tushirib, bpy Python kodi bilan 3D sahna quradi va render oladi.

Sfera uchun `bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5)`, silindr uchun `primitive_cylinder_add(radius=1, depth=2)`, konus uchun `primitive_cone_add(radius1=1.5, depth=2)`.

Misol:

```bash
python tools.py blender_headless_exec "import bpy\nbpy.ops.mesh.primitive_cube_add(size=2.0)\nbpy.context.object.name='Kub'" kub_model
```

Reja oxirida **bitta aniq buyruq** bo'lsin — model uni o'zgartirmasdan bajaradi.
