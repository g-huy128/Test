import sys
import ast
import random
import zlib
import marshal
import base64
import lzma
import bz2
import string
import os
import time
import requests
import json
import hashlib
import uuid
from datetime import datetime





# ==============================================================================
# FYNIX OBFUSCATOR v4.0  —  Kin Premium Engine + Full PyHydra
# ==============================================================================

# ── Unicode / CJK identifier pools ─────────────────────────────────────────────
_KO_SYL = [chr(c) for c in range(0xAC00, 0xD7A3 + 1)]   # Korean syllables (11172)
_KAT    = [chr(c) for c in range(0x30A1, 0x30F7 + 1)]    # Katakana
_CJK    = [chr(c) for c in range(0x4E00, 0x9FFF + 1)]    # CJK Unified Ideographs

KOREAN_CHARS = "".join(_KO_SYL)                           # fast charset string

# Mixed pool for maximum entropy identifiers
_MIXED = _KO_SYL + _KAT + _CJK

STRING_OFFSET = 0x8F9A7B
INT_MASK      = 0xDEADBEEF


def _cjk_var(length=None):
    """Random CJK/Hangul identifier, always starts with alphabetic char."""
    k = length or random.randint(4, 8)
    while True:
        s = "".join(random.choices(_MIXED, k=k))
        if s[0].isalpha():
            return s

def _ko_var(length=None):
    """Pure Korean syllable identifier."""
    k = length or random.randint(3, 7)
    return "".join(random.choices(_KO_SYL, k=k))

def _unique_vars(count, factory=None):
    """Generate `count` unique CJK identifiers."""
    f = factory or _cjk_var
    seen, out = set(), []
    while len(out) < count:
        s = f()
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out

def _rn():
    """General random name: 40% ASCII underscore, 60% CJK."""
    if random.random() < 0.4:
        return "_" + "".join(random.choice(string.ascii_letters) for _ in range(random.randint(6, 12)))
    return _cjk_var()


# ==============================================================================
# PYHYDRA: Byte-by-Byte Lambda XOR Engine
# ==============================================================================

def _to_lambda_xor(data_bytes, factory=None, max_lambdas=40):
    """
    Encode bytes as randomized lambda expressions in chunks.
    Splits large data into multiple smaller lists to avoid compiler hangs.
    Returns a Python list-literal string or sum() expression for large data.
    factory: callable that returns a variable name string
    max_lambdas: maximum lambdas per list (default 40 to safely avoid compilation issues)
    """
    if factory is None:
        factory = lambda: _cjk_var(random.randint(3, 6))
    
    # Split into  chunks if too large
    if len(data_bytes) > max_lambdas:
        chunk_size = max_lambdas
        chunks = [data_bytes[i:i+chunk_size] for i in range(0, len(data_bytes), chunk_size)]
        chunk_lists = []
        for chunk in chunks:
            parts = []
            for b in chunk:
                key = random.randint(1, 255)
                val = b ^ key
                vn  = factory()
                form = random.randint(0, 3)
                if form == 0:
                    parts.append(f"(lambda {vn}:{vn}^{key})({val})")
                elif form == 1:
                    parts.append(f"(lambda {vn}:{key}^{vn})({val})")
                elif form == 2:
                    parts.append(f"(lambda {vn}:~~({vn}^{key}))({val})")
                else:
                    parts.append(f"(lambda {vn}:{vn}^{hex(key)})({hex(val)})")
            chunk_lists.append("[" + ",".join(parts) + "]")
        return "sum([" + ",".join(chunk_lists) + "],[])  # split for compiler"
    
    # Small data: single list expression
    parts = []
    for b in data_bytes:
        key = random.randint(1, 255)
        val = b ^ key
        vn  = factory()
        form = random.randint(0, 3)
        if form == 0:
            # Standard: (lambda x: x ^ k)(v)
            parts.append(f"(lambda {vn}:{vn}^{key})({val})")
        elif form == 1:
            # Inverted key order: (lambda x: k ^ x)(v)
            parts.append(f"(lambda {vn}:{key}^{vn})({val})")
        elif form == 2:
            # Double complement: (lambda x: ~~(x ^ k))(v)
            parts.append(f"(lambda {vn}:~~({vn}^{key}))({val})")
        else:
            # Hex variant: (lambda x: x ^ k)(v)  with hex literals
            parts.append(f"(lambda {vn}:{vn}^{hex(key)})({hex(val)})")
    return "[" + ",".join(parts) + "]"

def _xor_str(s):
    """Encode ASCII string as lambda-XOR list."""
    return _to_lambda_xor(s.encode("utf-8"))

def _hx(s):
    """Return bytes.fromhex('...').decode() literal."""
    return "bytes.fromhex('{}').decode()".format(s.encode().hex())


# ==============================================================================
# HEAVY JUNK ENGINE (PyHydra-style Korean junk classes + dispatch tables)
# ==============================================================================

_BM = [0xDEAD, 0xBEEF, 0xCAFE, 0xBABE, 0xF00D, 0xC0DE, 0x1337, 0xA5A5,
       0xFF00, 0x5A5A, 0xAAAA, 0x3C3C, 0x7FFF, 0xCCCC, 0x0FF0]

def _ko_rv():
    """Random obfuscated value expression used in heavy junk."""
    a, b = random.randint(1, 0xFFFF), random.randint(1, 0xFFFF)
    m    = random.choice(_BM)
    vn   = _ko_var()
    opts = [
        f"(lambda {vn}:{vn}^{m})({a ^ m})",
        f"({hex(a)}^{hex(b)})&{hex(m)}",
        f"~{hex(a)}&{hex(m)}",
        f"({hex(a)}<<{random.randint(1,4)})|({hex(b)}>>{random.randint(1,3)})",
        _to_lambda_xor(bytes([random.randint(0, 255) for _ in range(random.randint(2, 5))])),
        f"'{_ko_var()}'",
    ]
    return random.choice(opts)

def _ko_junk_class():
    """One heavy junk class with Korean-named methods and lambda-XOR attributes."""
    cn    = _ko_var(random.randint(4, 7))
    sa    = _ko_var()
    attrs = _unique_vars(random.randint(3, 5), _ko_var)
    mns   = _unique_vars(3, _ko_var)
    a1    = random.randint(1, 0xFFF)
    m1    = random.choice(_BM)
    L = [f"class {cn}:"]
    for av in attrs:
        L.append(f"    {av}={_ko_rv()}")
    L += [
        f"    def __init__({sa},*args,**kwargs):",
        f"        {sa}._v={_ko_rv()}",
        f"        if 0:raise RuntimeError",
        f"    def {mns[0]}({sa},*args):",
        f"        {_ko_var()}={_ko_rv()}",
        f"        if 0:return False",
        f"        return({a1}^len(args))&{hex(m1)}",
        f"    def {mns[1]}({sa}):",
    ]
    for kv in _unique_vars(random.randint(2, 4), _ko_var):
        L.append(f"        {kv}={_ko_rv()}")
    L += [
        f"        return {hex(a1)}&{hex(m1)}",
        f"    def {mns[2]}({sa},*args):",
        f"        if 0:return(lambda _φ:_φ)(None)",
        f"        return {_ko_rv()}",
        "",
    ]
    return L

