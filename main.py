from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from sqlalchemy import UniqueConstraint
from fastapi.middleware.cors import CORSMiddleware

class ContestantBase(SQLModel):
    name: str = Field(index=True)
    age: int

class Contestant(ContestantBase, table=True):
    __table_args__ = (UniqueConstraint("phone"),)
    id: int | None = Field(default=None, primary_key=True)
    phone: int

class ContestantPublic(ContestantBase):
    phone: int

class ContestantCreate(ContestantBase):
    phone: int

class ContestantUpdate(ContestantBase):
    name: str | None = None
    age: int | None = None


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()
origins = [
    "http://localhost:5173",
    "http://localhost:8000",
    "https://kisxo.github.io/",
    "https://kisxo.github.io",
    "https://magicminute.online"

]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# ita stands for increadible talent of assam
@app.get("/ita/")
async def read_contestant(phone: int, session: SessionDep):
    statement = select(Contestant).where(Contestant.phone == phone)
    contestant = session.exec(statement).first()
    return contestant

@app.post("/ita", response_model=ContestantPublic)
async def create_contestant(contestant: ContestantCreate, session: SessionDep):
    db_contestant = Contestant.model_validate(contestant)
    session.add(db_contestant)
    session.commit()
    session.refresh(db_contestant)
    return db_contestant

@app.patch("/ita/", response_model=ContestantPublic)
def update_contestant(phone: int, contestant: ContestantUpdate, session: SessionDep):
    statement = select(Contestant).where(Contestant.phone == phone)
    contestant_db = session.exec(statement).first()
    if not contestant_db:
        raise HTTPException(status_code=404, detail="Hero not found")
    contestant_data = contestant.model_dump(exclude_unset=True)
    contestant_db.sqlmodel_update(contestant_data)
    session.add(contestant_db)
    session.commit()
    session.refresh(contestant_db)
    return contestant_db
