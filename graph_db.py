import sqlite3
import sympy as sp


class AletheiaMemory:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

        # Канонические связи констант
        self.relations = {
            sp.Symbol("hbar"): sp.Symbol("h") / (2 * sp.pi),
            # Кулоновская постоянная: k_e = 1 / (4 * pi * epsilon_0)
            sp.Symbol("k_e"): 1 / (4 * sp.pi * sp.Symbol("epsilon_0"))
        }

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quantities (
                name TEXT PRIMARY KEY,
                dimension TEXT,
                description TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS laws (
                name TEXT PRIMARY KEY,
                lhs TEXT,
                rhs TEXT
            )
        ''')
        self.conn.commit()

    def add_quantity(self, name: str, dimension: str, description: str = ""):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO quantities (name, dimension, description) VALUES (?, ?, ?)",
            (name, dimension, description),
        )
        self.conn.commit()

    def add_law(self, name: str, lhs_str: str, rhs_str: str):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO laws (name, lhs, rhs) VALUES (?, ?, ?)",
            (name, lhs_str, rhs_str),
        )
        self.conn.commit()

    def get_symbols_dict(self) -> dict:
        """Возвращает словарь известных размерностей для AletheiaVerifier."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, dimension FROM quantities")
        return {row["name"]: row["dimension"] for row in cursor.fetchall()}

    def _safe_parse(self, expr_str: str, safe_locals: dict) -> sp.Expr:
        if "__" in expr_str:
            raise ValueError("Запрещённые символы '__' во входном выражении")
        safe_globals = {
            "Integer": sp.Integer,
            "Float": sp.Float,
            "Rational": sp.Rational,
            # Безопасный парсер без Symbol не может создать новые символы:
            # parse_expr падает с "name 'Symbol' is not defined"
            "Symbol": sp.Symbol,
        }
        return sp.parse_expr(
            expr_str.replace("^", "**"),
            local_dict=safe_locals,
            global_dict=safe_globals,
        )

    def _substitute_equivalent(self, F_from: sp.Expr, F_to: sp.Expr) -> bool:
        """Проверяет, что F_to обращается в ноль на всех решениях F_from = 0."""
        if F_from == 0:
            return sp.simplify(F_to) == 0
        for sym in list(F_from.free_symbols):
            try:
                sols = sp.solve(F_from, sym)
            except Exception:
                continue
            if not isinstance(sols, (list, tuple)):
                sols = [sols]
            for sol in sols:
                try:
                    sub = sp.simplify(sp.cancel(F_to.subs(sym, sol)))
                except Exception:
                    continue
                if sub == 0:
                    return True
                equals = getattr(sub, "equals", None)
                if equals is not None and sub.equals(0):
                    return True
        return False

    def check_algebraic_law(
        self, proposed_lhs_str: str, proposed_rhs_str: str, law_name: str
    ) -> tuple:
        """
        Безопасная алгебраическая сверка формулы с каноническим законом.

        Сравнивается тождество ЦЕЛЫХ уравнений, а не их частей. Проверка
        инвариантна к:
          - обмену сторон (E = m*c**2  <=>  m*c**2 = E);
          - переносу слагаемых через знак равенства;
          - умножению уравнения на константу (0 = 2*J эквивалентно J = 0);
          - умножению на переменный множитель (m = E/c**2 эквивалентно E = m*c**2).
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT lhs, rhs FROM laws WHERE name = ?", (law_name,))
        row = cursor.fetchone()
        if not row:
            return False, f"Закон '{law_name}' не найден в Гиппокампе."

        # Собираем белый список символов прямо из базы знаний + базовые мат. функции
        safe_locals = {
            name: sp.Symbol(name) for name in self.get_symbols_dict().keys()
        }
        safe_locals.update({
            "pi": sp.pi,
            "exp": sp.exp,
            "log": sp.log,
            "sin": sp.sin,
            "cos": sp.cos,
            "sqrt": sp.sqrt,
        })
        # Символы из канонических связей (hbar, k_e, ...) должны быть
        # известны парсеру, даже если их нет в таблице quantities
        for sym, repl in self.relations.items():
            safe_locals.setdefault(str(sym), sym)
            for s in repl.free_symbols:
                safe_locals.setdefault(str(s), s)

        try:
            proposed_lhs_raw = self._safe_parse(proposed_lhs_str, safe_locals)
            proposed_rhs_raw = self._safe_parse(proposed_rhs_str, safe_locals)

            # Защита от неизвестных символов: parse_expr молча создаёт новые
            # Symbol для опечаток, поэтому явно отсекаем всё вне белого списка
            allowed = set(safe_locals.values())
            for sym, repl in self.relations.items():
                allowed.add(sym)
                allowed |= repl.free_symbols
            unknown = (proposed_lhs_raw.free_symbols
                       | proposed_rhs_raw.free_symbols) - allowed
            if unknown:
                names = ", ".join(sorted(str(s) for s in unknown))
                return False, (
                    f"ОШИБКА: неизвестные символы {names}. "
                    f"Добавьте их через add_quantity() или исправьте опечатку."
                )

            canonical_lhs = self._safe_parse(row["lhs"], safe_locals).subs(self.relations)
            canonical_rhs = self._safe_parse(row["rhs"], safe_locals).subs(self.relations)
            proposed_lhs = proposed_lhs_raw.subs(self.relations)
            proposed_rhs = proposed_rhs_raw.subs(self.relations)
        except Exception as e:
            return False, f"Ошибка безопасного парсинга SymPy: {e}"

        # Разность сторон: инвариантна к обмену сторон и переносу слагаемых
        prop = sp.together(proposed_lhs - proposed_rhs)
        canon = sp.together(canonical_lhs - canonical_rhs)

        # Шаг 1: прямое тождество
        residual = sp.simplify(sp.cancel(prop - canon))
        if residual == 0:
            return True, f"OK: совпадает с каноническим законом '{law_name}'."

        # Шаг 2: пропорциональность (уравнение умножено на ненулевую константу)
        if canon != 0:
            try:
                ratio = sp.simplify(sp.cancel(prop / canon))
                if ratio.is_number and ratio != 0:
                    return True, (
                        f"OK: эквивалентно каноническому закону '{law_name}' "
                        f"(умножено на {ratio})."
                    )
            except Exception:
                pass

        # Шаг 3: эквивалентность нулевых множеств через подстановку решения
        try:
            if (self._substitute_equivalent(canon, prop)
                    and self._substitute_equivalent(prop, canon)):
                return True, (
                    f"OK: эквивалентно каноническому закону '{law_name}' "
                    f"в преобразованной форме."
                )
        except Exception:
            pass

        return (
            False,
            f"ОШИБКА: физика не сходится с '{law_name}'. "
            f"Разница: {residual}. Проверьте константы и степени.",
        )
