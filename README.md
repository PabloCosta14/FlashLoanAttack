# Flashloan Attack Simulation (organizado y modular)

**Propósito:** proyecto educativo que simula un ataque tipo *flash loan* combinado con manipulación de un AMM y un oráculo ingenuo. Está organizado en módulos para mostrar buenas prácticas de arquitectura y facilitar la experimentación con defensas. **Solo uso educativo.**

---
## Estructura del proyecto

```
flashloan_project/
  main.py
  defi/
    amm.py         # Lógica del AMM (x*y=k, swaps)
    oracle.py      # Oráculo ingenuo + snippet comentado para TWAP
    flashloan.py   # Pool simple de flash loans
    lending.py     # Protocolo vulnerable de lending + snippet comentado para circuit breaker
    models.py      # Actor dataclass
  simulation/
    scenario_flashloan_attack.py  # Orquestador: ejecuta exactamente el ataque paso a paso
    transaction.py                # Context manager Transaction: snapshot/rollback y resumen on_commit
  utils/
    printer.py     # pretty() para imprimir estados y snippets de checks
    config.py      # parámetros (fees, LTV, iniciales)
  README.md
```

---
## Cómo ejecutar

Desde la raíz del proyecto (donde está `main.py`) ejecuta:

```bash
python3 main.py
```

Verás en pantalla el flujo de la simulación y, además, mensajes por cada **transacción** (pasos 2, 3 y 4) con:
- ENTER tx (snapshot),
- [SUMMARY ...] con datos numéricos (B gastado, A recibida, cambios de reservas),
- COMMIT tx (o ROLLBACK si algo falla).

---

## Dónde habilitar defensas (comentadas en el código)

El proyecto incluye **fragmentos comentados** que muestran cómo podrías activar contramedidas reales. Para activarlas debes editar los archivos y descomentar/adaptar el código, luego re-ejecutar `main.py`.

### 1) TWAP Oracle (anti-manipulación temporal)
Archivo: `defi/oracle.py`

Dentro hay una clase comentada `TWAPOracle` que mantiene una ventana de muestras y devuelve un promedio. Para usarla:
- Descomenta la clase `TWAPOracle` en `defi/oracle.py` (quita las líneas `#` que la rodean).
- En `simulation/scenario_flashloan_attack.py` reemplaza la creación del oráculo:
```py
# oracle = Oracle(amm)
oracle = TWAPOracle(amm, window_seconds=60)
```

### 2) Circuit breaker en lending (detectar saltos de precio)
Archivo: `defi/lending.py`

Hay una clase comentada `LendingProtocolWithCircuit`. Para usarla:
- Descomenta la clase en `defi/lending.py`.
- En el `scenario_flashloan_attack.py` instancia esa clase en vez de `LendingProtocol`:
```py
# protocol = LendingProtocol(oracle, LENDING_LTV)
protocol = LendingProtocolWithCircuit(oracle, ltv=LENDING_LTV, circuit_threshold=0.2)
```
- Puedes llamar `protocol.update_last_price()` periódicamente para refrescar la referencia.

### 3) Límites por transacción y slippage (demo)
Archivo: `simulation/scenario_flashloan_attack.py`

Al inicio del `run_flashloan_attack()` hay variables configurables (comentadas):
```py
# PER_TX_CAP_B = None  # e.g. 5000.0
PER_TX_CAP_B = None

# MAX_SLIPPAGE = None  # e.g. 0.15 for 15%
MAX_SLIPPAGE = None
```

Para activar estas defensas, edita esas líneas y asigna valores no-None. Por ejemplo:
```py
PER_TX_CAP_B = 5000.0
MAX_SLIPPAGE = 0.15
```

Luego ajusta los `pre_check`/`post_check` dentro de las transacciones (ya existe un lugar donde puedes aplicar estas variables para bloquear/rollback si el atacante intenta gastar más de `PER_TX_CAP_B` o mover el precio más del `MAX_SLIPPAGE`).

---

## Qué imprime cada transacción (ejemplo)
```
[TX-Step2-Manipulate] ENTER tx; snapshots taken.
[SUMMARY TX-Step2-Manipulate] B gastado=9900.00, A recibida=4967.36, AMM A: 10000.00 -> 5032.64, AMM B: 10000.00 -> 19870.30
[TX-Step2-Manipulate] COMMIT tx.
```

Y similares para `TX-Step3-DepositBorrow` y `TX-Step4-SellBack`.

---

## Ideas para la entrega / presentación

- Muestra el antes/después de las reservas del AMM y el valor del colateral en cada paso.  
- Activa una defensa (por ejemplo `MAX_SLIPPAGE = 0.15`) y muestra cómo la transacción falla y hace rollback.  
- Incluye en tu informe una discusión sobre por qué TWAP y circuit breakers reducen la ventana de manipulación.  
- Explica las limitaciones del modelo (simulación, no mercado real, no fees de gas, etc.).

---
## Notas técnicas

- La clase `Transaction` hace snapshot usando `deepcopy(obj.__dict__)`. Funciona para este proyecto porque los objetos son simples. Si más adelante agregas recursos externos, necesitarás otra estrategia de snapshot/rollback.
- Código educativo: no intentes reproducir esto en entornos reales ni atacar sistemas reales.

---
## Soporte

Si quieres que yo active por defecto una defensa (p.ej. `PER_TX_CAP_B = 5000` y `MAX_SLIPPAGE = 0.15`) o que genere un ejemplo de `README` en LaTeX, o una diapositiva con gráficos, dímelo y lo hago.

---
