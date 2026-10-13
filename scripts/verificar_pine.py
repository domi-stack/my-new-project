#!/usr/bin/env python3
"""Comprobaciones estaticas sobre un .pine. Sin ejecutar Pine: solo texto."""
import re, sys, collections

path = sys.argv[1]
raw = open(path, encoding="utf-8").read().split("\n")

OPEN = "([{"
CLOSE = ")]}"
PAIR = {")": "(", "]": "[", "}": "{"}


def strip(line):
    """Quita comentarios y literales de cadena, respetando que // dentro de
    una cadena no abre comentario. Las cadenas se sustituyen por '_', no por
    espacios: con espacios una linea que termina en cadena parece terminar en
    el operador que la precede y el detector de continuaciones se vuelve loco."""
    out = []
    i = 0
    q = None
    while i < len(line):
        c = line[i]
        if q:
            if c == "\\":
                out.append("__")
                i += 2
                continue
            if c == q:
                q = None
            out.append("_")
            i += 1
            continue
        if c in "\"'":
            q = c
            out.append("_")
            i += 1
            continue
        if c == "/" and i + 1 < len(line) and line[i + 1] == "/":
            break
        out.append(c)
        i += 1
    return "".join(out)


code = [strip(l) for l in raw]

# ---------------------------------------------------------------- 1. parentesis
print("== 1. parentesis / corchetes ==")
stack = []
errs = 0
for n, l in enumerate(code, 1):
    for c in l:
        if c in OPEN:
            stack.append((c, n))
        elif c in CLOSE:
            if not stack:
                print(f"  L{n}: cierra '{c}' sin abrir")
                errs += 1
            elif stack[-1][0] != PAIR[c]:
                print(f"  L{n}: cierra '{c}' pero lo abierto fue "
                      f"'{stack[-1][0]}' en L{stack[-1][1]}")
                errs += 1
                stack.pop()
            else:
                stack.pop()
for c, n in stack:
    print(f"  L{n}: '{c}' nunca se cierra")
    errs += 1
print(f"  {'OK' if errs == 0 else str(errs) + ' FALLOS'}")

# ------------------------------------------- 2. indentacion de continuaciones
print("\n== 2. continuaciones con indentacion multiplo de 4 ==")
def indent(n):
    """Indentacion real, medida sobre la linea cruda: la version despojada
    convierte las comillas en espacios y falsea la cuenta."""
    r = raw[n - 1]
    return len(r) - len(r.lstrip(" "))


depth = 0
errs2 = 0
for n, l in enumerate(code, 1):
    cont = depth > 0
    if cont and l.strip():
        ind = indent(n)
        if ind > 0 and ind % 4 == 0:
            print(f"  L{n}: indentacion {ind} dentro de parentesis: "
                  f"{raw[n-1].strip()[:70]}")
            errs2 += 1
    for c in l:
        if c in OPEN:
            depth += 1
        elif c in CLOSE:
            depth -= 1
    # continuacion por operador final (fuera de parentesis). '=>' no es un
    # operador de continuacion: abre un cuerpo de funcion o un caso de switch.
    s = l.rstrip()
    if depth == 0 and not s.endswith("=>") and \
       re.search(r"(?:\b(?:and|or|not)|[+\-*/%?:,=<>]=?)$", s):
        nxt = code[n] if n < len(code) else ""
        if nxt.strip():
            ind = indent(n + 1)
            if ind > 0 and ind % 4 == 0:
                print(f"  L{n+1}: indentacion {ind} tras operador en L{n}"
                      f": {raw[n].strip()[:70]}")
                errs2 += 1
print(f"  {'OK' if errs2 == 0 else str(errs2) + ' FALLOS'}")

# ------------------------------------------------ 3. declaracion antes de uso
print("\n== 3. declaracion antes de uso (ambito global) ==")
KW = set("""var varip float int bool string color line label box table array
matrix map series simple input const if else for while switch to by and or not
na true false and import export type method enum strategy indicator plot
plotshape plotchar plotarrow hline fill bgcolor barcolor alertcondition alert
request ta math str color_ array_ nz fixnan time timenow timeframe syminfo
barstate session dayofweek year month dayofmonth hour minute second high low
open close volume hl2 hlc3 ohlc4 hlcc4 bar_index last_bar_index
last_bar_time format location size shape style display scale extend xloc yloc
text position color label_style line_style box_style order dividends earnings
splits currency adjustment backadjustment settlement_as_close chart
syminfo_ runtime log str_ max_bars_back""".split())

