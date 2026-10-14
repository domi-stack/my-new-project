# Las fuentes de señal añadidas · S1 a S8

Fichero: `pine/MGC_FVG_ORB.pine`. **Es el único `.pine` del proyecto.**

## S7 · Order block (encargo 3)

La última vela contraria antes de un desplazamiento que rompe estructura. Dos pasos, y el primero **no es un setup sino un inventario**: cuando hay ruptura se busca hacia atrás la última vela contraria y se archiva su rango; después, al volver el precio, se emite el candidato.

| Input | Defecto | Para qué |
|---|---|---|
| Velas máximas entre el OB y la ruptura | 5 | Si la ruptura llega diez velas después, esa vela ya no es «la última antes del desplazamiento» |
| Desplazamiento mínimo | 1,0 ATR | Sin un mínimo, cualquier ruptura marginal deja un OB detrás |
| Altura mínima / máxima de la vela | 0,3 / 1,5 ATR | Por debajo es ruido; por encima el stop no cabe en el techo de puntos |
| Solo OB nunca mitigados | sí | Un OB al que el precio ya volvió ha gastado lo que tuviera dentro |
| R fijo del objetivo | 2,0 | |

**No repinta** porque la detección mira solo hacia atrás y la zona se fija en la vela de la ruptura.

### El solape con el FVG, y por qué el contador de conflictos no servía

Un OB y el FVG del mismo desplazamiento señalan casi siempre el mismo precio **y van en la misma dirección**. El contador de conflictos no los vería nunca: ese cuenta *desacuerdos*, y aquí hay **acuerdo duplicado**, que es un problema distinto — dos fuentes cobrándose la misma señal e inflando la muestra de las dos.

Si un FVG vivo solapa **más del 50 %** con el OB candidato, S7 no emite, y se cuenta en la fila `S7 descartados por solape`. Manda el FVG porque su nivel de entrada, el 50 %, es más preciso que «dentro de la banda».

**Cómo se mide ese 50 %, que es la parte no obvia:** contra la zona **menor** de las dos. Es lo que responde a «¿están señalando el mismo sitio?». Un FVG diminuto dentro de un OB grande solapa el 100 % de sí mismo y ahí manda el FVG; medirlo contra el OB habría dejado pasar justo ese caso.

---

## S8 · OTE · Optimal Trade Entry (encargo 3)

> **Esta es la hipótesis más débil de las ocho.**
>
> «El bloque 70,5-79 % no tiene ninguna evidencia publicada que lo distinga de cualquier otro porcentaje de retroceso. Es una convención de una comunidad, no un resultado medido. Se implementa para poder **medirlo** contra las otras fuentes en la tabla de grupos, no porque se sepa que funciona. Si tras 40 operaciones su esperanza no supera a la del FVG, no hay motivo para mantenerlo.»

Retroceso al bloque 70,5-79 % del último tramo impulsivo, tomado de `swHigh`/`swLow`. **Los dos porcentajes son inputs**, y esa es la consecuencia práctica del párrafo de arriba: poder moverlos es lo único que permite comprobar si ese bloque tiene algo que otro no tenga.

El tramo sale de pivotes **ya confirmados**, con su retardo inherente. Eso es a la vez la razón de que no repinte y de que el tramo se conozca algo tarde: son la misma cosa, y no se puede tener una sin la otra.

Stop más allá del **origen** del tramo, que es lo que invalida la lectura: si el precio vuelve ahí, el tramo no era impulsivo. Objetivo R fijo a 2,0 o el extremo del tramo, configurable. Caducidad de 24 velas, porque un retroceso que llega tres horas después no es el mismo contexto.

---

## Lo que NO se añadió, y la evidencia que lo impide

Esto está aquí para que nadie lo reintroduzca por tener la idea otra vez.

### ORB · ruptura del rango de apertura · MEDIDO Y DESCARTADO

Sobre **133 sesiones** de XAUUSD 5m:

| Métrica | Valor |
|---|---|
| Esperanza | **−0,028R** |
| Profit factor | **0,84** |
| Win rate | 51,1 % |
| Win rate de equilibrio | 53,1 % |

