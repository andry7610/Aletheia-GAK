import pytest
from orchestrator import AletheiaOrchestrator


@pytest.fixture
def brain():
    orch = AletheiaOrchestrator()
    orch.add_knowledge("h", "J*s", "Постоянная Планка")
    orch.add_knowledge("hbar", "J*s", "Приведенная постоянная Планка")
    orch.add_knowledge("f", "1/s", "Частота")
    orch.add_knowledge("E", "J", "Энергия")
    orch.add_knowledge("m", "kg", "Масса")
    orch.add_knowledge("c", "m/s", "Скорость света")

    orch.add_canonical_law("photon_energy", "E", "h * f")
    orch.add_canonical_law("einstein_mass_energy", "E", "m * c**2")
    return orch


def test_photon_energy_pass(brain):
    res = brain.evaluate_hypothesis("E = h * f", law_name="photon_energy")
    assert res["status"] == "PASS"
    assert res["stage"] == "full_check"


def test_photon_energy_equivalent_pi_pass(brain):
    res = brain.evaluate_hypothesis("E = hbar * 2 * pi * f", law_name="photon_energy")
    assert res["status"] == "PASS"


def test_trap5_hbar_vs_h_fail(brain):
    res = brain.evaluate_hypothesis("E = hbar * f", law_name="photon_energy")
    assert res["status"] == "FAIL"
    assert res["stage"] == "algebra_check"
    assert "hbar" in res["feedback_for_llm"]


def test_einstein_missing_square_fail(brain):
    res = brain.evaluate_hypothesis("E = m * c", law_name="einstein_mass_energy")
    assert res["status"] == "FAIL"
    assert res["stage"] == "dimension_check"


def test_code_injection_blocked(brain):
    res = brain.evaluate_hypothesis(
        "E = __import__('os').system('echo hack')", law_name="photon_energy"
    )
    assert res["status"] == "FAIL"


def test_llm_self_correction_loop(brain):
    # Имитация двухшагового диалога с LLM: шаг 1 — ошибка, шаг 2 — исправление по фидбеку
    first_try = "E = hbar * f"
    res1 = brain.evaluate_hypothesis(first_try, law_name="photon_energy")
    assert res1["status"] == "FAIL"
    assert "hbar" in res1["feedback_for_llm"]

    # LLM читает feedback_for_llm и исправляет формулу
    second_try = "E = h * f"
    res2 = brain.evaluate_hypothesis(second_try, law_name="photon_energy")
    assert res2["status"] == "PASS"