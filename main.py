"""Punto de entrada: corre el escenario seleccionado."""
# from simulation.scenario_flashloan_attack import run_flashloan_attack

# from simulation.scenario_circuit import run_flashloan_attack
# from simulation.scenario_per_tx_cap import run_flashloan_attack
# from simulation.scenario_slippage import run_flashloan_attack
from simulation.scenario_flashloan_attack import run_flashloan_attack

if __name__ == "__main__":
    run_flashloan_attack()