Quince variantes probadas (objetivo de 1,0× a 3,0×, con y sin filtro direccional) y **ninguna** supera el umbral de +0,10R. La única marginal —SELL, +0,080R— se explica por la tendencia del periodo: el oro cayó un **16,3 %** en la muestra, así que un sistema que solo vende en una muestra bajista gana por el sesgo de la muestra, no por la señal.

**No se reintroduce.** Y nótese el detalle que importa: el win rate está *por debajo* del de equilibrio. No es que falte ajuste de objetivo; es que la señal no tiene dirección.

S1 es el **espejo** de esto, y por eso es una hipótesis razonable — pero sigue sin estar medida, y el espejo de una estrategia perdedora no es automáticamente ganadora: entre las dos se quedan la comisión, el slippage y todas las veces en que la ruptura no falla.

### DXY como filtro · instrumentado, no promovido

Está en el script como contexto de solo lectura, y desde el encargo 3 también como **medición**: `Operacion.dxyAlEntrar` se captura al entrar y el registro publica la esperanza desglosada por dirección del dólar.

**Promoverlo a filtro exige 40 operaciones en cada grupo y que la diferencia sea real.** Hasta entonces es una fila de tabla, no una regla.

---

## La consolidación de la v2.9

Un `strategy()` y un `indicator()` no pueden ser el mismo script: Pine admite una sola declaración. Así que «un solo Pine con todo» significaba necesariamente que el strategy se quedara con todo y el indicador desapareciera. Eso es lo que hace la v2.9.

**Lo que se trajo del indicador v5.2** (commits `v2.9-1` a `v2.9-5`):

| Qué | Dónde | Estado |
|---|---|---|
| Filtro de chop por percentil de ATR | Grupo `Filtro de chop`, bit `V_CHOP` de la máscara | Apagado |
| Marcadores de tres niveles · punto, rombo, flecha | Grupo `Visual` | Encendido (es dibujo) |
| Resultado escrito en la etiqueta al cerrar | Grupo `Visual` | Encendido (es dibujo) |
| Payload JSON de alerta | Grupo `Alertas` | Formato `Texto` por defecto |
| Desactivación por esperanza negativa | Grupo `Reparto de cupo` | Apagado |

Dos de ellas **funcionan mejor aquí que en el indicador**, y no por casualidad: en el indicador el resultado de un disparo era *simulado* contra TP1 y SL, mientras que aquí es el PnL real de una operación cerrada, con su comisión y su slippage dentro. Eso afecta a la anotación de la etiqueta y a la desactivación automática.

**Lo que NO se trajo, y por qué.** Esto importa más que la lista anterior, porque es donde un merge a lo bruto habría estropeado el script:

- **El score 0-100 del v5 y su reparto de pesos.** El strategy ya tiene su propio score de zona con otros pesos. Traer el del v5 significaría tener dos puntuaciones compitiendo, o elegir una. **Elegir una es una decisión de trading, no de refactor**, y no es mía: dímelo y la hago.
- **El sesgo de cinco votos y la alineación 4H/1H/15m del score.** Mismo caso: el strategy ya calcula `bias5`, `bias1h` y `bias4h` y ya tiene un término de alineación con el marco mayor, solo ponderado distinto.
- **Zonas de FVG en 15m.** No hace falta portar nada: el input `Marco intermedio` admite `15`. Cada `request.security` es un recurso limitado (6 de 40 usados) y habría sido gastar uno para algo que ya se puede pedir.
- **El panel único del v5.** El strategy ya tiene dos tablas (diagnóstico y modo limpio). Una tercera sería ruido, que es justo lo que la v2.7 vino a quitar.
- **El modo Minimal.** El modo limpio (`Operar solo zonas ALTA`) ya hace eso.
- **El gatillo de 1 minuto.** Explicado en §2: desde un gráfico de 5m no se puede ver la secuencia de velas de 1m.
- **La cola de setups abiertos (`abiertos`).** En un `strategy()` con `pyramiding = 0` solo hay una posición a la vez, y `ops` más el Strategy Tester ya llevan la cuenta.

El fichero retirado sigue en el historial de git: `git show 771110d:pine/MGC_v5_indicador.pine` lo recupera entero.

