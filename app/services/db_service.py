import os
import random
from faker import Faker
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

fake = Faker('es')

# Obtenemos la URL de Railway automáticamente (prioriza MYSQL_URL o DATABASE_URL)
DATABASE_URL = os.getenv("MYSQL_URL") or os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Corregimos el protocolo para SQLAlchemy + PyMySQL
    if DATABASE_URL.startswith("mysql://"):
        DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
else:
    DATABASE_URL = "sqlite:///./personas.db"

# Creamos el engine (añadimos connect_args si fuera necesario, pero la URL de Railway ya trae todo)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
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
            print("📦 Datos iniciales insertados correctamente.")
    finally:
        db.close()

def get_persona_data():
    use_db = random.choice([True, False])
    
    if use_db:
        db = SessionLocal()
        try:
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
            print(f"Error en BD, usando Faker: {e}")
        finally:
            db.close()

    return {
        "nombres": fake.first_name(),
        "apellidos": fake.last_name(),
        "email": fake.email(domain=random.choice(["gmail.com", "outlook.com", "hotmail.com"])),
        "telefono": f"9{random.randint(10000000, 99999999)}",
        "dni": str(random.randint(10000000, 99999999))
    }