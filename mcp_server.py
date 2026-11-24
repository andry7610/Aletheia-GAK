# mcp_server.py
from mcp.server.fastmcp import FastMCP
from orchestrator import AletheiaOrchestrator

mcp = FastMCP("Aletheia-GAK")
brain = AletheiaOrchestrator()

# Загружаем базовые знания
brain.add_knowledge("h", "J*s", "Постоянная Планка")
brain.add_knowledge("hbar", "J*s", "Приведенная постоянная Планка")
brain.add_knowledge("f", "1/s", "Частота")
brain.add_knowledge("E", "J", "Энергия")
brain.add_knowledge("m", "kg", "Масса")
brain.add_knowledge("c", "m/s", "Скорость света")
brain.add_canonical_law("photon_energy", "E", "h * f")
brain.add_canonical_law("einstein_mass_energy", "E", "m * c**2")

@mcp.tool()
def verify_physics_equation(equation: str, law_name: str = None) -> str:
    """
    Проверяет физическое уравнение на размерности и алгебру.
    Используй это перед тем, как дать ответ пользователю.
    """
    res = brain.evaluate_hypothesis(equation, law_name=law_name)
    if res["status"] == "PASS":
        return f"✅ Уравнение верно: {equation}"
    else:
        return f"❌ Ошибка: {res['feedback_for_llm']}"

if __name__ == "__main__":
    mcp.run()