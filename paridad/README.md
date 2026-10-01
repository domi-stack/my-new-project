# Prueba de paridad Pine ↔ Python

Esto es lo que desbloquea la calibración. V2.1 §1.2 lo exige y es categórico: *"Si no coinciden, no se sigue. Una calibración sobre zonas distintas de las que dibuja el script no vale nada."*

El bloqueo es que esta prueba **requiere ejecutar Pine**, y eso solo lo puedes hacer tú. No son los datos: para la calibración larga hay trece años de M1 en el espejo `kk-at-5/xauusd-raw-data`, pero ese espejo no es lo que se usa en esta prueba — ver el apartado siguiente.

## Lo que esta prueba mide, y lo que no

Son **dos pruebas distintas** y conviene no mezclarlas:

| Prueba | Qué compara | ¿Bloquea la calibración? |
|---|---|---|
| **Paridad de código** | La detección de Pine contra la de Python, **sobre las mismas velas** | **Sí.** Es la de §1.2 |
| Paridad de datos | El espejo de GitHub contra el feed de OANDA | No. Es una comprobación aparte |

La paridad de código exige alimentar a Python con **las mismas velas que vio Pine**. Si Python lee el espejo de GitHub y Pine lee OANDA, cualquier diferencia que salga puede venir del feed y no del código, y entonces la prueba no distingue lo que pretende distinguir. Por eso hay que exportar también las velas desde TradingView.

La comparación espejo contra OANDA tiene su valor —dice si los datos de calibración representan bien el feed real— pero es un asunto separado y no bloquea nada. Lo que ya se sabe de ella: sobre 4.732 minutos solapados la diferencia mediana de cierre era de 0,11 USD.

## Paso 1 · Exportar de TradingView las DOS cosas

Sobre un gráfico de **OANDA:XAUUSD en 5 minutos**, y de los **mismos tres días** en los dos casos:

**a) Las velas.** Exportar los datos del gráfico a CSV (menú del gráfico, *Export chart data*). Guardar en `paridad/velas_YYYYMMDD.csv`. Estas son las velas que comerá el detector de Python.

**b) Los registros de zonas.**

1. Cargar `pine/MGC_FVG_ORB.pine` en ese mismo gráfico.
2. En **Exportación**, activar `Exportar zonas a Pine Logs` y fijar `Log desde` / `Log hasta` a los tres días elegidos. Acotar el rango importa: el panel tiene un límite de líneas y sin acotarlo los días que interesan se pierden entre miles de registros anteriores.
3. Copiar el panel de Pine Logs a `paridad/pine_logs_YYYYMMDD.csv`, un fichero por día.

Elegir tres días de carácter distinto, que es lo que pide la especificación: uno de tendencia clara, uno de rango y uno con dato macro fuerte (NFP, IPC, FOMC).

El panel puede prefijar la hora del navegador en cada línea; el comparador lo tolera, no hace falta limpiarlo.

## Formato de los registros

```
Z,fecha,id,marco,dir,top,bot,mid,estado          alta de zona
S,tNace,id,marco,dir,top,bot,mid,estado,tApertura   zona viva al abrir el rango
E,fecha,id,est_ant,est_nuevo,dir_ant,dir_nuevo   cambio de estado o inversión
P,fecha,id                                       zona retirada por purga FIFO
D,fecha,id,disparador,dir,entrada,stop,stop_pts,objetivo   disparo de entrada
```

En `S` la **primera** fecha es la de nacimiento de la zona, que es la clave por la que el comparador empareja; la última es la hora de apertura del rango. Usar la apertura como fecha de la zona haría que estas zonas nunca cuadraran con las que Python creó en su nacimiento real.

Fechas en `America/New_York`. `dir` es 1 para zona de compra y −1 para zona de venta. Los estados son 0 virgen, 1 mitigada parcial, 2 consumida.

**Z y S se tratan igual**: las dos dan de alta una zona. `S` existe porque el rango de exportación recorta los logs, y sin un inventario de las zonas que ya estaban vivas al abrirlo, el comparador las contaría como "solo en Python" y hundiría el porcentaje de emparejadas sin motivo. En `S` el estado y la dirección son los **actuales**, que pueden no ser los del nacimiento si la zona ya se mitigó o se invirtió.

