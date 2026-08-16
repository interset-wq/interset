"""读写模型（纯数据模型，非表模型），用于 API 请求体与响应体校验。"""

from typing import Optional

from sqlmodel import Field, SQLModel


class HeroBase(SQLModel):
    """Hero 公共字段。"""

    name: str = Field(min_length=1, max_length=80)
    secret_name: str = Field(min_length=1, max_length=80)
    age: Optional[int] = Field(default=None, ge=0, le=150)
    team_id: Optional[int] = Field(default=None)


class HeroCreate(HeroBase):
    """创建英雄的请求体。"""

    pass


class HeroRead(HeroBase):
    """英雄响应体，包含数据库生成的 id。"""

    id: int


class HeroUpdate(SQLModel):
    """更新英雄的请求体，所有字段可选（部分更新）。"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    secret_name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    age: Optional[int] = Field(default=None, ge=0, le=150)
    team_id: Optional[int] = Field(default=None)


class JoinedHeroRead(SQLModel):
    """hero LEFT JOIN team 查询结果行（DB 层实际 JOIN 输出）。"""

    id: int
    name: str
    secret_name: str
    age: Optional[int] = None
    team_id: Optional[int] = None
    team_name: Optional[str] = None


class TeamBase(SQLModel):
    """Team 公共字段。"""

    name: str = Field(min_length=1, max_length=80)
    headquarters: str = Field(min_length=1, max_length=200)


class TeamCreate(TeamBase):
    """创建团队的请求体。"""

    pass


class TeamUpdate(SQLModel):
    """更新团队的请求体，所有字段可选（部分更新）。"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    headquarters: Optional[str] = Field(default=None, min_length=1, max_length=200)


class TeamRead(TeamBase):
    """团队响应体，包含团队成员列表（体现 Relationship 查询）。"""

    id: int
    heroes: list[HeroRead] = []


class MissionBase(SQLModel):
    """Mission 公共字段。"""

    name: str = Field(min_length=1, max_length=80)
    location: Optional[str] = Field(default=None, max_length=200)


class MissionCreate(MissionBase):
    """创建任务的请求体，可附带关联英雄 id 列表（写入 M2M 中间表）。"""

    hero_ids: list[int] = []


class MissionRead(MissionBase):
    """任务响应体，包含关联英雄列表（体现 M2M 中间表查询）。"""

    id: int
    heroes: list[HeroRead] = []


class MissionHeroLinkRead(SQLModel):
    """mission_hero 中间表的读模型（DB 实际行，附关联名称便于展示）。"""

    mission_id: int
    hero_id: int
    role: Optional[str] = None
    mission_name: Optional[str] = None
    hero_name: Optional[str] = None
