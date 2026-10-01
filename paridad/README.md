# Prueba de paridad Pine ↔ Python

Esto es lo que desbloquea la calibración. V2.1 §1.2 lo exige y es categórico: *"Si no coinciden, no se sigue. Una calibración sobre zonas distintas de las que dibuja el script no vale nada."*

El bloqueo no son los datos — están disponibles, trece años de M1 en el espejo `kk-at-5/xauusd-raw-data`, ya contrastados contra un feed independiente de OANDA con diferencia mediana de 0,11 USD. El bloqueo es que esta prueba **requiere ejecutar Pine**, y eso solo lo puedes hacer tú.

## Paso 1 · Generar los Pine Logs

**El instrumento importa.** Los datos de Python son **XAUUSD spot**. Si cargas el script en MGC1! las zonas no van a coincidir: distinto feed, base futuros−spot variable y distinto tratamiento del parón de CME. Para la paridad hay que usar **OANDA:XAUUSD en 5 minutos**, que es el feed contra el que se contrastaron los datos.

1. Cargar `pine/MGC_FVG_ORB.pine` en un gráfico de **OANDA:XAUUSD, 5m**.
2. Activar **Exportación → Exportar zonas a Pine Logs**.
3. Abrir el panel de Pine Logs.
4. Elegir **tres días concretos** con carácter distinto, que es lo que pide la especificación:
   - uno de tendencia clara
   - uno de rango
   - uno con dato macro fuerte (NFP, IPC, FOMC)
5. Copiar el contenido del panel a `paridad/pine_logs_YYYYMMDD.csv`, un fichero por día, y subirlos.

El panel puede prefijar la hora del navegador en cada línea; el comparador lo tolera, no hace falta limpiarlo.

## Formato de los registros

```
Z,fecha,id,marco,dir,top,bot,mid,estado          alta de zona
E,fecha,id,est_ant,est_nuevo,dir_ant,dir_nuevo   cambio de estado o inversión
D,fecha,id,disparador,dir,entrada,stop,stop_pts,objetivo   disparo de entrada
```

Fechas en `America/New_York`. `dir` es 1 para zona de compra y −1 para zona de venta. Los estados son 0 virgen, 1 mitigada parcial, 2 consumida.

**Ninguna lógica de trading depende del input de exportación**: los tres bloques que lo consultan solo escriben. Está verificado por búsqueda y conviene volver a verificarlo si alguien toca esa parte.

## Paso 2 · Comparar

```bash
python3 paridad/comparar.py paridad/pine_logs_20260915.csv \
                            paridad/python_zonas_20260915.csv
```

El comparador empareja zonas por fecha de nacimiento, marco y dirección, con tolerancia de 0,3 USD en precio y 5 minutos en la fecha, porque los ids de las dos implementaciones no tienen por qué coincidir. Informa de las zonas que solo ve un lado y de las discrepancias de estado entre las que sí se emparejaron.

Sale con código 0 solo si se cumplen los dos criterios de §1.2:

- al menos el **95 %** de zonas emparejadas
- **ninguna** discrepancia de estado sin explicar

Si no se cumplen, no se sigue. No se baja el umbral.

## Paso 3 · Qué falta por escribir

El detector en Python (`paridad/detectar.py`) **todavía no existe**. Tiene que reimplementar exactamente lo que hace el `.pine`:

- FVG de tres velas, anchura mínima 0,5×ATR(14)
- CE al 50 %
- máquina de estados: virgen, mitigada parcial, consumida, invertida
- margen de invalidación 0,25×ATR
- zonas de 1H y 4H solo después de cerrar su vela

Se escribe cuando haya al menos un fichero de Pine Logs contra el que contrastarlo. Escribirlo antes es trabajar a ciegas: cualquier diferencia de interpretación saldría solo al comparar, y sin el fichero de referencia no se puede comparar.

## Paso 4 · Validación en futuros antes de operar

Calibrar en spot sirve para **encontrar** la ventaja, no para operarla. Antes de activar el filtro ALTA hay que verificarlo en el Strategy Tester sobre **MGC1!** (o GC1!) en el periodo de validación:

> Si la E[R] de las zonas ALTA en futuros se aleja más de **0,1R** de la de spot, el filtro no se activa.
