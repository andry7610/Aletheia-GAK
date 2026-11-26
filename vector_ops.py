# -*- coding: utf-8 -*-
"""
vector_ops — векторная алгебра для Aletheia-GAK (v1.2).

Операторы grad/div/rot/ddt — типизированные сущности:
  - ранг: 0 — скаляр, 1 — вектор;
  - единица: символьное выражение SymPy (V/m и т.п.), производные
    единицы приводятся к базовым СИ через BASE_UNITS (патч Лога);
  - роль: constant / scalar_field / vector_field.

Правила операторов:
  grad(скаляр) -> вектор,  единица / длина
  div(вектор)  -> скаляр,  единица / длина
  rot(вектор)  -> вектор,  единица / длина
  ddt(...)     -> тот же ранг, единица / время

Умножение: любое число скаляров * максимум один вектор.
Произведение двух векторов запрещено; произведение двух полей
помечается nonlinear=True (крючок для тождеств развёртки).
"""
from typing import Dict, NamedTuple

import sympy as sp
from sympy.parsing.sympy_parser import parse_expr

__all__ = [
    "grad", "div", "rot", "curl", "ddt",
    "RankChecker", "AletheiaTypeError", "Inferred", "SymbolInfo",
    "default_registry", "BASE_UNITS", "LENGTH", "TIME",
]

# ---- базовые единицы СИ (патч Лога: приведение производных единиц) ----
kg, A_, s_, m_ = sp.symbols("kg A s m")
BASE_UNITS = {
    sp.Symbol("V"): kg * m_**2 / (A_ * s_**3),
    sp.Symbol("C"): A_ * s_,
    sp.Symbol("T"): kg / (A_ * s_**2),
    sp.Symbol("F"): A_**2 * s_**4 / (kg * m_**2),
    sp.Symbol("Ohm"): kg * m_**2 / (A_**2 * s_**3),
}

LENGTH = sp.Symbol("m")
TIME = sp.Symbol("s")
DIMLESS = sp.Integer(1)

V = sp.Symbol("V")
C = sp.Symbol("C")
T = sp.Symbol("T")
F = sp.Symbol("F")
Amp = sp.Symbol("A")

CONSTANT = "constant"
SCALAR_FIELD = "scalar_field"
VECTOR_FIELD = "vector_field"
_FIELD_ROLES = (SCALAR_FIELD, VECTOR_FIELD)


class SymbolInfo(NamedTuple):
    rank: int
    unit: sp.Expr
    role: str


class Inferred(NamedTuple):
    rank: int
    unit: sp.Expr
    nonlinear: bool
    is_field: bool


def default_registry() -> Dict[str, SymbolInfo]:
    """Реестр символов по умолчанию: имя -> (ранг, единица, роль)."""
    return {
        "epsilon_0": SymbolInfo(0, F / LENGTH, CONSTANT),
        "mu_0":      SymbolInfo(0, T * LENGTH / Amp, CONSTANT),
        "c":         SymbolInfo(0, LENGTH / TIME, CONSTANT),
        "rho":       SymbolInfo(0, C / LENGTH**3, SCALAR_FIELD),
        "phi":       SymbolInfo(0, V, SCALAR_FIELD),
        "E":         SymbolInfo(1, V / LENGTH, VECTOR_FIELD),
        "B":         SymbolInfo(1, T, VECTOR_FIELD),
        "j":         SymbolInfo(1, Amp / LENGTH**2, VECTOR_FIELD),
    }


# ---- операторы ----
grad = sp.Function("grad")
div = sp.Function("div")
rot = sp.Function("rot")
curl = rot  # псевдоним для LLM
ddt = sp.Function("ddt")

# имя -> (ранг аргумента, ранг результата, делитель единицы)
OP_TABLE = {
    "grad": (0, 1, LENGTH),
    "div": (1, 0, LENGTH),
    "rot": (1, 1, LENGTH),
    "ddt": (None, None, TIME),  # ранг сохраняется
}
_ALIASES = {"curl": "rot"}


class AletheiaTypeError(TypeError):
    """Ошибка типа/ранга в проверяемом выражении."""


def _units_equal(a: sp.Expr, b: sp.Expr) -> bool:
    """Сравнивает единицы, приводя их к базовым СИ через BASE_UNITS."""
    a_base = a.subs(BASE_UNITS) if isinstance(a, sp.Expr) else a
    b_base = b.subs(BASE_UNITS) if isinstance(b, sp.Expr) else b
    return sp.simplify(a_base - b_base) == 0


