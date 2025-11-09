"""Escenario: Base (sin defensas)
Este escenario está configurado para demostrar: Control: ejecución del ataque sin defensas.

Explicación breve: en la sección marcada "APLICAR DEFENSA" se muestra el código que implementa
la defensa correspondiente y un comentario técnico de por qué se aplica ahí.
"""
from defi.amm import AMM
from defi.oracle import Oracle
from defi.flashloan import FlashLoanPool
from defi.lending import LendingProtocol
from defi.models import Actor
from utils.printer import pretty
from utils.config import *
from simulation.transaction import Transaction, TransactionError

def run_flashloan_attack():
    # Inicialización del entorno de simulación
    amm = AMM(AMM_RESERVE_A, AMM_RESERVE_B, AMM_FEE)
    oracle = Oracle(amm)
    pool = FlashLoanPool(FLASH_POOL_LIQUIDITY_B, FLASH_POOL_FEE)
    protocol = LendingProtocol(oracle, LENDING_LTV)
    attacker = Actor(a=ATTACKER_INITIAL_A, b=0.0)

    pretty("Estado inicial", amm, pool, protocol, attacker)

    # --- Escenario base (control): sin defensas ---
    # 1) Flash loan
    loan_b = 10_000.0
    received_b = pool.borrow(loan_b)
    attacker.b += received_b
    pretty("1) Toma flash loan en B", amm, pool, protocol, attacker)

    # 2) Manipula precio B -> A (transaccional)
    used_b = attacker.b * 0.99
    def post_check_step2():
        return attacker.b >= 0 and amm.a > 0 and amm.b > 0
    def summary_step2(before, after):
        try:
            a_before = before[id(amm)]['a']; b_before = before[id(amm)]['b']
            a_after = after[id(amm)]['a']; b_after = after[id(amm)]['b']
            attacker_a_before = before[id(attacker)]['a']; attacker_a_after = after[id(attacker)]['a']
            attacker_b_before = before[id(attacker)]['b']; attacker_b_after = after[id(attacker)]['b']
            spent_b = (attacker_b_before or 0) - (attacker_b_after or 0)
            received_a = (attacker_a_after or 0) - (attacker_a_before or 0)
            print(f"[SUMMARY TX-Step2] B gastado={spent_b:.2f}, A recibida={received_a:.2f}, AMM A: {a_before:.2f} -> {a_after:.2f}, AMM B: {b_before:.2f} -> {b_after:.2f}")
        except Exception:
            pass
    with Transaction(objects=[attacker, amm, pool, protocol], name='TX-Step2', post_check=post_check_step2, on_commit=summary_step2):
            got_a = amm.swap_b_for_a(used_b)
            attacker.b -= used_b
            attacker.a += got_a
    pretty("2) Manipula precio en AMM (B -> A)", amm, pool, protocol, attacker)

    # 3) Deposita A inflado y pide B (transaccional)
    def post_check_step3():
        return attacker.a >= 0 and protocol.debt_b >= 0
    def summary_step3(before, after):
        try:
            attacker_a_before = before[id(attacker)]['a']; attacker_a_after = after[id(attacker)]['a']
            attacker_b_before = before[id(attacker)]['b']; attacker_b_after = after[id(attacker)]['b']
            protocol_coll_before = before[id(protocol)]['collateral_a']; protocol_coll_after = after[id(protocol)]['collateral_a']
            protocol_debt_before = before[id(protocol)]['debt_b']; protocol_debt_after = after[id(protocol)]['debt_b']
            spent_a = (attacker_a_before or 0) - (attacker_a_after or 0)
            received_b = (attacker_b_after or 0) - (attacker_b_before or 0)
            print(f"[SUMMARY TX-Step3] A depositada={spent_a:.2f}, B recibido={received_b:.2f}, collateral: {protocol_coll_before} -> {protocol_coll_after}, debt: {protocol_debt_before} -> {protocol_debt_after}")
        except Exception:
            pass
    with Transaction(objects=[attacker, amm, pool, protocol], name='TX-Step3', post_check=post_check_step3, on_commit=summary_step3):
            deposit_a = attacker.a * 0.95
            attacker.a -= deposit_a
            protocol.deposit_collateral_a(deposit_a)
            amount_borrow = protocol.max_borrowable_b()
            protocol.borrow_b(amount_borrow)
            attacker.b += amount_borrow
    pretty("3) Deposita A inflado como colateral y pide B", amm, pool, protocol, attacker)

    # 4) Revierte precio A -> B (transaccional)
    sold_a = attacker.a * 0.90
    def post_check_step4():
        return attacker.a >= 0 and attacker.b >= 0 and amm.a > 0 and amm.b > 0
    def summary_step4(before, after):
        try:
            a_before = before[id(amm)]['a']; b_before = before[id(amm)]['b']
            a_after = after[id(amm)]['a']; b_after = after[id(amm)]['b']
            attacker_a_before = before[id(attacker)]['a']; attacker_a_after = after[id(attacker)]['a']
            attacker_b_before = before[id(attacker)]['b']; attacker_b_after = after[id(attacker)]['b']
            sold = (attacker_a_before or 0) - (attacker_a_after or 0)
            rec_b = (attacker_b_after or 0) - (attacker_b_before or 0)
            print(f"[SUMMARY TX-Step4] A vendida={sold:.2f}, B recibida={rec_b:.2f}, AMM A: {a_before:.2f} -> {a_after:.2f}, AMM B: {b_before:.2f} -> {b_after:.2f}")
        except Exception:
            pass
    with Transaction(objects=[attacker, amm, pool, protocol], name='TX-Step4', post_check=post_check_step4, on_commit=summary_step4):
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
