# seed_db.py
# Наполнение Гиппокампа (базы знаний): константы CODATA-2022,
# атомарные операторы и канонические законы, включая первый
# закон с нулевой правой частью (уравнение непрерывности).

import math


from graph_db import AletheiaMemory
from maxwell_seed import MAXWELL_FIELDS


# ------------------------------------------------------------------
# Справочник констант CODATA-2022.
# Формат записи: (имя, значение, размерность, описание).
# Точные константы зафиксированы SI-2019, погрешности нет.
# Вычисляемые константы (hbar, R, sigma_SB) выводятся из точных.
# ------------------------------------------------------------------
CONSTANTS = [
    ("c", 299792458.0, "m/s", "Скорость света в вакууме"),
    ("G", 6.67430e-11, "m**3/(kg*s**2)", "Гравитационная постоянная"),
    ("h", 6.62607015e-34, "J*s", "Постоянная Планка"),
    ("hbar", None, "J*s", "Приведённая постоянная Планка"),
    ("k_B", 1.380649e-23, "J/K", "Постоянная Больцмана"),
    ("e", 1.602176634e-19, "C", "Элементарный заряд"),
    ("m_e", 9.1093837139e-31, "kg", "Масса электрона"),
    ("m_p", 1.6726219259e-27, "kg", "Масса протона"),
    ("epsilon_0", 8.8541878188e-12, "F/m", "Электрическая постоянная"),
    ("mu_0", 1.25663706127e-6, "H/m", "Магнитная постоянная"),
    ("N_A", 6.02214076e23, "1/mol", "Число Авогадро"),
    ("R", None, "J/(mol*K)", "Универсальная газовая постоянная"),
    ("sigma_SB", None, "W/(m**2*K**4)", "Постоянная Стефана-Больцмана"),
]

# Вычисляемые значения: строго из точных констант, без ручного округления
_HBAR = 6.62607015e-34 / (2 * math.pi)
_R = 6.02214076e23 * 1.380649e-23
_SIGMA_SB = math.pi**2 * (1.380649e-23)**4 / (60 * _HBAR**3 * 299792458.0**2)

COMPUTED_VALUES = {
    "hbar": _HBAR,
    "R": _R,
    "sigma_SB": _SIGMA_SB,
}

# Быстрый доступ: имя -> числовое значение
CODATA_VALUES = {name: COMPUTED_VALUES.get(name, value) for name, value, _, _ in CONSTANTS}

# ------------------------------------------------------------------
# Атомарные дифференциальные операторы.
# Кл/(м^3 * с) = А/м^3, поэтому размерности обеих величин одинаковы.
# Вынесены на уровень модуля, чтобы тесты могли импортировать напрямую.
# ------------------------------------------------------------------
OPERATORS = [
    ("div_J", "A/m**3", "Оператор дивергенции плотности тока"),
    ("drho_dt", "A/m**3", "Частная производная плотности заряда по времени"),
]

# ------------------------------------------------------------------
# Канонические законы: (имя_закона, левая_часть, правая_часть).
# Тоже на уровне модуля — единый источник истины для базы и тестов.
# ------------------------------------------------------------------
LAWS = [
    # Механика
    ("newton_second", "F", "m * a"),
    ("kinetic_energy", "E_k", "0.5 * m * v**2"),
    ("momentum", "p", "m * v"),
    # Специальная теория относительности
    ("einstein_mass_energy", "E", "m * c**2"),
    # Квантовая механика
    ("planck_energy", "E", "h * f"),
    ("photon_energy_wavelength", "E", "h * c / lambda_"),
    ("photon_momentum", "p", "h / lambda_"),
    # Электродинамика
    ("ohm_law", "U", "I * R"),
    ("coulomb_law", "F", "k_e * q1 * q2 / r**2"),
    ("lorentz_force", "F", "q * E + q * v * B"),
    ("faraday_induction", "EMF", "- dPhi_dt"),
    # Термодинамика и статфизика
    ("ideal_gas_law", "P * V", "n * R * T"),
    ("boltzmann_energy", "E", "k_B * T"),
    # Волновая физика
    ("wave_equation", "v", "lambda_ * f"),
    # Сохранение заряда: первый канон с нулевой правой частью
    ("continuity_equation", "div_J + drho_dt", "0"),
    # Электродинамика, v1.2: уравнения Максвелла (канон с нулевой правой частью)
    ("faraday_law", "rot(E) + ddt(B)", "0"),
    ("gauss_electric", "div(E)", "rho/epsilon_0"),
    ("ampere_no_displacement", "rot(B)", "mu_0*j"),
    ("gauss_magnetic", "div(B)", "0"),
]