def _dead_while(ind=""):
    """Dead while-loop junk block."""
    wv = _rn()
    m  = random.choice(_BM)
    return [
        f"{ind}{wv}=0",
        f"{ind}while False:",
        f"{ind}    {wv}=({wv}^{hex(random.randint(1,0xFFF))})&{hex(m)}",
        f"{ind}    if {wv}>0xFFFF:break",
    ]

def _dispatch_table(ind=""):
    """Fake dispatch table junk."""
    tbl = _rn()
    lk  = _rn()
    ks  = [random.randint(0, 0xFF) for _ in range(random.randint(3, 7))]
    ent = ",".join(f"{hex(k)}:(lambda _z:_z^{hex(random.randint(1,0xFFF))})" for k in ks)
    return [
        f"{ind}{tbl}={{{ent}}}",
        f"{ind}{lk}={hex(random.choice(ks))}",
        f"{ind}if 0:{tbl}[{lk}]({hex(random.randint(1,0xFF))})",
    ]

def _fake_exception_handler(ind=""):
    """Dead try/except block with complex exception matching."""
    vn1 = _rn()
    vn2 = _ko_var()
    m = random.choice(_BM)
    return [
        f"{ind}try:",
        f"{ind}    if 0:",
        f"{ind}        {vn1}={hex(random.randint(1,0xFFF))}",
        f"{ind}        raise ValueError({hex(m)})",
        f"{ind}except (ValueError,TypeError,KeyError) as {vn2}:",
        f"{ind}    if 0:{vn1}=getattr({vn2},'args',({hex(m)},))[0]",
        f"{ind}except:",
        f"{ind}    pass",
    ]

def _nested_lambda_chain(ind=""):
    """Dead nested lambda chain — confuses decompilers."""
    vn = _rn()
    depth = random.randint(3, 6)
    expr = hex(random.randint(1, 0xFFF))
    for _ in range(depth):
        p = _ko_var(3)
        expr = f"(lambda {p}:{p}^{hex(random.choice(_BM))})({expr})"
    return [f"{ind}{vn}={expr}"]

def _opaque_predicate(ind=""):
    """Opaque predicate — always True/False but hard to prove statically."""
    vn = _rn()
    pat = random.choice([
        f"{ind}{vn}=((id(type)^id(object))&1)==((id(type)^id(object))&1)",
        f"{ind}{vn}=(len(str(id(None)))>0) and (type(None) is type(None))",
        f"{ind}{vn}=(hash(frozenset())^hash(frozenset()))==0",
        f"{ind}if (id(None)%2==id(None)%2):pass",
        f"{ind}if not(type(0) is type(1)):raise SystemError",
    ])
    return [pat]

def _time_reference_junk(ind=""):
    """Dead code referencing time module — decoy for analyst attention."""
    vn = _rn()
    vn2 = _ko_var()
    return [
        f"{ind}if 0:",
        f"{ind}    {vn}=__import__('time').time()",
        f"{ind}    {vn2}=int({vn}*1000)^{hex(random.choice(_BM))}",
        f"{ind}    if {vn2}>{hex(random.randint(0x1000,0xFFFF))}:pass",
    ]