**Ninguna lógica de trading depende del input de exportación**: los cuatro bloques que lo consultan solo escriben. Está verificado por búsqueda y conviene volver a verificarlo si alguien toca esa parte.

## Paso 2 · Comparar la detección

```bash
python3 paridad/comparar.py paridad/pine_logs_20260915.csv \
                            paridad/python_zonas_20260915.csv
```

El comparador empareja zonas por fecha de nacimiento, marco y dirección, con tolerancia de 0,3 USD en precio y 5 minutos en la fecha, porque los ids de las dos implementaciones no tienen por qué coincidir. Informa de las zonas que solo ve un lado y de las discrepancias entre las emparejadas.

En cada cambio de estado compara el estado anterior y el nuevo, la dirección anterior y la nueva, y la **hora** del cambio: sin margen en el marco del gráfico, porque ahí el cambio tiene que caer en la misma vela, y con una vela de 5m de margen en marcos superiores, porque el momento en que cada implementación ve la vela superior cerrada puede diferir en un paso.

Sale con código 0 solo si se cumple todo esto:

- al menos el **95 %** de zonas emparejadas (criterio de §1.2)
- **ninguna** discrepancia de estado sin explicar (criterio de §1.2)
- ninguna zona que llegara al rango en estados distintos
- ninguna cola FIFO desalineada

Si no se cumplen, no se sigue. No se baja el umbral.

## Paso 3 · Especificación de `detectar.py`

El detector en Python **todavía no existe**. Leerá `paridad/velas_YYYYMMDD.csv` —las velas exportadas de TradingView, no el espejo de GitHub— y debe reproducir exactamente lo que hace el `.pine`. Lo que sigue no es una lista de deseos: cada punto corresponde a una forma concreta en que las dos implementaciones podrían divergir sin que la divergencia signifique nada.

### a) Calentamiento antes del rango

Leer velas desde **al menos tres semanas antes** del día de prueba, y emitir registros **solo dentro del rango**, con un `S` por cada zona viva al abrirlo.

El motivo: una zona de 4H puede nacer días antes del día que se compara y seguir viva. Si Python empieza a leer el mismo día del rango, esa zona no existe en su estado y aparecería como "solo en Pine", hundiendo el porcentaje de emparejadas por una razón que no tiene nada que ver con la lógica de detección. Tres semanas cubren con holgura la vida útil de una zona de 4H más el calentamiento del ATR(14).

### b) Un único `E` por vela

Por cada vela y cada zona, como mucho **un** registro `E`, comparando el estado y la dirección **al inicio** de la vela contra los del final.

Pine funciona así por construcción: la máquina de estados captura estado y dirección al entrar en la iteración de esa zona y escribe un solo registro si algo cambió al salir. Una vela puede mover una zona de virgen a mitigada y de mitigada a consumida en el mismo paso, y Pine emite **un** registro `0 -> 2`, no dos. Un detector que emitiera los pasos intermedios produciría secuencias más largas y el comparador lo marcaría como discrepancia.

### c) Purga FIFO idéntica

Cola de **60 zonas** (el valor por defecto de `Máximo de zonas en memoria`), descartando siempre la más antigua, y emitiendo un registro `P` al hacerlo.

Si las colas no coinciden, un lado sigue informando de zonas que el otro ya olvidó. El comparador detecta ese caso y lo reporta aparte, pero conviene que no ocurra: con la misma cola no hay nada que explicar.

### Cuándo escribirlo

Se escribe cuando haya al menos un par de ficheros —velas y logs del mismo día— contra el que contrastarlo. Escribirlo antes es trabajar a ciegas: cualquier diferencia de interpretación saldría solo al comparar, y sin los ficheros de referencia no se puede comparar.

Una vez haya paridad de código, la calibración sí puede correr sobre el histórico largo del espejo de GitHub: para entonces se sabrá que el detector reproduce lo que hace el script, y lo que hace falta son los trece años de velas que TradingView no exporta de una vez.

## Paso 4 · Validación en futuros antes de operar

Calibrar en spot sirve para **encontrar** la ventaja, no para operarla. Antes de activar el filtro ALTA hay que verificarlo en el Strategy Tester sobre **MGC1!** (o GC1!) en el periodo de validación:

> Si la E[R] de las zonas ALTA en futuros se aleja más de **0,1R** de la de spot, el filtro no se activa.
