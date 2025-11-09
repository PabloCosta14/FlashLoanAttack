"""Protocolo de lending vulnerable que usa el oráculo para valorar colateral A en B."""
class LendingProtocol:
    def __init__(self, oracle, ltv: float = 0.7):
        self.oracle = oracle
        self.ltv = float(ltv)
        self.collateral_a = 0.0
        self.debt_b = 0.0
    def deposit_collateral_a(self, amount_a: float):
        self.collateral_a += amount_a
    def max_borrowable_b(self) -> float:
        value_b = self.collateral_a * self.oracle.price_a_in_b()
        return max(0.0, value_b * self.ltv - self.debt_b)
    def borrow_b(self, amount_b: float):
        assert amount_b <= self.max_borrowable_b() + 1e-9, "Would exceed LTV"
        self.debt_b += amount_b
    def liquidatable(self) -> bool:
        value_b = self.collateral_a * self.oracle.price_a_in_b()
        return self.debt_b > value_b * self.ltv + 1e-9


# --- Defensa (comentada) ---
# Circuit breaker simple: no permitir nuevos préstamos si el precio se movió más de X% en una ventana.
# Descomenta e integra según convenga.
# class LendingProtocolWithCircuit(LendingProtocol):
#     def __init__(self, oracle, ltv=0.7, circuit_threshold=0.2):
#         super().__init__(oracle, ltv)
#         self.circuit_threshold = circuit_threshold
#         self.last_price = oracle.price_a_in_b()
#     def borrow_b(self, amount_b: float):
#         current = self.oracle.price_a_in_b()
#         if abs(current - self.last_price) / max(self.last_price, 1e-12) > self.circuit_threshold:
#             raise Exception("Circuit breaker: price moved too much, borrowing paused")
#         super().borrow_b(amount_b)
#     def update_last_price(self):
#         self.last_price = self.oracle.price_a_in_b()
# ---------------------------
