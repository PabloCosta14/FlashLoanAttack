"""AMM: implementación de un AMM constante x*y=k con fee."""
class AMM:
    def __init__(self, reserve_a: float, reserve_b: float, fee: float = 0.003):
        self.a = float(reserve_a)
        self.b = float(reserve_b)
        self.fee = float(fee)
    def price_a_in_b(self) -> float:
        return self.b / self.a
    def swap_a_for_b(self, dx: float) -> float:
        assert dx > 0, "dx must be positive"
        dx_net = dx * (1 - self.fee)
        k = self.a * self.b
        new_a = self.a + dx_net
        new_b = k / new_a
        dy = self.b - new_b
        self.a = new_a
        self.b = new_b
        return dy
    def swap_b_for_a(self, dy_in: float) -> float:
        assert dy_in > 0, "dy_in must be positive"
        dy_net = dy_in * (1 - self.fee)
        k = self.a * self.b
        new_b = self.b + dy_net
        new_a = k / new_b
        dx = self.a - new_a
        self.a = new_a
        self.b = new_b
        return dx
