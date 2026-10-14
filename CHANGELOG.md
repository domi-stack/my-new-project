# CHANGELOG · MGC FVG + Estructura

Un solo fichero: `pine/MGC_FVG_ORB.pine`. Cada entrada dice **qué** cambió y **por qué**, que es lo que importa seis meses después.

Convención: ⚠️ marca lo que **mueve la lista de operaciones** del Strategy Tester. Todo lo demás es dibujo, medición o inputs apagados.

---

## v5.6 · Capa HOD/LOD · se integra como medición, no como señal

Portado de `HOD_LOD_Zonas v1.0` (fichero aportado por el usuario) a la **sección 11**. En la apertura del día dibuja dos cajas —dónde es probable el máximo, dónde el mínimo— usando solo lo que se sabe en ese momento, y al cerrar el día se puntúa a sí misma.

**No mueve la lista de operaciones, y no por los defectos sino por construcción:** no genera candidatos, no aparece en la máscara de vetos y no toca ninguna decisión de entrada. Encenderla cambia el dibujo y añade una tabla; nada más.

### Por qué no es una fuente S9

Su propia cabecera dice que no es una señal de entrada y que **no simula operaciones, así que no dice nada sobre si gana dinero**. Exponerla como disparador habría contradicho al autor. Entra donde entran el perfil horario y la deriva por hora: describe, no opera.

### La aritmética que hay que tener delante antes de mirar la tabla

Cobertura y ancho de caja son **la misma magnitud vista de dos formas**: una caja más ancha siempre cubre más. Por eso la tabla muestra siempre las dos cifras juntas, y por eso hay una fila que dice literalmente «cobertura sin ancho: no es métrica». Sobre 109 sesiones de XAUUSD (ADR 122,8 pts), con el predictor calibrado a posteriori —o sea haciendo trampa a favor del modelo—:

| Ancho de caja | HOD | LOD | CONJUNTA |
|---|---|---|---|
| 6 % del ADR (el defecto comercial) | 14,7 % | 11,0 % | **0,0 %** |
| 30 % del ADR | 47,7 % | 38,5 % | 5,5 % |
| 50 % del ADR | 65,1 % | 57,8 % | 25,7 % |

Para una cobertura conjunta del 91 % hacen falta cajas de **~140 % del ADR cada una**. Con el 6 % por defecto la cobertura conjunta en oro es cero, y no es un fallo del modelo: el máximo exacto del día no cabe en una ventana de 7 puntos.

### Cuatro bugs del fichero original, arreglados al portarlo

| Bug | Qué hacía | Arreglo |
|---|---|---|
| **CW10002** | `ta.change(time("D"))` dentro de un `and` detrás de un `or`. Función con estado que puede no evaluarse: historial equivocado y **ningún error**. Es la misma clase que el usuario reportó en la v5.2 | Se calcula en ámbito global |
| **División entera en `f_pc`** | `a / b * 100.0` con los dos argumentos `int`. En Pine `int/int` trunca, así que con `a < b` da 0: **toda la columna de cobertura habría salido «0.0%»**. Verificado: 14/109 → 0,0 % en vez de 12,8 %; 52/109 → 0,0 % en vez de 47,7 % | `a * 100.0 / b` |
| **La misma división en la «Ventaja»** | El veredicto contra el predictor tonto solo podía salir 0 o ±100 pp. Es justo la cifra que uno mira para decidir si apagar el contexto | `* 100.0 /` y formato `F_SIGNO`, que de paso evita el `-+6.5` |
| **«Media de 20 días» que eran 100 minutos** | El input prometía la media de 20 días; el código era `ta.sma(close, 20)`, que en 5 minutos son **20 velas**. Uno de los cuatro filtros de contexto medía otra cosa | Array propio de cierres diarios, media de los 20 últimos. Con array y no con `request.security` para no gastar presupuesto y, sobre todo, para usar **la misma frontera de día** que el resto de la sección |

### Decisiones de integración