def verify_codata_consistency():
    # Самопроверка базы: тождества между константами CODATA-2022.
    c = 299792458.0
    h = 6.62607015e-34
    k_B = 1.380649e-23
    N_A = 6.02214076e23
    eps_0 = 8.8541878188e-12
    mu_0 = 1.25663706127e-6

    checks = []

    # 1) eps_0 * mu_0 * c^2 = 1 (тождество SI-2019)
    r1 = eps_0 * mu_0 * c**2
    checks.append(("epsilon_0 * mu_0 * c**2 = 1", math.isclose(r1, 1.0, rel_tol=1e-9), r1))

    # 2) hbar = h / (2*pi)
    r2 = _HBAR * 2 * math.pi
    checks.append(("hbar * 2*pi = h", math.isclose(r2, h, rel_tol=1e-15), r2))

    # 3) R = N_A * k_B
    r3 = N_A * k_B
    checks.append(("R = N_A * k_B", math.isclose(_R, r3, rel_tol=1e-15), _R))

    # 4) sigma_SB = pi^2 * k_B^4 / (60 * hbar^3 * c^2)
    sigma_ref = math.pi**2 * k_B**4 / (60 * _HBAR**3 * c**2)
    r4 = abs(_SIGMA_SB - sigma_ref) / sigma_ref
    checks.append(("sigma_SB из точных констант", r4 < 1e-9, _SIGMA_SB))

    all_ok = True
    for name, passed, value in checks:
        status = "OK" if passed else "FAIL"
        print(f"  [{status}] {name} (значение: {value:.12g})")
        all_ok = all_ok and passed
    if not all_ok:
        raise AssertionError("База констант несогласованна: тождество CODATA не сошлось.")
    return True


def populate_knowledge_base(db_path="aletheia_memory.db"):
    memory = AletheiaMemory(db_path=db_path)

    print("[*] Начинаем наполнение базы знаний...")

    # 1. ФУНДАМЕНТАЛЬНЫЕ КОНСТАНТЫ (CODATA 2022)
    for name, value, dim, desc in CONSTANTS:
        memory.add_quantity(name, dim, desc)
    print(f"  [+] Загружено {len(CONSTANTS)} фундаментальных констант.")

    # 1а. ДИФФЕРЕНЦИАЛЬНЫЕ ОПЕРАТОРЫ
    for name, dim, desc in OPERATORS:
        memory.add_quantity(name, dim, desc)
    print(f"  [+] Загружено {len(OPERATORS)} дифференциальных операторов.")

    # 1б. ПОЛЯ ЭЛЕКТРОДИНАМИКИ (v1.2) — только до законов Максвелла!
    for name, dim, desc in MAXWELL_FIELDS:
        memory.add_quantity(name, dim, desc)
    print(f"  [+] Загружено {len(MAXWELL_FIELDS)} полей электродинамики.")

    # 2. КАНОНИЧЕСКИЕ ФИЗИЧЕСКИЕ ЗАКОНЫ
    # В LAWS теперь 19 законов, включая 4 уравнения Максвелла.
    # Порядок соблюдён: поля уже в quantities — _safe_parse их пропустит.
    for name, lhs, rhs in LAWS:
        memory.add_law(name, lhs, rhs)
    print(f"  [+] Загружено {len(LAWS)} канонических законов.")

    # 3. САМОПРОВЕРКА БАЗЫ
    print("[*] Проверка самосогласованности констант CODATA:")
    verify_codata_consistency()

    print(f"\n[!] База данных '{db_path}' готова к работе!")
    return memory


if __name__ == "__main__":
    memory = populate_knowledge_base()
    memory.close()