class RankChecker:
    """Проход по AST: вывод ранга, единицы и признака нелинейности."""

    def __init__(self, registry: Dict[str, SymbolInfo] = None):
        self.registry = registry if registry is not None else default_registry()

    # ---- публичный API ----
    def check(self, expr) -> Inferred:
        if isinstance(expr, str):
            raise AletheiaTypeError("check() принимает Expr; для строк используйте check_text()")
        return self._infer(expr)

    def check_text(self, text: str) -> Inferred:
        """Парсинг строки гипотезы с подстановкой символов и операторов."""
        if "__" in text:
            raise AletheiaTypeError("Запрещённые символы '__' во входном выражении")
        safe_globals = {
            "Integer": sp.Integer,
            "Float": sp.Float,
            "Rational": sp.Rational,
            "Symbol": sp.Symbol,
            "Function": sp.Function,
        }
        local = {name: sp.Symbol(name) for name in self.registry}
        local.update({"grad": grad, "div": div, "rot": rot,
                      "curl": rot, "ddt": ddt})
        try:
            expr = parse_expr(text, local_dict=local, global_dict=safe_globals)
        except Exception as e:
            raise AletheiaTypeError(f"Не удалось разобрать выражение: {e}") from e
        return self.check(expr)

    # ---- внутренний проход ----
    def _infer(self, expr) -> Inferred:
        if isinstance(expr, (sp.Integer, sp.Float, sp.Rational)):
            return Inferred(0, DIMLESS, False, False)

        if isinstance(expr, sp.Symbol):
            info = self.registry.get(expr.name)
            if info is None:
                raise AletheiaTypeError(
                    f"Неизвестный символ '{expr.name}' — его нет в реестре"
                )
            return Inferred(info.rank, info.unit, False,
                            info.role in _FIELD_ROLES)

        if isinstance(expr, sp.Add):
            terms = [self._infer(a) for a in expr.args]
            head, rest = terms[0], terms[1:]
            for t in rest:
                if t.rank != head.rank:
                    raise AletheiaTypeError(
                        f"Нельзя складывать скаляр и вектор: '{expr}'"
                    )
                if not _units_equal(t.unit, head.unit):
                    raise AletheiaTypeError(
                        f"Несовместимые единицы в сумме '{expr}': "
                        f"{t.unit} и {head.unit}"
                    )
            return Inferred(head.rank, head.unit,
                            any(t.nonlinear for t in terms),
                            any(t.is_field for t in terms))

        if isinstance(expr, sp.Mul):
            factors = [self._infer(a) for a in sp.Mul.make_args(expr)]
            rank_sum = sum(f.rank for f in factors)
            vec_count = sum(1 for f in factors if f.rank == 1)
            if vec_count > 1:
                raise AletheiaTypeError(
                    f"Произведение двух векторных полей не поддерживается: "
                    f"'{expr}'. Используйте тождества векторного анализа"
                )
            unit = DIMLESS
            field_count = 0
            for f in factors:
                unit = unit * f.unit
                field_count += 1 if f.is_field else 0
            return Inferred(rank_sum, unit, field_count >= 2,
                            vec_count == 1 or field_count >= 1)

        if isinstance(expr, sp.Pow):
            base = self._infer(expr.base)
            if base.rank != 0:
                raise AletheiaTypeError(
                    f"Возведение в степень допустимо только для скаляров: '{expr}'"
                )
            if not expr.exp.is_number:
                raise AletheiaTypeError(f"Показатель степени должен быть числом: '{expr}'")
            return Inferred(0, base.unit**expr.exp, base.nonlinear, base.is_field)

        if isinstance(expr, sp.Derivative):
            raise AletheiaTypeError(
                "Явная производная Derivative не поддерживается — "
                "используйте оператор ddt()"
            )

        if isinstance(expr, sp.core.function.AppliedUndef):
            name = _ALIASES.get(expr.func.__name__, expr.func.__name__)
            if name not in OP_TABLE:
                raise AletheiaTypeError(
                    f"Неизвестная функция '{expr.func.__name__}' — "
                    f"доступны grad/div/rot/curl/ddt"
                )
            if len(expr.args) != 1:
                raise AletheiaTypeError(
                    f"Оператор '{name}' принимает ровно один аргумент: '{expr}'"
                )
            arg = self._infer(expr.args[0])
            exp_rank, res_rank, unit_div = OP_TABLE[name]
            if exp_rank is not None and arg.rank != exp_rank:
                kind = "вектор" if exp_rank == 1 else "скаляр"
                raise AletheiaTypeError(
                    f"Оператор '{name}' применим только к {kind}у: '{expr}'"
                )
            if exp_rank is None:  # ddt: ранг сохраняется
                return Inferred(arg.rank, arg.unit / unit_div,
                                arg.nonlinear, True)
            return Inferred(res_rank, arg.unit / unit_div, arg.nonlinear, True)

        raise AletheiaTypeError(f"Неподдерживаемый узел выражения: {expr}")
