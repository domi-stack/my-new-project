# CHANGELOG · MGC FVG + Estructura

Un solo fichero: `pine/MGC_FVG_ORB.pine`. Cada entrada dice **qué** cambió y **por qué**, que es lo que importa seis meses después.

Convención: ⚠️ marca lo que **mueve la lista de operaciones** del Strategy Tester. Todo lo demás es dibujo, medición o inputs apagados.

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

Todas apagadas. Documento propio: `docs/ESTRATEGIAS_S1_S5.md`. Encargo archivado en `docs/ENCARGO_S1_S5.md`.

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