| Decisión | Motivo |
|---|---|
| **`i_hlOn` apaga el dibujo y la tabla, NO el motor** | Los arrays y los `ta.*` siguen en ámbito global. Si el motor estuviera detrás del interruptor se evaluaría de forma intermitente y el histórico saldría mal al encenderlo. Es el patrón del filtro de chop, y lo que la cabecera del fichero original ya advertía |
| **Día propio: `time("D")`, no el día CME de las 18:00 ET** | `hod`/`lod` y el régimen usan el día CME. Las cifras de calibración de arriba se tomaron con `time("D")`; cambiar la frontera movería **lo que el modelo mide**, no solo cuándo lo mide |
| **Tabla en `middle_right`** | `diag` y `limpia` ya se apilan en `top_right` |
| **`i_hlVerHist`: maxval 300 → 100** | Aritmética, no gusto: 300 días son 600 cajas y Pine admite 500. Con las zonas al máximo (200) y los rangos de sesión al máximo (60) quedan 240 libres, o sea 120 días; se deja en 100 por margen. Pasado el límite Pine borra las cajas viejas **sin avisar**, y lo que se ve deja de corresponder con lo que la tabla cuenta |
| **`max_lines_count`: 400 → 500** | Peor caso con todo al máximo: 460/500 cajas y 330/500 líneas. Plots 26/64 y `request.security` 6/40 sin cambios |
| **Se quedan fuera `pHigh`, `pLow`, `dBarIni`** | Se escribían en cada cambio de día y no se leían en ninguna parte |
| **Se queda fuera el `alertcondition`** | «Zonas del día calculadas» en una estrategia solo añade ruido |

Única colisión entre los 90 identificadores nuevos y los existentes: `G_VIS` → `G_HL_VIS`.

**No compilado.** No hay TradingView ni intérprete de Pine en este entorno. Pasa los cinco chequeos estáticos de `scripts/verificar_pine.py` y los recuentos de recursos de arriba; nada más está verificado.

---

## Encargo 3 · S7 order block y S8 OTE

Las dos **apagadas**, así que con los defectos de la v5.4 la lista de operaciones no se mueve. Documento: `docs/ESTRATEGIAS_S1_S8.md` (renombrado desde `_S1_S5`).

| Cambio | Motivo |
|---|---|
| **S7 · order block** | La última vela contraria antes de un desplazamiento que rompe estructura. Dos pasos, y el primero es un **inventario**, no un setup: al romper se archiva el rango de esa vela; al volver el precio se emite el candidato |
| **S7 · cede ante el FVG cuando solapan** | Un OB y el FVG del mismo desplazamiento señalan el mismo precio **y en la misma dirección**, así que el contador de conflictos no los vería: ese cuenta desacuerdos, y aquí hay **acuerdo duplicado** — dos fuentes cobrándose la misma señal e inflando la muestra de las dos. Con más del 50 % de solape, S7 no emite, y hay fila propia en el diagnóstico |
| **El 50 % se mide contra la zona menor** | Es lo que responde a «¿señalan el mismo sitio?». Un FVG diminuto dentro de un OB grande solapa el 100 % de sí mismo; medirlo contra el OB habría dejado pasar justo ese caso |
| **S8 · OTE** | El aviso va en el código **y** en el tooltip, literal: el bloque 70,5-79 % es una convención de una comunidad, no un resultado medido. Los dos porcentajes son **inputs** precisamente por eso |
| **DXY instrumentado, no promovido** | `Operacion.dxyAlEntrar` capturado **al entrar** —recalcularlo al cerrar mediría otra cosa— y fila de esperanza por dirección del dólar. `i_verDxy` pasa a `true` porque con él apagado `dxyDir` vale 0 siempre y la fila no podría medir nada. Sigue sin entrar en ninguna decisión |
| **ORB · medido y descartado, por escrito** | 133 sesiones: esperanza −0,028R, PF 0,84, win rate 51,1 % contra 53,1 % de equilibrio. Quince variantes, ninguna sobre +0,10R. La única marginal se explica por una muestra en la que el oro cayó 16,3 %. Queda en `docs/ESTRATEGIAS_S1_S8.md` para que nadie lo reintroduzca por tener la idea otra vez |

