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
  S,tNace,id,marco,dir,top,bot,mid,estado,tApertura
        zona ya viva al abrir el rango. La PRIMERA fecha es la de nacimiento,
        que es la clave de emparejamiento; la última es la apertura del rango.
  E,fecha,id,estado_ant,estado_nuevo,dir_ant,dir_nuevo   cambio de estado
  P,fecha,id                                   zona retirada por purga FIFO
  D,fecha,id,disparador,dir,entrada,stop,stop_pts,objetivo   disparo

Z y S se tratan igual: las dos dan de alta una zona. S existe porque el rango de
exportación recorta los logs, y sin un inventario de las zonas que ya estaban
vivas al abrirlo, el comparador las contaría como "solo en Python".

El mismo formato se espera del lado de Python para las filas Z/S y E.

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
# Tolerancia de la HORA de un cambio de estado. En el marco del gráfico el
# cambio tiene que caer en la misma vela: cero margen. En marcos superiores se
# admite una vela de 5m, porque el momento en que la implementación "ve" la
# vela superior cerrada puede diferir en un paso.
TOL_CAMBIO_5M = 0
TOL_CAMBIO_HTF = 5
UMBRAL_EMPAREJADAS = 0.95


@dataclass
class Zona:
    fecha: datetime   # nacimiento, tanto en Z como en S
    zid: str
    marco: str
    direccion: int
    top: float
    bot: float
    mid: float
    # (fecha, estado_ant, estado_nuevo, dir_ant, dir_nuevo)
    estados: list[tuple[datetime, int, int, int, int]] = field(default_factory=list)

    # Solo en zonas que llegan por S: estado declarado al abrir el rango, y la
    # hora de esa apertura. Sirve para cotejar el estado de arranque.
    estado_s: int | None = None
    t_apertura: datetime | None = None
    # Instante en que la zona salió de la cola FIFO, si salió.
    t_purga: datetime | None = None

    @property
    def es_htf(self) -> bool:
        return self.marco.upper() not in ("5M", "5")

    def clave(self) -> tuple:
        return (self.marco, self.direccion)


