"""Oracle ingenuo que lee el price spot desde el AMM."""
class Oracle:
    def __init__(self, amm):
        self.amm = amm
    def price_a_in_b(self) -> float:
        # Oráculo ingenuo: devuelve el precio spot del AMM
        return self.amm.price_a_in_b()


# --- Defensa (comentada) ---
# Ejemplo de TWAP simple: mantener ventanas de precios y devolver promedio ponderado.
# Descomenta y adapta según necesites.
# import collections, time
# class TWAPOracle:
#     def __init__(self, amm, window_seconds=60):
#         self.amm = amm
#         self.window = window_seconds
#         self.samples = collections.deque()  # (timestamp, price)
#     def sample(self):
#         self.samples.append((time.time(), self.amm.price_a_in_b()))
#         # eliminar muestras viejas
#         while self.samples and self.samples[0][0] < time.time() - self.window:
#             self.samples.popleft()
#     def price_a_in_b(self):
#         self.sample()
#         if not self.samples:
#             return self.amm.price_a_in_b()
#         return sum(p for (_, p) in self.samples) / len(self.samples)
# ---------------------------