---

## v5.4 · Tres incoherencias, y las seis fuentes encendidas

### Las tres correcciones

| Cambio | Motivo |
|---|---|
| **`i_maxTrades` admite 0 = sin límite** | Era el único freno que no seguía la convención de `0 = apagado` de `i_maxPerdDia`, `i_minRDia`, `i_maxRDia` e `i_enfriar`, y por tanto el único que no se podía apagar. `minval` 0, `maxval` 50, y en la máscara el bit solo se pone si `i_maxTrades > 0`. De paso: `V_DIARIO` lo comparten el límite y los frenos, así que con el límite a 0 el panel decía «límite diario alcanzado» cuando lo que había era un freno — ahora distingue |
| ⚠️ **Las flechas EJECUTAR solo salen si se envió la orden** | **Bug mío, de la v2.9-2.** `accTxt := "EJECUTAR"` se asignaba con `setDir != 0`, que es el resultado del resolutor, y la máscara se evalúa **después**. Salían flechas grandes en velas sin ninguna entrada: con el límite diario alcanzado, decenas de flechas y cero operaciones. Ahora hay una bandera `opEjecutada` que se pone a true en la **única** llamada a `strategy.entry` del fichero, así que el número de flechas coincide con el de entradas por construcción. El candidato vetado tiene estado propio, «SEÑAL VETADA», que **nombra** los vetos, y marcador propio: una **x pequeña**, nunca un triángulo |
| **Un solo criterio de zona operable** | Había dos para la misma pregunta: el modo limpio exigía estado y no disparada; la capa de acción exigía además `tier >= 1` y distancia dentro de `i_distMaxATR`. Discrepaban y se veía: la tabla mostraba una zona a 6,79 ATR con el radio en 6,0. Ahora las dos consumen `f_zonaOperable`. Es un **predicado**, no una función que devuelva un índice, porque los consumidores necesitan cosas distintas —una zona frente a N por lado— y lo que había que unificar era el criterio |

### ⚠️ Las seis fuentes pasan a encendidas, y el cupo diario a 0

`i_s1On`, `i_s2On`, `i_s3On`, `i_s4On`, `i_s5On` e `i_s6On` pasan a `true`. `i_maxTrades` pasa de 3 a **0**.

**Esto rompe la garantía de regresión que había desde la v2.8.** Hasta aquí, los defectos reproducían la línea base y eso era una propiedad del código. Ya no: con seis fuentes activas y sin cupo diario, la lista de operaciones con los defectos **no se parece** a la de la v2.7.

#### Para la línea base de regresión hay que poner, a mano:

| Input | Valor |
|---|---|
| `Máximo de operaciones al día` | **1** |
| `Activar S1 · barrido de liquidez` | **false** |
| `Activar S2 · pullback a VWAP` | **false** |
| `Activar S3 · fade de bandas` | **false** |
| `Activar S4 · segundo movimiento tras noticias` | **false** |
| `Activar S5 · sesgo horario` | **false** |
| `Activar S6 · barrido con confirmación` | **false** |
| `Modo horario` | `Ventana NY` |
| Los cuatro frenos y el enfriamiento | 0 |

Con eso vuelve el camino de la v2.7 y la comparación contra `backtests/baseline-v2.7.csv` sigue teniendo sentido. **Sin eso, no.**

#### Tres cosas que cambian de peso al encenderlas todas