def estado_en(z: Zona, t: datetime) -> int:
    """Estado de una zona en el instante t, replicando sus cambios hasta ahí.

    Una zona nace virgen (0); cada cambio registrado la mueve. Lo que importa es
    el último cambio con fecha menor o igual a t.
    """
    est = 0
    for fecha, _ant, nuevo, _da, _dn in sorted(z.estados):
        if fecha <= t:
            est = nuevo
        else:
            break
    return est


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
                if k < len(fila) and fila[k] in ("Z", "S", "E", "P", "D"):
                    tipo, off = fila[k], k
                    break
            if tipo is None:
                continue
            campos = fila[off:]
            try:
                # Z y S dan de alta una zona; si llegan las dos para el mismo
                # id, gana la primera y la segunda no sobrescribe el historial.
                if tipo in ("Z", "S") and len(campos) >= 8:
                    z = Zona(
                        fecha=_parse_fecha(campos[1]),
                        zid=campos[2],
                        marco=campos[3],
                        direccion=int(campos[4]),
                        top=float(campos[5]),
                        bot=float(campos[6]),
                        mid=float(campos[7]),
                    )
                    if tipo == "S":
                        # Estado declarado al abrir el rango y hora de apertura.
                        z.estado_s = int(campos[8]) if len(campos) > 8 else None
                        if len(campos) > 9:
                            z.t_apertura = _parse_fecha(campos[9])
                    if z.zid not in zonas:
                        zonas[z.zid] = z
                    elif tipo == "S":
                        # Si ya se vio por Z, S solo aporta el estado de arranque.
                        zonas[z.zid].estado_s = z.estado_s
                        zonas[z.zid].t_apertura = z.t_apertura
                elif tipo == "E" and len(campos) >= 5:
                    zid = campos[2]
                    if zid in zonas:
                        # dir_ant/dir_nuevo pueden faltar en registros antiguos
                        da = int(campos[5]) if len(campos) > 5 else 0
                        dn = int(campos[6]) if len(campos) > 6 else 0
                        zonas[zid].estados.append(
                            (_parse_fecha(campos[1]), int(campos[3]), int(campos[4]), da, dn)
                        )
                elif tipo == "P" and len(campos) >= 3:
                    zid = campos[2]
                    if zid in zonas:
                        zonas[zid].t_purga = _parse_fecha(campos[1])
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

    # Discrepancias de estado entre zonas que sí se emparejaron. Se compara la
    # secuencia completa: estado anterior y nuevo, dirección anterior y nueva, y
    # la HORA del cambio con tolerancia según el marco.
    discrepan: list[tuple[Zona, str]] = []
    for zp, zq in pares:
        tol = TOL_CAMBIO_HTF if zp.es_htf else TOL_CAMBIO_5M
        # Solo se cotejan los cambios DENTRO de la ventana observada. Lo que
        # pasó antes ya lo resume el estado de arranque, y si un lado emitiera
        # registros previos y el otro no, las secuencias no cuadrarían nunca por
        # una razón que no tiene nada que ver con la lógica.
        desde = zp.t_apertura
        sp = [e for e in sorted(zp.estados) if desde is None or e[0] >= desde]
        sq = [e for e in sorted(zq.estados) if desde is None or e[0] >= desde]
        if len(sp) != len(sq):
            discrepan.append((zp, f"nº de cambios: pine={len(sp)} python={len(sq)}"))
            continue
        for ep, eq in zip(sp, sq):
            dmin = abs((ep[0] - eq[0]).total_seconds()) / 60.0
            if dmin > tol:
                discrepan.append((zp,
                    f"hora del cambio {ep[1]}->{ep[2]}: pine={ep[0]:%H:%M} "
                    f"python={eq[0]:%H:%M} (desfase {dmin:.0f} min, tolerancia {tol})"))
                break
            if (ep[1], ep[2]) != (eq[1], eq[2]):
                discrepan.append((zp,
                    f"estado: pine {ep[1]}->{ep[2]} vs python {eq[1]}->{eq[2]}"))
                break
            if (ep[3], ep[4]) != (eq[3], eq[4]):
                discrepan.append((zp,
                    f"dirección: pine {ep[3]}->{ep[4]} vs python {eq[3]}->{eq[4]}"))
                break

    # Estado de arranque: para las zonas que Pine declaró por S, comprobar que
    # Python estaba en el mismo estado en esa misma vela. Si no coinciden, las
    # dos implementaciones llegaron al rango con historias distintas y comparar
    # lo que pasa dentro del rango no significa nada.
    arranque: list[tuple[Zona, int, int]] = []
    for zp, zq in pares:
        if zp.estado_s is None or zp.t_apertura is None:
            continue
        est_py = estado_en(zq, zp.t_apertura)
        if est_py != zp.estado_s:
            arranque.append((zp, zp.estado_s, est_py))

    print(f"\ndiscrepancias de estado al abrir el rango: {len(arranque)}")
    for zp, ep, eq in arranque[:15]:
        print(f"   {zp.fecha:%Y-%m-%d %H:%M} {zp.marco:>3}: al abrir el rango "
              f"pine={ep} python={eq}")

    # Purga: si un lado retiró la zona de su cola FIFO, el otro no debería
    # seguir informando cambios de esa zona después. Que lo haga significa que
    # las colas no están alineadas, y entonces las zonas que un lado olvida y el
    # otro no falsean toda la comparación. Se reporta aparte de las
    # discrepancias de estado porque la causa y el arreglo son distintos.
    purga: list[tuple[Zona, str]] = []
    for zp, zq in pares:
        for a, b, quien in ((zp, zq, "pine"), (zq, zp, "python")):
            if a.t_purga is None:
                continue
            posteriores = [e for e in b.estados if e[0] > a.t_purga]
            if posteriores:
                otro = "python" if quien == "pine" else "pine"
                purga.append((zp,
                    f"purgada en {quien} a las {a.t_purga:%Y-%m-%d %H:%M} pero "
                    f"{otro} informa {len(posteriores)} cambio(s) después "
                    f"(el primero a las {min(e[0] for e in posteriores):%H:%M})"))

    print(f"\ndiscrepancias de purga: {len(purga)}")
    for zp, motivo in purga[:15]:
        print(f"   {zp.fecha:%Y-%m-%d %H:%M} {zp.marco:>3}: {motivo}")

    print(f"\ndiscrepancias de estado en zonas emparejadas: {len(discrepan)}")
    for zp, motivo in discrepan[:15]:
        print(f"   {zp.fecha:%Y-%m-%d %H:%M} {zp.marco:>3}: {motivo}")

    ok = pct >= UMBRAL_EMPAREJADAS and not discrepan and not arranque and not purga
    print("\n" + ("PARIDAD OK: se puede seguir con la calibración"
                  if ok else
                  "PARIDAD INSUFICIENTE: NO seguir con la calibración"))
    if not ok:
        if pct < UMBRAL_EMPAREJADAS:
            print(f"  emparejadas {pct:.1%}, por debajo del {UMBRAL_EMPAREJADAS:.0%} exigido")
        if discrepan:
            print(f"  {len(discrepan)} discrepancias de estado sin explicar")
        if arranque:
            print(f"  {len(arranque)} zonas llegaron al rango en estados distintos")
        if purga:
            print(f"  {len(purga)} zonas con las colas FIFO desalineadas")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
