# -*- coding: utf-8 -*-
"""
derivation — слой вывода: получение законов из законов (v1.3).

Слой тождеств (identities.py) схлопывает тавтологии, истинные для любых полей.
Слой вывода идёт дальше: он использует СВОЙСТВА ОПЕРАТОРОВ, истинные всегда,
чтобы выводить новые законы из уже существующих. Правила:

  1. Линейность grad/div/rot: раскрытие по суммам и скалярным множителям.
     Множители-векторы берутся из реестра (vector_fields) — слой вывода
     не угадывает ранги, а ЧИТАЕТ их у реестра. Ошибки рангов всё равно
     ловит RankChecker каскада — защита в глубину.
  2. Коммутативность div и ddt (теорема Шварца): div(ddt(f)) == ddt(div(f)).
  3. Вынос константы из-под ddt: ddt(k*f) -> k*ddt(f); ddt(const) -> 0.

Ни одно из правил не является физическим законом, поэтому вывод ничего
не подсовывает в канон: результат возвращается как выражение + журнал шагов,
сверка с каноном — явно, через zero_form_matches.

Визитная карточка v1.3 — непрерывность из полного Ампера и Гаусса:

    div(rot(B) - mu_0*(j + epsilon_0*ddt(E))) = 0
      --тождество div(rot(B)) = 0-->   -mu_0*(div(j) + epsilon_0*ddt(div(E))) = 0
      --Гаусс: div(E) = rho/eps_0-->   -mu_0*(div(j) + epsilon_0*ddt(rho/eps_0)) = 0
      --eps_0 — константа-->           -mu_0*(div(j) + ddt(rho)) = 0
      --множитель != 0-->              div(j) + ddt(rho) = 0
      --псевдоним канона v1.1-->       div(j) + drho_dt = 0

Конвенция имён: в каноне v1.1 производная скалярного поля по времени хранится
как именованный символ (ddt(rho) -> drho_dt). Псевдоним применяется ЯВНО
последним шагом и виден в журнале — это не тихая подмена.
"""
from typing import FrozenSet, List, Optional, Set, Tuple

import sympy as sp
from sympy.core.function import AppliedUndef
from sympy.parsing.sympy_parser import parse_expr

from vector_ops import AletheiaTypeError, grad, div, rot, curl, ddt
from identities import simplify_identities

__all__ = [
    "expand_op_linearly", "commute_div_ddt", "extract_constants_from_ddt",
    "normalize_zero_form", "apply_canon_alias", "derive_continuity",
    "zero_form_matches",
]

# распознавание операторов — в согласии с identities.py
_OP_ALIASES = {"curl": "rot"}
_OP_NAMES = {"grad", "div", "rot", "ddt"}

_SAFE_GLOBALS = {
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    "Symbol": sp.Symbol,
    "Function": sp.Function,
}


def _op_name(func) -> Optional[str]:
    """Каноническое имя оператора или None."""
    name = func.__name__
    if name in _OP_ALIASES:
        name = _OP_ALIASES[name]
    return name if name in _OP_NAMES else None


def _is_op_node(expr) -> bool:
    return (isinstance(expr, AppliedUndef)
            and _op_name(expr.func) is not None)


def _safe_parse(text: str) -> sp.Expr:
    """Безопасный разбор: только числа, Symbol/Function и наши операторы."""
    if "__" in text:
        raise AletheiaTypeError("Запрещённые символы '__' во входном выражении")
    local = {"grad": grad, "div": div, "rot": rot, "curl": curl, "ddt": ddt}
    try:
        return parse_expr(text, local_dict=local, global_dict=_SAFE_GLOBALS)
    except Exception as e:
        raise AletheiaTypeError(f"Не удалось разобрать выражение: {e}") from e


