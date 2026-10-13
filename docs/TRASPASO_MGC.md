# MGC · Estado del bot para traspaso

Documento de contexto para continuar el trabajo en otra conversación. Fecha: 12 de octubre de 2026.

**Fichero**: `pine/MGC_FVG_ORB.pine` · Pine Script v6 · `strategy()` · MGC 5 minutos
**Tamaño**: 3.754 líneas, 136 inputs
**Versión**: v2.8 (cinco fuentes de señal nuevas, S1 a S5, todas apagadas)
**Segundo fichero**: `pine/MGC_v5_indicador.pine` · v5.2 · 1.295 líneas, 31 inputs · `indicator()` · 24 h, puerta de calidad única. **Falta su versión `strategy()`**, que estaba pedida en el mismo encargo.
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

**Regresión.** Con `Modo horario = Ventana NY`, máximo diario en 1, los cuatro frenos a 0 y los disparadores nuevos apagados, la lista de operaciones debía coincidir con la línea base. Esa comparación **no se ha podido hacer**: el CSV sigue sin generarse porque requiere TradingView (ver §1). La v2.7 invalida además esa línea base; ver abajo.

---

### v2.7 · Limpieza visual, y dos bugs de niveles

Ocho commits (`a74be8a` a `5a6dbc5`). **El punto 1 era una verificación de niveles y encontró dos bugs**; el resto es dibujo y no puede mover una operación.

| Punto | Cambio | ¿Mueve operaciones? |
|---|---|---|
| 1a | HOD/LOD se miden desde las 18:00 ET en los tres modos horarios, con clave de día propia. Lo rotulado como «máximo de sesión» era el extremo de la **ventana** | **No.** `sessHigh`/`sessLow` siguen intactos y son los que alimentan barridos y holgura |
| 1b | PDH/PDL pasan a ser los extremos del **día de trading anterior**, acumulados del gráfico, con la fecha en el rótulo | **Sí.** Ver §5b |
| 2 | Relleno solo en la zona activa más cercana por lado; el resto, contorno de 1 px. Si dos zonas se solapan manda la de marco mayor. Tope `X_DER` de 5 velas a la derecha | No |
| 3 | Rótulos de 40 caracteres como tope duro, formato `4H FVG ▼ 4171–4191`, y supresión por prioridad a menos de 0,5 ATR | No |
| 4 | Máximo cuatro líneas de nivel a la vez, dentro de 6 ATR, con los números redondos en el mismo presupuesto | No |
| 5 | Filas de tabla sin dato ocultas, y por debajo de 30 operaciones «muestra insuficiente (n=X)» sin cifras | No |
| 6 | El aviso de gráfico spot desaparece del todo. El input `Base futuros − spot` se mantiene | No |

**Dos trampas que aparecieron dos veces y conviene no reintroducir:**

1. **Leer el array que se está modificando.** La regla del solape y la supresión de rótulos recorren las zonas decidiendo cuáles se ven. Si leen el mismo array que acaban de escribir, el resultado depende del orden del recorrido. Las dos leen una copia, o el array de visibilidad ya cerrado, nunca `z.visible` a medio actualizar.
2. **La caché de renderizado se queda corta al añadir una decisión de dibujo.** `rendTier`/`rendEst` evitaban restilar sin motivo, pero al entrar el relleno y el rótulo había dos decisiones más que la caché no veía. `rendFill` las codifica en un número.

---

### v5.1 · Indicador · antirrepintado y panel

Siete commits (`810cb16` a `c7cb868`) sobre `pine/MGC_v5_indicador.pine`. Ningún peso, umbral, R:R mínimo ni regla de ARMADO o DISPARO cambia; comprobado con un diff restringido a esas expresiones.

1. **VIGILAR solo al cierre.** `hayVigilar`/`vigDir` se recalculaban en cada tick, así que el círculo aparecía y desaparecía a mitad de vela según el precio entrara y saliera del medio ATR de la zona. Pasan a `var` y solo se tocan con `barstate.isconfirmed`.
2. **Marcos superiores sin desfase.** Las cuatro llamadas a `request.security` que ya llevaban la expresión desplazada `[1]` pasan de `lookahead_off` a **`lookahead_on`**. Ese par es el idioma que no repinta; `lookahead_off` con expresión desplazada entrega el dato cuando el marco superior cierra en tiempo real, pero una vela superior más tarde en el histórico, así que las dos series no son la misma. Las llamadas: `[pdh, pdl]`, las tres `f_fvgHtf` (15, 60, 1D) y `f_estructura` con `shift = true`, **más `atr5`**, que no estaba en la lista del encargo pero cumple su criterio: `tfSetup` es `"5"` y en un gráfico de 1m es marco superior, de modo que dejarlo habría conservado el desfase justo en el ATR, que alimenta la anchura mínima del FVG y el score. Revisado que no queda ninguna expresión sin desplazar dentro de un `lookahead_on`; la única es `time` en `f_fvgHtf`, que es la excepción admitida y la que dispara `nuevo15`/`nuevo60`/`nuevoDd`.
3. **Apertura diaria del propio gráfico**, con `timeframe.change("1D")`. Se pedía al diario con `open` **sin desplazar**, que es la única combinación que de verdad miraría al futuro con `lookahead_on`. Ya no queda ninguna llamada en `lookahead_off`.
4. **Fuera el aviso de gráfico spot sin base.** Queda solo el de temporalidad, que sí cambia lo que el indicador puede detectar. El input `Base futuros − spot` se mantiene y sigue convirtiendo los precios del panel.
5. **Fuera las filas «Calib. total» y «NY / Asia»** y el input que las mostraba. Una fila que dice «n=14 · 57% · +0,12R» invita a creerse una ventaja que con esa muestra no está medida. Las arrays de calibración siguen, porque las usa *Desactivar setups con esperanza negativa*: lo que se quita es publicar la cifra, no medirla.
6. **El panel oculta Score, E/SL/TP1, R:R, Contratos y Antigüedad cuando no hay setup vivo**, con el mismo contador de filas que la v2.7 §5.

