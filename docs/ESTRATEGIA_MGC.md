# MGC · Estrategia FVG + Estructura de mercado (5 minutos)

Documento de referencia de `pine/MGC_FVG_ORB.pine`. Pine Script v6, `strategy()`, para Micro Gold Futures en velas de 5 minutos.

Generado desde el código en su estado actual (832 líneas, 42 inputs, 10 secciones).

---

## 1. Instrumento y aritmética del riesgo

| Dato | Valor |
|------|-------|
| Contrato | MGC (Micro Gold Futures) |
| 1 punto | 10 USD por contrato |
| 1 tick | 0,10 puntos = 1 USD |
| Riesgo objetivo | 150 USD por operación |
| Beneficio objetivo | 300 USD por operación |
| Comisión | 1 USD por orden = 2 USD round turn |
| Slippage modelado | 1 tick |

**La restricción que condiciona todo el diseño.** No se puede operar menos de 1 contrato. Con 10 USD por punto y 150 USD de riesgo, el stop tiene un **techo duro de 15 puntos**:

```
150 USD / (10 USD/punto × 1 contrato) = 15 puntos
```

De ahí se derivan dos consecuencias que no son opcionales:

- Un stop estructural más ancho de 15 puntos **no se recorta**: la operación se descarta. Recortarlo dejaría el stop dentro del ruido que debía absorber, y entonces salta antes de que la idea se invalide de verdad.
- El dimensionamiento solo escala **hacia arriba**. Con un stop de 7,5 puntos caben 2 contratos sin pasar de 150 USD. Nunca hacia abajo, porque 1 contrato es el suelo.

El objetivo de 300 USD son 30 puntos con 1 contrato, es decir **2R**. Con el ATR(14) de 5m alrededor de 4,5 puntos, eso son **6,7×ATR** dentro de una ventana de 3,5 horas. Está en el límite de lo que el instrumento entrega en una sesión: espera un porcentaje de acierto bajo y dependiente de pocas operaciones grandes.

---

## 2. Ventana de operativa

Las entradas solo ocurren dentro de la ventana; la posición puede correr más allá, pero nunca pasada la hora de cierre forzoso, que manda sobre stop y objetivo.

Dos anclajes seleccionables:

| Anclaje | Ventana | Cierre forzoso |
|---------|---------|----------------|
| Reloj de Madrid | 15:30-19:00 `Europe/Madrid` | 21:00 Madrid |
| Apertura de NY (**por defecto**) | 09:30-13:00 `America/New_York` | 15:00 NY |

**Por qué existen los dos.** Europa y EE.UU. cambian de hora en fechas distintas. Entre el **25 de octubre y el 1 de noviembre de 2026**, Madrid está en UTC+1 con Nueva York todavía en UTC-4: esa semana, las 15:30 de Madrid son las 10:30 de Nueva York, una hora después de la apertura. Anclar a la apertura mantiene la ventana sobre la sesión que mueve el oro; anclar a Madrid es más cómodo para operar en vivo. La detección usa `time(timeframe.period, sesión, zona)`, que gestiona el horario de verano de cada zona por su cuenta.

Máximo **1 operación al día** (configurable), con el contador reiniciado por día natural de la zona de anclaje.

---

## 3. Los dos disparadores de entrada

Independientes. El FVG tiene prioridad cuando ambos coinciden en la misma vela, porque su nivel es más preciso.

### 3.1 FVG en su 50%

Un Fair Value Gap es un imbalance de tres velas:

- **Alcista** (soporte): `low[0] > high[2]`. La zona es `[high[2], low[0]]`.
- **Bajista** (resistencia): `high[0] < low[2]`. La zona es `[high[0], low[2]]`.

Se exige una **anchura mínima de 0,5×ATR**: un hueco más estrecho que media vela media no sirve como zona de entrada.

Se detectan en el marco actual (5m) y, vía `request.security`, en el intermedio (1H) y el mayor (4H).

**Máquina de estados de cada zona:**

| Estado | Significado | ¿Operable? |
|--------|-------------|-----------|
| Virgen | Nunca tocada por el precio | Sí |
| Mitigada parcial | Tocada, con el 50% intacto | Sí |
| Consumida | 50% perforado | No, en su dirección original |
| Invertida | Rota al otro lado + margen | Sí, cambiando de signo |

La **inversión** es lo que pediste: un FVG bajista que se rompe al alza cambia de dirección, vuelve al estado virgen y pasa a operarse como soporte.