def expand_op_linearly(expr: sp.Expr, op: str = "div",
                       vector_fields: FrozenSet[str] = frozenset()) -> sp.Expr:
    """Линейность: div(A + k*B) -> div(A) + k*div(B), div(k*V) -> k*div(V).

    Раскрывает только ЗАДАННЫЙ оператор. «Единицей» раскрытия служит
    либо операторный узел (например, ddt(E)), либо векторное поле из
    vector_fields. Чисто скалярные произведения не трогаются.
    """
    def is_unit(f: sp.Expr) -> bool:
        return _is_op_node(f) or (isinstance(f, sp.Symbol)
                                  and f.name in vector_fields)

    if isinstance(expr, sp.Add):
        return sp.Add(*[expand_op_linearly(a, op, vector_fields)
                        for a in expr.args])
    if isinstance(expr, sp.Mul):
        return sp.Mul(*[expand_op_linearly(f, op, vector_fields)
                        for f in expr.args])
    if (isinstance(expr, AppliedUndef) and _op_name(expr.func) == op
            and len(expr.args) == 1):
        arg = expr.args[0]
        if isinstance(arg, sp.Add):
            return sp.Add(*[expand_op_linearly(expr.func(a), op, vector_fields)
                            for a in arg.args])
        if isinstance(arg, sp.Mul):
            units, scalars = [], []
            for f in sp.Mul.make_args(arg):
                (units if is_unit(f) else scalars).append(f)
            if len(units) == 1:
                # div(k*V) -> k*div(V): оператор сохраняется, выносится множитель
                return expand_op_linearly(
                    sp.Mul(*scalars, expr.func(units[0])), op, vector_fields)
            if not units:
                return expr  # оператор от чисто скалярного выражения не трогаем
        return expr
    if isinstance(expr, AppliedUndef):
        return expr.func(*[expand_op_linearly(a, op, vector_fields)
                           for a in expr.args])
    return expr


def commute_div_ddt(expr: sp.Expr) -> sp.Expr:
    """Шварц: div(ddt(f)) -> ddt(div(f)). Применяется рекурсивно."""
    if isinstance(expr, sp.Add):
        return sp.Add(*[commute_div_ddt(a) for a in expr.args])
    if isinstance(expr, sp.Mul):
        return sp.Mul(*[commute_div_ddt(f) for f in expr.args])
    if isinstance(expr, AppliedUndef):
        name = _op_name(expr.func)
        if (name == "div" and len(expr.args) == 1
                and isinstance(expr.args[0], AppliedUndef)
                and _op_name(expr.args[0].func) == "ddt"
                and len(expr.args[0].args) == 1):
            inner = expr.args[0].args[0]
            return commute_div_ddt(ddt(div(inner)))
        return expr.func(*[commute_div_ddt(a) for a in expr.args])
    return expr


def _is_const_factor(f: sp.Expr, constants: Set[str]) -> bool:
    """Число, константа из реестра или целочисленная степень константы."""
    if f.is_number:
        return True
    if isinstance(f, sp.Symbol) and f.name in constants:
        return True
    if (isinstance(f, sp.Pow) and isinstance(f.base, sp.Symbol)
            and f.base.name in constants):
        return True
    return False


def extract_constants_from_ddt(expr: sp.Expr, constants: Set[str]) -> sp.Expr:
    """ddt(k*f) -> k*ddt(f); ddt(константы) -> 0."""
    if isinstance(expr, sp.Add):
        return sp.Add(*[extract_constants_from_ddt(a, constants)
                        for a in expr.args])
    if isinstance(expr, sp.Mul):
        return sp.Mul(*[extract_constants_from_ddt(f, constants)
                        for f in expr.args])
    if (isinstance(expr, AppliedUndef) and _op_name(expr.func) == "ddt"
            and len(expr.args) == 1):
        arg = expr.args[0]
        if isinstance(arg, sp.Symbol) and arg.name in constants:
            return sp.S.Zero
        if isinstance(arg, sp.Mul):
            const_f, rest_f = [], []
            for f in sp.Mul.make_args(arg):
                (const_f if _is_const_factor(f, constants) else rest_f).append(f)
            if const_f and rest_f:
                return sp.Mul(*const_f, expr.func(sp.Mul(*rest_f)))
            if const_f and not rest_f:
                return sp.S.Zero
    return expr