**Checklist, prueba 9 nueva:** comparar un día completo en Bar Replay y exigir que rombos y flechas caigan en la misma vela que en el histórico. Es la prueba del punto 2, y es más estrecha que la prueba 1: esa mira si algo repinta, esta mira si histórico y vivo son la misma serie.

---

### v5.2 · Contexto multimarco y disparos con resultado

Dos commits (`6408ccd`, `7e750c9`), uno por bloque. **El bloque A del encargo ya estaba aplicado en la v5.1**, así que no generó commit; verificado punto por punto.

**Bloque B · contexto multimarco.** Zonas de 4H (`f_fvgHtf` en `"240"`, peso 9, entre el 1H y el diario). `f_estructura` también en 60 y 240, de modo que el sesgo pasa de uno a **cinco votos** (VWAP, apertura, 15m, 1H, 4H) con umbral 3. El componente de alineación del score reparte el **mismo** `w_sesgo` entre los tres marcos (4H 40 %, 1H 32 %, 15m 28 %; a favor entero, rango la mitad, en contra cero): el peso total no cambia, lo que cambia es que un setup con el 4H a favor y el 15m en contra deja de puntuar igual que al revés. Rangos de Asia y Londres acumulados solo en velas confirmadas y **fijados al cerrar la sesión** —acumulador y valor fijado son dos variables distintas, porque un nivel que se mueve no es un nivel— y metidos en los barridos, el inventario de niveles y las confluencias. `barrUpNom`/`barrDnNom` dicen qué nivel se barrió, con el encadenado en orden de importancia del nivel. `ctxTxt` en una fila nueva del panel.

**Bloque C · los disparos se quedan con su resultado.** El fallo de fondo: el seguimiento del resultado vivía dentro del bucle por dirección, así que solo podía medir el setup al que `sL`/`sS` apuntaba en ese momento, y un ARMADO nuevo en la misma dirección **dejaba al anterior sin medir y sin archivar**. Ahora cada disparo vive en `abiertos` con su `uid` hasta que cierra, y puede haber varios a la vez en el mismo sentido.

Tres decisiones que conviene no revertir por descuido:

1. **La entrada real es el cierre de la vela del DISPARO**, no el del ARMADO, y el R:R se recalcula con ella. El del armado casi siempre es mejor que el real porque el precio ya ha avanzado hacia el objetivo, así que filtrar con él era filtrar con una cifra optimista.
2. **El resultado solo se mide con `bar_index > barDisparo`.** Medir las mechas de la vela del disparo cuenta movimiento anterior a la entrada, y en una vela de desplazamiento eso regala un TP1 o inventa un SL que nadie tocó estando dentro.
3. **TP1 y SL en la misma vela cuentan como SL.** No se sabe cuál llegó antes, y quedarse con el bueno es mentirse en la propia calibración.

`f_archivar` corta cajas y líneas en la vela del cierre y las guarda en colas de 120 etiquetas, 240 cajas y 330 líneas (120 disparos completos, con margen bajo los 500 de la declaración para zonas, niveles y el setup vivo). Input nuevo `i_verHist`, encendido.

---

### v2.8 · Cinco fuentes de señal nuevas (S1 a S5)

Ocho commits (`62ec8d6` a `26dc416`). **Todas apagadas por defecto.** El documento propio es `docs/ESTRATEGIAS_S1_S5.md`; aquí va solo lo que un relevo necesita saber para no romperlo.

**La arquitectura, que es la decisión importante.** Las cinco estrategias **no reimplementan la ejecución**. Cada una deja un `Cand` en una lista y un resolutor elige uno, que entra por el mismo embudo de siempre: máscara de vetos, dimensionamiento, redondeo a ticks y `strategy.entry`. Tres consecuencias:

