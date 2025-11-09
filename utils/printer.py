"""Funciónes de presentación (sin lógica de negocio)."""
def pretty(title: str, amm, pool, prot, attacker):
    print(f"\n== {title} ==")
    print(f"AMM reserves: A={amm.a:.2f}, B={amm.b:.2f} | spot B per A = {amm.price_a_in_b():.4f}")
    print(f"Flash pool B liquidity: {pool.b:.2f}")
    print(f"Protocol: collateral A={prot.collateral_a:.2f}, debt B={prot.debt_b:.2f}, liquidatable={prot.liquidatable()}")
    print(f"Attacker: A={attacker.a:.2f}, B={attacker.b:.2f}")


# --- Ejemplos de checks (comentados) que podrías usar en production ---
# 1) Slippage check example (to use, implement invocation in scenario):
# def check_slippage(old_price, new_price, max_slippage):
#     change = abs(new_price - old_price) / max(old_price, 1e-12)
#     return change <= max_slippage
