"""SQLModel 表模型定义：Team（团队）、Hero（英雄）、Mission（任务）及多对多中间表。"""

from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Team(SQLModel, table=True):
    """团队表。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    headquarters: str

    # 一对多：一个团队拥有多个英雄
    heroes: list["Hero"] = Relationship(back_populates="team")


class MissionHeroLink(SQLModel, table=True):
    """Hero 与 Mission 的多对多中间表（junction table，含额外字段 role）。"""

    __tablename__ = "mission_hero"

    mission_id: int = Field(foreign_key="mission.id", primary_key=True)
    hero_id: int = Field(foreign_key="hero.id", primary_key=True)
    # 额外字段：英雄在任务中扮演的角色
    role: Optional[str] = Field(default=None, max_length=80)


class Mission(SQLModel, table=True):
    """任务表，与 Hero 是多对多关系（通过中间表 mission_hero）。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    location: Optional[str] = Field(default=None, max_length=200)

    # 多对多：一个任务可以关联多个英雄
    heroes: list["Hero"] = Relationship(
        back_populates="missions", link_model=MissionHeroLink
    )


class Hero(SQLModel, table=True):
    """英雄表，属于某个团队（team_id 可为空），可参与多个任务（M2M）。"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    secret_name: str
    age: Optional[int] = Field(default=None, index=True)
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")

    # 多对一：英雄归属团队
    team: Optional["Team"] = Relationship(back_populates="heroes")

    # 多对多：英雄可以参与多个任务
    missions: list["Mission"] = Relationship(
        back_populates="heroes", link_model=MissionHeroLink
    )
