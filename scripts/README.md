# Verificación estática del Pine

`verificar_pine.py` no compila nada: aquí no hay intérprete de Pine. Comprueba cinco cosas que **sí** se pueden ver en el texto y que Pine rechaza o, peor, acepta en silencio.

```bash
python3 -I scripts/verificar_pine.py pine/MGC_FVG_ORB.pine
```

| Control | Qué caza | Por qué existe |
|---|---|---|
| 1 · Paréntesis y corchetes | Desequilibrios y cierres cruzados | Lo barato primero |
| 2 · Indentación de continuaciones | Una continuación con indentación **múltiplo de 4** | Pine la lee como un bloque anidado. Apareció de verdad en `Zona.new()` |
| 3 · Declaración antes de uso | Usar un nombre global antes de declararlo | Pine lo rechaza. Cazó `asiaLoFijo` leído 70 líneas antes de existir |
| 4 · Funciones que asignan a globales | `x := ...` dentro de una función sobre una global | Pine lo prohíbe; solo se pueden mutar arrays y objetos |
| 5 · Identificadores locales sin declarar | Nombres `f_*`, `i_*`, `V_*`, `N_*`… usados y nunca escritos | El más reciente, y cazó tres funciones referenciadas sin escribir |

**Lo que no comprueba**, y por tanto hay que mirar a mano o en TradingView:

- tipos, firmas y aritmética;
- `ta.*` con estado dentro de un ternario, un `and` o un bloque condicional (**CW10002**) — para eso hay un grep aparte, en `docs/TRASPASO_MGC.md` §v5.3;
- los cupos de `plot`, `request.security`, líneas, cajas y etiquetas;
- y por supuesto si la estrategia gana dinero.

Los falsos positivos que tuvo y se corrigieron, por si vuelven: medir la indentación sobre la línea con las cadenas blanqueadas, tomar `=>` por operador de continuación, confundir `for k = 0 to 3` con una declaración global, y leer el `atr` de `ta.atr` como la variable `atr`.
