# -*- coding: utf-8 -*-
"""
maxwell_seed — канонические уравнения Максвелла для Гиппокампа (v1.2).

Четыре закона в канонической форме с нулевой правой частью —
в том же стиле, что уравнение непрерывности из v1.1.

Важно (честная оговорка): форма Ампера без тока смещения.
Полная форма rot(B) - mu_0*(j + epsilon_0*ddt(E)) = 0 — следующий этап,
она требует произведений полей на константы с производными по времени
и отдельного соглашения о непрерывности.

Символы полей: E, B, j, rho — добавляются в quantities при посеве.
"""
import sympy as sp

MAXWELL_FIELDS = [
    ("E", "V/m", "Напряжённость электрического поля (вектор)"),
    ("B", "T", "Магнитная индукция (вектор)"),
    ("j", "A/m**2", "Плотность тока (вектор)"),
    ("rho", "C/m**3", "Объёмная плотность заряда"),
]

MAXWELL_LAWS = {
    "faraday_law": {
        "lhs": "rot(E) + ddt(B)",
        "rhs": "0",
        "description": "Закон Фарадея: rot E = -dB/dt",
    },
    "gauss_electric": {
        "lhs": "div(E)",
        "rhs": "rho/epsilon_0",
        "description": "Теорема Гаусса для электрического поля",
    },
    "ampere_no_displacement": {
        "lhs": "rot(B)",
        "rhs": "mu_0*j",
        "description": "Закон Ампера (без тока смещения)",
    },
    "gauss_magnetic": {
        "lhs": "div(B)",
        "rhs": "0",
        "description": "Теорема Гаусса для магнитного поля: нет магнитных зарядов",
    },
}


def get_maxwell_laws() -> list[tuple[str, str, str]]:
    """Список (имя, lhs, rhs) для add_law."""
    return [(name, law["lhs"], law["rhs"])
            for name, law in MAXWELL_LAWS.items()]