1. **La regresión se sostiene estructuralmente.** Con las cinco apagadas la lista está vacía, el bucle del resolutor no se ejecuta, y los cinco puntos donde el embudo consulta lo nuevo están detrás de `setKind == "Estrategia"`, que nunca es verdad. No hay una sola instrucción nueva en el camino hasta la orden. **Esto no se ha verificado contra el Strategy Tester** porque aquí no hay TradingView; el argumento es estructural, no empírico.
2. Las estrategias nuevas pasan por **todos** los vetos existentes, así que la fila de vetos exclusivos dice cuál las ahoga.
3. Añadir una sexta estrategia es escribir un bloque que llame a `f_addCand` y añadir un grupo a la tabla. Nada más.

**Orden de los commits, y por qué ese orden.** La instrumentación va **primero** (`62ec8d6`): añadir cinco estrategias a la vez multiplica el riesgo de encontrar ruido, y un total positivo puede venir de una sola fuente mientras las otras pierden. Si la medición no está en pie antes, no hay forma de saberlo.

**Tres trampas que ya costaron tiempo y conviene no reintroducir:**

1. **`esAsia` necesita el `not esNueva`.** Sin él, un candidato de S1 que cayera en la misma vela que un barrido del rango asiático se tomaría por un disparador ASIA y se le aplicaría el stop del otro.
2. **La condición de S2 está hoisteada a una variable** en vez de envolver el `if` en dos líneas. Una condición partida seguida de un cuerpo indentado es justo donde la regla de indentación de Pine se vuelve ambigua.
3. **`max_bars_back = 500` es necesario**, no decorativo: `close[k]` en S1 y `vwap[N]` en S2 son desplazamientos **variables**, y Pine no siempre infiere el buffer cuando el índice no es constante.

**Dos añadidos míos, declarados como tales en el código y en el documento:**

- el clasificador de régimen por defecto exige **además** un desplazamiento neto mínimo, porque el rango por sí solo llama «tendencia» a un día de bandazos que cierra donde abrió. Con el umbral a 0 queda el criterio tal como se especificó;
- S5 por defecto **mide** la hipótesis del sesgo horario en los propios datos en vez de aplicarla, con el nuevo acumulador de deriva por hora. El modo «hipótesis fija» existe para contrastar.

**Lo que queda explícitamente sin validar:** las cinco. S1 es una inferencia sobre el espejo del ORB, no un hecho. S2 y S3 son hipótesis **y** solo se pueden medir a medias con datos de spot, porque su VWAP es una aproximación. S4 es hipótesis y además depende de una norma de prop firm sin comprobar.

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
13. **El máximo y el mínimo del día se dibujaban desde la ventana, no desde el día** (v2.7 §1a). Solo afectaba al dibujo: en `Ventana NY` lo rotulado como «máximo de sesión» era el extremo de 09:30-13:00 ET, así que un máximo hecho de madrugada no aparecía. Corregido con una clave de día propia anclada a las 18:00 ET. Sin impacto en operaciones: `sessHigh`/`sessLow` siguen intactos y son los que alimentan los barridos y la holgura.
14. **PDH y PDL pertenecían a un periodo distinto del que el script llama «día»** (v2.7 §1b). **Este sí tiene impacto en operaciones**, y está detallado en el apartado siguiente.

---

## 5b. El bug de PDH/PDL · impacto en operaciones

Se pedían al diario del exchange:

```pine
[pdh, pdl] = request.security(syminfo.tickerid, "1D", [high[1], low[1]], lookahead = barmerge.lookahead_on)
```

El idioma no repinta —eso estaba bien— pero **el corte de la vela diaria no es el día de trading del script**. El script define el día desde las **18:00 ET**; el diario del exchange rueda a las 17:00 ET en oro spot de OANDA y a la medianoche de su propia zona en cualquier símbolo sin sesión de futuros. El nivel que salía era el extremo de *otro* periodo, y la fecha a la que correspondía no era la del día de trading anterior.

**Tres reglas lo leen**, así que la corrección mueve la lista de operaciones:

| Dónde | Qué decide |
|---|---|
| `swpPdl` / `swpPdh` | barridos de liquidez del día anterior, que son un disparador de entrada |
| Confluencia de nivel del score | puntos de score, y el score alimenta el veto de fuerza mínima y el filtro ALTA |
| Filtro de holgura, con `usePrevDay` | veta la entrada si no hay recorrido hasta el obstáculo |

Ahora PDH/PDL se acumulan del propio gráfico con la misma clave de día que HOD/LOD y quedan fijos en el cambio de día, así que no repintan.

**Coste asumido:** en el primer día de trading del histórico no hay día anterior, de modo que PDH/PDL valen `na` y los barridos de día anterior no pueden dispararse ese día. Antes el diario los daba desde la primera vela. Es un día menos de muestra a cambio de que el nivel sea el que el script dice que es.

**Consecuencia para la regresión:** la línea base v2.2 queda invalidada por este cambio. Hace falta **una línea base nueva, v2.7**, y la diferencia contra la v2.2 se explica por estas tres reglas y por nada más. Protocolo en `backtests/README.md`.

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