1. **Sin límite diario ≠ riesgo sin límite.** `pyramiding = 0` y el veto de posición abierta siguen permitiendo **una sola operación a la vez**, así que las señales se serializan en vez de acumularse. Lo que sí cambia es cuántas entran al día.
2. **El reparto de cupo y la regla de conflicto pasan a mandar de verdad.** Con una sola fuente nunca se usaban. Ahora `Prioridad` (que sigue en `FVG primero`) decide quién gana la vela, y `Conflictos de dirección` del panel dice cuántas veces dos fuentes se contradijeron: **si ese número es alto, se están estorbando y el problema no es el umbral de ninguna.**
3. **S2 y S3 dependen del clasificador de régimen.** Son excluyentes por construcción, pero si el clasificador pasa el día «sin clasificar» —menos de 12 velas— ninguna de las dos opera.

#### Y lo que no ha cambiado

Que las cinco son **hipótesis sin validar** y S6 también. Encenderlas las pone a medir, no las valida. Lo que decide si alguna vale es su propia fila de la tabla de resultados a 40 operaciones para el signo y 100 para la magnitud — y el caso que esta versión hace más probable es justamente el que la tabla existe para detectar: **un total positivo que viene de una sola fuente mientras las otras pierden.**

---

## v5.3 · Hacer que dispare y poder medirlo

Encargo 2. Partía del indicador v5.2, que daba **cero disparos en cinco días** con decenas de ARMADO. Esa máquina entra aquí como la fuente **S6**, apagada.

**Fase 1 completa. La fase 2 está pendiente de tus contadores** — ver el final de este apartado.

| Cambio | Motivo |
|---|---|
| ⚠️ **Formato de números con signo** (`F_SIGNO`) | `"+#.##"` hace que Pine añada el `+` que se le pide **además** del `-` del número: un −6,5 salía como `-+6.5`. Estaba en **ocho** sitios, o sea en todas las R negativas del script. No mueve operaciones, pero sí lo que leías de ellas |
| **CW10002 en `f_liqPrevia`** | Dos `ta.barssince` dentro de un ternario. `ta.barssince` lleva estado: si no se evalúa en cada vela, su historial sale mal **sin dar error**. El aviso que reportaste del v5.2 estaba aquí también |
| **CW10002 en el CHoCH de S6** | Introducido por mí al escribir S6, y encontrado al ampliar el verificador. Mismo patrón, misma corrección |
| **S6 · máquina ARMADO → DISPARO** | La del v5, como fuente más. La mide la misma tabla por estrategia que a S1-S5 |
| **S6 · SL saneado** (§1.2) | Mecha + colchón de spread en USD/oz; si queda más cerca de 0,8 ATR se **aleja**; por encima de 2,5 ATR no dispara. **Esto reduce el R:R, no lo aumenta**: el 13,6R del diagnóstico pasa a ~2,2R. Aquel R:R venía de un denominador casi nulo, dentro del spread |
| **S6 · sin rearmes en cascada** (§1.3) | Solo se arma con barrido nuevo o sin setup activo, y el campo `barBarrido` impide que el mismo barrido rearme en cada vela. Eso producía los racimos |
| **S6 · modo diagnóstico** (§1.1) | Los cinco filtros se evalúan **siempre**, sin cortocircuito, con contador de *bloquea* y de *exclusivo*. Con evaluación perezosa el primero de la cadena se queda todos los bloqueos. La cuenta se acumula en el setup y se reparte **al morir**, para que un ARMADO que vive quince velas no valga por quince bloqueos |
| **Tabla Registro** (§1.5) | Los últimos diez disparos operación a operación, con estadística por sesión y por a favor/contra el sesgo. La de resultados agrega; esta no, y es la que permite mirar una operación y decir que no debería haber salido |
| **E[R] desde el primer día, marcada PROVISIONAL** (criterio 7) | Para que el número exista y no se olvide mirarlo. Con 20 sesiones no se concluye nada, y por eso lleva la advertencia en vez de no estar |
| **Alerta de resultado al cerrar** | Tercer evento JSON tras «entrada». Sin él, un webhook sabe lo que se abrió pero nunca en qué acabó |
| **Comisión y slippage como inputs** (§1.6) | `strategy()` admite inputs. Cambiar de bróker ya no obliga a editar código |
| **Fondo semitransparente en las cuatro tablas** | El panel tiene que leerse sobre las velas sin taparlas |
| **Fusión de rótulos a menos de 0,3 ATR** | La regla de la v2.7 silenciaba el de menor prioridad, y eso pierde información: si el PDL y el mínimo de Asia están pegados, saber que **coinciden** vale más que ver solo uno |
| **Aviso de temporalidad dentro del panel** | Para que se vea en cualquier marco, no solo en el correcto |
| **Inputs de la fase 2, con los valores actuales** | Tercera vía de confirmación, ventana de CHoCH y TP1 de respaldo: implementados y apagados. La fase 2 solo cambiará los defectos que el contador exclusivo señale |

