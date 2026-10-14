# Encargo original · cinco estrategias nuevas (S1 a S5)

> **Nota de procedencia, añadida al archivar el encargo.** Todo lo que sigue a la línea divisoria es el texto del encargo tal como se recibió, sin editar. Se archiva porque era la única de las especificaciones seguidas que vivía solo en el chat, y porque las decisiones que delegaba («propón uno medible», «implementa la que argumentes mejor», «define qué pasa si…») solo se pueden auditar con el enunciado delante.
>
> **Estado: implementado.** Commits `v2.8-1` a `v2.8-9` sobre `pine/MGC_FVG_ORB.pine`. La respuesta punto por punto —qué se decidió, qué se delegó, qué quedó sin validar y qué no se pudo comprobar— está en **`docs/ESTRATEGIAS_S1_S8.md`**.
>
> **Las tres preguntas que el encargo invitaba a hacer, y sus respuestas:**
>
> | Pregunta | Respuesta |
> |---|---|
> | ¿Sobre qué fichero? El encargo dice «el indicador», pero pide cupo diario, lista del Strategy Tester y comisión/slippage, que solo existen en el `strategy()` | «Tendría que ser un único Pine desde siempre» → se integró en `pine/MGC_FVG_ORB.pine` |
> | ¿Qué cuenta como «pendiente definida» del VWAP en S2? | Variación en N velas contra ATR: `(VWAP − VWAP[N]) / ATR` |
> | Pine no puede escribir ficheros: ¿cómo se materializa el «exportable a CSV»? | Pine Logs, una línea por operación cerrada |
>
> **Un requisito que no se pudo cumplir y conviene que quede escrito:** «Exporta la lista antes y después y compárala». El entorno donde se escribió el código no ejecuta Pine, así que esa comparación **no se hizo**. En su lugar se da un argumento estructural de por qué la lista no puede cambiar con los defectos (§7.5 de `ESTRATEGIAS_S1_S8.md`). La comparación sigue pendiente y es del usuario.

---

Trabajo sobre el indicador Pine v6 de MGC (5 minutos) que ya existe en el repo.
Quiero integrar cinco estrategias nuevas como fuentes de señal adicionales,
conviviendo con la lógica de FVG + estructura que ya está implementada.

NO reescribas el script desde cero. Integra, y justifica cada decisión.

═══════════════════════════════════════════════════════════════════
LAS CINCO ESTRATEGIAS
═══════════════════════════════════════════════════════════════════

S1 · BARRIDO DE LIQUIDEZ (falsa ruptura)
→ El precio supera el máximo o mínimo del día anterior, de Asia o de Londres,
  pero la vela de 5m cierra de vuelta dentro del rango
→ Entrada contra la ruptura, al cierre de esa vela
→ Stop más allá del extremo del barrido, con margen configurable
→ Objetivo: VWAP del día o R fijo, buscando 1,5 a 2R
→ Ventana 08:00 a 11:30 ET, máximo una operación por lado y día
→ Filtros necesarios: penetración mínima para que cuente como barrido,
  penetración máxima por encima de la cual es ruptura real y no se opera,
  y número máximo de cierres fuera del nivel antes de volver (más cierres
  fuera significa aceptación del precio, no barrido)

S2 · PULLBACK A VWAP EN DÍA TENDENCIAL
→ Pasados 30 a 60 minutos desde la apertura de NY
→ Precio por encima (o por debajo) de un VWAP con pendiente definida
→ Entrada en el retroceso al VWAP o a la banda de 1σ
→ Requiere definir qué cuenta como "pendiente": pídeme el criterio o
  propón uno medible (ángulo, variación en N velas, posición relativa)

S3 · FADE DE LAS BANDAS ±2σ, SOLO EN DÍAS DE RANGO
→ Complementaria de S2 y mutuamente excluyente con ella

S4 · SEGUNDO MOVIMIENTO TRAS NOTICIAS
→ No se entra en el primer minuto. Se espera de 5 a 15 minutos
→ Se opera la ruptura, o el fallo, del rango inicial de 5 minutos
→ Lista de horas de publicación configurable (CPI, NFP, FOMC)

S5 · SESGO HORARIO (filtro, no sistema)
→ Hipótesis: el oro sube en horario asiático y cae el resto del día
→ Se usa para inclinar la dirección de S1 y S2, nunca como disparador
→ Implementar como modificador de puntuación, desactivable

═══════════════════════════════════════════════════════════════════
CONFLICTOS QUE TIENES QUE RESOLVER EXPLÍCITAMENTE
═══════════════════════════════════════════════════════════════════

1. S2 y S3 se anulan entre sí sin un filtro de régimen
   Necesito un clasificador tendencia/rango que decida cuál de las dos está
   activa cada día. Propón dos o tres opciones (ADX, rango acumulado contra
   múltiplo de ATR, posición del precio respecto al VWAP a lo largo del día),
   implementa la que argumentes mejor y deja las otras como input.
   Sin este filtro, no implementes ni S2 ni S3.

2. S2 pide señal en 1 minuto, pero el gráfico es de 5
   O se resuelve con request.security a 1m (y entonces explica cómo evitas
   el repintado), o se adapta la entrada a 5m y dices qué se pierde.
   Elige una y justifícala.

3. Reparto de cupo entre estrategias
   El script tiene límite de operaciones diarias. Con seis fuentes de señal
   (las cinco nuevas más la de FVG), la primera que dispare se lleva el cupo.
   Propón un mecanismo de prioridad o de cupo por estrategia. Por defecto,
   el comportamiento actual no debe cambiar.

4. Solapamiento de señales en la misma vela
   Define qué pasa si S1 y S3 disparan a la vez en direcciones opuestas.

