"""Minimal KiCad s-expression reader/writer used by the v1 generators."""
import re

class Sym(str):
    """Unquoted atom."""

_tok = re.compile(r'\s*(\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+)')

def parse(text):
    stack, cur = [], []
    for m in _tok.finditer(text):
        t = m.group(1)
        if t == '(':
            stack.append(cur); cur = []
        elif t == ')':
            done = cur; cur = stack.pop(); cur.append(done)
        elif t.startswith('"'):
            cur.append(t[1:-1].replace('\\"', '"').replace('\\\\', '\\'))
        else:
            cur.append(Sym(t))
    return cur[0]

def dump(x, ind=0):
    if isinstance(x, list):
        simple = all(not isinstance(e, list) for e in x)
        if simple:
            return '(' + ' '.join(dump(e) for e in x) + ')'
        out = '(' + ' '.join(dump(e) for e in x if not isinstance(e, list))
        for e in x:
            if isinstance(e, list):
                out += '\n' + '  ' * (ind + 1) + dump(e, ind + 1)
        return out + ')'
    if isinstance(x, Sym):
        return str(x)
    if isinstance(x, bool):
        return 'yes' if x else 'no'
    if isinstance(x, (int, float)):
        s = f'{x:.4f}'.rstrip('0').rstrip('.')
        return '0' if s in ('-0', '') else s
    return '"' + str(x).replace('\\', '\\\\').replace('"', '\\"') + '"'

def find(node, key):
    return [e for e in node if isinstance(e, list) and e and e[0] == key]

def first(node, key):
    r = find(node, key)
    return r[0] if r else None

_lib_cache = {}
def lib_symbol(lib, name, root='/usr/share/kicad/symbols'):
    """Return a fully resolved (extends flattened) symbol from a KiCad library."""
    if lib not in _lib_cache:
        _lib_cache[lib] = parse(open(f'{root}/{lib}.kicad_sym').read())
    L = _lib_cache[lib]
    syms = {s[1]: s for s in find(L, 'symbol')}
    s = syms[name]
    ext = first(s, 'extends')
    if ext:
        parent = syms[ext[1]]
        props = {p[1]: p for p in find(s, 'property')}
        new = [Sym('symbol'), name]
        for e in parent[2:]:
            if isinstance(e, list) and e[0] == 'property' and e[1] in props:
                new.append(props.pop(e[1]))
            elif isinstance(e, list) and e[0] == 'symbol':
                new.append([Sym('symbol'), e[1].replace(ext[1], name, 1)] + e[2:])
            else:
                new.append(e)
        new += list(props.values())
        s = new
    return s

def symbol_pins(sym):
    """[(number, name, x, y, angle, length, type)] for unit 1 (and unit 0 shared)."""
    pins = []
    for sub in find(sym, 'symbol'):
        unit = int(sub[1].rsplit('_', 2)[-2])
        if unit not in (0, 1):
            continue
        for p in find(sub, 'pin'):
            at = first(p, 'at'); ln = first(p, 'length')
            pins.append((first(p, 'number')[1], first(p, 'name')[1], float(at[1]), float(at[2]),
                         float(at[3]) if len(at) > 3 else 0.0, float(ln[1]), str(p[1])))
    return pins