def normalize_zero_form(expr: sp.Expr) -> sp.Expr:
    """Нулевая форма k*F = 0 <=> F = 0 при k != 0: снимает общий множитель.

    Снимает ТОЛЬКО общий для всех слагаемых коэффициент (с одинаковым
    числовым отношением) — иначе выражение непропорционально и не трогается.
    """
    expr = sp.expand(expr)
    if not isinstance(expr, sp.Add):
        return expr

    def split(term):
        if _is_op_node(term):
            return sp.S.One, term
        if isinstance(term, sp.Mul):
            ops = [f for f in term.args if _is_op_node(f)]
            if len(ops) == 1:
                others = [f for f in term.args if f is not ops[0]]
                return sp.Mul(*others), ops[0]
        return None

    parts = [split(t) for t in expr.args]
    if any(p is None for p in parts):
        return expr
    c0 = parts[0][0]
    if c0 == 0:
        return expr
    ratios = [sp.simplify(c / c0) for c, _n in parts]
    if all(r == ratios[0] and r != 0 for r in ratios):
        return sp.Add(*[n for _c, n in parts])
    return expr


def apply_canon_alias(expr: sp.Expr) -> sp.Expr:
    """Конвенция имён канона v1.1: ddt(rho) -> drho_dt (производная скалярного поля)."""
    def _match(e):
        return (isinstance(e, AppliedUndef) and _op_name(e.func) == "ddt"
                and len(e.args) == 1 and isinstance(e.args[0], sp.Symbol))

    def _repl(e):
        return sp.Symbol(f"d{e.args[0].name}_dt")

    return expr.replace(_match, _repl)


def derive_continuity(
        ampere_lhs: str = "rot(B) - mu_0*(j + epsilon_0*ddt(E))",
        ampere_rhs: str = "0",
        gauss_from: str = "div(E)",
        gauss_to: str = "rho/epsilon_0",
        constants: FrozenSet[str] = frozenset({"epsilon_0"}),
        vector_fields: FrozenSet[str] = frozenset({"E", "B", "j"}),
) -> Tuple[sp.Expr, List[str]]:
    """Вывод уравнения непрерывности из полного Ампера + Гаусса.

    Возвращает (выражение_нулевой_формы, журнал_шагов).
    vector_fields — векторные поля реестра (в проекте берутся из SymbolInfo).
    """
    steps: List[str] = []

    expr = _safe_parse(f"div(({ampere_lhs}) - ({ampere_rhs}))")
    steps.append("0. дивергенция разности частей закона")

    expr = sp.expand(expr)
    expr = expand_op_linearly(expr, "div", vector_fields)
    steps.append("1. линейность div: раскрытие по суммам и скалярам")

    expr = simplify_identities(expr)
    steps.append("2. тождество div(rot(B)) = 0 (слой v1.2)")

    expr = commute_div_ddt(expr)
    steps.append("3. коммутация div(ddt(f)) -> ddt(div(f)) — Шварц")

    lhs_node = _safe_parse(gauss_from)
    rhs_node = _safe_parse(gauss_to)
    new_expr = expr.replace(lambda e: e == lhs_node, lambda e: rhs_node)
    if new_expr != expr:
        expr = new_expr
        steps.append(f"4. подстановка Гаусса: {gauss_from} -> {gauss_to}")

    expr = extract_constants_from_ddt(expr, set(constants))
    steps.append("5. вынос констант из-под ddt")

    expr = normalize_zero_form(expr)
    steps.append("6. снятие ненулевого скалярного множителя")

    expr = apply_canon_alias(expr)
    steps.append("7. псевдоним канона: ddt(rho) -> drho_dt")

    return expr, steps


def zero_form_matches(derived: sp.Expr, canon_lhs: str,
                      canon_rhs: str = "0") -> bool:
    """Структурная сверка нулевых форм: derived == canon_lhs - canon_rhs."""
    canon = _safe_parse(f"({canon_lhs}) - ({canon_rhs})")
    return sp.expand(derived - canon) == 0