---

**Todo lo que sigue describe las cinco estrategias de la v2.8.**

**Todas apagadas por defecto.** Con la configuración de fábrica el script hace exactamente lo que hacía en la v2.7, y eso no es una promesa: es una propiedad del código, explicada en §7.

---

## 0. Lo primero: qué está validado y qué no

Esta tabla es la parte más importante del documento. Lo que no está aquí marcado como validado, no lo está.

| Fuente | Estado | Qué sabemos |
|---|---|---|
| **FVG + estructura** | Sin calibrar, pero es la referencia | Es el sistema original. La tabla de probabilidad por cubos de §1 de la V2.1 **no está hecha**, así que el filtro ALTA sigue forzado a off. Define la línea base de regresión. |
| **S1 · barrido** | **Hipótesis sin comprobar** | Viene de inferir que, si la ruptura del ORB tiene esperanza negativa, su fallo podría ser donde está la ventaja. **Es una inferencia, no un hecho.** El espejo de una estrategia perdedora no es automáticamente ganadora: entre las dos se quedan la comisión, el slippage y todas las veces en que la ruptura no falla. |
| **S2 · pullback a VWAP** | **Hipótesis sin comprobar** | Además, medible solo a medias con datos de spot: ver §6. |
| **S3 · fade de bandas** | **Hipótesis sin comprobar** | Igual que S2, y peor: la señal es la desviación típica de un VWAP aproximado. |
| **S4 · noticias** | **Hipótesis sin comprobar** | Y antes de encenderla hay que comprobar la norma de la prop firm: ver §5. |
| **S5 · sesgo horario** | **Hipótesis, y el script la mide** | «El oro sube en Asia y cae el resto del día» no está comprobado. Por defecto S5 **no aplica el enunciado: mide la deriva por hora en tus propios datos** y usa su signo. Si en tus datos no es cierto, el filtro no se lo inventa. |

---

## 1. S1 · Barrido de liquidez (falsa ruptura)

El precio pasa de un nivel de liquidez y la vela de 5m **cierra de vuelta dentro**. Entrada contra la ruptura al cierre de esa vela.

Niveles que cuentan: máximo y mínimo del día anterior, de Asia y de Londres (configurable). Los de Asia y Londres se toman **fijados al cerrar la sesión**: mientras la sesión está abierta su extremo se mueve, y un nivel que se mueve no es un nivel.

**Los tres filtros son lo que distingue un barrido de las dos cosas que se le parecen:**

| Input | Defecto | Qué descarta |
|---|---|---|
| Penetración mínima | 0,3 USD/oz | Un roce. Por debajo de esto no hubo barrido. |
| Penetración máxima | 4,0 USD/oz | Una ruptura **real**. Por encima no se opera aunque la vela cierre de vuelta dentro: eso ya no es «han cazado stops», es «el precio se ha ido y ha hecho un retroceso». |
| Cierres fuera admitidos | 1 | **Aceptación** del precio en el nivel nuevo. Si tres velas seguidas han cerrado al otro lado, el mercado ha aceptado ese precio y lo que viene después no es la vuelta de un barrido. |

Stop más allá de la mecha + margen (0,5 USD/oz). Ventana 08:00-11:30 ET, independiente del modo horario general. Máximo una operación por lado y día.

**Objetivo: tres modos, y el defecto es `R fijo` a 1,8R** (dentro del 1,5 a 2R que pide la especificación). Razón: es el único de los tres cuya esperanza se puede interpretar sin modelar además dónde estaba el VWAP en cada operación. `VWAP del día` no genera señal si el VWAP queda detrás de la entrada; la variante con reserva cae al R fijo en ese caso, lo que **mezcla dos objetivos distintos en el mismo grupo de medición**. Si la usas, sábelo.

---

## 2. S2 · Pullback a VWAP en día tendencial

Solo con el día clasificado como **TENDENCIA** (§4). Entrada en el retroceso que toca el VWAP, o la banda de 1σ, y cierra de vuelta al lado correcto.

### El criterio de pendiente

**`(VWAP − VWAP[N]) / ATR ≥ umbral`**, con N = 12 velas y umbral 0,25 por defecto.

