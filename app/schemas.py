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