### Fase 2 · aplicada con los valores del encargo

**Leer esto antes que la tabla.** La fase 2 iba a decidirse con los contadores de 20 sesiones, y esos contadores no existen: aquí no se puede ejecutar Pine. Lo aplicado son **los valores que el encargo propone**, no valores medidos. El modo diagnóstico se queda encendido para comprobar cada relajación *a posteriori*, y los valores de la fase 1 están en esta tabla, así que revertir cualquiera es cambiar un número.

| Input | Fase 1 | Fase 2 | Nota |
|---|---|---|---|
| Score a favor del sesgo | 65 | **50** | El ARMADO del diagnóstico tenía 57: con 65 no pasaba, con 50 sí. Es la relajación de la que más depende la frecuencia |
| Score contra el sesgo | 65 | 65 | Sin cambio, como pedías |
| R:R mínimo | 1,5 | **1,2** | No es que 1,2 sea mejor: con el SL saneado los R:R bajan, así que 1,2 contra el SL nuevo se parece a 1,5 contra el viejo |
| Percentil de chop | 30 | **20** | |
| Rango de `enRango` | 3,0 ATR | **2,0 ATR** | |
| Usar filtro de chop | sí | sí | Sin cambio |
| Proximidad a zona | 0,5 ATR | **1,0 ATR** | Con 0,5 la zona tenía que estar casi tocando el precio |
| Memoria del CHoCH | 0 velas | **6 velas** | Con 0 se exigía el CHoCH en la vela **exacta** del ARMADO, que es casi imposible |
| TP1 de respaldo | no | **sí, 2R** | Rotulado «TP1 2R fijo»: un objetivo inventado y uno medido no se mezclan en la misma estadística sin saber cuál es cuál |
| Tercera vía de confirmación | no | **sí** | **La de más riesgo de las siete** |

**Por qué la de confirmación es la más arriesgada:** las otras seis ensanchan un umbral. Esta añade una **forma nueva** de confirmar, y una confirmación más laxa no es lo mismo que un umbral más bajo. Si la esperanza se hunde, hay que mirar esa primero.

**Recálculo del score en la vela de confirmación.** El del ARMADO describía la vela del *barrido*, y entre las dos pueden pasar doce velas. Dos de sus componentes son propiedades de la vela gatillo —desplazamiento y volumen— y congelarlos medía la vela equivocada; el de R:R se mide ahora contra la entrada real. No se toca la función ni sus pesos: la misma fórmula, otra vela. Si la zona murió entre medias se conserva el score del ARMADO, porque perder el setup por un dato que ya no existe sería castigarlo dos veces.

### Revisión de S6 · tres fallos encontrados al releerlo

1. ⚠️ **Faltaba la invalidación por SL.** El v5 mataba el ARMADO por caducidad **o** por cierre más allá del SL, y solo porté la caducidad. Un ARMADO con el SL ya perforado no es un setup esperando confirmación: es un setup equivocado, y dejarlo vivo consigue que dispare más tarde en el peor sitio.
2. **Un barrido podía armar dos veces.** `mismoBar` solo comparaba contra el setup vivo, así que uno que caducaba mientras su barrido seguía reciente rearmaba sobre el mismo barrido. Con los defectos no ocurre (memoria 6, caducidad 12), pero sí al subir la memoria por encima de la caducidad.
3. **El criterio 2 no se podía comprobar sumando.** Los contadores por filtro no sirven, porque un setup bloqueado por dos cuenta en los dos. Ahora hay un contador de **setups** resueltos y el panel publica la cuadratura con un ✔ o un ✘.

