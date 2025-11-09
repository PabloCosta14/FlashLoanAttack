# Simulación de un Ataque con Flash Loan  


---

## ¿De qué trata este proyecto?

Este es un simulador educativo que reproduce un ataque clásico en DeFi (finanzas descentralizadas), donde un actor malintencionado —llamado “atacante”— usa un préstamo flash loan (un préstamo que se pide y se devuelve en una sola transacción) para manipular temporalmente el precio de un activo y así obtener ganancias ilícitas.

El objetivo no es promover el ataque, sino entender cómo funciona, por qué es posible, y sobre todo: cómo prevenirlo con buenas prácticas y mecanismos de defensa.



## ¿Cómo funciona el ataque? 

1. **El atacante toma un préstamo gigante… sin poner garantía.**  
   Gracias a los flash loans, puede pedir miles de dólares por unos segundos —siempre y cuando los devuelva en la misma transacción.

2. **Con ese dinero, “mueve” el mercado artificialmente.**  
   Usa un pool de liquidez (como los de Uniswap), donde el precio depende de la proporción entre dos activos (por ejemplo, Token A y Token B). Al comprar mucho Token A con Token B, hace que el precio de A suba mucho… pero solo por un instante.

3. **Ese precio inflado se le reporta a un oráculo “ingenuo”.**  
   Un oráculo es un componente que le dice a otros contratos cuál es el precio actual de un activo. Si el oráculo solo mira el último precio del pool —y no considera datos históricos—, se cree el engaño.

4. **El atacante usa ese precio falso para pedir un préstamo real.**  
   En un protocolo de préstamos (como Aave), deposita Token A como garantía. Como el oráculo dice que A vale mucho, recibe más dinero del que realmente merece.

5. **Finalmente, revierte la manipulación y se queda con ganancias.**  
   Vende el Token A de vuelta al pool, devolviendo el mercado a su estado original, paga el flash loan (más una pequeña comisión), y se queda con el dinero extra que obtuvo del préstamo fraudulento.

En resumen: usa dinero prestado para engañar al sistema, sacar ventaja, y devolver todo… menos las ganancias.

---

## ¿Cómo se puede evitar esto?

El simulador incluye varias estrategias reales que los protocolos usan hoy para protegerse. Se pueden activar fácilmente para ver cómo detienen el ataque antes de que termine.

### 1. Oráculos con promedio en el tiempo (TWAP)  
En vez de usar el último precio, el oráculo calcula un promedio de los precios observados durante los últimos minutos.  
Así, una subida repentina (como la del ataque) no afecta tanto el valor reportado, y el precio sigue siendo más confiable.

### 2. Circuit breakers (interruptores de emergencia)  
El protocolo de préstamos puede detectar cambios bruscos en el precio (por ejemplo, una variación mayor al 20% en pocos segundos). Si detecta esto, pausa temporalmente las operaciones sensibles hasta que el mercado se estabilice.

### 3. Límites prácticos:  
- **Límite por transacción**: Se restringe la cantidad máxima que se puede mover en una sola operación.  
- **Control de deslizamiento (slippage)**: Si una operación intenta mover el precio más allá de un umbral razonable (por ejemplo, 15%), se rechaza automáticamente.

Estas medidas no son infalibles, pero hacen el ataque mucho más difícil, costoso o directamente inviable.

---

## ¿Cómo está organizado el simulador?

El código está dividido en módulos claros, pensados para facilitar el aprendizaje:

| Carpeta | Función |
|--------|----------|
| `defi/` | Contiene los componentes del ecosistema: el mercado (AMM), el oráculo, el protocolo de préstamos, etc. |
| `simulation/` | Ejecuta el ataque paso a paso, registrando cada transacción con entradas y salidas numéricas. |
| `utils/` | Proporciona herramientas para mostrar el estado del sistema antes y después de cada operación. |

Al ejecutar el programa (`python main.py`), se muestra cada etapa del ataque con datos concretos. Si se activa una defensa, se puede observar cómo la transacción se cancela automáticamente (rollback), evitando el daño.

