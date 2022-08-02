#!/usr/bin/env python3

# A script to collide PNGs with the same header
# and optionally craft the prefix and launch UniColl

# Ange Albertini 2018-2021

import sys
import struct
import hashlib
import glob
import os
import shutil

def get_data(args):
  fn1, fn2 = args

  with open(fn1, "rb") as f:
    d1 = f.read()
  with open(fn2, "rb") as f:
    d2 = f.read()

  assert d1.startswith(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
  assert d2.startswith(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

  assert d1[:0x21] == d2[:0x21]

  return d1, d2


d1, d2 = get_data(sys.argv[1:3])

hash = hashlib.sha256(d1[:0x21]).hexdigest()[:8]

print(f"Header hash: {hash}")

if not glob.glob(f"png1-{hash}.bin"):
  print("Not found! Launching computation...")

  # make the complete prefix
  with open("prefix", "wb") as f:
    f.write(b"".join([
    # 00-20 - original common header
    d1[:0x21],
    # 21-46 - padding chunk
    b"\0\0\0\x1a", b"aNGE", b":MD5 ISREALLY DEAD NOW!!1!", b"ROFL",

    # 47-C7 - collision chunk

    # 47-4F
    # this is the end of the collision prefix,
    # => lengths of 0x75 and 0x175
    b"\0\0\0\x75", b"mARC", b"!",

    # the end of the collision blocks if they're not computed
    # 50-BF
    # " " * 0x70,
  ]))

  # Note: make sure poc_no.sh is unmodified (ie, N=1)
  os.system("../hashclash/scripts/poc_no.sh prefix")

  shutil.copyfile("collision1.bin", f"png1-{hash}.bin")
  shutil.copyfile("collision2.bin", f"png2-{hash}.bin")

with open(f"png1-{hash}.bin", "rb") as f:
  block1 = f.read()
with open(f"png2-{hash}.bin", "rb") as f:
  block2 = f.read()

assert len(block1) == 0xC0
assert len(block2) == 0xC0

ascii_art = b"""
/==============\\
|*            *|
|  PNG IMAGE   |
|     with     |
|  identical   |
|   -prefix    |
| MD5 collision|
|              |
|  by          |
| Marc Stevens |
|  and         |
|Ange Albertini|
|              |
|*            *|
\\==============/
BRK!
""".replace(b"\n", b"").replace(b"\r", b"")

assert len(ascii_art) == 0xF4

suffix = b"".join([
    # C0-C7
    b"RealHash", # the remaining of the mARC chunk

    # C8-1C3 the tricky fake chunk

    # the length, the type and the data should all take 0x100
      struct.pack(">I", 0x100 - 4*2 + len(d2[0x21:])),
      b"jUMP",
      # it will cover all data chunks of d2,
      # and the 0x100 buffer
      ascii_art,
    b"\xDE\xAD\xBE\xEF", # fake CRC for mARC

    # 1C8 - Img2 + 4
    d2[0x21:],
    b"\x5E\xAF\x00\x0D", # fake CRC for jUMP after d2's IEND
    d1[0x21:],
  ])

with open(f"{hash}-1.png", "wb") as f:
  f.write(b"".join([
    block1,
    suffix
    ]))

with open(f"{hash}-2.png", "wb") as f:
  f.write(b"".join([
    block2,
    suffix
    ]))
