# MGC · Estado del bot para traspaso

Documento de contexto para continuar el trabajo en otra conversación. Fecha: 10 de octubre de 2026.

**Fichero**: `pine/MGC_FVG_ORB.pine` · Pine Script v6 · `strategy()` · MGC 5 minutos
**Tamaño**: 2.530 líneas, 85 inputs
**Versión**: v2.6 (varias operaciones diarias, a cualquier hora, por decisión del usuario)
**Segundo fichero**: `pine/MGC_v5_indicador.pine` · 996 líneas · `indicator()` · 24 h, puerta de calidad única. **Falta su versión `strategy()`**, que estaba pedida en el mismo encargo.
**Repos**: `domi-stack/crisol` (main) y `domi-stack/my-new-project` (rama `claude/orb-day-trading-bot-es-3bo9db`, PR #1 abierto)

Documentos de especificación que se han seguido, en orden de precedencia creciente:
1. `INSTRUCCIONES_V2_SENALES_Y_LECTURA.md` — fases 1 a 5
2. `INSTRUCCIONES_V2_1_ALTA_PROBABILIDAD.md` — manda sobre el anterior donde choquen
3. `CORRECCIONES_V2_2.md` — cinco correcciones y el protocolo de desbloqueo de la calibración

Ficheros añadidos en v2.2:
- `backtests/README.md` — protocolo de la línea base de regresión
- `paridad/comparar.py` + `paridad/README.md` — prueba de paridad Pine ↔ Python
- `docs/ESTRATEGIA_MGC.md` — documento de estrategia, ahora en el repo y corregido

---

## 1. NADA DE ESTO SE HA EJECUTADO

Lo primero y más importante. El entorno donde se escribió **no tiene TradingView ni intérprete de Pine**. El script no se ha compilado ni se ha pasado por el Strategy Tester ni una vez.

Lo que sí se verificó, con comprobadores estáticos propios:

- Paréntesis balanceados
- Ninguna continuación de expresión con indentación múltiplo de 4 (Pine la interpretaría como bloque local)
- Ninguna función ni variable global usada antes de declararse
- Ningún input declarado sin usar
- Ninguna tabla escribiendo fuera de las filas o columnas que declara
- Ningún `break` ni `continue` (Pine no los tiene)

**Pendiente de verificación humana:**

- Que compile
- La regresión: con `Modo horario = Ventana NY` y `Operar solo zonas ALTA = no`, la lista de operaciones debe reproducir la de partida (regla 0.1 del V2.1)
- Criterios de aceptación 2 a 6 del V2.1: nunca más de 2 zonas visibles con defectos, Bar Replay vela a vela, ninguna entrada entre 16:45 y 18:15 ET, ninguna posición el viernes tras las 16:50 ET, legibilidad en tema claro y oscuro
- Que no se agote el cupo de objetos con 6 meses de datos de 5m

---

## 2. Qué está implementado

### Fase 0 · Cimientos (no estaban especificados; diseño propio)

El V2 §6 daba por implementado un documento prerequisito, `INSTRUCCIONES_DIBUJOS_LECTURA.md`, que **nunca se aportó**. Las estructuras siguientes son diseño propio y están documentadas en el código para poder reconciliarlas si ese documento aparece.

- **UDT `Zona`**: geometría, identidad (incluido el ATR de su propio marco, pedido en la misma tupla de `request.security` que ya devolvía la zona), estado, score, campos de dibujo.
- **UDT `Operacion`**: disparador, tier, riesgo planificado en USD, anchura del stop, marca de entrada y bandera de cierre forzoso. El riesgo se guarda al entrar y **no se recalcula**: R = PnL / riesgo planificado.
- **Máscara de vetos**: una sola función (`f_mascara`) que evalúan tanto la ejecución como la máscara teórica de la capa de acción. Pine no tiene operadores de bits, así que se construye sumando y se consulta con división entera. Doce bits.
- **Dos contadores por veto**: *bloquea* (cuántos vetó, solo o acompañado) y *exclusivo* (cuántos vetó él solo). El exclusivo es el informativo: dice cuántas operaciones ganarías relajando ese filtro y nada más.
- **Ciclo de vida de dibujos**: crear una vez, mutar después, ocultar con transparencia 100, borrar solo al salir de una cola FIFO.
- **Un id de entrada por disparador**: `FVG5`, `FVG1H`, `FVG4H`, `SWP`, `SB`, `ASIA`, con disparador y tier en el comentario de la orden.

### Fase 1 · Legibilidad

Radio de proximidad en ATR, recorte de zonas de 5m por lado conservando las más cercanas, consumidas ocultas por defecto, rangos de Asia y Londres en cajas FIFO fijadas al cerrar la sesión, números redondos (cuatro líneas movidas, no recreadas), etiquetas de nivel al borde derecho, fondo de la ventana Silver Bullet.

### Fase 2 · Score de fuerza 0-100

Siete componentes recalculados en cada vela confirmada: marco, estado, desplazamiento contra el ATR de su propio marco, liquidez previa, alineación con el 4H, confluencia de nivel (una sola vez) y timing en ventana Silver Bullet. Tiers FUERTE/MEDIA/débil con transparencia 55/75/90 y gradiente de color interpolado. Restilado solo cuando cambia el tier o el estado. Desglose en tooltip de labels invisibles, porque las cajas de Pine no admiten tooltip.

**Los pesos son a priori y no están validados.** El código lo dice encima de la función.

### Fase 3 · Capa de acción

Estado único por vela con la prioridad del documento: GESTIONAR, EJECUTAR, NO OPERAR, PREPARAR, ESPERAR CONFIRMACIÓN, VIGILAR. La máscara teórica es la misma función evaluada como si la entrada fuera en el CE de la zona. Aviso de incoherencia con la ATM de NinjaTrader cuando el stop difiere más de 0,5 pts, con el riesgo real en los dos casos. Aviso de precios spot si el ticker no es de futuros de oro.

### Fase 5 · Tablas de medición

Tabla de resultados por disparador y por tier con n, win %, E[R], PF, drawdown en R y % de cierre forzoso. Las filas con n<40 salen en gris. Fila de diagnóstico con mediana y percentil 80 del stop estructural de todos los setups vistos, por disparador, frente al ATR medio de 20 sesiones. Fecha de inicio del diagnóstico respetada por las dos tablas.

### Fase 4 · Disparadores nuevos (todos apagados por defecto)

Silver Bullet con la secuencia completa (barrido → CHoCH contrario → FVG de la vela de desplazamiento → entrada al 50%), con stop en el FVG o el swing del MSS y **no** en la mecha del barrido. Falso rompimiento del rango asiático ampliando el conjunto de niveles del barrido existente. Veto por ADR agotado. Números redondos como obstrucción opcional. Contexto DXY de solo lectura.

### V2.1 · Modo limpio y 24 h

Modo limpio (encendido por defecto): una zona por lado en transparencia 25 con borde de 2 px, línea de CE, y todo lo demás oculto tras su propio input. Tabla reducida de cinco filas.

Modo 24 h (nuevo defecto): día de trading CME desde las 18:00 ET, entradas bloqueadas de 16:45 a 18:15 ET y opcionalmente en horas de noticias, cierre a las 16:50 ET todos los días incluido el viernes, horizonte máximo de 8 h.

---

### v2.2 · Correcciones previas a la primera ejecución

Seis commits (`2123543` a `65a2869`):

- **C1 · Bug grave corregido.** En modo 24 h la bandera de cierre forzoso quedaba abierta por arriba hasta medianoche, y la máscara de vetos bloquea con ella. El día CME abre a las 18:00 ET, así que **no había entradas entre las 18:00 y las 23:59**: el "24 h" real era 00:00-16:45. Ahora la bandera cubre solo 16:50-18:00. El contador de minutos al cierre tenía la misma raíz y devolvía 0 toda la tarde.
- **C2 · Patrón de marcos superiores.** Las siete llamadas a `request.security` pasan de `lookahead_off` a **`lookahead_on` con la expresión desplazada `[1]`**, que es el idioma que no repinta. `f_structure` lleva un parámetro `shift` en lugar de duplicarse, porque en el marco del propio gráfico no debe retrasarse. El rango consumido del día **ya no se pide al diario** (pedir la vela en formación era el caso que repinta): se acumula en el marco del gráfico desde el inicio del día de trading.
- **C3 · Cupo de objetos.** Las etiquetas de señal tenían cola FIFO de 200. Sin ella, al pasar el cupo Pine borraba las más antiguas, que son los pools creados en la primera vela, y desaparecían justo en la última vela. Auditadas todas las creaciones: ninguna queda sin acotar.
- **C4 · Línea base de regresión.** Protocolo en `backtests/README.md`. La anterior no servía: la versión de partida no operaba nunca y tres correcciones cambian decisiones a propósito.
- **C5 · Defectos seguros.** Modo horario vuelve a **`Ventana NY`**. Con 1 operación al día y sin calibración, el modo 24 h gasta el cupo en la primera señal del día CME (que empieza a medianoche en Madrid) y bloquea la sesión de Nueva York. El modo 24 h queda para observar.
- **Exportador de Pine Logs** (apagado por defecto) con registros `Z`/`E`/`D` e ids de zona, más `paridad/comparar.py` probado.

---

### v2.3 y v2.4 · Paridad

Nueve commits (`f5384f4` a `5ce8837`). Ninguno toca una decisión de trading: todos sirven a la prueba de paridad de `paridad/README.md`.

- **v2.3-1 · Bug de repintado.** El ATR dentro de `f_htfFvg` no estaba desplazado bajo `lookahead_on`. Como alimenta el test de anchura mínima, **el criterio que decidía si existía un hueco repintaba él mismo**. Auditadas después todas las expresiones `lookahead_on`.
- **v2.3-2 a v2.3-5, v2.4-1 a v2.4-4.** Exportación acotada a un rango con inventario `S` de las zonas vivas al abrirlo (y con la fecha de **nacimiento** como clave, no la de apertura del rango), registros `P` de purga FIFO, el comparador aceptándolos y comprobando dirección y momento, la separación entre paridad de código y paridad de datos, la especificación de `detectar.py` y el rango por defecto de un solo día (un mes desbordaba el panel de logs).

---

### v2.5 · Filtro de hora plana

Un commit (`98dd521`). Mide el rango medio de cada hora del día **sobre el propio gráfico** y veta las horas que quedan por debajo de una fracción de la media de todas, con muestra mínima antes de vetar. Es lo que hacía viable el modo 24 h cuando el cupo era de una operación al día: sin él, la primera señal del día CME —normalmente en Asia— se llevaba la operación y Nueva York se quedaba fuera. Con el cupo en 3 deja de ser imprescindible, pero sigue encendido por defecto.

---

### v2.6 · Varias operaciones diarias, a cualquier hora

Once commits (`17ba3d8` a `f1d04a8`). **Son decisiones del usuario, no recomendaciones mías**, y el encargo decía explícitamente que no se discutieran: varias operaciones al día, a cualquier hora, señales confirmadas al cierre de vela y gráfico con colores claros. Ninguna regla de entrada, stop, objetivo, filtro ni sizing cambia.

| Punto | Cambio |
|---|---|
| 1 | `max_lines_count` de 100 a 400: las líneas de operación nuevas no caben en 100 |
| 2 | `Modo horario` vuelve a **24 h** por defecto. Esto **revierte C5 de la v2.2**, que lo había puesto en `Ventana NY` por prudencia. El tooltip y el comentario dicen ahora que es el defecto por decisión del usuario, y que `Ventana NY` se conserva porque es parte de la línea base |
| 3 | Máximo de operaciones al día: **3** por defecto, techo de 10 |
| 4 | Freno diario (pérdidas seguidas, suelo en R, techo en R) y enfriamiento entre operaciones. **Los cuatro a 0, apagados.** No añaden bits a la máscara: comparten `límite diario` y `posición abierta`, para que los contadores de veto no cambien de significado |
| 5 | Etiqueta de señal en tres líneas: dirección y hora de Madrid, los tres precios, contratos y riesgo en dólares. Cola FIFO de 200 intacta |
| 6 | Tres líneas horizontales por operación (entrada gris discontinua, stop roja, objetivo verde), extendidas mientras vive la posición, con cola FIFO de 90 |
| 7 | Campo `Zona.elegida` y `f_atenuarZona`: en modo limpio, una zona que llegó a destacarse deja un rastro atenuado en vez de desaparecer |
| 8 | `i_marcasLimpio` (encendido): las marcas de CHoCH y de barrido sobreviven al modo limpio |
| 9 | La fila `Hoy` de la tabla limpia añade `· FRENO` y se pone naranja cuando un freno está cortando |
| 10 | Cabecera del script: decía "una sola operación diaria", que era lo contrario de lo configurado |

**Dos arreglos de las comprobaciones de cierre** (`f1d04a8`), ninguno de ellos toca una regla:

- Las cinco líneas de continuación de `Zona.new()` estaban a 20 espacios. Pine exige que la indentación de una continuación **no** sea múltiplo de cuatro, porque si lo es la lee como un bloque anidado. Pasan a 21.
- `i_pasoRedondo` estaba en el grupo **Visual**, pero lo leen la confluencia de nivel del score y el filtro de holgura cuando se eligen los números redondos como obstáculo: decide entradas. Pasa a **Filtros**, con el tooltip diciéndolo. El valor por defecto no cambia, así que la regresión no se mueve.

Los otros tres controles de la lista salen limpios: paréntesis balanceados, todo declarado antes de usarse y ninguna función asignando a una variable global.

**Regresión.** Con `Modo horario = Ventana NY`, máximo diario en 1, los cuatro frenos a 0 y los disparadores nuevos apagados, la lista de operaciones debe coincidir con `backtests/baseline-v2.2.csv`. Esa comparación **no se ha podido hacer**: el CSV de la línea base sigue sin generarse porque requiere TradingView (ver §1).

---

## 3. Lo que NO está hecho, y por qué

### La calibración histórica (V2.1 §1) — BLOQUEADA

Es el punto 1 del orden de implementación del V2.1 y de ella cuelgan los porcentajes de §3.1.2 y el filtro ALTA de §4.

**Los datos sí están disponibles**: el espejo público `kk-at-5/xauusd-raw-data` tiene 128 ficheros M1 mensuales desde 2013 — trece años, muy por encima de los 24 meses que pide §1.1. Se contrastó contra un feed independiente de OANDA sobre 4.732 minutos solapados con diferencia mediana de 0,11 USD, y contiene las huellas del calendario real (Viernes Santo, cierre anticipado del Juneteenth y del 3 de julio, cambio de horario de verano en EE.UU.). Dukascopy está bloqueado por la política de red del entorno y su fetcher no existe en el repo.

**El bloqueo es otro**: §1.2 exige una prueba de paridad obligatoria entre las zonas que detecta Python y las que **dibuja Pine**, exportadas desde Pine, y dice literalmente que si no coinciden no se sigue. Eso requiere ejecutar Pine. Sin esa prueba, cualquier cubo calculado sería una calibración sobre zonas distintas de las que usa el script, que es exactamente lo que el documento prohíbe.

**Ya existe la mitad del camino** (v2.2): el exportador de Pine Logs y el comparador `paridad/comparar.py`, probado contra registros sintéticos en sus dos ramas.

**Lo que falta, y solo lo puede hacer quien ejecute Pine**: cargar el script en **OANDA:XAUUSD 5m** (no en MGC1!: los datos de Python son spot y en futuros las zonas no coincidirían por el feed y la base futuros-spot), activar el exportador y subir el panel de logs de tres días — uno de tendencia, uno de rango y uno con dato macro. Ver `paridad/README.md`.

**`paridad/detectar.py` no está escrito a propósito**: tiene que replicar la detección de Pine exactamente, y hacerlo antes de tener un fichero de logs real contra el que contrastarlo es trabajar a ciegas.

### Consecuencias de esa laguna

- **No se muestra ningún porcentaje** en ninguna caja ni tabla. Las tablas dicen `SIN CALIBRAR`.
- **El orden de zonas usa el score**, no una probabilidad. El §0.2 del V2 permite el score para dibujar.
- **`Operar solo zonas ALTA` está apagado**, no encendido como pide §4 del V2.1: sin tabla calibrada ninguna zona cumpliría el criterio y vetaría *todas* las entradas, que es peor que no filtrar. Su bit `noALTA` y sus contadores están en la máscara, listos.

---

## 4. Desviaciones deliberadas de la especificación

| Dónde | Especificación | Qué se hizo | Por qué |
|---|---|---|---|
| V2.1 §4 | `Operar solo zonas ALTA` = sí | apagado | Sin calibración vetaría todo |
| V2.1 §3.1.2 | Texto con `52 % · +0,5R` | score y tier + `SIN CALIBRAR` | P y E[R] no existen |
| V2 §1.4 | Texto `4H ▲ 82 FUERTE` | ese formato, con el score real | Correcto desde la fase 2 |
| V2 §1.5 | Niveles de sesión punteados | stepline de 1 px | `plot` no tiene estilo punteado en Pine |
| V2 §2.2 | Tooltip en la caja | tooltip en label invisible | Las cajas de Pine no admiten tooltip |
| V2 §5.1 | — | filas con n<40 en gris | §9 fija ese umbral; la tabla no debe invitar a concluir sin muestra |
| V2 §2.1 | — | input de anclaje eliminado | El modo horario del V2.1 ya expresa esa elección y el input quedaba sin efecto |
| V2.2 C4 | Etiquetar el commit `baseline-v2.2` | tag solo en local | El proxy de git del entorno corta la conexión al enviar tags (probado con tag anotado y ligero). El commit de referencia es `65a2869` y sí está en el remoto: etiquetar con `git tag baseline-v2.2 65a2869` |

---

## 5. Bugs encontrados y corregidos, para no reintroducirlos

Tres de ellos habrían impedido compilar o habrían dejado la estrategia sin operar nunca:

1. **La estrategia no habría operado jamás.** La máquina de estados marcaba la zona como consumida al perforar el 50% *antes* de que la sección de entrada la evaluara, así que el selector no encontraba nunca una zona válida. Resuelto con un campo que registra en qué vela se produjo el disparo.
2. **Toda zona nacía ya "mitigada"**: el borde del hueco *es* el mínimo o máximo de la vela que lo crea, así que el test de toque se cumplía por definición. Ahora la vela de creación se excluye.
3. **El BOS de continuación era inalcanzable** por el encadenado de condiciones, y el BOS se repetía en cada vela mientras el precio siguiera fuera del swing. Ahora cada nivel de swing solo puede romperse una vez.
4. **Las zonas invertidas quedaban inoperables** porque al pasar a estado 3 dejaban de cumplir `state <= 1`. Ahora la inversión cambia el signo y vuelve al estado virgen.
5. **La detección de barridos del extremo de sesión nunca podía disparar**: comparaba la vela actual contra un extremo que ya había absorbido esa misma vela. Ahora lee el valor de la vela anterior.
6. **El filtro de holgura ahogaba las señales**: los extremos de sesión contaban como obstrucción dura, y el máximo de la sesión está casi siempre a 5-20 puntos del precio, así que vetaba casi cualquier entrada en retroceso. Ahora qué obstruye es un input y por defecto solo cuentan las zonas de marco mayor.
7. **El disparo estaba sobre-restringido** respecto a lo que se había pedido: la elección fue "cierre dentro de la zona" y se había implementado como "cierre exactamente en el 50%", mucho más estrecho. Ahora es un input y por defecto cubre toda la banda.
8. **Funciones de tonalidad usadas antes de declararse** y **`asiaLoFijo` leído 70 líneas antes de su declaración**: Pine rechaza ambos.
9. **Asignación a una variable global desde dentro de una función**: Pine permite mutar arrays, no variables. Este volvió a aparecer al escribir el contador de ids del exportador y se resolvió con un array de un elemento.
10. **El modo 24 h no operaba las primeras seis horas del día CME** (C1), por una bandera de cierre forzoso abierta por arriba.
11. **Patrón de marcos superiores propenso a repintado** (C2): `lookahead_off` hace que histórico y tiempo real no coincidan, y una de las llamadas no llevaba ningún desplazamiento.
12. **Pools de dibujo borrados por el recolector de Pine** (C3) al no tener cola las etiquetas de señal.

---

## 6. Limitaciones de Pine encontradas por el camino

Útiles para quien continúe:

- **No hay operadores de bits.** Las máscaras se construyen sumando y se consultan con división entera.
- **No hay `break` ni `continue`.** Se sustituyen por condiciones de guarda.
- **Una función no puede asignar a una variable global.** Sí puede mutar un array o un objeto por referencia.
- **Las continuaciones de expresión no pueden llevar indentación múltiplo de 4** o se interpretan como bloque local. Dentro de paréntesis la regla no aplica.
- **Un ternario `?:` evalúa las dos ramas**, así que leer un campo de un objeto que puede ser `na` dentro de un ternario revienta. Hay que usar `if`/`else`.
- **Las cajas no admiten tooltip**; solo las labels.
- **`plot` no tiene estilo punteado.**
- **`request.security` no puede estar dentro de un bloque condicional.**
- **Las funciones y las variables globales deben declararse antes de usarse.**

---

## 7. Riesgos abiertos sobre la estrategia, no sobre el código

1. **El techo de 15 puntos puede ser el cuello de botella real.** Con 10 USD por punto y 150 USD de riesgo, 15 puntos es el máximo con un contrato, y los stops de los barridos van a la mecha, que con el oro actual pasa de ahí con facilidad. **El primer dato a mirar al cargarlo es la fila `Stop med/p80` frente al ATR de 20 sesiones.** Si la distribución de stops está por encima de 15 puntos, ningún ajuste de filtros lo arregla.
2. **El objetivo de 2R es ambicioso.** 300 USD son 30 puntos, alrededor de 6,7×ATR en 5m. En una ventana de 3,5 horas eso está en el límite de lo que el instrumento entrega en una sesión. Si el porcentaje de cierres forzosos sale alto, el problema es el objetivo, no el filtro.
3. **El modo B acepta operar contra el marco mayor.** No exige alineación, así que tomará setups al alza dentro de una estructura bajista de 4H. Es el subconjunto de peor calidad del sistema. Si el resultado global sale malo, conviene probar el modo A antes de tocar nada más.
4. **El límite de 1 operación al día es el techo absoluto de frecuencia**: unas 21 señales al mes como máximo, pase lo que pase con los filtros. Si se quieren más, hay que cambiar esa regla de riesgo, que es una decisión de cuenta. Es además la razón por la que el modo 24 h no puede ser el defecto todavía: el día CME empieza a medianoche en Madrid y el cupo se lo llevaría Asia.
5. **El score no está validado.** Si la tabla de resultados no muestra al tier FUERTE batiendo al débil en E[R] con al menos 40 operaciones en cada uno, el score es decorativo y no debe usarse como filtro.
