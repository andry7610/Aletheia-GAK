# seed_db.py
# Наполнение Гиппокампа (базы знаний) константами CODATA и каноническими законами.

from graph_db import AletheiaMemory

def populate_knowledge_base(db_path="aletheia_memory.db"):
    memory = AletheiaMemory(db_path=db_path)
    
    print("[*] Начинаем наполнение базы знаний...")

    # ==========================================
    # 1. ФУНДАМЕНТАЛЬНЫЕ КОНСТАНТЫ (CODATA 2018/2022)
    # ==========================================
    constants = [
        ("c", "m/s", "Скорость света в вакууме"),
        ("G", "m**3 / (kg * s**2)", "Гравитационная постоянная"),
        ("h", "J*s", "Постоянная Планка"),
        ("hbar", "J*s", "Приведенная постоянная Планка"),
        ("k_B", "J/K", "Постоянная Больцмана"),
        ("e", "C", "Элементарный заряд"),
        ("m_e", "kg", "Масса электрона"),
        ("m_p", "kg", "Масса протона"),
        ("epsilon_0", "F/m", "Электрическая постоянная"),
        ("mu_0", "H/m", "Магнитная постоянная"),
        ("N_A", "1/mol", "Число Авогадро"),
        ("R", "J/(mol*K)", "Универсальная газовая постоянная"),
        ("sigma_SB", "W/(m**2 * K**4)", "Постоянная Стефана-Больцмана"),
    ]
    
    for name, dim, desc in constants:
        memory.add_quantity(name, dim, desc)
        
    print(f"  [+] Загружено {len(constants)} фундаментальных констант.")

    # ==========================================
    # 2. КАНОНИЧЕСКИЕ ФИЗИЧЕСКИЕ ЗАКОНЫ
    # ==========================================
    # Список кортежей: (имя_закона, левая_часть, правая_часть)
    laws = [
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
        ("lorentz_force", "F", "q * E + q * v * B"), # Векторная сумма в скалярном виде для проверки
        ("faraday_induction", "EMF", "- dPhi_dt"),
        
        # Термодинамика и статфизика
        ("ideal_gas_law", "P * V", "n * R * T"),
        ("boltzmann_energy", "E", "k_B * T"),
        
        # Волновая физика
        ("wave_equation", "v", "lambda_ * f"),
    ]
    
    for name, lhs, rhs in laws:
        memory.add_law(name, lhs, rhs)
        
    print(f"  [+] Загружено {len(laws)} канонических законов.")
    
    # ==========================================
    # 3. ДОПОЛНИТЕЛЬНЫЕ СВЯЗИ (SymPy relations)
    # ==========================================
    # В graph_db.py уже есть hbar = h / (2*pi). 
    # Добавим кулоновскую постоянную k_e = 1 / (4 * pi * epsilon_0)
    # Для этого расширим словарь relations прямо в graph_db.py (см. ниже)
    
    memory.close()
    print(f"\n[!] База данных '{db_path}' готова к работе!")

if __name__ == "__main__":
    populate_knowledge_base()