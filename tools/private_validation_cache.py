#!/usr/bin/env python3
"""Content-addressed, private-only fast path for expensive source/asset checks.

Never stores Nintendo assets, a filename, ZIP member data or any original bytes.
The cache is valid only for exactly the same resource ZIP AND validation source.
A failed validator is never cached. Public CI exercises synthetic resources.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

VERSION=1
CACHE_RELATIVE=Path("build/private-validation-cache.json")
SUFFIXES={".py",".c",".h",".json"}
SCAN_DIRS=("source","tools","tests")
STATIC_ASSETS=re.compile(r'nitro:/([^"\s]+)')


def _sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda:file.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def fingerprint(root:Path,archive:Path)->dict:
    root=root.resolve(strict=True)
    archive=archive.resolve(strict=True)
    if not archive.is_file():
        raise ValueError("private resource archive is not a file")
    if archive.stat().st_size==0:
        raise ValueError("private resource archive is empty")
    files=[]
    for directory in SCAN_DIRS:
        folder=root/directory
        if folder.is_dir():
            files.extend(p for p in folder.rglob("*")
                         if p.is_file() and p.suffix in SUFFIXES)
    if (root/"Makefile").is_file():
        files.append(root/"Makefile")
    h=hashlib.sha256()
    # The original-resource validators inspect C sources only for literal
    # nitro:/ paths and editor maxima in avatar.c. Hash exact dependencies,
    # not unrelated gameplay C code. This makes the fast path useful for
    # ordinary code iteration without hiding new asset requirements.
    for path in sorted(files,key=lambda p:p.relative_to(root).as_posix()):
        if path.is_symlink():
            raise ValueError("source validation depends on a symbolic link: "+str(path))
        rel=path.relative_to(root).as_posix().encode("utf-8")
        if path.suffix==".c" and path.name not in ("avatar.c", "gallery_balloon_clan.c"):
            literals=STATIC_ASSETS.findall(path.read_text(encoding="utf-8"))
            if not literals:
                continue
            checksum=hashlib.sha256("\\0".join(literals).encode("utf-8")).digest()
        else:
            checksum=bytes.fromhex(_sha(path))
        h.update(len(rel).to_bytes(4,"little"))
        h.update(rel)
        h.update(checksum)
    return {"version":VERSION,"archive_size":archive.stat().st_size,
            "archive_sha256":_sha(archive),"source_sha256":h.hexdigest()}


def cache_hit(root:Path,archive:Path)->bool:
    path=root/CACHE_RELATIVE
    if not path.is_file() or path.is_symlink():
        return False
    try:
        data=json.loads(path.read_text(encoding="utf-8"))
        return isinstance(data,dict) and data==fingerprint(root,archive)
    except (OSError,ValueError,TypeError,UnicodeError):
        return False


def cache_store(root:Path,archive:Path)->None:
    root=root.resolve(strict=True)
    data=fingerprint(root,archive)
    cache=root/CACHE_RELATIVE
    cache.parent.mkdir(parents=True,exist_ok=True)
    if cache.is_symlink() or cache.parent.is_symlink():
        raise ValueError("unsafe private validation cache path")
    temp=cache.with_name(cache.name+".tmp-"+str(os.getpid()))
    try:
        fd=os.open(temp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as handle:
            json.dump(data,handle,sort_keys=True,indent=2)
            handle.write("\n")
        os.replace(temp,cache)
    finally:
        if temp.exists():
            temp.unlink()
