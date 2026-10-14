# Línea base de regresión · v2.7

> **La v2.2 queda invalidada.** La v2.7 §1b corrige un bug en PDH/PDL que **mueve la lista de operaciones**: se pedían a la vela diaria del exchange, cuyo corte no es el día de trading del script. Lo leen los barridos del día anterior, la confluencia de nivel del score y el filtro de holgura. El detalle está en `docs/TRASPASO_MGC.md` §5b.
>
> Lo que hay que generar es por tanto **`backtests/baseline-v2.7.csv`**. Si llega a existir un `baseline-v2.2.csv`, sirve solo para medir la diferencia, y esa diferencia tiene que explicarse por esas tres reglas y por nada más.
>
> Todo lo demás de la v2.7 es dibujo y no puede mover ni una operación: HOD/LOD, relleno de zonas, rótulos, tope de cuatro niveles, filas de tabla y la retirada del aviso de spot.

## ⚠️ Desde la v5.4 los defectos YA NO son la línea base

Hasta la v5.3, cargar el script y no tocar nada reproducía la línea base. **Eso ha dejado de ser cierto**: la v5.4 enciende las seis fuentes nuevas y pone el cupo diario a 0. Antes de generar o comparar nada hay que fijar a mano:

| Input | Valor |
|---|---|
| `Máximo de operaciones al día` | **1** |
| `Activar S1` … `Activar S6` (los seis) | **false** |
| `Modo horario` | `Ventana NY` |
| Los cuatro frenos y el enfriamiento | 0 |
| `Operar solo zonas ALTA` | no |
| `Operar Silver Bullet` / `falso rompimiento asiático` | no |
| `Veto por ADR agotado` | no |
| `Fuerza mínima para operar` | 0 |
| `Vetar entradas en volatilidad comprimida` | no |

Con menos que eso, lo que midas no es comparable con nada.

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

3. **Decidir qué hacer con el cambio de contrato.** `MGC1!` es un continuo: al vencer un contrato, la serie salta al siguiente y ese salto de precio no es un movimiento del mercado. Sin tratarlo, un hueco de roll puede crear un FVG que no existió, disparar un stop que nadie tocó o contaminar el ADR. Hay dos formas válidas y hay que usar una:

   - **Ajuste por cambio de contrato activado**: en los ajustes del símbolo del gráfico, activar *Adjust for contract changes* (o *Continuous contract*, según la versión). La serie queda empalmada y los huecos de roll desaparecen.
   - **Sin ajuste, excluyendo las sesiones de roll**: listar las fechas de vencimiento del periodo y descartar del CSV las operaciones de esas sesiones. El oro en CME tiene contratos activos en febrero, abril, junio, agosto, octubre y diciembre, y el roll práctico ocurre a finales del mes anterior al vencimiento.

   Anotar abajo cuál se usó. Mezclar las dos entre pasadas invalida la comparación.

4. En el Strategy Tester, pestaña **List of Trades**, exportar a CSV.
5. Guardar como `backtests/baseline-v2.7.csv` y subirlo al repo.
6. Anotar abajo la fecha, el rango de datos y el número de operaciones.

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
Etiqueta            : baseline-v2.7
Tratamiento del roll: [ ] ajuste por cambio de contrato activado
                      [ ] sin ajuste, sesiones de roll excluidas (listar fechas)
```

> El tag `baseline-v2.2` existe en local pero **no está en el remoto**: el proxy de git del entorno corta la conexión al enviar tags, probado con tag anotado y ligero. El commit de referencia es `65a2869`. Para etiquetarlo: `git tag baseline-v2.2 65a2869 && git push origin baseline-v2.2`.

## Qué más entregar en la misma pasada

Además del CSV, dos cosas que deciden los siguientes pasos:

1. **Captura de la tabla de diagnóstico**, con las filas de vetos (`bloquea` y `EXCLUSIVO`) y la fila `Stop med/p80`. El contador exclusivo dice cuántas operaciones ganarías relajando un filtro y nada más; la fila de stops dice si el techo de 15 puntos es el cuello de botella real. Si la distribución de stops está por encima de 15, ningún ajuste de filtros lo cambia.
2. **Pine Logs de 3 días** con `Exportar zonas a Pine Logs` activado, para la prueba de paridad. Ver `paridad/README.md`.