**Disparo:** configurable, y **ya no es "cierre en el 50%"**.

| Modo | Condición | Frecuencia |
|---|---|---|
| **Cierre dentro de la zona** (por defecto) | Primer cierre dentro de la banda entre el borde cercano y el 50% | Bastantes más señales |
| Cierre en el 50% | El cierre debe alcanzar el 50% exacto | Mucho más restrictivo |

El defecto cambió porque la elección original fue "cierre de vela dentro de la zona" y se había implementado como el 50% exacto, que es una condición mucho más estrecha: la mayoría de los toques se quedan a medio camino y nunca cierran pasado el medio, así que la zona moría sin disparar. Era la causa principal de la escasez de señales.

En los dos modos la zona sigue muriendo al perforar su 50%. Una zona dispara **una sola vez**.

> **Pendiente de medir**: las dos variantes hay que compararlas en el Strategy Tester. Entrar más arriba en la zona aleja el stop del swing, así que parte de las señales que gana el modo ancho las puede descartar el techo de 15 puntos. El contador `stop > techo` de la tabla de diagnóstico dice cuántas.

**Invalidación:** cierre al otro lado del borde lejano más un margen de **0,25×ATR**. Es adaptativo a propósito: un margen fijo queda ancho con ATR a 3 puntos y corto con ATR a 7.

### 3.2 Barrido de liquidez

Mecha que supera un extremo previo y **cierra de vuelta dentro**. Barrer mínimos genera **COMPRA**, barrer máximos genera **VENTA**: la mecha ha cazado los stops del lado contrario y el cierre de vuelta dice que no había continuación.

Extremos considerados, configurables:

| Opción | Niveles |
|--------|---------|
| Solo día anterior | Máximo y mínimo del día anterior |
| Día anterior + sesión (por defecto) | Lo anterior más los extremos de la sesión en curso |
| Todo | Lo anterior más los swings confirmados |

El máximo y el mínimo del día anterior son los niveles con más liquidez acumulada, y son los que importan más.

**Stop:** la propia mecha del barrido más el colchón. Si el precio vuelve más allá de ella, la lectura del barrido era falsa.

> **Advertencia sin resolver.** Las mechas de barrido son largas por naturaleza, así que `cierre − mínimo` pasa de 15 puntos con facilidad y el techo de riesgo descarta la operación. El contador `stop>15pts` de la tabla te dirá cuántas se pierden por esto. Si sale alto, hay que replantear dónde va ese stop; no se ha tocado por adelantado porque sería especular sin datos.

---

## 4. Estructura de mercado

**Swings** por pivotes configurables (5 a cada lado en 5m, 3 en marcos superiores). El pivote confirma con ese retardo por construcción, que es precisamente lo que hace que la estructura no repinte.

**Sesgo** por marco, calculado sobre los dos últimos swings de cada lado:

- **Alcista**: máximos ascendentes **y** mínimos ascendentes (HH + HL)
- **Bajista**: máximos descendentes **y** mínimos descendentes (LH + LL)
- **Rango**: cualquier otra combinación

Se muestra por separado para 5m, 1H y 4H.

**BOS** (ruptura de estructura): ruptura en la dirección de la tendencia vigente, o sea continuación.
**CHoCH** (cambio de carácter): primera ruptura **contra** la tendencia vigente.

Cada nivel de swing solo puede romperse una vez: se recuerda el último roto para no repetir la señal en cada vela mientras el precio siga fuera.

---

## 5. Niveles de sesión y VWAP

- Máximo y mínimo de la sesión, actualizados en vivo
- Máximo y mínimo del día anterior (vela diaria ya cerrada)
- Apertura de la sesión
- VWAP de sesión con bandas de desviación

**Las reglas asociadas**, porque ningún indicador se dibuja sin una:

- El **VWAP filtra dirección**: largos solo con el cierre por encima, cortos por debajo.
- Las **bandas rechazan entradas extendidas** más allá de ±σ, para no perseguir precio.
- Ambos se aplican **solo a las entradas por FVG** salvo que se pidan también para los barridos. Un barrido de mínimos ocurre con el precio hundido, por debajo del VWAP y fuera de la banda inferior: exigirle el lado correcto del VWAP eliminaría exactamente las señales que ese disparador busca. Las entradas por FVG sí son de continuación y ahí el filtro tiene sentido.

---

## 6. La regla de conflicto entre marcos

