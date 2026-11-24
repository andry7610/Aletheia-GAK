# llm_bridge.py
import os
from orchestrator import AletheiaOrchestrator

class LLMBridge:
    def __init__(self, api_key=None, base_url=None, model="deepseek-chat", mode="mock"):
        self.mode = mode
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
        self.model = model
        self.brain = AletheiaOrchestrator()
        self._setup_knowledge()

    def _setup_knowledge(self):
        # Базовые знания (можно расширять)
        self.brain.add_knowledge("h", "J*s", "Постоянная Планка")
        self.brain.add_knowledge("hbar", "J*s", "Приведенная постоянная Планка")
        self.brain.add_knowledge("f", "1/s", "Частота")
        self.brain.add_knowledge("E", "J", "Энергия")
        self.brain.add_knowledge("m", "kg", "Масса")
        self.brain.add_knowledge("c", "m/s", "Скорость света")
        self.brain.add_canonical_law("photon_energy", "E", "h * f")
        self.brain.add_canonical_law("einstein_mass_energy", "E", "m * c**2")

    def _call_llm(self, prompt: str) -> str:
        if self.mode == "mock":
            # Заглушка для тестов (имитация галлюцинации и исправления)
            if "исправь" in prompt.lower():
                return "E = h * f"  # Правильный ответ после фидбека
            return "E = hbar * f"  # Первая (ошибочная) попытка
        
        # Реальный вызов API (OpenAI-совместимый)
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        return response.choices[0].message.content.strip()

    def solve_with_verification(self, task: str, law_name: str = None, max_retries=3):
        print(f"[*] Задача: {task}")
        current_prompt = f"Реши физическую задачу. Напиши только уравнение вида 'lhs = rhs': {task}"
        
        for attempt in range(max_retries):
            print(f"  [*] Попытка {attempt+1}...")
            hypothesis = self._call_llm(current_prompt)
            print(f"      LLM выдал: {hypothesis}")
            
            # Прогон через AletheiaOrchestrator
            result = self.brain.evaluate_hypothesis(hypothesis, law_name=law_name)
            
            if result["status"] == "PASS":
                print(f"  [+] УСПЕХ: {result['message']}")
                return hypothesis, result
            else:
                print(f"  [-] ОШИБКА: {result['message']}")
                # Цикл самоисправления: отправляем фидбек обратно
                current_prompt = (
                    f"Твоя предыдущая попытка '{hypothesis}' не прошла проверку: {result['feedback_for_llm']}. "
                    f"Исправь и напиши только уравнение:"
                )
        
        print("  [!] Не удалось найти правильное решение за отведенные попытки.")
        return None, result

# Тест моста
if __name__ == "__main__":
    bridge = LLMBridge(mode="mock")
    bridge.solve_with_verification("Найди энергию фотона", law_name="photon_energy")