decl = {}          # nombre -> primera linea de declaracion global
for n, l in enumerate(code, 1):
    if l[:1] == " " or not l.strip():
        continue
    s = l.strip()
    # 'for k = 0 to 3' declara una variable de bucle, no una global: sin este
    # descarte el nombre del contador se toma por una global declarada en la
    # ultima linea donde aparece un bucle, y todo uso anterior sale marcado.
    if re.match(r"^(?:for|if|while|else|switch)\b", s):
        continue
    # 'const' y 'var' pueden ir ANTES del tipo: 'const int N = 1' tiene dos
    # tokens antes del nombre y la version anterior solo admitia uno, asi que
    # tomaba la constante por no declarada.
    m = re.match(r"^(?:(?:const|var|varip)\s+)?(?:[A-Za-z_][\w<>.]*\s+)?"
                 r"([A-Za-z_]\w*)\s*(?:=(?!=)|:=)", s)
    if m:
        decl.setdefault(m.group(1), n)
    m = re.match(r"^([A-Za-z_]\w*)\s*\(.*\)\s*=>", s)
    if m:
        decl.setdefault(m.group(1), n)
    m = re.match(r"^(?:type|enum)\s+([A-Za-z_]\w*)", s)
    if m:
        decl.setdefault(m.group(1), n)
    # tuplas: [a, b] = ...
    m = re.match(r"^\[([^\]]+)\]\s*=(?!=)", s)
    if m:
        for part in m.group(1).split(","):
            p = part.strip().split()[-1]
            decl.setdefault(p, n)

errs3 = 0
for n, l in enumerate(code, 1):
    # (?<![\w.]) descarta lo que va tras un punto: en 'ta.atr' el trozo 'atr'
    # no es la variable global atr, y sin este descarte 'float atr = ...
    # ta.atr(...)' se denuncia a si misma.
    for name in set(re.findall(r"(?<![\w.])([A-Za-z_]\w*)\b", l)):
        if name in KW or name not in decl:
            continue
        if decl[name] > n:
            # ignorar la propia linea de declaracion de un bloque multilinea
            print(f"  L{n}: '{name}' se usa antes de declararse en L{decl[name]}")
            errs3 += 1
print(f"  {'OK' if errs3 == 0 else str(errs3) + ' AVISOS (verificar a mano)'}")

# --------------------------------- 4. funcion que asigna a variable global
print("\n== 4. funciones que asignan a una variable global ==")
globals_ = set(decl)
errs4 = 0
i = 0
while i < len(code):
    s = code[i].strip()
    m = re.match(r"^([A-Za-z_]\w*)\s*\(([^)]*)\)\s*=>", s) if code[i][:1] != " " else None
    if m:
        fname, params = m.group(1), m.group(2)
        pnames = {p.strip().split()[-1] for p in params.split(",") if p.strip()}
        locals_ = set(pnames)
        j = i + 1
        while j < len(code) and (not code[j].strip() or code[j][:1] == " "):
            b = code[j].strip()
            dm = re.match(r"^(?:var(?:ip)?\s+)?(?:[A-Za-z_][\w<>.]*\s+)?"
                          r"([A-Za-z_]\w*)\s*=(?!=)", b)
            if dm:
                locals_.add(dm.group(1))
            am = re.match(r"^([A-Za-z_]\w*)\s*:=", b)
            if am and am.group(1) not in locals_ and am.group(1) in globals_:
                print(f"  L{j+1}: {fname}() asigna a '{am.group(1)}' "
                      f"(global, declarada en L{decl[am.group(1)]})")
                errs4 += 1
            j += 1
        i = j
        continue
    i += 1
print(f"  {'OK' if errs4 == 0 else str(errs4) + ' FALLOS'}")

# ------------------------------------- 5. identificadores del proyecto sin declarar
#  Pine tiene cientos de builtins, asi que comprobar TODO nombre daria ruido.
#  Pero los nombres que siguen las convenciones de este proyecto (f_, i_, w_,
#  V_, G_, N_, s6, F_) son por definicion locales: si se usan y no se declaran,
#  Pine lo rechaza. Es el fallo que la comprobacion 3 no puede ver, porque esa
#  solo mira el ORDEN de los que si estan declarados.
print("\n== 5. identificadores locales usados y nunca declarados ==")
#  La comprobacion 3 solo indexa declaraciones de ambito global, porque es de
#  ORDEN y el orden solo importa ahi. Esta es de EXISTENCIA, asi que tiene que
#  mirar tambien las declaraciones dentro de bloques y de funciones.
declAny = set(decl)
for l in code:
    s = l.strip()
    if re.match(r"^(?:for|if|while|else|switch)\b", s):
        continue
    m = re.match(r"^(?:(?:const|var|varip)\s+)?(?:[A-Za-z_][\w<>.]*\s+)?"
                 r"([A-Za-z_]\w*)\s*(?:=(?!=)|:=)", s)
    if m:
        declAny.add(m.group(1))
    m = re.match(r"^([A-Za-z_]\w*)\s*\(.*\)\s*=>", s)
    if m:
        declAny.add(m.group(1))
    m = re.match(r"^\[([^\]]+)\]\s*=(?!=)", s)
    if m:
        for part in m.group(1).split(","):
            declAny.add(part.strip().split()[-1])
CONV = re.compile(r"^(f_|i_|w\d*_|V_|G_|N_|S6_|F_|s6[A-Z])")
usados = {}
for n, l in enumerate(code, 1):
    for name in set(re.findall(r"(?<![\w.])([A-Za-z_]\w*)\b", l)):
        if CONV.match(name) and name not in declAny:
            usados.setdefault(name, n)
errs5 = 0
for name, n in sorted(usados.items(), key=lambda kv: kv[1]):
    print(f"  L{n}: '{name}' no se declara en ninguna parte")
    errs5 += 1
print(f"  {'OK' if errs5 == 0 else str(errs5) + ' FALLOS'}")