### Lo que sigue pendiente, y de quién

**Tuyo:** los criterios 1 a 5 requieren ejecutar Pine. S6 viene **apagada** —eso preserva la garantía de regresión del encargo 1— así que el criterio 3 se mide encendiendo S6 y dejando el resto en sus defectos.

**Y lo importante:** la fase 2 está aplicada pero **no validada**. Lo que decide si cada relajación era correcta no es que ahora dispare, es la E[R] de la tabla Registro a 100 operaciones.

### Una advertencia sobre el objetivo de frecuencia


Tu propia nota lo dice y conviene repetirlo aquí: *«2 a 6 disparos por día siempre se alcanza relajando lo suficiente»*. Con score 30, R:R 1,0 y el chop apagado dispararía diez veces al día sin haber encontrado nada. La frecuencia es un medio para acumular muestra, no el resultado.

---

## v2.9 · Un solo Pine

Absorbe del indicador v5.2 lo que aportaba y **retira el segundo fichero**. Un `strategy()` y un `indicator()` no pueden ser el mismo script, así que «todo en uno» obligaba a que el strategy se quedara con todo.

| Cambio | Motivo |
|---|---|
| **Filtro de chop por percentil de ATR** (apagado) | El de hora plana mide el rango **medio** de cada hora; este mide la volatilidad de **hoy**. Un día muerto a una hora normalmente buena solo lo caza el segundo. Reutiliza la cola de 20 sesiones que ya existía, para no tener dos sitios con el mismo dato |
| **Marcadores de tres niveles** | Punto, rombo, flecha, derivados de la **misma** capa de acción que la etiqueta y la tabla, así que no pueden contradecirse |
| **Resultado escrito en la etiqueta al cerrar** | Aquí es mejor que en el indicador: allí era simulado contra TP1/SL, aquí es el PnL real con comisión y slippage dentro |
| **Payload JSON de alerta** | Lleva la estrategia que originó la señal, así que un bot puede dimensionar distinto según la fuente |
| **Desactivación por esperanza negativa** (apagada) | El tooltip avisa de lo importante: es una decisión tomada **dentro** del backtest con sus propios datos, así que mejora el resultado por construcción y no es extrapolable |
| **Lo que NO se trajo** | El score y el sesgo del v5 son implementaciones **alternativas** de cosas que el strategy ya hace. Elegir una es una decisión de trading, no de refactor |

---

## v2.8 · Cinco fuentes de señal nuevas (S1 a S5)

Todas apagadas. Documento propio: `docs/ESTRATEGIAS_S1_S8.md`. Encargo archivado en `docs/ENCARGO_S1_S5.md`.

| Cambio | Motivo |
|---|---|
| **Instrumentación primero** | Añadir cinco estrategias a la vez multiplica el riesgo de encontrar ruido, y un total positivo puede venir de una sola fuente. Si la medición no está en pie antes, no hay forma de saberlo |
| **Capa de candidatos** | Las cinco no reimplementan la ejecución: dejan un candidato y el resolutor elige. Eso es lo que sostiene la regresión y lo que hace que pasen por **todos** los vetos existentes |
| **Clasificador de régimen** | Sin él, S2 y S3 se anulan. Por defecto rango del día contra ADR, porque se conoce a cada vela y es adimensional. **Añadido mío declarado**: exige además desplazamiento neto, porque el rango solo llama «tendencia» a un día de bandazos que cierra donde abrió |
| **S2 en 5m y no en 1m** | Pedir 1m desde 5m devuelve solo la última vela de 1m de cada una, no la secuencia. Coste declarado: el toque se detecta hasta 4 minutos más tarde y el stop sale 1-3 USD/oz más ancho |
| **Reparto de cupo y conflictos** | Prioridad en cuatro modos y cupo propio por estrategia. Dos fuentes en sentidos opuestos: no se opera ninguna, porque dos sistemas que se contradicen no es una señal débil, es ausencia de señal |
| **S5 mide la hipótesis en vez de aplicarla** | Acumula la deriva por hora en tus datos y usa su signo. Si el oro no sube en Asia en tus datos, el filtro no se lo inventa |

