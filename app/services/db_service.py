import os
import random
from faker import Faker
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

fake = Faker('es')

# 1. Intentamos leer DATABASE_URL o MYSQL_URL que provee Railway a
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL")

if DATABASE_URL:
    # Aseguramos que SQLAlchemy use el driver pymysql para MySQL
    if DATABASE_URL.startswith("mysql://"):
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
else:
    # 2. Si no hay una URL directa, intentamos armarla con las variables separadas de Railway
    mysql_host = os.getenv("MYSQLHOST")
    if mysql_host:
        user = os.getenv("MYSQLUSER", "root")
        password = os.getenv("MYSQL_PASSWORD") or os.getenv("MYSQLPASSWORD") or os.getenv("MYSQL_ROOT_PASSWORD", "")
        port = os.getenv("MYSQLPORT", "3306")
        database = os.getenv("MYSQL_DATABASE") or os.getenv("MYSQLDATABASE", "railway")
        DATABASE_URL = f"mysql+pymysql://{user}:{password}@{mysql_host}:{port}/{database}"
    else:
        # 3. Plan B local: SQLite si estás probando en tu PC
        DATABASE_URL = "sqlite:///./personas.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PersonaModel(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    telefono = Column(String(50), nullable=False)
    dni = Column(String(50), nullable=False)

def init_db():
    # Crea las tablas automáticamente si no existen
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        count = db.query(PersonaModel).count()
        if count == 0:
            sample_data = []
            for _ in range(50):
                persona = PersonaModel(
                    nombres=fake.first_name(),
                    apellidos=fake.last_name(),
                    email=fake.email(domain="gmail.com"),
                    telefono=f"9{random.randint(10000000, 99999999)}",
                    dni=str(random.randint(10000000, 99999999))
                )
                sample_data.append(persona)
            
            db.add_all(sample_data)
            db.commit()
            print("📦 Datos iniciales insertados en la base de datos correctamente.")
    finally:
        db.close()

def get_persona_data():
    # Lógica híbrida: alterna entre base de datos real (MySQL/SQLite) y datos aleatorios de Faker
    use_db = random.choice([True, False])
    
    if use_db:
        db = SessionLocal()
        try:
            # Selecciona aleatoriamente usando RAND() para MySQL o RANDOM() para SQLite
            random_func = text("RANDOM()") if "sqlite" in DATABASE_URL.lower() else text("RAND()")
            persona = db.query(PersonaModel).order_by(random_func).first()
            
            if persona:
                return {
                    "nombres": persona.nombres,
                    "apellidos": persona.apellidos,
                    "email": persona.email,
                    "telefono": persona.telefono,
                    "dni": persona.dni
                }
        except Exception as e:
            print(f"Error consultando la base de datos, usando plan B aleatorio: {e}")
        finally:
            db.close()

    # Plan B / Opción aleatoria con Faker
    return {
        "nombres": fake.first_name(),
        "apellidos": fake.last_name(),
        "email": fake.email(domain=random.choice(["gmail.com", "outlook.com", "hotmail.com"])),
        "telefono": f"9{random.randint(10000000, 99999999)}",
        "dni": str(random.randint(10000000, 99999999))
    }