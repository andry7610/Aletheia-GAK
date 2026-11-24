# orchestrator.py
# Aletheia-GAK: Мозг системы. Объединяет физическую (размерности) и
# алгебраическую (канонические законы) проверки.

import json
from verifier import AletheiaVerifier
from graph_db import AletheiaMemory

class AletheiaOrchestrator:
    def __init__(self, db_path=":memory:"):
        self.verifier = AletheiaVerifier()
        self.memory = AletheiaMemory(db_path=db_path)

    def evaluate_hypothesis(self, hypothesis_str: str, law_name: str = None) -> dict:
        """
        Главный вход. Принимает строку вида "lhs = rhs".
        Если передан law_name, проверяет алгебру по канону.
        Возвращает dict с результатом и фидбеком для LLM.
        """
        result = {
            "status": "FAIL",
            "stage": "none",
            "message": "",
            "feedback_for_llm": ""
        }

        # Шаг 1. Извлекаем известные размерности из Гиппокампа
        symbols = self.memory.get_symbols_dict()

        # Шаг 2. Проверка размерностей (Verifier)
        dim_ok, dim_msg = self.verifier.verify_equation(hypothesis_str, symbols)
        if not dim_ok:
            result["stage"] = "dimension_check"
            result["message"] = dim_msg
            result["feedback_for_llm"] = (
                f"Твоя формула не прошла проверку размерностей: {dim_msg}. "
                f"Пожалуйста, исправь единицы измерения или проверь, все ли переменные "
                f"введены правильно. (Известные переменные: {list(symbols.keys())})"
            )
            return result

        # Если размерности сошлись, но закон не указан — просто успех
        if not law_name:
            result["status"] = "PASS"
            result["stage"] = "dimension_check_only"
            result["message"] = "OK: Размерности сходятся. (Алгебра не проверялась, т.к. не указан закон)."
            return result

        # Шаг 3. Проверка алгебры (Hippocampus)
        # Разделяем строку обратно на lhs и rhs
        if "=" not in hypothesis_str:
            result["status"] = "FAIL"
            result["stage"] = "format"
            result["message"] = "Ошибка формата: нет знака '='."
            return result
            
        lhs_str, rhs_str = [part.strip() for part in hypothesis_str.split("=", 1)]
        
        alg_ok, alg_msg = self.memory.check_algebraic_law(lhs_str, rhs_str, law_name)
        if not alg_ok:
            result["stage"] = "algebra_check"
            result["message"] = alg_msg
            result["feedback_for_llm"] = (
                f"Размерности верные, но физика не сходится с каноническим законом '{law_name}': {alg_msg}. "
                f"Проверь коэффициенты и константы (например, не перепутал ли ты h и hbar, или не забыл ли 1/2)."
            )
            return result

        # Всё сошлось!
        result["status"] = "PASS"
        result["stage"] = "full_check"
        result["message"] = f"OK: Размерности и алгебра сходятся с законом '{law_name}'."
        return result

    def add_knowledge(self, name: str, dimension: str, description: str = ""):
        """Метод для пополнения памяти (обучение)."""
        self.memory.add_quantity(name, dimension, description)

    def add_canonical_law(self, name: str, lhs: str, rhs: str):
        """Добавление эталонного закона."""
        self.memory.add_law(name, lhs, rhs)


# ==========================================
# Тесты для проверки работы Оркестратора
# ==========================================
if __name__ == "__main__":
    brain = AletheiaOrchestrator()

    # 1. Обучаем базу
    brain.add_knowledge("h", "J*s", "Постоянная Планка")
    brain.add_knowledge("hbar", "J*s", "Приведенная постоянная Планка")
    brain.add_knowledge("f", "1/s", "Частота")
    brain.add_knowledge("E", "J", "Энергия")
    brain.add_knowledge("m", "kg", "Масса")
    brain.add_knowledge("c", "m/s", "Скорость света")

    brain.add_canonical_law("photon_energy", "E", "h * f")
    brain.add_canonical_law("einstein_mass_energy", "E", "m * c**2")

    print("=== ТЕСТ 1: Правильный фотон ===")
    res = brain.evaluate_hypothesis("E = h * f", law_name="photon_energy")
    print(json.dumps(res, ensure_ascii=False, indent=2))

    print("\n=== ТЕСТ 2: Ловушка с hbar ===")
    res = brain.evaluate_hypothesis("E = hbar * f", law_name="photon_energy")
    print(json.dumps(res, ensure_ascii=False, indent=2))

    print("\n=== ТЕСТ 3: Ошибка размерности (забыли c^2) ===")
    res = brain.evaluate_hypothesis("E = m * c", law_name="einstein_mass_energy")
    print(json.dumps(res, ensure_ascii=False, indent=2))

    print("\n=== ТЕСТ 4: Неизвестная переменная (LLM выдумал x) ===")
    res = brain.evaluate_hypothesis("E = x * f", law_name="photon_energy")
    print(json.dumps(res, ensure_ascii=False, indent=2))