Es un cociente, así que es **adimensional**: el mismo umbral vale en MGC y en XAUUSD y no depende del zoom ni de la escala del gráfico. Ese es el motivo de no medir un ángulo en grados: en Pine un ángulo depende de la escala de precio, y el mismo mercado da ángulos distintos en dos pantallas.

Lleva una guarda: si el VWAP se reinició hace menos de N velas, la pendiente estaría comparando dos sesiones distintas, así que se anula y S2 no opera.

### La ventana, y una advertencia

30 a 60 minutos tras la apertura de NY, **tal como lo especificaste**. Es una ventana estrecha: el retroceso tiene que ocurrir justo ahí, y la mayoría de días no ocurrirá. Si lo que querías era «no antes de 30 minutos», sube el límite superior.

### Por qué 5 minutos y no 1

La especificación pedía señal en 1 minuto. **No se hace, y no es por comodidad.**

Pedir `"1"` con `request.security` desde un gráfico de 5m devuelve **solo la última vela de 1m contenida en cada vela de 5m**, no la secuencia de cinco. El toque al VWAP ocurre en cualquiera de las cinco, así que en cuatro de cada cinco casos sería invisible. La única forma de ver la secuencia sería `lookahead_on` sin desplazar, que **sí lee el futuro**.

**Lo que se pierde al quedarse en 5m**, y es un coste real, no cero:

- el toque se detecta hasta cuatro minutos más tarde;
- el stop sale más ancho, porque se mide contra la mecha de una vela de 5m en vez de una de 1m. Con el ATR(14) de 5m alrededor de 4,5 puntos, eso son típicamente entre 1 y 3 USD/oz más de riesgo por operación, que sobre un objetivo de 1,8R es entre un 6 % y un 15 % de la R.

---

## 3. S3 · Fade de las bandas ±2σ en día de rango

Solo con el día clasificado como **RANGO**. Misma forma que S1, con la banda haciendo de nivel: la vela perfora la banda y cierra de vuelta dentro.

Objetivo por defecto el **VWAP**, que es la vuelta a la media y lo natural en un fade. El R fijo está disponible para medir la misma entrada con un objetivo comparable al de las demás.

**S2 y S3 son mutuamente excluyentes por construcción**, no por un filtro añadido: S2 exige `regimen == 1` y S3 exige `regimen == -1`, y `regimen` es un solo valor por vela. No hay un `and not` que alguien pueda quitar por descuido y dejarlas peleando en el mismo día.

---

## 4. El clasificador de régimen

Sin esto no se puede implementar ni S2 ni S3. Tres opciones, implementadas las tres y seleccionables por input.

| Opción | Cómo | Por qué no es el defecto |
|---|---|---|
| **Rango del día / ADR** (defecto) | Rango del día de trading dividido por el ADR(20), **y** desplazamiento neto mínimo | — |
| ADX | `ta.dmi(14,14)` sobre el umbral | En 5 minutos arrastra entre 15 y 20 velas de retardo: dictamina «tendencia» cuando el movimiento ya ha ocurrido. Está para comparar, no porque lo recomiende. |
| Persistencia respecto al VWAP | Fracción de velas del día cerradas al mismo lado | Más robusta al ruido, pero no dice nada en los primeros 30 minutos, que es justo cuando S2 quiere entrar. |

**El defecto se eligió porque se conoce a cada vela, es adimensional —el mismo umbral vale en MGC y en XAUUSD— y no tiene parámetro de suavizado que ajustar.**

### Un añadido mío, declarado

El criterio por defecto exige **además** un desplazamiento neto mínimo: `|cierre − apertura| / rango ≥ 0,5`.

No estaba en la especificación. Está porque **el rango por sí solo no distingue tendencia de ruido**: un día que da bandazos de 1,3 ADR y cierra donde abrió es un día de **rango con swings grandes**, y el criterio de rango solo lo llamaría tendencia, activando S2 el día en que S3 era la correcta. El umbral es un input y **con 0 queda el criterio tal como lo especificaste**.

