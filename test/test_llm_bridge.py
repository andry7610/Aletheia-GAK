from llm_bridge import LLMBridge


def test_llm_bridge_self_correction_success():
    bridge = LLMBridge(mode="mock")
    eq, result = bridge.solve_with_verification("Найди энергию фотона", law_name="photon_energy")
    assert eq == "E = h * f"
    assert result["status"] == "PASS"
    assert result["stage"] == "full_check"


def test_llm_bridge_exhausts_retries_when_stubborn(monkeypatch):
    bridge = LLMBridge(mode="mock")
    # Подменяем ответ LLM так, чтобы она упрямо выдавала ошибку и не исправлялась
    monkeypatch.setattr(bridge, "_call_llm", lambda prompt: "E = hbar * f")
    eq, result = bridge.solve_with_verification("Найди энергию фотона", law_name="photon_energy", max_retries=2)
    assert eq is None
    assert result["status"] == "FAIL"
    assert result["stage"] == "algebra_check"
