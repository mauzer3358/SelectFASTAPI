from fastapi import FastAPI, HTTPException, Query, Depends, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional

# Инициализация базы данных
DATABASE_URL = "sqlite:///./directors.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Определение модели режиссера
class Director(Base):
    __tablename__ = "directors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    genre = Column(String)
    experience = Column(Integer)
    budget = Column(Integer)


# Создание таблиц
Base.metadata.create_all(bind=engine)


# Pydantic схема для входных данных
class DirectorCreate(BaseModel):
    name: str
    genre: str
    experience: int
    budget: int


# Инициализация FastAPI
app = FastAPI()


# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Форма для добавления режиссера
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <body>
            <h2>Добавить режиссера</h2>
            <form action="/directors/" method="post">
                Имя: <input type="text" name="name"><br>
                Жанр: <input type="text" name="genre"><br>
                Опыт: <input type="number" name="experience"><br>
                Бюджет: <input type="number" name="budget"><br>
                <input type="submit" value="Добавить">
            </form>
            <h2>Поиск режиссера</h2>
            <form action="/directors/search/" method="get">
                Имя: <input type="text" name="name"><br>
                Опыт (мин): <input type="number" name="min_experience"><br>
                Бюджет (макс): <input type="number" name="max_budget" value="0"><br>
                <input type="submit" value="Найти">
            </form>
        </body>
    </html>
    """


# Добавление нового режиссера в базу данных
@app.post("/directors/", response_class=HTMLResponse)
def create_director(
        name: str = Form(...),
        genre: str = Form(...),
        experience: int = Form(...),
        budget: int = Form(...),
        db: Session = Depends(get_db)
):
    db_director = Director(name=name, genre=genre, experience=experience, budget=budget)
    db.add(db_director)
    db.commit()
    db.refresh(db_director)
    return f"""
    <html>
        <body>
            <h2>Режиссер добавлен</h2>
            <p>Имя: {db_director.name}</p>
            <p>Жанр: {db_director.genre}</p>
            <p>Опыт: {db_director.experience} лет</p>
            <p>Бюджет: {db_director.budget} у.е. за смену</p>
            <a href="/">Вернуться на главную</a>
        </body>
    </html>
    """


# Поиск режиссеров по указанным критериям
@app.get("/directors/search/", response_class=HTMLResponse)
def search_director(
        name: Optional[str] = Query(None),
        min_experience: Optional[int] = Query(None),
        max_budget: Optional[int] = Query(None),
        db: Session = Depends(get_db)
):
    query = db.query(Director)
    filters = []

    if name:
        filters.append(Director.name.ilike(f"%{name}%"))
    if min_experience is not None:
        filters.append(Director.experience >= min_experience)
    if max_budget is not None and max_budget > 0:
        filters.append(Director.budget <= max_budget)

    if filters:
        query = query.filter(*filters)

    directors = query.all()

    if not directors:
        directors = db.query(Director).all()

    result_html = "<html><body><h2>Найденные режиссеры</h2><ul>"
    for director in directors:
        result_html += f"<li>{director.name} - {director.genre}, Опыт: {director.experience} лет, Бюджет: {director.budget} у.е.</li>"
    result_html += "</ul><a href='/'>Вернуться на главную</a></body></html>"
    return result_html