Todo se mide sobre el día de trading de las **18:00 ET** (la misma clave que HOD/LOD), para que el régimen no cambie de significado al cambiar el modo horario. Hay un mínimo de 12 velas antes de clasificar: sin él, a las 18:05 ET todos los días parecen de rango y S3 operaría cada madrugada.

El régimen y su dato crudo salen en una fila de la tabla de diagnóstico, para poder ajustar el umbral con números del gráfico en vez de a ojo.

---

## 5. S4 · Segundo movimiento tras noticias

> **ANTES DE ENCENDERLA: comprueba si tu prop firm restringe operar noticias.** Muchas evaluaciones prohíben tener posición abierta en una ventana alrededor de las publicaciones y anulan la cuenta o la operación si se incumple, con independencia del resultado. Que el código pueda no significa que el contrato permita. El aviso está también en el tooltip del input, que es donde se lee antes de encenderlo.

El **rango inicial es la vela que contiene la publicación**. En un gráfico de 5 minutos eso es literalmente «el rango inicial de 5 minutos» de la especificación, sin pedir nada a otro marco. Y no se entra en el primer minuto por construcción: la primera vela después de la publicación ya está a 5 minutos.

Dos modos, los dos activos dentro de la estrategia:

- **Ruptura**: cierre fuera del rango inicial, en esa dirección. Stop al otro lado del rango, que es lo que invalida la lectura.
- **Fallo**: mecha fuera y cierre de vuelta dentro, en la dirección contraria. Stop más allá de la mecha.

Si el rango de la noticia es enorme, el stop se pasa del techo de 15 puntos y la máscara lo veta. **Ese es el comportamiento correcto** en una vela desbocada, y el contador de vetos lo registrará.

La lista de horas es independiente de la del bloqueo por noticias de la Ventana de operativa, a propósito: una sirve para bloquear y la otra para operar. **Si usas las dos a la vez, el veto de bloqueo se aplica también a S4 y la dejará sin operar.**

Las horas por defecto (08:30, 10:00, 14:00 ET) son las habituales de IPC/NFP, datos de la mañana y FOMC. **No son una lista verificada**: ajústala al calendario real.

---

## 6. S5 · Sesgo horario, y el aviso de datos

### S5 no es un sistema

No dispara nunca nada. Solo suma o resta puntos a los candidatos de **S1 y S2** (no a S3 ni a S4). Un candidato arranca en 50 neutro.

El descarte es un **input aparte**: `Puntuación mínima del candidato`, 0 por defecto. Con 0, encender S5 **no cambia ninguna decisión**, solo la puntuación que se ve. Eso separa *describir* de *filtrar*, que en una hipótesis sin comprobar es la diferencia importante.

### El defecto mide la hipótesis en vez de aplicarla

Se acumula la deriva (cierre − apertura) de cada hora ET sobre los datos que estés usando y se toma su signo, con muestra mínima de 20 horas por franja. La fila `Deriva de la hora` de la tabla de diagnóstico la publica con su n, así que la hipótesis se puede **contrastar** de un vistazo. El modo «hipótesis fija (Asia alcista)» existe para comparar contra lo medido, no como verdad.

El rango por hora ya se medía desde la v2.5; **la deriva es otra cosa**: el rango dice cuánto se mueve una hora, la deriva dice hacia dónde.

### Aviso de datos · afecta a S2 y S3

**MGC tiene volumen real, así que su VWAP es fiable. XAUUSD spot de Dukascopy tiene volumen de ticks, así que su VWAP es una aproximación.**

Consecuencia práctica: un backtest de S2 o S3 sobre datos de spot mide una serie que **no es la que operarías**. Sirve para **descartar** (si pierde ahí, es poco probable que gane con el VWAP bueno) pero no para **confirmar**. En S3 el problema es mayor, porque la señal no es el VWAP sino su **desviación típica**, que hereda el error amplificado.

El aviso está en los tooltips de `i_s2On` y `i_s3On`.

---

## 7. Los cuatro conflictos, resueltos

### 7.1 · S2 contra S3 → clasificador de régimen

Resuelto en §4. Mutuamente excluyentes por construcción.

### 7.2 · S2 pedía 1 minuto → se queda en 5

