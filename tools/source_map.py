#!/usr/bin/env python3
"""Generate an evidence-based original-data -> DS source map, not invented symbols."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
original=json.loads((ROOT/'assets/manifest.json').read_text())
code=(ROOT/'assets/exefs/code-decompressed.bin').read_bytes()
def refs(text):
    out=[]
    for enc in ['ascii','utf-16-le']:
        needle=text.encode(enc);start=0
        while True:
            at=code.find(needle,start)
            if at<0:break
            out.append(dict(encoding=enc,offset=hex(at)));start=at+len(needle)
    return out
scenes=[
 ('Main menu',['Plaza/PlazaTop','Plaza/PlazaBG_Up','EDITCommon/CmnBg'],'source/menu.c; source/main.c; source/ui.c','running reconstructed menu; substitute font and incomplete animation/material effects'),
 ('Gallery',['Select/EDITSelectBase','Select/SelectMii'],'source/menu.c; source/main.c; source/ui.c','100 slots and original grid; original-resource head thumbnails; permission-aware copy and touch confirmation; sorting incomplete'),
 ('Editor',['Editor/EditorCommon','Editor/EditFaceTab','Editor/EditFace','Editor/EditHair','Editor/EditEye','Editor/EditEyebrow','Editor/EditNose','Editor/EditMouth','Editor/EditGlasses','Editor/EditBody'],'source/ui.c; source/avatar.c; source/editor.c','original icons, layout-derived hits, paging, colors, face subtabs, transform/reset controls and captured free-drag body sliders; accessory picker wired; remaining original effects incomplete'),
 ('Profile',['Editor/Profile','Dialog/DialogGender','Dialog/DialogFirstGender','Dialog/DialogBirthday','Dialog/DialogColor','Dialog/DialogOpen','Dialog/DialogAdmission','Dialog/DialogBtnCommon02'],'source/profile.c; source/main.c; source/ui.c; tools/profile_assets.py','original layout-derived profile, gender/date/color/permission dialogs and touch confirmation; ASCII DS keyboard adaptation, original number font; international keyboard incomplete'),
 ('Accessories',['Editor/EditEtcTab'],'source/main.c; source/ui.c','original glasses/mustache/beard/mole selector routes to editor'),
 ('Face rendering',['CFL_Res.dat'],'source/cfl_resource.c; source/head.c','original CFL heads plus original male/female CGFX body meshes and sampled original Wait00 idle poses; software camera/lighting and body proportions remain provisional; other animations and exact timing incomplete'),
 ('Body geometry and skeleton',['MaleBody.bcmdl','FemaleBody.bcmdl','MiiAnim/Wait00.bcskla'],'tools/body_models.py; source/head.c; source/ui.c','original indexed rigid meshes, bone palettes, SRT hierarchy and sampled idle poses mapped; body-models.json records offsets/attributes; body proportion coefficients provisional'),
 ('Image export',[],'source/image.c; source/ui.c; source/main.c','gallery SELECT: private BMP adaptation to DS/DSi SD filesystem; sharing permission and no-overwrite policy; physical writes untested'),
 ('Mii file import',[],'source/exchange.c; source/mii_codec.c; source/editor.c; source/main.c','standard 96-byte CFSD/FFSD file decoding and transactional import; received copy-disabled Miis are read-only'),
 ('Saving',[],'source/save_nds.c; source/save_compact.c; source/save.c','100-slot private DS format; new 8 KiB snapshot; retained 64 KiB legacy support; not Nintendo Mii serialization'),
 ('Camera',['Camera'],'source/camera_ds.c','DSi-only controller, hardware untested; not photo recognition'),
 ('Send/Receive',['Network','Wireless'],'source/main.c','explicit unavailable notice; no transport implemented'),
 ('QR/Image',['QR/QREncode','QR/BtnQR','Dialog/DialogPhotoSelect'],'source/mii_codec.c; source/mii_qr.c; source/qr_scan.c; source/qr_photo.c; source/main.c; source/ui.c','original QR/menu data, authenticated payload, PNG export and DSi-only scanner path; physical camera/SD/stock-device checks pending'),
]
layout_runtime={}
for title,layouts,source,state in scenes:
    for name in layouts:layout_runtime[name]=(title,source,state)
layouts=[]
for p in sorted((ROOT/'assets/decoded/layout').glob('*.arc.files/blyt/*.bclyt')):
    name=p.parent.parent.name.removesuffix('.arc.files')+'/'+p.stem
    entry=dict(original=str(p.relative_to(ROOT)),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    if name in layout_runtime:
        title,source,state=layout_runtime[name];entry.update(scene=title,ds_source=source,status=state)
    else:entry.update(status='extracted; see generated editor-category table for additional rendered pages, otherwise not wired to a runtime scene')
    layouts.append(entry)
fields=re.findall(r'\{"([^"]+)",(\d+),(\d+)\}',(ROOT/'source/avatar.c').read_text())
fieldmap=[]
for i,(name,maximum,initial) in enumerate(fields):
    status='profile UI, validation and storage; permission flags enforced for local copy only, future exports/transfers incomplete'
    if i<=42:status='head preview parameter; original meshes/textures with provisional software composition'
    if i==0:status='original male/female CGFX body selection; original CFL head attributes independent'
    if i in [43,44]:status='live original body slider/knob and decoded body geometry; proportion coefficients provisional'
    if i==45:status='favorite-color metadata, cap tint and original body recoloring'
    if i>=52:status='legacy temporary input field; names use validated touch keyboard'
    if i==61:status='persistent received/special status, migrated from obsolete legacy creator-input byte'
    fieldmap.append(dict(ds_field=i,name=name,maximum=int(maximum),initial=int(initial),state=status))
assets=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((ROOT/'nitrofiles').rglob('*')) if p.is_file()]
result=dict(original_product=original['product'],original_rom_sha256=original['input_sha256'],original_executable='assets/exefs/code-decompressed.bin',original_source_available=False,code_evidence_notice='String locations are binary offsets, not identified functions or proof of implemented behavior. 3DS ARM11/PICA/OS code is not executed on the DS.',code_string_locations={s:refs(s) for s in ['CFL_Res.dat','PlazaTop','SelectMii','EditorCommon','QREncode','EditHair']},scenes=[dict(name=t,original_layouts=l,ds_source=s,status=st) for t,l,s,st in scenes],layouts=layouts,fields=fieldmap,runtime_assets=assets,coordinate_mapping=dict(bottom_screen='320x240 -> 256x192; x/y * 0.8, generated hitboxes',top_screen='400x240 -> 256x192; x * 0.64, y * 0.8',head='128x128 resource preview with original body, skeleton/head anchor and sampled original Wait00 idle poses; camera/lighting/proportion coefficients provisional'))
p=ROOT/'reference/SOURCE_MAP.json';p.write_text(json.dumps(result,indent=2)+'\n')
print(f'Mapped {len(layouts)} original layouts, {len(fieldmap)} profile fields, {len(assets)} runtime assets')
