import json
keys=[{'t':0.0,'frame':0,'rotation_y':0,'color':'#0284c7'},{'t':0.5,'frame':24,'rotation_y':180,'color':'#38bdf8'},{'t':1.0,'frame':48,'rotation_y':360,'color':'#0284c7'}]
with open('sphere_keyframes.json','w') as f: json.dump(keys, f)
print('Keyframes saved: 2.0s rotating sphere timeline')