Resuelto en §2, con el coste declarado.

### 7.3 · Reparto de cupo entre seis fuentes

Las cinco estrategias **no reimplementan la ejecución**. Cada una deja un *candidato* en una lista, y un resolutor elige uno que entra por el mismo embudo de siempre: máscara de vetos, dimensionamiento, redondeo a ticks y `strategy.entry`.

Dos mecanismos, combinables:

- **Prioridad**, cuatro modos: `FVG primero` (defecto, reproduce lo anterior), `Estrategias nuevas primero`, `La que menos haya operado hoy` (reparto rotatorio, que es lo que evita que una sola fuente se coma el cupo todos los días) y `Por puntuación del candidato` (que necesita S5 encendido para ordenar algo).
- **Cupo diario propio** por estrategia, todos a 0. Un cupo propio **acota** la estrategia, no le reserva sitio: el límite diario global sigue mandando por encima.

Los contadores se incrementan **cuando la orden ya está puesta**, no al generar el candidato: un candidato que la máscara veta no gasta cupo.

### 7.4 · Dos señales opuestas en la misma vela

**Por defecto no se opera ninguna.** Dos sistemas que se contradicen no es una señal débil: es ausencia de señal. La alternativa (`Manda la de mayor prioridad`) está disponible.

El conflicto **incluye al candidato heredado**: si el FVG compra y S3 vende, el desacuerdo es el mismo que entre dos estrategias nuevas. Se cuentan las veces que ocurre y sale en la fila `Conflictos de dirección` de la tabla: **si ese número es alto, las estrategias se están estorbando y el problema no es el umbral de ninguna.**

### 7.4b · Una interacción que conviene conocer

Si una estrategia nueva **gana la prioridad** a un FVG que disparaba en la misma vela, el FVG no se opera —correcto— y su zona **no** se marca como disparada. Pero la máquina de estados ya la habrá marcado **consumida**, porque el precio perforó su 50 %, y eso ocurre con independencia de que se operase o no: es comportamiento del sistema original, no algo que rompa la capa nueva.

Consecuencia práctica: con `Estrategias nuevas primero` o con el reparto rotatorio, **cada vez que una estrategia nueva se adelanta a un FVG, esa zona se pierde sin haberse operado**. No es un error, es el precio de cambiar la prioridad, y es una razón más para dejar `FVG primero` mientras no haya medición.

### 7.5 · La garantía de regresión

No he podido exportar la lista del Strategy Tester antes y después: en este entorno no hay TradingView. Lo que sí puedo dar es un argumento más fuerte que una comparación, porque es estructural:

Con las cinco apagadas, la lista de candidatos queda **vacía**. El bucle del resolutor no se ejecuta. El resultado es el candidato heredado tal cual, y los cinco puntos donde el embudo consulta lo nuevo (`esNueva` en el stop, en el objetivo, en el id, en el motivo y en los contadores) están todos detrás de `setKind == "Estrategia"`, que nunca es verdad. **No hay una sola instrucción nueva en el camino hasta la orden.**

La comparación sigue siendo tuya, y merece la pena hacerla igual: `backtests/README.md` tiene el protocolo. Lo que no se sostendría es que yo diga que la hice.

---

## 8. La instrumentación

Cada señal queda etiquetada con la estrategia que la originó, y la etiqueta sobrevive hasta el cierre: `Operacion.estrategia`.

### Tabla de resultados por estrategia

14 grupos: los 6 disparadores de FVG/barrido, las 4 estrategias nuevas, los 3 tiers y el total. S5 no tiene grupo porque no origina ninguna operación propia.

Por grupo: **n, win %, E[R], profit factor, drawdown máximo en R y % de cierres forzados**. El drawdown se calcula sobre la curva de equity **de ese grupo por separado**, no como parte del total.

Dos reglas de honestidad, heredadas de la v2.7:

- un grupo **sin operaciones no ocupa fila**;
- por debajo de **30** operaciones no se muestra ni porcentaje ni R, solo `muestra insuficiente (n=X)`. Un 60 % sobre ocho operaciones no es un 60 %, y ponerlo en una tabla invita a creérselo;
- entre 30 y 40 la fila sale **en gris**: hay cifras, pero no son concluyentes.

