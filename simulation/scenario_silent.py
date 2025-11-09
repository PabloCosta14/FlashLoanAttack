"""Escenario orquestador que ejecuta el ataque paso a paso usando los módulos de defi."""
from defi.amm import AMM
from defi.oracle import Oracle
from defi.flashloan import FlashLoanPool
from defi.lending import LendingProtocol
from defi.models import Actor
from utils.printer import pretty
from utils.config import *
from simulation.transaction import Transaction, TransactionError

def run_flashloan_attack():
    # Inicialización del mundo
    amm = AMM(AMM_RESERVE_A, AMM_RESERVE_B, AMM_FEE)
    oracle = Oracle(amm)
    pool = FlashLoanPool(FLASH_POOL_LIQUIDITY_B, FLASH_POOL_FEE)
    protocol = LendingProtocol(oracle, LENDING_LTV)
    attacker = Actor(a=ATTACKER_INITIAL_A, b=0.0)

    pretty("Estado inicial", amm, pool, protocol, attacker)

    # --- Defensas opcionales (comentadas) para ensayar ---
    # 1) Per-tx cap: limitar cuánto B puede usar un atacante por transacción:
    # PER_TX_CAP_B = None  # set to e.g. 5000.0 to enable
    PER_TX_CAP_B = None

    # 2) Slippage check: porcentaje máximo de cambio de precio permitido por trade
    # MAX_SLIPPAGE = None  # set to e.g. 0.15 for 15%
    MAX_SLIPPAGE = None

    # 3) Circuit breaker / update price (uso en LendingProtocolWithCircuit si se habilita)
    # protocol.update_last_price()  # solo si usas LendingProtocolWithCircuit

    # Nota: para activar una defensa, descomenta la variable y ajústala según el escenario.

    # 1) Flash loan
    loan_b = 10_000.0
    received_b = pool.borrow(loan_b)
    attacker.b += received_b
    pretty("1) Toma flash loan en B", amm, pool, protocol, attacker)

    # 2) Manipula precio B -> A  (transaccional)
    used_b = attacker.b * 0.99

    def logger(msg):
        print(msg)

    def post_check_step2():
        # ejemplo: chequear que no haya saldo negativo
        return attacker.b >= 0 and amm.a > 0 and amm.b > 0

    def summary_step2(before, after):
        try:
            a_before = before[id(amm)]['a'] if id(amm) in before else None
            b_before = before[id(amm)]['b'] if id(amm) in before else None
            a_after = after[id(amm)]['a'] if id(amm) in after else None
            b_after = after[id(amm)]['b'] if id(amm) in after else None
            attacker_a_before = before[id(attacker)]['a'] if id(attacker) in before else None
            attacker_a_after = after[id(attacker)]['a'] if id(attacker) in after else None
            attacker_b_before = before[id(attacker)]['b'] if id(attacker) in before else None
            attacker_b_after = after[id(attacker)]['b'] if id(attacker) in after else None
            spent_b = (attacker_b_before or 0) - (attacker_b_after or 0)
            received_a = (attacker_a_after or 0) - (attacker_a_before or 0)
            print(f"[SUMMARY TX-Step2-Manipulate] B gastado={spent_b:.2f}, A recibida={received_a:.2f}, AMM A: {a_before:.2f} -> {a_after:.2f}, AMM B: {b_before:.2f} -> {b_after:.2f}")
        except Exception as e:
            print("[SUMMARY TX-Step2-Manipulate] error computing summary:", e)

    with Transaction(objects=[attacker, amm, pool, protocol], name='TX-Step2-Manipulate', post_check=post_check_step2, on_commit=summary_step2):
            got_a = amm.swap_b_for_a(used_b)
            attacker.b -= used_b
            attacker.a += got_a

    pretty("2) Manipula precio en AMM (B -> A)", amm, pool, protocol, attacker)

    # 3) Deposita A inflado y pide B (transaccional)
    def post_check_step3():
        # verificar que el protocolo no permita deuda negativa y que el attacker no tenga A negativo
        return attacker.a >= 0 and protocol.debt_b >= 0

    def summary_step3(before, after):
        try:
            attacker_a_before = before[id(attacker)]['a'] if id(attacker) in before else None
            attacker_a_after = after[id(attacker)]['a'] if id(attacker) in after else None
            attacker_b_before = before[id(attacker)]['b'] if id(attacker) in before else None
            attacker_b_after = after[id(attacker)]['b'] if id(attacker) in after else None
            protocol_coll_before = before[id(protocol)]['collateral_a'] if id(protocol) in before else None
            protocol_coll_after = after[id(protocol)]['collateral_a'] if id(protocol) in after else None
            protocol_debt_before = before[id(protocol)]['debt_b'] if id(protocol) in before else None
            protocol_debt_after = after[id(protocol)]['debt_b'] if id(protocol) in after else None
            spent_a = (attacker_a_before or 0) - (attacker_a_after or 0)
            received_b = (attacker_b_after or 0) - (attacker_b_before or 0)
            print(f"[SUMMARY TX-Step3-DepositBorrow] A depositada={spent_a:.2f}, B recibido={received_b:.2f}, protocol collateral: {protocol_coll_before} -> {protocol_coll_after}, debt: {protocol_debt_before} -> {protocol_debt_after}")
        except Exception as e:
            print("[SUMMARY TX-Step3-DepositBorrow] error computing summary:", e)

    with Transaction(objects=[attacker, amm, pool, protocol], name='TX-Step3-DepositBorrow', post_check=post_check_step3, on_commit=summary_step3):
            deposit_a = attacker.a * 0.95
            attacker.a -= deposit_a
            protocol.deposit_collateral_a(deposit_a)
            amount_borrow = protocol.max_borrowable_b()
            protocol.borrow_b(amount_borrow)
            attacker.b += amount_borrow

    pretty("3) Deposita A inflado como colateral y pide B", amm, pool, protocol, attacker)

    # 4) Revierte precio A -> B (vende A restante) (transaccional)
    sold_a = attacker.a * 0.90

    def post_check_step4():
        # prevenir estados con saldos negativos o AMM inválido
        return attacker.a >= 0 and attacker.b >= 0 and amm.a > 0 and amm.b > 0

    def summary_step4(before, after):
        try:
            a_before = before[id(amm)]['a'] if id(amm) in before else None
            b_before = before[id(amm)]['b'] if id(amm) in before else None
            a_after = after[id(amm)]['a'] if id(amm) in after else None
            b_after = after[id(amm)]['b'] if id(amm) in after else None
            attacker_a_before = before[id(attacker)]['a'] if id(attacker) in before else None
            attacker_a_after = after[id(attacker)]['a'] if id(attacker) in after else None
            attacker_b_before = before[id(attacker)]['b'] if id(attacker) in before else None
            attacker_b_after = after[id(attacker)]['b'] if id(attacker) in after else None
            sold = (attacker_a_before or 0) - (attacker_a_after or 0)
            rec_b = (attacker_b_after or 0) - (attacker_b_before or 0)
            print(f"[SUMMARY TX-Step4-SellBack] A vendida={sold:.2f}, B recibida={rec_b:.2f}, AMM A: {a_before:.2f} -> {a_after:.2f}, AMM B: {b_before:.2f} -> {b_after:.2f}")
        except Exception as e:
            print("[SUMMARY TX-Step4-SellBack] error computing summary:", e)

    with Transaction(objects=[attacker, amm, pool, protocol], name='TX-Step4-SellBack', post_check=post_check_step4, on_commit=summary_step4):
            out_b = amm.swap_a_for_b(sold_a)
            attacker.a -= sold_a
            attacker.b += out_b

    pretty("4) Revierte el precio en AMM (A -> B)", amm, pool, protocol, attacker)

    # 5) Repaga flash loan + fee
    fee = loan_b * pool.fee
    repayment = loan_b + fee
    assert attacker.b >= repayment, "Attacker can't repay flash loan in this toy setup"
    attacker.b -= repayment
    pool.repay(repayment)
    pretty("5) Paga el flash loan + comisión", amm, pool, protocol, attacker)

    # Resultado
    profit_b = attacker.b
    print(f"\n>>> Ganancia neta del atacante (en B) después de repagar el flash loan: {profit_b:.2f} B\n")

    # Defensas (texto para el informe)
    print("""Defensas observadas (recomendadas para el informe):
1) Oráculos robustos: TWAP de varias ventanas o feeds externos resistentes a manipulaciones on-chain.
2) Límite de préstamo por bloque / cool-down entre cambios de precio y uso crediticio.
3) LTV conservador + haircuts mayores para colaterales volátiles.
4) Límites de tamaño (per-transaction caps) y slippage checks estrictos.
5) Circuit breakers: pausar préstamos cuando el precio se mueva X desviaciones estándar en un corto lapso.
6) Requerir varias fuentes de precio y mediana agregada.
""")