═══════════════════════════════════════════════════════════════════
INSTRUMENTACIÓN (la parte más importante)
═══════════════════════════════════════════════════════════════════

Cada señal debe quedar etiquetada con la estrategia que la originó, y esa
etiqueta tiene que sobrevivir hasta el cierre de la operación.

Implementa una tabla de resultados por estrategia, visible en barstate.islast:
→ Número de operaciones, win rate, esperanza en R, R total
→ Drawdown máximo de esa estrategia por separado
→ Aviso "muestra insuficiente" cuando n < 40, para que no se lea como
  conclusión
→ Exportable a CSV

Motivo: añadir cinco estrategias a la vez multiplica el riesgo de encontrar
ruido. Sin medición por separado, un resultado global positivo puede venir
de una sola estrategia mientras las otras cuatro pierden dinero, y no habría
forma de saberlo.

═══════════════════════════════════════════════════════════════════
RESTRICCIONES
═══════════════════════════════════════════════════════════════════

→ Pine Script v6
→ Sin repintado: toda decisión sobre velas confirmadas. Si usas
  request.security, explica el idioma que empleas y por qué no repinta
→ Todos los inputs nuevos DESACTIVADOS por defecto
→ Ningún cambio puede alterar la lista de operaciones del Strategy Tester
  con la configuración actual. Exporta la lista antes y después y compárala
→ Comisión 2 USD round turn, slippage 1 tick
→ Parámetros de precio en unidades de precio (USD/oz), no en ticks, para que
  el script valga igual en MGC que en XAUUSD

═══════════════════════════════════════════════════════════════════
CONTEXTO QUE AFECTA A LA VALIDACIÓN
═══════════════════════════════════════════════════════════════════

→ MGC tiene volumen real, así que su VWAP es fiable. Mis datos históricos de
  backtest son de XAUUSD spot de Dukascopy, donde el volumen es de ticks y el
  VWAP es solo una aproximación. Esto afecta a S2 y S3: adviértelo en el
  código y en la documentación.

→ Antes de activar S4 tengo que comprobar si mi prop firm restringe operar
  noticias. Deja la estrategia implementada pero con un aviso en el tooltip.

→ S1 es el espejo del ORB que ya medí: si la ruptura tiene expectativa
  negativa, su fallo podría ser donde está la ventaja. Es una inferencia sin
  comprobar, no un hecho. No la trates como validada en los comentarios.

═══════════════════════════════════════════════════════════════════
ENTREGABLE
═══════════════════════════════════════════════════════════════════

1. El script integrado, comentado en español
2. Un documento que explique cada estrategia, sus parámetros y qué está
   validado frente a qué es hipótesis
3. Al final: qué métricas mirar, cuántas operaciones por estrategia hacen
   falta para que el resultado signifique algo, y qué valores indicarían
   ausencia de ventaja

Pregúntame lo que necesites antes de escribir código. Prefiero responder tres
preguntas que recibir cinco estrategias con criterios que yo no he definido.

---

## Trazabilidad · cada punto del encargo y dónde quedó

| Punto del encargo | Dónde está |
|---|---|
| S1 barrido de liquidez, con los tres filtros | `v2.8-4`, grupo de inputs `S1 · Barrido de liquidez` · doc §1 |
| S2 pullback a VWAP, con el criterio de pendiente | `v2.8-5`, grupo `S2 · Pullback a VWAP` · doc §2 |
| S3 fade de bandas | `v2.8-5`, grupo `S3 · Fade de bandas` · doc §3 |
| S4 segundo movimiento tras noticias | `v2.8-6`, grupo `S4 · Segundo movimiento tras noticias` · doc §5 |
| S5 sesgo horario como modificador | `v2.8-7`, grupo `S5 · Sesgo horario` · doc §6 |
| Conflicto 1 · clasificador de régimen | `v2.8-2`, grupo `Régimen de mercado` · doc §4 |
| Conflicto 2 · 1 minuto contra 5 | `v2.8-5` · doc §2, con el coste declarado |
| Conflicto 3 · reparto de cupo | `v2.8-3`, grupo `Reparto de cupo` · doc §7.3 |
| Conflicto 4 · señales opuestas | `v2.8-3`, input `Dos estrategias en sentidos opuestos` · doc §7.4 |
| Instrumentación · etiqueta que sobrevive | `v2.8-1`, campo `Operacion.estrategia` |
| Instrumentación · tabla por estrategia | `v2.8-1`, 14 grupos en la tabla de resultados · doc §8 |
| Instrumentación · aviso de muestra insuficiente | `v2.8-1`, heredado de la v2.7: nada por debajo de 30, gris hasta 40 |
| Instrumentación · exportable a CSV | `v2.8-1`, registro `O` en Pine Logs |
| Inputs nuevos desactivados por defecto | Verificado input por input: diez defectos nuevos, todos `false`, `0` o `FVG primero` |
| Precios en USD/oz, no en ticks | Todos los parámetros de las cinco estrategias · doc §0 y cabecera de la sección 7b del script |
| Comisión 2 USD round turn, slippage 1 tick | Ya estaban en la declaración `strategy()` desde la v2; sin cambios |
| Aviso de VWAP aproximado en spot | Tooltips de `i_s2On` y `i_s3On` · doc §6 |
| Aviso de prop firm en S4 | Tooltip de `i_s4On` · doc §5 |
| S1 no tratada como validada | Cabecera del grupo S1 en el script, cabecera del fichero y doc §0 |
| Entregable 3 · métricas, muestra y ausencia de ventaja | doc §9 |
| «Exporta la lista antes y después y compárala» | **NO HECHO.** No hay TradingView en el entorno; argumento estructural en doc §7.5. Pendiente del usuario |
