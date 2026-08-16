"""SQLModel 表模型定义：Team（团队）与 Hero（英雄），一对多关系。"""

from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Team(SQLModel, table=True):
    """团队表。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    headquarters: str

    # 一对多：一个团队拥有多个英雄
    heroes: list["Hero"] = Relationship(back_populates="team")


class Hero(SQLModel, table=True):
    """英雄表，属于某个团队（team_id 可为空）。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    secret_name: str
    age: Optional[int] = Field(default=None, index=True)
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")

    # 多对一：英雄归属团队
    team: Optional["Team"] = Relationship(back_populates="heroes")