El caso para el que se diseñó: estructura alcista en 5m con CHoCH confirmado, dentro de una estructura bajista en 4H, con un FVG bajista de 4H sin mitigar por encima.

| Modo | Regla | Coste |
|------|-------|-------|
| **A** | Solo a favor del marco mayor | Pocas señales, y te pone a contramano justo cuando el marco mayor gira: el CHoCH del 5m suele ser el primer síntoma de ese giro |
| **B** (por defecto) | Opera el marco menor hacia el siguiente nivel del mayor, exigiendo holgura mínima en múltiplos de riesgo | Descarta setups sin recorrido, que es el objetivo. No exige alineación, así que acepta operaciones contra el 4H |
| **C** | Alineación de los tres marcos | Muy restrictivo, pocas señales al mes, y entrada tardía en el tramo |

**Por qué el modo B necesita la holgura.** Poner el objetivo en el nivel del marco mayor sin más produce esperanza negativa cuando ese nivel está cerca: arriesgarías 150 USD para ganar 120. Con la holgura por defecto de **2R**, si el nivel no está a 30 puntos o más no hay operación, y el nivel funciona como filtro de holgura en vez de como objetivo. Por debajo de 2R el nivel pasa a ser el objetivo real y el ratio empeora.

**Qué cuenta como obstrucción** (solo en modo B):

| Opción | Niveles que obstruyen |
|--------|----------------------|
| Solo zonas del marco mayor (por defecto) | FVG de 1H y 4H sin mitigar, en dirección opuesta |
| + máx/mín del día anterior | Lo anterior más PDH/PDL |
| + extremos de sesión | Lo anterior más el máximo/mínimo de la sesión |

> **Cuidado con la última opción.** El máximo de la sesión está casi siempre a 5-20 puntos del precio, así que tratarlo como pared hace que la holgura de 2R vete casi cualquier entrada en retroceso — y las entradas en FVG son retrocesos por definición. Romper el máximo de la sesión es precisamente lo que ocurre en un día de tendencia, no una pared. Esta era la causa de que salieran tan pocas señales antes de corregirlo.

En caso de **solape entre zonas** manda el marco mayor: 4H > 1H > 5m, y a igualdad de marco, la más cercana al precio.

---

## 7. Garantías de no repintado

- Toda decisión se toma sobre velas cerradas (`barstate.isconfirmed`), y `calc_on_every_tick = false`.
- Los pivotes confirman con su retardo inherente.
- Todas las llamadas a marcos superiores usan `lookahead_off` y leen velas **ya cerradas en su propio marco** (desplazamiento `[1]`/`[3]`), así que un FVG de 4H aparece cuando existe y no antes.
- Stops y objetivos se redondean a la rejilla de ticks **en contra**, para que el backtest no dé por alcanzado un nivel que en real no se habría tocado.

**Una salvedad honesta:** `process_orders_on_close = true` hace que la entrada se ejecute al cierre de la vela que dispara. En real el relleno llegaría en la apertura siguiente o a un tick o dos de distancia; el slippage de 1 tick lo aproxima, pero no es idéntico.

---

## 8. Tabla de diagnóstico

Se dibuja arriba a la derecha y muestra:

- Modo de conflicto activo
- Sesgo de 5m, 1H y 4H
- FVG operable más cercano por arriba y por abajo, con su distancia **en ATR**
- ATR actual en puntos
- Operaciones del día sobre el límite
- Estado de la ventana: abierta, cerrada o cierre forzoso
- Zonas activas sobre el total en memoria
- **Setups vistos → operados**
- **Vetados por**: ventana/límite, MTF, VWAP, barrido, stop>15pts, holgura

Las dos últimas filas son las importantes cuando la queja es "salen pocas señales": **el número más grande nombra el filtro que ahoga**. Convierte una sospecha en un dato.

---

## 9. Referencia de inputs

### Instrumento
| Input | Defecto |
|-------|---------|
| USD por punto | 10.0 |
| Tamaño de tick (pts) | 0.10 |

### Ventana de operativa
| Input | Defecto |
|-------|---------|
| Anclaje de la ventana | Apertura de NY |
| Ventana (hora de Madrid) | 1530-1900 |
| Ventana (hora de NY) | 0930-1300 |
| Hora de cierre forzoso (Madrid) | 21 |
| Hora de cierre forzoso (NY) | 15 |
| Máximo de operaciones al día | 1 |

