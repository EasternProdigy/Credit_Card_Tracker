#!/usr/bin/env python3
"""`ngspice -b file.cir` replacement that drives the shared libngspice (the engine KiCad's
simulator uses) when the ngspice CLI is not installed. Prints ngspice's stdout/stderr lines."""
import ctypes, sys, os
lib = ctypes.CDLL(os.environ.get('LIBNGSPICE', 'libngspice.so.0'))
out = []
PRINT = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
STAT = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p)
EXIT = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_bool, ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
def _p(s, i, v):
    t = s.decode(errors='replace')
    for pre in ('stdout ', 'stderr '):
        if t.startswith(pre): t = t[len(pre):]
    out.append(t); return 0
cb_p, cb_s, cb_e = PRINT(_p), STAT(lambda s, i, v: 0), EXIT(lambda *a: 0)
lib.ngSpice_Init(cb_p, cb_s, cb_e, None, None, None, None)
args = [a for a in sys.argv[1:] if not a.startswith('-')]
f = os.path.abspath(args[0])
lib.ngSpice_Command(f'source {f}'.encode())
src = open(f).read().lower()
if '.control' not in src:
    lib.ngSpice_Command(b'run')
print('\n'.join(out))
