"""英雄 CRUD 路由：演示 FastAPI 特性（依赖注入、分页、状态码、响应模型）与 SQLModel 查询。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlmodel import Session, select

from app.database import get_session
from app.models import Hero, Team
from app.schemas import HeroCreate, HeroRead, HeroUpdate, JoinedHeroRead, PaginatedHeroes

router = APIRouter(prefix="/heroes", tags=["heroes"])

# 可复用的会话依赖类型别名（Annotated + Depends 推荐写法）
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=PaginatedHeroes)
def read_heroes(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    """分页查询英雄列表，返回当前页数据与总条数。"""
    total = session.exec(select(func.count()).select_from(Hero)).one()
    heroes = session.exec(
        select(Hero).order_by(Hero.id).offset(offset).limit(limit)
    ).all()
    return {"items": heroes, "total": total}


@router.get("/joined", response_model=list[JoinedHeroRead])
def read_joined(session: SessionDep) -> list[dict]:
    """hero LEFT JOIN team 的实际查询结果（DB 层执行，非前端拼接）。"""
    rows = session.exec(
        select(Hero, Team.name)
        .join(Team, Hero.team_id == Team.id, isouter=True)
        .order_by(Hero.id)
    ).all()
    return [
        {
            "id": hero.id,
            "name": hero.name,
            "secret_name": hero.secret_name,
            "age": hero.age,
            "team_id": hero.team_id,
            "team_name": team_name,
        }
        for hero, team_name in rows
    ]


@router.get("/{hero_id}", response_model=HeroRead)
def read_hero(hero_id: int, session: SessionDep) -> Hero:
    """按 id 查询单个英雄。"""
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hero not found"
        )
    return hero


@router.post("", response_model=HeroRead, status_code=status.HTTP_201_CREATED)
def create_hero(hero: HeroCreate, session: SessionDep) -> Hero:
    """创建英雄。"""
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero


@router.patch("/{hero_id}", response_model=HeroRead)
def update_hero(hero_id: int, hero: HeroUpdate, session: SessionDep) -> Hero:
    """部分更新英雄（PATCH）。"""
    db_hero = session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hero not found"
        )
    hero_data = hero.model_dump(exclude_unset=True)
    db_hero.sqlmodel_update(hero_data)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero


@router.delete("/{hero_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hero(hero_id: int, session: SessionDep) -> None:
    """删除英雄。"""
    db_hero = session.get(Hero, hero_id)
    if not db_hero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hero not found"
        )
    session.delete(db_hero)
    session.commit()
