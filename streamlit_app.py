import streamlit as st
from orchestrator import AletheiaOrchestrator

st.set_page_config(page_title="Aletheia-GAK", page_icon="⚖️", layout="wide")
st.title("⚖️ Aletheia-GAK: Нейросимволический Верификатор")

brain = AletheiaOrchestrator()
brain.add_knowledge("h", "J*s", "Постоянная Планка")
brain.add_knowledge("hbar", "J*s", "Приведённая постоянная Планка")
brain.add_knowledge("f", "1/s", "Частота")
brain.add_knowledge("E", "J", "Энергия")
brain.add_knowledge("m", "kg", "Масса")
brain.add_knowledge("c", "m/s", "Скорость света")

brain.add_canonical_law("photon_energy", "E", "h * f")
brain.add_canonical_law("einstein_mass_energy", "E", "m * c**2")

st.markdown("""
### Проверьте уравнение
Введите уравнение, и система проверит:
1. **Размерности** (нельзя сложить Ньютоны с ускорением).
2. **Алгебру** (ловит `hbar` вместо `h`).
""")

law_choice = st.selectbox(
    "Эталонный закон для алгебраической сверки (необязательно):",
    ["photon_energy", "einstein_mass_energy", "Без сверки с законом (только размерности)"],
)
equation = st.text_input("Уравнение:", "E = hbar * f")

if st.button("Проверить"):
    law_name = None if law_choice.startswith("Без сверки") else law_choice
    res = brain.evaluate_hypothesis(equation, law_name=law_name)
    if res["status"] == "PASS":
        st.success(f"✅ {res['message']}")
    else:
        st.error(f"❌ {res['message']}")
        st.warning(f"Подсказка для LLM: {res['feedback_for_llm']}")
