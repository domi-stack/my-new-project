# Línea base de regresión · v2.2

## Por qué se rehace

La regla 0.1 del V2.1 compara contra "la lista de operaciones de partida". Esa lista no sirve:

- La versión de partida **no operaba nunca**: la máquina de estados marcaba la zona como consumida al perforar el 50% antes de que la sección de entrada la evaluara, así que el selector no encontraba nunca una zona válida.
- Tres correcciones posteriores cambian decisiones **a propósito**: la detección de barridos del extremo de sesión (que nunca podía disparar), el filtro de holgura (que vetaba casi todo al tratar los extremos de sesión como pared) y el disparo de entrada (que estaba restringido al 50% exacto en lugar de a la banda elegida).

No existe línea base válida anterior a la v2.2. Esta carpeta la establece.

## Cómo generarla

Esto requiere TradingView y hay que hacerlo a mano: el entorno donde se escribió el script no ejecuta Pine.

1. Cargar `pine/MGC_FVG_ORB.pine` en un gráfico de **MGC1!** en 5 minutos.
2. Fijar estos inputs, que son la combinación de referencia:

| Grupo | Input | Valor |
|---|---|---|
| Ventana de operativa | Modo horario | `Ventana NY` |
| Solo alta probabilidad | Operar solo zonas ALTA | no |
| Disparadores nuevos | Operar Silver Bullet | no |
| Disparadores nuevos | Operar falso rompimiento asiático | no |
| Filtros | Veto por ADR agotado | no |
| Fuerza de zona | Fuerza mínima para operar | 0 |

Todo lo demás, en su valor por defecto.

3. En el Strategy Tester, pestaña **List of Trades**, exportar a CSV.
4. Guardar como `backtests/baseline-v2.2.csv` y subirlo al repo.
5. Anotar abajo la fecha, el rango de datos y el número de operaciones.

## Cómo se usa

Cualquier fase futura cuya especificación diga "regresión idéntica" se compara contra este CSV, no contra una versión anterior del script.

Un cambio que altere la lista **no es automáticamente un error**: tiene que ser un cambio que la especificación pidiera a propósito. Lo que delata un fallo es una lista distinta cuando la especificación decía que no debía cambiar.

## Registro de la línea base

Rellenar al generarla:

```
Fecha de generación :
Instrumento         : MGC1!
Temporalidad        : 5m
Rango de datos      :
Nº de operaciones   :
Commit              : (git rev-parse --short HEAD)
Etiqueta            : baseline-v2.2
```

## Qué más entregar en la misma pasada

Además del CSV, dos cosas que deciden los siguientes pasos:

1. **Captura de la tabla de diagnóstico**, con las filas de vetos (`bloquea` y `EXCLUSIVO`) y la fila `Stop med/p80`. El contador exclusivo dice cuántas operaciones ganarías relajando un filtro y nada más; la fila de stops dice si el techo de 15 puntos es el cuello de botella real. Si la distribución de stops está por encima de 15, ningún ajuste de filtros lo cambia.
2. **Pine Logs de 3 días** con `Exportar zonas a Pine Logs` activado, para la prueba de paridad. Ver `paridad/README.md`.
