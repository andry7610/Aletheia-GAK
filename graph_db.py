import sqlite3
import sympy as sp


class AletheiaMemory:
    def __init__(self, db_path=":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

        # Канонические связи констант
        self.relations = {
            sp.Symbol("hbar"): sp.Symbol("h") / (2 * sp.pi)
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

    def get_symbols_dict(self) -> dict[str, str]:
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
        }
        return sp.parse_expr(
            expr_str.replace("^", "**"),
            local_dict=safe_locals,
            global_dict=safe_globals,
        )

    def check_algebraic_law(
        self, proposed_lhs_str: str, proposed_rhs_str: str, law_name: str
    ) -> tuple[bool, str]:
        """Безопасная алгебраическая сверка формулы с каноническим законом."""
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

        try:
            canonical_lhs = self._safe_parse(row["lhs"], safe_locals).subs(self.relations)
            canonical_rhs = self._safe_parse(row["rhs"], safe_locals).subs(self.relations)

            proposed_lhs = self._safe_parse(proposed_lhs_str, safe_locals).subs(self.relations)
            proposed_rhs = self._safe_parse(proposed_rhs_str, safe_locals).subs(self.relations)
        except Exception as e:
            return False, f"Ошибка безопасного парсинга SymPy: {e}"

        diff_lhs = sp.simplify(proposed_lhs - canonical_lhs)
        diff_rhs = sp.simplify(proposed_rhs - canonical_rhs)

        if diff_lhs == 0 and diff_rhs == 0:
            return True, f"OK: совпадает с каноническим законом '{law_name}'."
        return (
            False,
            f"ОШИБКА: физика не сходится с '{law_name}'. "
            f"Разница: {diff_lhs} = {diff_rhs}. Проверьте константы (например, h vs hbar).",
        )


if __name__ == "__main__":
    mem = AletheiaMemory()
    mem.add_quantity("h", "J*s", "Постоянная Планка")
    mem.add_quantity("hbar", "J*s", "Приведенная постоянная Планка")
    mem.add_quantity("f", "1/s", "Частота")
    mem.add_quantity("E", "J", "Энергия")

    mem.add_law("photon_energy", "E", "h * f")

    ok, msg = mem.check_algebraic_law("E", "h * f", "photon_energy")
    print(f"Тест 1 (Правильно E = h*f): {'[PASS]' if ok else '[FAIL]'} -> {msg}")

    ok, msg = mem.check_algebraic_law("E", "hbar * f", "photon_energy")
    print(f"Тест 2 (Ловушка E = hbar*f): {'[PASS]' if ok else '[FAIL]'} -> {msg}")

    ok, msg = mem.check_algebraic_law("E", "hbar * 2 * pi * f", "photon_energy")
    print(f"Тест 3 (Эквивалент E = hbar*2*pi*f): {'[PASS]' if ok else '[FAIL]'} -> {msg}")

    ok, msg = mem.check_algebraic_law("E", "__import__('os').system('echo hack')", "photon_energy")
    print(f"Тест 4 (Защита от инъекции): {'[PASS]' if ok else '[FAIL]'} -> {msg}")
