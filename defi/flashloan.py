"""Pool de flash loans (modelo simple)."""
class FlashLoanPool:
    def __init__(self, liquidity_b: float, fee: float = 0.0009):
        self.b = float(liquidity_b)
        self.fee = float(fee)
    def borrow(self, amount_b: float) -> float:
        assert amount_b <= self.b + 1e-12, "Not enough liquidity in flash pool"
        self.b -= amount_b
        return amount_b
    def repay(self, amount_b: float):
        self.b += amount_b