### Fair Value Gaps
| Input | Defecto |
|-------|---------|
| Periodo del ATR | 14 |
| Anchura mínima del FVG (x ATR) | 0.5 |
| Margen de invalidación (x ATR) | 0.25 |
| Detectar FVG en el marco intermedio | sí |
| Detectar FVG en el marco mayor | sí |
| Marco intermedio | 60 |
| Marco mayor | 240 |
| Máximo de zonas en memoria | 60 |

### Estructura de mercado
| Input | Defecto |
|-------|---------|
| Pivote izquierda / derecha (5m) | 5 / 5 |
| Pivote izquierda / derecha (marcos superiores) | 3 / 3 |

### Riesgo y objetivo
| Input | Defecto |
|-------|---------|
| Riesgo por operación (USD) | 150.0 |
| Objetivo por operación (USD) | 300.0 |
| Techo del stop (puntos) | 15.0 |
| Referencia del stop | Swing |
| Colchón del stop (x ATR) | 0.30 |
| Escalar contratos si el stop es ajustado | sí |

### Conflicto entre marcos
| Input | Defecto |
|-------|---------|
| Regla de conflicto | B · Hasta el nivel del marco mayor |
| Holgura mínima al nivel del marco mayor (R) | 2.0 |
| Qué obstruye el recorrido (modo B) | Solo zonas del marco mayor |

### Filtros
| Input | Defecto |
|-------|---------|
| Exigir el lado correcto del VWAP de sesión | sí |
| Desviaciones de las bandas de VWAP | 1.0 |
| Rechazar entradas fuera de la banda de VWAP | sí |
| Exigir barrido de liquidez previo | no |
| Velas de memoria del barrido | 12 |

### Entradas por barrido de liquidez
| Input | Defecto |
|-------|---------|
| Operar los barridos como entrada | sí |
| Qué extremos se consideran barridos | Día anterior + sesión |
| Aplicar los filtros de VWAP a los barridos | no |

### Visual
| Input | Defecto |
|-------|---------|
| Dibujar zonas / niveles / VWAP | sí |
| Mostrar tabla de diagnóstico | sí |
| Etiquetas COMPRA / VENTA | sí |

---

## 10. Qué mirar en el Strategy Tester

Por orden de importancia:

1. **Profit factor** y **esperanza por operación en R**. Por debajo de 0,15R no hay negocio después de costes.
2. **Máximo drawdown en R**, no en porcentaje. Una cuenta de evaluación muere por drawdown, no por falta de beneficio. Si el peor tramo pasa de 4-5R seguidos en contra, la evaluación se cae antes de llegar al objetivo.
3. **Racha perdedora máxima**. Con una operación al día, una racha de ocho son ocho días seguidos en rojo. Decide si lo aguantas antes de empezar.
4. **Porcentaje de operaciones cerradas por cierre forzoso**. Si supera el 30%, la ventana es demasiado corta para el objetivo que se pide.

**Tamaño de muestra:** hacen falta **40 operaciones para que el signo de la esperanza no sea ruido y 100 para fiarse de la magnitud**. Con filtros restrictivos y una operación diaria, eso son entre cuatro y diez meses de datos. Cualquier conclusión con 15 operaciones es una anécdota.

**Señales de que no hay ventaja:**

- Profit factor entre 0,9 y 1,1 con más de 60 operaciones: es ruido, no señal.
- Esperanza que se vuelve negativa al quitar las tres mejores operaciones: medías suerte.
- Win rate por encima del 70% con profit factor bajo: cortas ganancias y dejas correr pérdidas.
- Resultados que se desploman al mover el pivote de 5 a 6, o el ATR de 14 a 15: sobreajuste al ruido.

---

## 11. Limitaciones conocidas

Tres cosas que no están resueltas y conviene tener delante:

1. **El techo de 15 puntos frente a los barridos.** Es muy probable que descarte una parte grande de los barridos por la anchura natural de sus mechas. Mira el contador antes de sacar conclusiones sobre ese disparador.
2. **El modo B acepta operar contra el marco mayor.** No exige alineación, así que tomará barridos al alza dentro de una estructura bajista de 4H. Ese es el subconjunto de peor calidad del sistema. Si el resultado global sale malo, prueba el modo A antes de tocar nada más.
3. **2R en 3,5 horas es ambicioso.** 30 puntos son 6,7×ATR. Si el porcentaje de cierres forzosos sale alto, el problema no es el filtro: es el objetivo. Ahí la conversación es sobre salidas parciales, que cambiaría la especificación de la cuenta.