---

## v2.7 · Limpieza visual, y dos bugs de niveles

| Cambio | Motivo |
|---|---|
| **HOD/LOD desde las 18:00 ET** | Lo rotulado como «máximo de sesión» era el extremo de la **ventana**: con `Ventana NY` un máximo de madrugada no aparecía. Sin impacto en operaciones |
| ⚠️ **PDH/PDL del día de trading anterior** | Se pedían al diario del exchange, cuyo corte no es el día del script. **Lo leen tres reglas**, así que invalida la línea base v2.2. Detalle en `docs/TRASPASO_MGC.md` §5b |
| **Relleno solo en la zona activa más cercana** | El relleno es lo que satura y lo que hace que todas parezcan igual de importantes |
| **Rótulos de 40 caracteres** | La caja destacada decía 64. Lo largo al tooltip, que no ocupa píxeles hasta que se pide |
| **Tope de 4 líneas de nivel** | Con los números redondos en el mismo presupuesto: si no contaran, cuatro de ellos se comen el gráfico |
| **Filas de tabla sin dato, ocultas** | Y nada de cifras por debajo de 30 operaciones: un 60 % sobre ocho no es un 60 % |

---

## v2.6 · Varias operaciones diarias

Decisiones del usuario, no recomendaciones: 24 h por defecto, cupo diario 3, señales al cierre de vela. Revierte a propósito la C5 de la v2.2. Frenos diarios y enfriamiento disponibles pero **a 0**.

---

## v2.3 a v2.5

- **v2.3-1 · bug de repintado**: el ATR dentro de `f_htfFvg` no estaba desplazado bajo `lookahead_on`. Como alimenta el test de anchura mínima, **el criterio que decidía si existía un hueco repintaba él mismo**.
- **v2.3 / v2.4 · paridad**: exportador acotado, inventario de zonas vivas, purga FIFO registrada, especificación de `detectar.py`.
- **v2.5 · filtro de hora plana**: mide el rango de cada hora sobre el propio gráfico, para poder operar 24 h sin que una hora muerta se lleve la operación del día.

---

## v2.2 · Correcciones previas a la primera ejecución

- **C1**: en modo 24 h la bandera de cierre forzoso quedaba abierta hasta medianoche, así que **no había entradas entre las 18:00 y las 23:59**. El «24 h» real era 00:00-16:45.
- **C2**: las siete llamadas a `request.security` pasan a `lookahead_on` con la expresión desplazada `[1]`, que es el idioma que **no** repinta.
- **C3**: cupo de objetos. Sin cola propia, Pine borraba las etiquetas más antiguas, que son los pools creados en la primera vela.
- **C4**: protocolo de línea base en `backtests/README.md`. La anterior no servía: la versión de partida **no operaba nunca**.

---

## Antes de la v2.2 · los bugs que habrían impedido operar

Los tres primeros son los que convierten «no da señales» en «no puede dar señales»:

1. **La estrategia no habría operado jamás**: la máquina de estados marcaba la zona consumida al perforar el 50 % **antes** de que la sección de entrada la evaluara.
2. **Toda zona nacía ya mitigada**: el borde del hueco *es* el extremo de la vela que lo crea, así que el test de toque se cumplía por definición.
3. **El BOS de continuación era inalcanzable** por el encadenado de condiciones.
4. Zonas invertidas inoperables, barridos de sesión que no podían disparar, filtro de holgura que ahogaba las señales, disparo sobre-restringido al 50 % exacto.

El historial completo, con el razonamiento de cada uno, está en `docs/TRASPASO_MGC.md` §5.