def _generate_heavy_junk(nc=15, nv=40, nf=15):
    """
    Generate hundreds of lines of dead-code junk:
    Korean variable chains, junk classes, junk functions, dispatch tables,
    fake exception handlers, and nested lambda chains.
    """
    lines = []
    # CJK variable chains
    for kv in _unique_vars(nv, _ko_var):
        lines.append(f"{kv}={_ko_rv()}")
    lines.append("")
    # dead while loops
    for _ in range(max(2, nc // 4)):
        lines.extend(_dead_while())
        lines.append("")
    # junk classes
    for _ in range(nc):
        lines.extend(_ko_junk_class())
    # junk functions
    for _ in range(nf):
        fn = _rn()
        va = _ko_var()
        m  = random.choice(_BM)
        a  = random.randint(1, 0xFFF)
        b  = random.randint(1, 0xFFF)
        lines += [
            f"def {fn}(*args):",
            f"    {va}={hex(a)}^{hex(b)}",
            f"    if 0:return None",
            f"    return {va}&{hex(m)}",
            "",
        ]
    # dispatch tables
    for _ in range(max(3, nc // 3)):
        lines.extend(_dispatch_table())
    lines.append("")
    # fake exception handlers
    for _ in range(max(2, nc // 5)):
        lines.extend(_fake_exception_handler())
        lines.append("")
    # nested lambda chains
    for _ in range(max(3, nc // 3)):
        lines.extend(_nested_lambda_chain())
    lines.append("")
    # opaque predicates
    for _ in range(max(2, nc // 4)):
        lines.extend(_opaque_predicate())
    lines.append("")
    # time reference decoys
    for _ in range(max(2, nc // 5)):
        lines.extend(_time_reference_junk())
        lines.append("")
    # trailing variable chain
    for kv in _unique_vars(nv, _ko_var):
        lines.append(f"{kv}={_ko_rv()}")
    lines.append("")
    return "\n".join(lines)


# ==============================================================================
# PYHYDRA OUTPUT ENGINE: _generate_output (full copy + improvements)
# Produces: CJK junk → PyHydra XOR chunks → __Fynix_Hydra__ → __Fynix_Executor__
# ==============================================================================

def _generate_cjk_junk(count=20):
    """Junk CJK classes with lambda-XOR fields."""
    lines = []
    for _ in range(count):
        cn    = _cjk_var(8)
        fn1   = _cjk_var(10)
        fn2   = _cjk_var(10)
        tv1   = _cjk_var(6)
        tv2   = _cjk_var(6)
        args1 = _cjk_var()
        kw1   = _cjk_var()
        lines += [
            f"class __{cn}__:",
            f"    def __init__(Fynix, *{args1}, **{kw1}):",
            f"        Fynix._{tv1} = {_to_lambda_xor(b'JUNK', factory=lambda: _cjk_var(random.randint(4,7)))}",
            f"    def {fn1}(Fynix, {tv2}):",
            f"        if (((id(Fynix)>>3)&7)^8)%2 != 0: return False",
            f"        global {_cjk_var()}, {_cjk_var()}",
            f"        return (lambda {tv1}: {tv1} ^ 1337)({random.randint(1000, 9999)})",
            f"    def {fn2}(Fynix):",
            f"        try:",
            f"            getattr(Fynix, '{_cjk_var()}')()",
            f"        except:",
            f"            pass",
            "",
        ]
    return "\n".join(lines)


def _generate_output(payload):
    """
    Full PyHydra output template.
    Architecture:
      1. CJK junk classes
      2. Payload split into N chunks, each byte lambda-XOR'd with CJK var names
      3. Payload var = bytes(chunk0 + chunk1 + ...)
      4. Hydra class — recovers globals/builtins/eval/compile/bytes
      5. Executor class — rebuilds core decoder src via XOR, compile+exec's it
    payload: bytes (b85-encoded marshalled bytecode)
    """
    # XOR-encode sensitive strings
    xor_builtins = _to_lambda_xor(b"builtins",  factory=lambda: _cjk_var(random.randint(4, 7)))
    xor_dict     = _to_lambda_xor(b"__dict__",  factory=lambda: _cjk_var(random.randint(4, 7)))
    xor_eval     = _to_lambda_xor(b"eval",      factory=lambda: _cjk_var(random.randint(4, 7)))
    xor_compile  = _to_lambda_xor(b"compile",   factory=lambda: _cjk_var(random.randint(4, 7)))
    xor_bytes_   = _to_lambda_xor(b"bytes",     factory=lambda: _cjk_var(random.randint(4, 7)))
    # Obfuscate '<string>' literal passed to compile()
    xor_string_tag = _to_lambda_xor(b"<string>", factory=lambda: _cjk_var(random.randint(4, 7)))

    # Randomized class/variable names — no more predictable __Fynix_Hydra__
    payload_var   = _cjk_var(8)   # replaces Fynix_PAYLOAD
    hydra_cls     = f"__{_cjk_var(6)}__"  # replaces __Fynix_Hydra__
    executor_cls  = f"__{_cjk_var(6)}__"  # replaces __Fynix_Executor__
    # Randomized global vars — no more predictable _g, _b, _e, _c, _bytes
    g_globals = _cjk_var(4)
    g_builtins = _cjk_var(4)
    g_eval = _cjk_var(4)
    g_compile = _cjk_var(4)
    g_bytes = _cjk_var(4)

    # Core decoder source — stored XOR'd, rebuilt at runtime
    _cd_b64 = _cjk_var(5)
    _cd_zlib = _cjk_var(5)
    core_decoder = (
        f"{_cd_b64}=__import__(bytes.fromhex('{b'base64'.hex()}').decode())\n"
        f"{_cd_zlib}=__import__(bytes.fromhex('{b'zlib'.hex()}').decode())\n"
        f"exec({_cd_zlib}.decompress({_cd_b64}.b85decode({payload_var})).decode('utf-8','ignore'), globals())"
    )
    xor_core = _to_lambda_xor(core_decoder.encode("utf-8"), factory=lambda: _cjk_var(random.randint(4, 7)))

    # Split payload into CJK-named XOR chunks
    nch       = random.randint(8, 16)
    csz       = max(1, len(payload) // nch)
    chunks    = [payload[i:i+csz] for i in range(0, len(payload), csz)]
    cvars     = [_cjk_var(6) for _ in chunks]

    # Method / argument names
    v_args   = _cjk_var()
    v_kwargs = _cjk_var()
    v_a      = _cjk_var()
    hydra_setup  = _cjk_var(8)
    exec_method  = _cjk_var(8)
    instance_var = _cjk_var(5)

    # Obfuscate header strings to avoid static signatures
    enc_own = _xor_str("Kin @kinmataccroi")
    enc_obf = _xor_str("Fynix Premium")
    enc_usr = _xor_str("Kindepzai")

    L = [
        "# -*- coding: utf-8 -*-",
        f"__OBF__ = bytes({enc_obf}).decode()",
        f"__OWN__ = bytes({enc_own}).decode()",
        f"__USR__ = bytes({enc_usr}).decode()",
        "",
        _generate_cjk_junk(random.randint(10, 20)),
    ]

    # Payload chunk lambda-XOR assignments
    for var, chunk in zip(cvars, chunks):
        L.append(f"{var} = {_to_lambda_xor(chunk, factory=lambda: _cjk_var(random.randint(4,7)))}")
    if cvars:
        L.append(f"{payload_var} = bytes(sum([{','.join(cvars)}], []))")
    else:
        L.append(f"{payload_var} = b''")

    # Payload integrity check — hash the payload and verify at runtime
    payload_hash = hashlib.sha256(payload).hexdigest()[:16]
    _v_hash = _cjk_var(6)
    _v_hashlib = _cjk_var(5)
    L.append(f"{_v_hashlib} = __import__({_hx('hashlib')})")
    L.append(f"{_v_hash} = {_v_hashlib}.sha256({payload_var}).hexdigest()[:16]")
    L.append(f"if {_v_hash} != '{payload_hash}':")
    L.append(f"    raise SystemExit(0)")
    L.append("")

    # Hydra class — sets up globals/builtins/eval/compile/bytes via CJK names
    L += [
        f"class {hydra_cls}:",
        f"    def __init__(Fynix, *{v_args}, **{v_kwargs}):",
        f"        Fynix._{v_args} = {v_args}; Fynix._{v_kwargs} = {v_kwargs}",
        f"    def {hydra_setup}(Fynix, *{v_args}, **{v_kwargs}):",
        f"        global {g_globals}, {g_builtins}, {g_eval}, {g_compile}, {g_bytes}",
        f"        {g_globals} = globals()",
        f"        {g_builtins} = object.__getattribute__(__import__(bytes({xor_builtins}).decode()), bytes({xor_dict}).decode())",
        f"        {g_eval} = {g_builtins}[bytes({xor_eval}).decode()]",
        f"        {g_compile} = {g_builtins}[bytes({xor_compile}).decode()]",
        f"        {g_bytes} = {g_builtins}[bytes({xor_bytes_}).decode()]",
        f"    def __call__(Fynix, *{v_args}, **{v_kwargs}):",
        f"        pass  # reserved",
        "",
        _generate_cjk_junk(random.randint(15, 25)),
    ]

    # Executor class — rebuilds + executes the bootstrap decoder
    _exc_var = _cjk_var(6)
    L += [
        f"class {executor_cls}:",
        f"    def __init__(Fynix, *{_cjk_var()}, **{_cjk_var()}): pass",
        f"    def __str__(Fynix): return {g_bytes}({xor_core}).decode()",
        f"    def {exec_method}(Fynix, {v_a}):",
        f"        {g_eval}({g_compile}({v_a}, bytes({xor_string_tag}).decode(), bytes.fromhex('{b'exec'.hex()}').decode()), {g_globals})",
        "    def __getattribute__(Fynix, name): return object.__getattribute__(Fynix, name)",
        f"    def __call__(Fynix, *args, **kwargs):",
        f"        return Fynix.{exec_method}(args[0]) if args else Fynix.{exec_method}(Fynix.__str__())",
        "",
        _generate_cjk_junk(random.randint(10, 20)),
    ]
    # Lambda junk line — pre-generate the param name so it's consistent
    _lambda_param = _cjk_var(6)
    L += [
        f"(lambda {_lambda_param}: (0 and {_lambda_param}(), {_lambda_param}()))(lambda *args, **kwargs: None)",
        "try:",
        f"    {instance_var} = {hydra_cls}()",
        f"    {instance_var}.{hydra_setup}()",
        f"    {executor_cls}()()",
        f"except Exception as {_exc_var}: pass",
        "",
        _generate_heavy_junk(nc=random.randint(10, 18), nv=random.randint(30, 50), nf=random.randint(10, 18)),
    ]

    return "\n".join(L)


# ==============================================================================
# ANTI-PYCDC TRAPS (v1, v2, v3)
# ==============================================================================

def apply_anti_pycdc_v1(code):
    """Walrus traps + deep ternary + co_consts mutation."""
    traps = []
    for _ in range(6):
        vn = _ko_var(3)
        traps.append(f"if 0:[({vn}:=x) for x in range(1) if ({vn}:=0)==0]")
    ternary = "None"
    for i in range(60):
        ternary = f"({ternary} if {i}%2 else None)"
    vn = _ko_var(3)
    traps.append(f"if 0:_{vn}={ternary}")
    traps.append("if 0:(lambda:[(z:=i) for i in range(1)])()")
    mutation = """
try:
    _뮤트=lambda:None
    _코=_뮤트.__code__
    _뮤트.__code__=_코.replace(co_consts=_코.co_consts+(None,Ellipsis,NotImplemented,b'\\xfe\\xff',0xDEAD))
except:pass
"""
    extra = "\n".join([f"{_ko_var(3)}=__import__('random').randint(1,1000)" for _ in range(10)])
    return "\n".join(traps) + "\n" + extra + "\n" + mutation + "\n" + code


def apply_anti_pycdc_v2(code):
    """Async traps + match/case + exception groups."""
    async_trap = """
if 0:
    async def _비동기뮤트():
        async for _ in (x async for x in ()):pass
        await __import__('asyncio').sleep(0)
        async with type('_cm',(),{'__aenter__':lambda s:s,'__aexit__':lambda s,*a:None})() as _:pass
"""
    match_trap = """
if 0:
    match {'key': [1,2,3]}:
        case {'key': [1, *rest]} if rest:
            pass
        case {'key': [_, _, third]} as captured:
            pass
        case _:
            pass
"""
    excgroup_trap = """
try:
    pass
except* ValueError as _eg1:
    pass
except* (TypeError, KeyError) as _eg2:
    pass
"""
    annot_trap = """
if 0:
    _: dict[str, *tuple[int, ...]] = {}
"""
    fstr_parts = []
    for _ in range(5):
        vn   = _ko_var(3)
        nums = ",".join(str(random.randint(32, 126)) for _ in range(15))
        fstr_parts.append(f"if 0:{vn}=''.join(chr(i) for i in [{nums}])")
    return async_trap + "\n" + match_trap + "\n" + excgroup_trap + "\n" + "\n".join(fstr_parts) + "\n" + annot_trap + "\n" + code


def apply_anti_pycdc_v3(code):
    """Metaclass traps + descriptor chain + bytecode injection."""
    metaclass_trap = """
try:
    class _메타트랩(type):
        def __new__(mcs,name,bases,ns,**kw):
            ns['__slots__']=('__dict__','__weakref__')
            return super().__new__(mcs,name,bases,ns)
        def __class_getitem__(cls,item):return cls
        def __init_subclass__(cls,**kw):super().__init_subclass__(**kw)
    class _래퍼(metaclass=_메타트랩):
        __match_args__=('__class__',)
        def __set_name__(self,owner,name):pass
        def __get__(self,obj,tp=None):return self
        def __set__(self,obj,value):pass
        def __delete__(self,obj):pass
except:pass
"""
    bytecode_inject = """
try:
    _더미=lambda:None
    _co=_더미.__code__
    _더미.__code__=_co.replace(
        co_stacksize=_co.co_stacksize+256,
        co_consts=_co.co_consts+(
            type('_봉인',(),{'__repr__':lambda s:'<sealed>'})(),
            frozenset({None,Ellipsis,NotImplemented}),
            complex(float('inf'),float('nan')),
        )
    )
except:pass
"""
    compr_traps = []
    for _ in range(3):
        vn = _ko_var(3)
        compr_traps.append(f"if 0:[({vn}:=i+1) for i in range(1) for _ in range(1) if ({vn}:=0)==0]")
    return metaclass_trap + "\n" + bytecode_inject + "\n" + "\n".join(compr_traps) + "\n" + code


def apply_anti_pycdc(code, strength=3):
    if strength >= 1:
        code = apply_anti_pycdc_v1(code)
    if strength >= 2:
        code = apply_anti_pycdc_v2(code)
    if strength >= 3:
        code = apply_anti_pycdc_v3(code)
    return code


# ==============================================================================
# AST-BASED STRING OBFUSCATION
# ==============================================================================

class _AstObfuscator(ast.NodeTransformer):
    def visit_Expr(self, node):
        # Prevent obfuscating docstrings
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return node
        return self.generic_visit(node)
        
    def visit_Constant(self, node):
        # String obfuscation
        if isinstance(node.value, str) and len(node.value) > 1:
            try:
                # Do not obfuscate too large strings to save time
                if len(node.value) < 1000:
                    xor_repr = _to_lambda_xor(node.value.encode('utf-8'))
                    expr = f"bytes({xor_repr}).decode('utf-8')"
                    return ast.parse(expr).body[0].value
            except:
                pass
        # Int obfuscation
        elif type(node.value) is int:
            if 3 <= node.value <= 0xFFFFFFFF:
                try:
                    a = random.randint(1, 0xFFFFFFFF)
                    b = random.randint(1, 0xFFFFFFFF)
                    val = node.value ^ a ^ b
                    expr = f"({val}^{b}^{a})"
                    return ast.parse(expr).body[0].value
                except:
                    pass
        return self.generic_visit(node)
        
    def visit_JoinedStr(self, node):
        # Do not descend into f-strings
        return self.generic_visit(node)

def apply_ast_string_obf(source_code):
    try:
        if not hasattr(ast, "unparse"):
            return source_code  # Requires Python 3.9+
        tree = ast.parse(source_code)
        _AstObfuscator().visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)
    except Exception:
        return source_code


# ==============================================================================
# ULTRA-ANTI: Full runtime anti-debug + anti-dump + anti-hook + anti-VM
# ==============================================================================

def ultra_anti():
    """
    Return the full ultra-anti source string.
    Checks (each adds to suspicious score, exit if >= 3):
      1.  NtQueryInformationProcess (Windows PEB debugger port)
      2.  IsDebuggerPresent + CheckRemoteDebuggerPresent
      3.  sys.gettrace — Python-level debugger
      4.  sys.settrace hook self-test
      5.  sys.monitoring (Python 3.12+ coverage hooks)
      6.  Timing check (slow = being stepped through)
      7.  Windows: tasklist scan for 40+ known tools
      8.  Linux/Android: ps scan for frida, gdb, lldb, strace
      9.  /proc/self/status TracerPid (Linux — most reliable)
      10. /proc/self/maps — frida/gadget injection detection
      11. VM environment variables + platform strings
      12. Windows registry VM/hypervisor check
      13. Anti-patch: IsDebuggerPresent prologue byte check (CC / E9 / 90)
      14. Anti-dump: SetProcessWorkingSetSize / HeapSetInformation
      15. Module import guard (blocks dis, pdb, inspect, pycdc)
      16. HTTP proxy / port scan (anti-Fiddler/Burp/Charles)
      17. Anti-frida: checks for frida-agent DLL in loaded modules
      18. Self-integrity: own file hash
    """
    return r"""
try:
    import sys as _sys, os as _os, time as _time, random as _rnd, hashlib as _hs, socket as _sock

    try:
        import ctypes as _ct
    except:
        _ct = None

    try:
        import subprocess as _sp
    except:
        _sp = None

    try:
        import platform as _pl
    except:
        _pl = None

    _sus = 0

    # ===== 1. NtQueryInformationProcess — Windows PEB debugger port + Thread Hide =====
    try:
        if _ct and _sys.platform == "win32":
            _ntdll = _ct.windll.ntdll
            _k32   = _ct.windll.kernel32
            _port  = _ct.c_ulong()
            _ntdll.NtQueryInformationProcess(
                _k32.GetCurrentProcess(), 7,
                _ct.byref(_port), _ct.sizeof(_port), None
            )
            if _port.value != 0:
                _sus += 5
            # 0x11 is ThreadHideFromDebugger — hides thread from debugger events
            _ntdll.NtSetInformationThread(_k32.GetCurrentThread(), 0x11, 0, 0)
    except:
        pass

    # ===== 2. IsDebuggerPresent / CheckRemoteDebuggerPresent =====
    try:
        if _ct and _sys.platform == "win32":
            _k32 = _ct.windll.kernel32
            if _k32.IsDebuggerPresent():
                _sus += 5
            _rdb = _ct.c_int(0)
            _k32.CheckRemoteDebuggerPresent(_k32.GetCurrentProcess(), _ct.byref(_rdb))
            if _rdb.value != 0:
                _sus += 5
    except:
        pass

    # ===== 3. sys.gettrace — Python debugger =====
    try:
        if hasattr(_sys, "gettrace") and _sys.gettrace() is not None:
            _sus += 5
    except:
        pass

    # ===== 4. sys.settrace self-test =====
    try:
        _trp = [False]
        def _tfn(f, e, a):
            _trp[0] = True
            return None
        _sys.settrace(_tfn)
        _x = 1 + 1
        _sys.settrace(None)
        if _trp[0]:
            _sus += 5
    except:
        pass

    # ===== 5. Python 3.12+ sys.monitoring coverage hooks =====
    try:
        if hasattr(_sys, "monitoring"):
            _mon = _sys.monitoring
            if callable(getattr(_mon, "get_tool", None)):
                for _tid in range(6):
                    if _mon.get_tool(_tid) is not None:
                        _sus += 3
                        break
    except:
        pass

    # ===== 6. Timing check =====
    try:
        _t1 = _time.perf_counter()
        for _ in range(600000):
            pass
        _t2 = _time.perf_counter()
        if (_t2 - _t1) > 6.0:
            _sus += 3
    except:
        pass

    # ===== 7. Windows: tasklist scan =====
    try:
        if _sys.platform == "win32" and _sp:
            _DEVNULL = getattr(_sp, "DEVNULL", None) or open(_os.devnull, "w")
            _out = _sp.check_output(
                ["tasklist", "/fo", "csv", "/nh"],
                stderr=_DEVNULL, timeout=5
            )
            _low = _out.decode("utf-8", errors="ignore").lower()
            _bad = [
                "x64dbg", "x32dbg", "x96dbg", "ollydbg", "windbg",
                "ida64", "ida", "ghidra", "cheatengine", "processhacker",
                "wireshark", "fiddler", "charles", "burpsuite", "httpdebugger",
                "httpdebuggerui", "mitmproxy", "proxyman", "zaproxy", "telerik",
                "dnspy", "de4dot", "ilspy", "dotpeek", "reflector",
                "justdecompile", "megadumper", "pydumpck", "uncompyle6",
                "decompyle3", "pycdc", "frida", "frida-server",
                "scylla", "lordpe", "pestudio", "protection_id",
                "die.exe", "detect-it-easy", "reshacker", "dependencywalker",
                "procexp", "procmon", "autoruns", "tcpview",
                "vboxservice", "vmtoolsd", "vmwaretray", "vmacthlp",
                "vgauthservice", "df5serv", "vboxtray", "vmsrvc", "vmusrvc",
                "qemu-ga", "xenservice", "prl_tools", "prl_cc",
                "joeboxserver", "joeboxcontrol", "ksdumper", "ksdumperclient",
                "httptoolkit",
            ]
            _mc = sum(1 for _p in _bad if _p in _low)
            if _mc >= 1:
                _sus += 5
    except:
        pass

    # ===== 8. Linux/Android: ps scan =====
    try:
        if _sys.platform.startswith("linux") and _sp:
            _DEVNULL = getattr(_sp, "DEVNULL", None) or open(_os.devnull, "w")
            _out = _sp.check_output(["ps", "aux"], stderr=_DEVNULL, timeout=5)
            _low = _out.decode("utf-8", errors="ignore").lower()
            _lbad = ["frida-server", "frida-gadget", "gdb", "lldb",
                     "/debugserver", "strace", "ltrace", "radare2", "r2"]
            if any(_x in _low for _x in _lbad):
                _sus += 4
    except:
        pass

    # ===== 9. /proc/self/status TracerPid =====
    try:
        if _sys.platform.startswith("linux"):
            with open("/proc/self/status", "r") as _f:
                for _ln in _f:
                    if _ln.startswith("TracerPid:"):
                        _tv = int(_ln.split(":")[1].strip())
                        if _tv != 0:
                            _sus += 10
                        break
    except:
        pass

    # ===== 10. /proc/self/maps — frida/gadget injection =====
    try:
        if _sys.platform.startswith("linux"):
            with open("/proc/self/maps", "r") as _f:
                _maps = _f.read().lower()
            _frida_signs = ["frida", "gadget", "linjector", "xposed"]
            if any(_s in _maps for _s in _frida_signs):
                _sus += 10
    except:
        pass

    # ===== 11. VM environment + platform strings =====
    try:
        _estr = str(_os.environ).lower()
        _vmi  = ["vmware", "vbox", "qemu", "hyperv", "xen",
                 "parallels", "kvm", "sandbox", "virtualbox", "docker"]
        if any(_v in _estr for _v in _vmi):
            _sus += 2
    except:
        pass
    try:
        if _pl:
            _utxt = str(_pl.uname()).lower()
            if any(_v in _utxt for _v in ["vmware", "vbox", "xen", "qemu", "kvm"]):
                _sus += 2
    except:
        pass

    # ===== 12. Windows registry VM check =====
    try:
        if _sys.platform == "win32":
            import winreg as _wr
            _reg_paths = [
                ("HKLM\\SYSTEM\\CurrentControlSet\\Services\\Disk\\Enum", "0"),
                ("HKLM\\HARDWARE\\DEVICEMAP\\Scsi\\Scsi Port 0\\Scsi Bus 0\\Target Id 0\\Logical Unit Id 0", "Identifier"),
            ]
            for _rp, _rv in _reg_paths:
                try:
                    _hive, _path = _rp.split("\\", 1)
                    _hmap = {"HKLM": _wr.HKEY_LOCAL_MACHINE, "HKCU": _wr.HKEY_CURRENT_USER}
                    _k = _wr.OpenKey(_hmap[_hive], _path)
                    _val, _ = _wr.QueryValueEx(_k, _rv)
                    _wr.CloseKey(_k)
                    if any(_v in str(_val).lower() for _v in ["vmware", "vbox", "virtual", "qemu"]):
                        _sus += 3
                except:
                    pass
    except:
        pass

    # ===== 13. Anti-patch: IsDebuggerPresent prologue byte check =====
    try:
        if _ct and _sys.platform == "win32":
            _k32  = _ct.windll.kernel32
            _addr = _k32.GetProcAddress(_k32._handle, b"IsDebuggerPresent")
            _buf  = (_ct.c_char * 4).from_address(_addr)
            _sig  = bytes(_buf)
            # INT3 patch (CC), JMP patch (E9), NOP sled (90)
            if _sig[0:1] in (b"\xCC", b"\xE9", b"\x90\x90"):
                _sus += 5
    except:
        pass

    # ===== 14. Anti-dump: NtSetInformationProcess HeapFlags =====
    try:
        if _ct and _sys.platform == "win32":
            _k32 = _ct.windll.kernel32
            _k32.SetErrorMode(1)
            # Heap: disable terminate-on-corruption so dumps capture partial state
            _ct.windll.ntdll.RtlSetHeapInformation(None, 1, None, 0)
            # SetProcessWorkingSetSize — forces pages out, breaks memory dumpers
            _k32.SetProcessWorkingSetSize(_k32.GetCurrentProcess(), -1, -1)
    except:
        pass

    # ===== 15. Module import guard =====
    try:
        _BLOCKED = frozenset({"dis", "pdb", "pudb", "bdb", "trace",
                               "pycdc", "uncompyle6", "decompyle3",
                               "cProfile", "profile", "coverage"})
        _orig_imp = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__
        def _guarded(name, *a, **kw):
            if name.split(".")[0] in _BLOCKED:
                raise ImportError(f"Module '{name}' is restricted")
            return _orig_imp(name, *a, **kw)
        __builtins__.__import__ = _guarded
    except:
        pass

    # ===== 16. HTTP proxy / Fiddler / Burp / Charles ports =====
    try:
        _proxy_ports = [8080, 8888, 3128, 8118, 9999, 8081, 8000,
                        9080, 8008, 11371, 6060, 2121, 8443, 7777]
        for _port in _proxy_ports:
            try:
                _s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
                _s.settimeout(0.15)
                _res = _s.connect_ex(("127.0.0.1", _port))
                _s.close()
                if _res == 0:
                    _sus += 3
                    break
            except:
                pass
    except:
        pass

    # ===== 17. Anti-Frida: loaded module name scan (Windows) =====
    try:
        if _ct and _sys.platform == "win32":
            _ps2 = _ct.windll.psapi
            _k32 = _ct.windll.kernel32
            _hProc = _k32.GetCurrentProcess()
            _mods  = (_ct.c_void_p * 1024)()
            _cbNeeded = _ct.c_ulong()
            if _ps2.EnumProcessModules(_hProc, _ct.byref(_mods), _ct.sizeof(_mods), _ct.byref(_cbNeeded)):
                _nMods = _cbNeeded.value // _ct.sizeof(_ct.c_void_p)
                for _i in range(_nMods):
                    _buf = _ct.create_unicode_buffer(260)
                    _ps2.GetModuleFileNameExW(_hProc, _mods[_i], _buf, 260)
                    _mn = _buf.value.lower()
                    if any(_fx in _mn for _fx in ["frida", "gadget", "detours", "minhook"]):
                        _sus += 10
                        break
    except:
        pass

    # ===== 18. Self-integrity check =====
    try:
        _self_path = _os.path.abspath(_sys.argv[0]) if _sys.argv else None
        if _self_path and _os.path.exists(_self_path):
            with open(_self_path, "rb") as _sf:
                _sdata = _sf.read(65536)
            if len(_sdata) < 50:
                _sus += 3
    except:
        pass

    # ===== FINAL VERDICT =====
    if _sus >= 3:
        try:
            # Corrupt own globals silently
            import ctypes as _ct2
            _ct2.memset(id(globals()), 0, 8)
        except:
            pass
        try:
            _os._exit(0)
        except:
            pass
        try:
            _sys.exit(0)
        except:
            pass

except:
    pass
"""


def apply_ultra_anti(code, android_compatible=False):
    """Obfuscate ultra_anti payload with polymorphic encoder and prepend to code."""
    anti_src = ultra_anti()
    # Encode the anti-debug code with polymorphic encoder (no nested anti_pycdc to avoid huge size)
    anti_obf = obfuscate_polymorphic(anti_src, use_anti_pycdc=False)
    if android_compatible:
        # On Android: skip Windows ctypes blocks silently — they're wrapped in try/except anyway
        # Just prepend a platform guard that exits if it's obviously a Windows-only debugger
        return f"{anti_obf}\n{code}"
    return f"{anti_obf}\n{code}"


# ==============================================================================
# POLYMORPHIC OBFUSCATION: Multi-XOR + shuffled base encoders
# ==============================================================================

def obfuscate_polymorphic(code, use_anti_pycdc=False, anti_pycdc_strength=2):
    if use_anti_pycdc:
        code = apply_anti_pycdc(code, strength=anti_pycdc_strength)

    key1 = random.randint(1, 255)
    key2 = random.randint(1, 255)
    key3 = random.randint(1, 255)
    key4 = random.randint(1, 255)
    data = code.encode("utf-8")
    reverse_flag = random.choice([True, False])

    data = bytes([b ^ key1 for b in data])
    data = bytes([b ^ key2 for b in data])
    if reverse_flag:
        data = data[::-1]
    data = bytes([b ^ key3 for b in data])
    data = bytes([b ^ key4 for b in data])

    encoders = [
        ("b85", base64.b85encode),
        ("b64", base64.b64encode),
        ("b32", base64.b32encode),
        ("b16", base64.b16encode),
    ]
    random.shuffle(encoders)

    # Random compression selection for polymorphism
    comp_choices = [
        ("zlib", lambda d: zlib.compress(d, level=9), "__import__('zlib').decompress"),
        ("lzma", lambda d: lzma.compress(d), "__import__('lzma').decompress"),
        ("bz2", lambda d: bz2.compress(d, compresslevel=9), "__import__('bz2').decompress"),
    ]
    comp_name, comp_func, decomp_expr = random.choice(comp_choices)
    data = comp_func(data)

    order = []
    for name, func in encoders:
        data = func(data)
        order.append(name)

    encoded = data.decode()
    size = random.randint(40, 80)
    parts = [encoded[i:i+size] for i in range(0, len(encoded), size)]
    joined = " ".join([f"b'{p}'" for p in parts])

    vd  = _rn(); vk1 = _rn(); vk2 = _rn()
    vk3 = _rn(); vk4 = _rn(); vt  = _rn()

    decode_map = {
        "b85": "__import__('base64').b85decode",
        "b64": "__import__('base64').b64decode",
        "b32": "__import__('base64').b32decode",
        "b16": "__import__('base64').b16decode",
    }
    chain = vd
    for name in reversed(order):
        chain = f"{decode_map[name]}({chain})"

    exec_forms = [
        ("call", "__import__('builtins').exec"),
        ("dict", "__import__('builtins').__dict__['exec']"),
        ("concat", "__import__('builtins').__dict__['e'+'x'+'e'+'c']"),
    ]
    exec_kind, exec_fn = random.choice(exec_forms)

    # Junk blocks: pre-data, between XOR ops, and before exec
    junk_pre  = "\n".join([f"{_ko_var()}={_ko_rv()}" for _ in range(random.randint(6, 12))])
    junk_mid  = "\n".join([f"{_ko_var()}={_ko_rv()}" for _ in range(random.randint(3, 6))])
    junk_post = "\n".join([f"{_ko_var()}={_ko_rv()}" for _ in range(random.randint(3, 6))])
    rev_line  = f"{vt}={vt}[::-1]" if reverse_flag else ""

    # Build the exec line using the chosen polymorphic form
    exec_line = f"{exec_fn}({vt}.decode('utf-8',errors='ignore'), globals())"

    return f"""# -*- coding: utf-8 -*-
{junk_pre}
{vd}={joined}
{vk1}={key1}
{vk2}={key2}
{vk3}={key3}
{vk4}={key4}
{vt}={decomp_expr}({chain})
{junk_mid}
{vt}=bytes([b^{vk1} for b in {vt}])
{vt}=bytes([b^{vk2} for b in {vt}])
{rev_line}
{vt}=bytes([b^{vk3} for b in {vt}])
{vt}=bytes([b^{vk4} for b in {vt}])
{junk_post}
{exec_line}
"""


# ==============================================================================
# CORE PAYLOAD PIPELINE
# ==============================================================================

def encode_source_to_payload(source_code, use_compilation=True):
    """
    source -> (compile ->) marshal -> zlib -> base85
    Returns bytes (b85).
    """
    if use_compilation:
        co   = compile(source_code, "<string>", "exec")
        data = marshal.dumps(co)
    else:
        data = source_code.encode("utf-8", errors="replace")
    return base64.b85encode(zlib.compress(data, level=9))


def create_decode_script(encoded_payload, use_compilation=True):
    """
    Build a minimal loader that is itself a valid Python script.
    Uses hex encoding for payload and __import__ with hex names for modules.
    """
    hex_payload = encoded_payload.hex()

    # Obfuscate module names using hex encoding
    _v_sys = _rn()
    _v_io = _rn()
    _v_b64 = _rn()
    _v_zlib = _rn()
    _v_marshal = _rn()
    _v_data = _rn()

    if use_compilation:
        # Obfuscate 'marshal' module name via hex encoding
        exec_logic = f"exec(__import__({_hx('marshal')}).loads({_v_data}), globals())"
    else:
        exec_logic = f"exec({_v_data}.decode('utf-8', errors='ignore'), globals())"

    return f"""{_v_sys}=__import__({_hx('sys')})
{_v_io}=__import__({_hx('io')})
{_v_b64}=__import__({_hx('base64')})
{_v_zlib}=__import__({_hx('zlib')})
try:
    if not isinstance({_v_sys}.stdout, {_v_io}.TextIOWrapper) or getattr({_v_sys}.stdout, 'encoding', '').lower() not in ('utf-8', 'utf8'):
        {_v_sys}.stdout = {_v_io}.TextIOWrapper({_v_sys}.stdout.buffer, encoding='utf-8', errors='replace')
    if not isinstance({_v_sys}.stderr, {_v_io}.TextIOWrapper) or getattr({_v_sys}.stderr, 'encoding', '').lower() not in ('utf-8', 'utf8'):
        {_v_sys}.stderr = {_v_io}.TextIOWrapper({_v_sys}.stderr.buffer, encoding='utf-8', errors='replace')
except: pass
{_v_data} = {_v_zlib}.decompress({_v_b64}.b85decode(bytes.fromhex({hex_payload!r})))
{exec_logic}
"""


def simple_obf_payload(decode_script):
    """
    Wrap decode_script in PyHydra premium output.
    1. Compress decode_script -> b85 payload
    2. Pass to _generate_output (full PyHydra architecture)
    """
    data      = decode_script.encode("utf-8")
    compressed = zlib.compress(data, level=9)
    payload   = base64.b85encode(compressed)
    return _generate_output(payload)


# ==============================================================================
# FULL OBFUSCATION PIPELINE
# ==============================================================================

def run_obfuscation(source_code, level=2, use_anti_debug=True,
                    use_compilation=True, android_compatible=False):
    """
    5-step premium pipeline:
      1. Anti-PyCDC traps (if not marshalling — traps are text-only)
         If marshalling: inject CJK junk vars before compile
      2. ultra_anti debug detection (if enabled)
      3. encode: source -> (marshal ->) zlib -> b85
      4. create thin loader script
      5. wrap in PyHydra CJK class-matrix (marshalled)
    """
    junk_sizes = {1: (8, 20, 8), 2: (15, 40, 15), 3: (25, 70, 25)}
    nc, nv, nf = junk_sizes.get(level, junk_sizes[2])

    print(f"  [1/5] Anti-PyCDC traps (strength={level})...")
    if level > 0 and not use_compilation:
        source_code = apply_anti_pycdc(source_code, strength=level)
    elif level > 0:
        # Inject junk vars visible to the compiler — makes marshal harder to read
        source_code = _generate_heavy_junk(nc=level*3, nv=level*10, nf=level*3) + "\n" + source_code

    print(f"  [2/5] ultra_anti inject ({'ON' if use_anti_debug else 'off'})...")
    if use_anti_debug:
        source_code = apply_ultra_anti(source_code, android_compatible=android_compatible)

    print(f"  [2.5/5] AST Constant Encryption (Strings+Numbers)...")
    if level >= 2 and use_compilation:
        source_code = apply_ast_string_obf(source_code)

    print(f"  [3/5] Encoding payload (bytecode={'marshal' if use_compilation else 'raw'})...")
    encoded = encode_source_to_payload(source_code, use_compilation=use_compilation)

    print(f"  [4/5] Building loader ({len(encoded):,} bytes encoded)...")
    decode_script = create_decode_script(encoded, use_compilation=use_compilation)

    print(f"  [5/5] PyHydra CJK class-matrix wrapping...")
    result = simple_obf_payload(decode_script)

    return result


# ==============================================================================
# FILE UTILITIES
# ==============================================================================

def extract_imports(source_code):
    import re
    imports = set()
    p1 = r"^import\s+([\w\.]+)(?:\s+as\s+\w+)?$"
    p2 = r"^from\s+([\w\.]+)\s+import"
    for line in source_code.splitlines():
        line = line.strip()
        m = re.match(p1, line)
        if m:
            mod = m.group(1).split(".")[0]
            if mod not in ("__future__",):
                imports.add(mod)
        m = re.match(p2, line)
        if m:
            mod = m.group(1).split(".")[0]
            if mod not in ("__future__",):
                imports.add(mod)
    return imports


def compile_to_exe(py_file, source_code):
    import subprocess
    basename   = os.path.basename(py_file).replace(".py", "")
    cpu_jobs   = max(1, os.cpu_count() or 1)
    imports    = extract_imports(source_code)
    cmd = [
        "python", "-m", "nuitka",
        "--onefile", "--output-dir=dist_final", "--remove-output",
        "--python-flag=-OO", f"--jobs={cpu_jobs}",
        "--nofollow-import-to=tkinter", "--nofollow-import-to=unittest",
        "--nofollow-import-to=pydoc",   "--nofollow-import-to=doctest",
        "--nofollow-import-to=difflib", "--lto=no",
        "--no-progressbar", "--python-flag=no_site",
        "--include-module=hashlib",  "--include-module=marshal",
        "--include-module=zlib",     "--include-module=base64",
        "--include-module=ctypes",   "--include-module=socket",
        "--include-module=ssl",      "--include-module=platform",
        "--include-module=subprocess","--include-module=winreg",
        "--include-module=warnings", "--include-module=inspect",
        "--include-module=random",   "--include-module=string",
        "--include-module=re",       "--include-module=time",
        "--include-module=struct",   "--include-module=io",
        "--include-module=abc",      "--include-module=functools",
        "--include-module=itertools","--include-module=collections",
        "--include-module=threading","--include-module=traceback",
        "--include-module=types",    "--include-module=copy",
        "--include-module=enum",     "--include-module=logging",
        "--include-module=urllib",   "--include-module=urllib3",
        "--include-module=http",     "--include-module=email",
        "--include-module=xml",      "--include-module=html",
    ]
    for imp in imports:
        cmd.append(f"--include-module={imp}")
    cmd.append(py_file)
    print(f"  Compiling with Nuitka ({cpu_jobs} jobs)...")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if res.returncode == 0:
            exe_path = os.path.join("dist_final", f"{basename}.exe")
            if os.path.exists(exe_path):
                print(f"  [OK] Compiled: {exe_path}")
                return True, exe_path
            print("  [OK] Compiled — check dist_final/ for .exe")
            return True, "dist_final/"
        print(f"  [ERROR] Nuitka: {res.stderr[:500]}")
        return False, res.stderr
    except FileNotFoundError:
        print("  [ERROR] Nuitka not found. pip install nuitka")
        return False, "nuitka not found"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


# ==============================================================================
# INTERACTIVE GUI MODE
# ==============================================================================

def main_interactive(saved_key=None, key_info=None):
    print("=" * 70)
    print("    ███████╗██╗   ██╗███╗   ██╗██╗██╗  ██╗")
    print("    ██╔════╝╚██╗ ██╔╝████╗  ██║██║╚██╗██╔╝")
    print("    █████╗   ╚████╔╝ ██╔██╗ ██║██║ ╚███╔╝ ")
    print("    ██╔══╝    ╚██╔╝  ██║╚██╗██║██║ ██╔██╗ ")
    print("    ██║        ██║   ██║ ╚████║██║██╔╝ ██╗")
    print("    ╚═╝        ╚═╝   ╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝")
    print("    Fynix Obfuscator v4.0  — Kin Premium Engine + PyHydra")
    print("    Made by Kin & Bduy  |  python 3.10+")
    print("=" * 70)
    print()

    # ── File ──
    while True:
        input_file = input("Enter Python file path: ").strip().strip('"').strip("'")
        if not input_file:
            continue
        if not os.path.exists(input_file):
            print(f"  [!] File not found: {input_file}")
            continue
        try:
            with open(input_file, "r", encoding="utf-8", errors="replace") as f:
                source_code = f.read()
            if not source_code.strip():
                print("  [!] File is empty.")
                continue
            break
        except Exception as e:
            print(f"  [!] Error reading file: {e}")

    # ── Level ──
    print()
    print("  Obfuscation Levels:")
    print("    1 — Light  (fast, minimal junk, basic PyHydra)")
    print("    2 — Medium (balanced, recommended)")
    print("    3 — Heavy  (max junk, maximum PyHydra + full anti-debug)")
    while True:
        try:
            level = int(input("Select level [1-3]: ").strip())
            if 1 <= level <= 3:
                break
        except ValueError:
            pass
        print("  [!] Enter 1, 2 or 3")

    use_anti_debug = input("Enable ultra_anti protection? (y/n) [y]: ").strip().lower()
    use_anti_debug = use_anti_debug not in ("n", "no")

    use_compilation = input("Compile to bytecode (marshal)? (y/n) [y]: ").strip().lower()
    use_compilation = use_compilation not in ("n", "no")

    print()
    print("  Output Format:")
    print("    1 — .py  (Python script)")
    print("    2 — .exe (Nuitka compiled)")
    while True:
        try:
            output_format = int(input("Select output format [1-2]: ").strip())
            if 1 <= output_format <= 2:
                break
        except ValueError:
            pass
        print("  [!] Enter 1 or 2")

    android_compatible = False
    if output_format == 1:
        tc = input("Termux/Android compatible? (y/n) [n]: ").strip().lower()
        android_compatible = tc in ("y", "yes")

    input_dir      = os.path.dirname(os.path.abspath(input_file))
    input_filename = os.path.basename(input_file)
    output_file    = os.path.join(input_dir, f"obf-{input_filename}")

    print()
    print(f"[*] Obfuscating : {input_file}")
    print(f"[*] Output      : {output_file}")
    print()

    try:
        result = run_obfuscation(
            source_code,
            level=level,
            use_anti_debug=use_anti_debug,
            use_compilation=use_compilation,
            android_compatible=android_compatible,
        )
    except Exception as e:
        import traceback
        print(f"\n[ERROR] Obfuscation failed: {e}")
        traceback.print_exc()
        return

    if output_format == 1:
        final = result
        if android_compatible:
            final = "#!/data/data/com.termux/files/usr/bin/python3\n" + final
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final)
        try:
            os.chmod(output_file, 0o755)
        except:
            pass
        sz = os.path.getsize(output_file)
        print(f"\n[SUCCESS] Saved: {output_file} ({sz:,} bytes)")
        if android_compatible:
            print(f"[*] Run on Termux: python3 {output_file}")

    elif output_format == 2:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result)
        sz = os.path.getsize(output_file)
        print(f"\n[*] .py saved: {output_file} ({sz:,} bytes)")
        ok, path = compile_to_exe(output_file, source_code)
        if ok:
            print(f"[SUCCESS] .exe: {path}")
        else:
            print(f"[WARN] .exe compilation failed — .py is still usable")

    # If the user is using the API key system with limits, deduct usage
    if saved_key and key_info and key_info.get("obf_limit") != "Unlimited":
        success, new_limit = deduct_usage(saved_key)
        if success:
            print(f"\n[+] Key usage deducted. Remaining uses: {new_limit}")
        else:
            print(f"\n[!] Failed to deduct key usage: {new_limit}")


# ==============================================================================
# ENTRY POINT
# ==============================================================================

def main():
    import sys, io
    # Force UTF-8 output on Windows console
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    print("=" * 75)
    print("    Fynix OBFUSCATOR v4.0  —  Kin Premium Engine + PyHydra")
    print("    Kin & Bduy with love")
    print("=" * 75)
    print()

    if not sys.stdin.isatty():
        print("[!] Non-interactive stdin detected.")
        print("[*] Run directly: python fynix_obf3.py")
        return

    print("[*] Key Verification")
    print("-" * 40)

    key_path  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keyobf.txt")
    saved_key = None
    if os.path.exists(key_path):
        with open(key_path, "r") as f:
            saved_key = f.read().strip()

    if not saved_key:
        try:
            saved_key = input("[>] Enter your key: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[!] No key provided.")
            return

    if not saved_key:
        print("[!] No key provided.")
        return

    # Prefer the online strict validation (HWID lock) if token is available
    status, info = False, "No token"
    if GITHUB_TOKEN:
        status, info = check_key_online(saved_key)
    if not status:
        # Fallback to local keys.txt / raw URL
        status, info = fetch_key_info_from_github(saved_key)

    if status:
        time_details = parse_key_time(info)
        print(f"[+] Key valid!")
        print(f"  - Uses remaining: {info.get('obf_limit', 'N/A')}")
        print(f"  - Expiry: {time_details['remaining_time']} ({time_details['status']})")
        print("-" * 40)
    else:
        print(f"[!] Key validation failed: {info}")
        return

    main_interactive(saved_key, info)


if __name__ == "__main__":
    main()