### Exportación

Pine no puede escribir ficheros. El equivalente es el **registro `O` en Pine Logs**, una línea por operación cerrada (apagado por defecto, input `Exportar operaciones cerradas a Pine Logs`):

```
O,entrada_ET,salida_ET,estrategia,disparador,tier,dir,precio_ent,precio_sal,stop_pts,riesgo_usd,pnl_usd,R,forzado
```

Con cabecera, emitida una sola vez. Se copia el panel de logs y se pega en un `.csv`. Da el detalle operación a operación, no solo el agregado, así que **cualquier métrica se puede recalcular fuera del script** — incluidas las que esta tabla no muestra.

---

## 9. Qué mirar, cuánta muestra hace falta y qué indica que no hay ventaja

### Las métricas, por orden de importancia

1. **Esperanza por operación en R, por estrategia.** Es la única que compone. Por debajo de **0,15R** después de costes no hay negocio: con 2 USD de comisión round turn y 1 tick de slippage sobre un riesgo de 150 USD, los costes se comen alrededor de 0,02R por operación, pero la varianza se come mucho más.
2. **Profit factor, por estrategia.** Entre 0,9 y 1,1 con más de 60 operaciones es ruido con buena presentación.
3. **Drawdown máximo en R, por estrategia.** No en porcentaje. Una cuenta de evaluación muere por drawdown, no por falta de beneficio.
4. **Racha perdedora máxima.** Con seis fuentes y varias operaciones al día, una racha de ocho puede caber en tres días.
5. **Contador de vetos exclusivos.** Dice cuántas operaciones ganarías relajando *un* filtro y nada más. Es lo que convierte «salen pocas señales» en un dato.
6. **Conflictos de dirección.** Si es alto, las estrategias se estorban.

### Cuántas operaciones

**Por estrategia, no en total.** Esto es el punto entero de la instrumentación.

| Muestra | Qué permite decir |
|---|---|
| < 30 | Nada. La tabla no muestra cifras a propósito. |
| 30 - 40 | El signo, con reservas. La tabla lo marca en gris. |
| **40** | El **signo** de la esperanza deja de ser ruido. |
| **100** | La **magnitud** empieza a ser fiable. |
| 200+ | Se puede empezar a cortar por sesión o por régimen. |

Con S1 acotada a una operación por lado y día dentro de una ventana de 3,5 horas, 40 operaciones son del orden de **tres a seis meses**. Con la ventana estrecha de S2 pueden ser bastante más. **Mídelo: la columna n está ahí para eso.** Si una estrategia no llega a 40 en un año de datos, el problema no es su esperanza, es que no hay muestra posible y no se puede validar.

### Qué indica que no hay ventaja

Cualquiera de estos, **por estrategia**:

- profit factor entre **0,9 y 1,1 con más de 60** operaciones;
- esperanza que **se vuelve negativa al quitar las tres mejores** operaciones: lo que había era una cola, no un sistema;
- **win rate alto con profit factor bajo**: muchos aciertos pequeños pagando pérdidas grandes, que es el perfil que estalla;
- resultados que **se desploman al mover un parámetro un punto**: el valor estaba ajustado a la muestra;
- esperanza positiva **solo en una sesión o un año concretos** y negativa en el resto;
- y el específico de esta versión: **un total positivo que, al abrirlo por estrategia, viene de una sola fuente mientras las otras cuatro pierden.** Para eso existe la tabla. Si pasa, lo correcto es apagar las cuatro, no quedarse con el total.

### Advertencia sobre lo que acabas de añadir

Son **cinco estrategias nuevas a la vez**, cada una con entre cinco y ocho parámetros. Eso son del orden de treinta grados de libertad nuevos sobre la misma muestra de datos. Con treinta grados de libertad **siempre** se encuentra una combinación que gana en el histórico, y casi nunca significa nada.

Lo honesto es medirlas de una en una, con los parámetros en su defecto, y no tocar nada hasta tener los 40 de cada una. Los umbrales y el R:R mínimo son lo que tiene sentido optimizar después; los pesos del score y los márgenes de stop, no.
