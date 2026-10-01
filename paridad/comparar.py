#!/usr/bin/env python3
"""Compara las zonas que detecta Pine con las que detecta la reimplementación
en Python, que es la prueba de paridad obligatoria de V2.1 §1.2.

Sin esta prueba la calibración no vale: una tabla de cubos construida sobre
zonas distintas de las que dibuja el script no dice nada sobre el script.

Entradas
--------
  paridad/pine_logs_YYYYMMDD.csv   panel de Pine Logs copiado tal cual
  paridad/python_zonas_YYYYMMDD.csv  salida del detector en Python

Formato de los registros de Pine
--------------------------------
  Z,fecha,id,marco,dir,top,bot,mid,estado      alta de zona
  E,fecha,id,estado_ant,estado_nuevo,dir_ant,dir_nuevo   cambio de estado
  D,fecha,id,disparador,dir,entrada,stop,stop_pts,objetivo   disparo

El mismo formato se espera del lado de Python para las filas Z y E.

Criterio para seguir con la calibración (V2.1 §1.2):
  - al menos el 95 % de zonas emparejadas
  - ninguna discrepancia de estado sin explicar

Uso
---
  python3 paridad/comparar.py paridad/pine_logs_20260915.csv \
                              paridad/python_zonas_20260915.csv
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Tolerancia de precio al emparejar, en USD. V2.1 §1.2 fija 0,3.
TOL_PRECIO = 0.3
# Tolerancia de nacimiento, en minutos. Una zona de 4H puede registrarse con
# algún desfase según cuándo cierre su vela en cada implementación.
TOL_MINUTOS = 5
UMBRAL_EMPAREJADAS = 0.95


@dataclass
class Zona:
    fecha: datetime
    zid: str
    marco: str
    direccion: int
    top: float
    bot: float
    mid: float
    estados: list[tuple[datetime, int, int]] = field(default_factory=list)

    def clave(self) -> tuple:
        return (self.marco, self.direccion)


def _parse_fecha(txt: str) -> datetime:
    return datetime.strptime(txt.strip(), "%Y-%m-%d %H:%M")


def leer(path: Path) -> dict[str, Zona]:
    """Lee un CSV de registros y devuelve las zonas indexadas por su id."""
    zonas: dict[str, Zona] = {}
    with open(path, newline="") as fh:
        for fila in csv.reader(fh):
            fila = [c.strip() for c in fila if c.strip() != ""]
            if not fila:
                continue
            # El panel de Pine Logs puede prefijar la hora del navegador; se
            # busca el marcador de tipo en las dos primeras columnas.
            tipo = None
            off = 0
            for k in (0, 1):
                if k < len(fila) and fila[k] in ("Z", "E", "D"):
                    tipo, off = fila[k], k
                    break
            if tipo is None:
                continue
            campos = fila[off:]
            try:
                if tipo == "Z" and len(campos) >= 8:
                    z = Zona(
                        fecha=_parse_fecha(campos[1]),
                        zid=campos[2],
                        marco=campos[3],
                        direccion=int(campos[4]),
                        top=float(campos[5]),
                        bot=float(campos[6]),
                        mid=float(campos[7]),
                    )
                    zonas[z.zid] = z
                elif tipo == "E" and len(campos) >= 5:
                    zid = campos[2]
                    if zid in zonas:
                        zonas[zid].estados.append(
                            (_parse_fecha(campos[1]), int(campos[3]), int(campos[4]))
                        )
            except (ValueError, IndexError):
                print(f"  aviso: fila ilegible y omitida: {fila}", file=sys.stderr)
    return zonas


def emparejar(pine: dict[str, Zona], py: dict[str, Zona]):
    """Empareja por nacimiento, marco y dirección, con tolerancia de precio."""
    libres = list(py.values())
    pares: list[tuple[Zona, Zona]] = []
    solo_pine: list[Zona] = []

    for zp in sorted(pine.values(), key=lambda z: z.fecha):
        mejor = None
        mejor_d = None
        for zq in libres:
            if zp.clave() != zq.clave():
                continue
            dmin = abs((zp.fecha - zq.fecha).total_seconds()) / 60.0
            if dmin > TOL_MINUTOS:
                continue
            dprecio = max(abs(zp.top - zq.top), abs(zp.bot - zq.bot))
            if dprecio > TOL_PRECIO:
                continue
            if mejor_d is None or dprecio < mejor_d:
                mejor, mejor_d = zq, dprecio
        if mejor is None:
            solo_pine.append(zp)
        else:
            pares.append((zp, mejor))
            libres.remove(mejor)
    return pares, solo_pine, libres


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(2)

    p_pine, p_py = Path(sys.argv[1]), Path(sys.argv[2])
    for p in (p_pine, p_py):
        if not p.exists():
            raise SystemExit(f"no existe: {p}")

    pine = leer(p_pine)
    py = leer(p_py)
    print(f"zonas en Pine   : {len(pine)}")
    print(f"zonas en Python : {len(py)}")
    if not pine and not py:
        raise SystemExit("ningún registro legible en ninguno de los dos ficheros")

    pares, solo_pine, solo_py = emparejar(pine, py)
    total = len(pares) + len(solo_pine) + len(solo_py)
    pct = len(pares) / total if total else 0.0

    print(f"\nemparejadas     : {len(pares)}  ({pct:.1%} del total)")
    print(f"solo en Pine    : {len(solo_pine)}")
    print(f"solo en Python  : {len(solo_py)}")

    if solo_pine:
        print("\n-- zonas que solo ve Pine (hasta 15)")
        for z in solo_pine[:15]:
            print(f"   {z.fecha:%Y-%m-%d %H:%M}  {z.marco:>3} dir={z.direccion:+d}"
                  f"  {z.bot:.2f}-{z.top:.2f}")
    if solo_py:
        print("\n-- zonas que solo ve Python (hasta 15)")
        for z in solo_py[:15]:
            print(f"   {z.fecha:%Y-%m-%d %H:%M}  {z.marco:>3} dir={z.direccion:+d}"
                  f"  {z.bot:.2f}-{z.top:.2f}")

    # Discrepancias de estado entre zonas que sí se emparejaron.
    discrepan = []
    for zp, zq in pares:
        sp = [(e[1], e[2]) for e in sorted(zp.estados)]
        sq = [(e[1], e[2]) for e in sorted(zq.estados)]
        if sp != sq:
            discrepan.append((zp, sp, sq))

    print(f"\ndiscrepancias de estado en zonas emparejadas: {len(discrepan)}")
    for zp, sp, sq in discrepan[:15]:
        print(f"   {zp.fecha:%Y-%m-%d %H:%M} {zp.marco:>3}: pine={sp} python={sq}")

    ok = pct >= UMBRAL_EMPAREJADAS and not discrepan
    print("\n" + ("PARIDAD OK: se puede seguir con la calibración"
                  if ok else
                  "PARIDAD INSUFICIENTE: NO seguir con la calibración"))
    if not ok:
        if pct < UMBRAL_EMPAREJADAS:
            print(f"  emparejadas {pct:.1%}, por debajo del {UMBRAL_EMPAREJADAS:.0%} exigido")
        if discrepan:
            print(f"  {len(discrepan)} discrepancias de estado sin explicar")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
