import sqlite3
import random
from faker import Faker

fake = Faker('es')
DB_NAME = "personas.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres TEXT NOT NULL,
            apellidos TEXT NOT NULL,
            email TEXT NOT NULL,
            telefono TEXT NOT NULL,
            dni TEXT NOT NULL
        )
    ''')
    
    # Insertar datos de prueba iniciales si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM personas")
    count = cursor.fetchone()[0]
    if count == 0:
        sample_data = []
        for _ in range(50):
            sample_data.append((
                fake.first_name(),
                fake.last_name(),
                fake.email(domain="gmail.com"),
                f"9{random.randint(10000000, 99999999)}",
                str(random.randint(10000000, 99999999))
            ))
        cursor.executemany('''
            INSERT INTO personas (nombres, apellidos, email, telefono, dni)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_data)
        conn.commit()
    conn.close()

def get_persona_data():
    """Consulta aleatoria a la base de datos de personas o decide inventarlos con Faker"""
    # El servidor decide de vez en cuando si usa la DB o inventa dinámicamente
    use_db = random.choice([True, False])
    
    if use_db:
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT nombres, apellidos, email, telefono, dni FROM personas ORDER BY RANDOM() LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    "nombres": row[0],
                    "apellidos": row[1],
                    "email": row[2],
                    "telefono": row[3],
                    "dni": row[4]
                }
        except Exception:
            pass

    # Plan B o inventado directamente con formato real (@gmail.com, etc.)
    return {
        "nombres": fake.first_name(),
        "apellidos": fake.last_name(),
        "email": fake.email(domain=random.choice(["gmail.com", "outlook.com", "hotmail.com"])),
        "telefono": f"9{random.randint(10000000, 99999999)}",
        "dni": str(random.randint(10000000, 99999999))
    }