"""任务路由：演示 SQLModel 多对多（M2M）关系与中间表 mission_hero 的查询。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.database import get_session
from app.models import Hero, Mission, MissionHeroLink
from app.schemas import (
    MissionCreate,
    MissionHeroLinkCreate,
    MissionHeroLinkRead,
    MissionHeroLinkUpdate,
    MissionRead,
    PaginatedMissionHeroLinks,
    PaginatedMissions,
)

router = APIRouter(prefix="/missions", tags=["missions"])

SessionDep = Annotated[Session, Depends(get_session)]


def _link_with_names(link: MissionHeroLink, session: Session) -> dict:
    """把中间表行附上任务名与英雄名，供响应返回（PSQL 风格展示）。"""
    mission = session.get(Mission, link.mission_id)
    hero = session.get(Hero, link.hero_id)
    return {
        "mission_id": link.mission_id,
        "hero_id": link.hero_id,
        "role": link.role,
        "mission_name": mission.name if mission else None,
        "hero_name": hero.name if hero else None,
    }


@router.get("/links", response_model=PaginatedMissionHeroLinks)
def read_mission_hero_links(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    """分页返回 mission_hero 中间表的实际数据行，附任务名与英雄名。"""
    total = session.exec(select(func.count()).select_from(MissionHeroLink)).one()
    rows = session.exec(
        select(MissionHeroLink, Mission.name, Hero.name)
        .join(Mission, Mission.id == MissionHeroLink.mission_id)
        .join(Hero, Hero.id == MissionHeroLink.hero_id)
        .order_by(MissionHeroLink.mission_id, MissionHeroLink.hero_id)
        .offset(offset)
        .limit(limit)
    ).all()
    items = [
        {
            "mission_id": link.mission_id,
            "hero_id": link.hero_id,
            "role": link.role,
            "mission_name": mission_name,
            "hero_name": hero_name,
        }
        for link, mission_name, hero_name in rows
    ]
    return {"items": items, "total": total}


@router.post("/links", response_model=MissionHeroLinkRead, status_code=status.HTTP_201_CREATED)
def create_mission_hero_link(
    link: MissionHeroLinkCreate, session: SessionDep
) -> dict:
    """创建 mission_hero 中间表行（关联任务与英雄，可带 role）。"""
    db_link = MissionHeroLink.model_validate(link)
    session.add(db_link)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Mission-Hero link already exists",
        )
    session.refresh(db_link)
    return _link_with_names(db_link, session)


@router.patch("/links/{mission_id}/{hero_id}", response_model=MissionHeroLinkRead)
def update_mission_hero_link(
    mission_id: int, hero_id: int, link: MissionHeroLinkUpdate, session: SessionDep
) -> dict:
    """更新中间表 mission_hero 的行（目前仅 role）。"""
    db_link = session.get(MissionHeroLink, (mission_id, hero_id))
    if not db_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission-Hero link not found"
        )
    link_data = link.model_dump(exclude_unset=True)
    db_link.sqlmodel_update(link_data)
    session.add(db_link)
    session.commit()
    session.refresh(db_link)
    return _link_with_names(db_link, session)


@router.delete(
    "/links/{mission_id}/{hero_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_mission_hero_link(mission_id: int, hero_id: int, session: SessionDep) -> None:
    """删除中间表 mission_hero 的行（取消任务与英雄的关联）。"""
    db_link = session.get(MissionHeroLink, (mission_id, hero_id))
    if not db_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission-Hero link not found"
        )
    session.delete(db_link)
    session.commit()


@router.get("", response_model=PaginatedMissions)
def read_missions(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    """分页查询所有任务，返回当前页数据与总条数。"""
    total = session.exec(select(func.count()).select_from(Mission)).one()
    missions = session.exec(
        select(Mission)
        .options(selectinload(Mission.heroes))
        .order_by(Mission.id)
        .offset(offset)
        .limit(limit)
    ).all()
    return {"items": missions, "total": total}


@router.get("/{mission_id}", response_model=MissionRead)
def read_mission(mission_id: int, session: SessionDep) -> Mission:
    """按 id 查询任务及其关联英雄。"""
    mission = session.exec(
        select(Mission)
        .where(Mission.id == mission_id)
        .options(selectinload(Mission.heroes))
    ).first()
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found"
        )
    return mission


@router.post("", response_model=MissionRead, status_code=status.HTTP_201_CREATED)
def create_mission(mission: MissionCreate, session: SessionDep) -> Mission:
    """创建任务，并按 hero_ids 关联英雄（写入中间表 mission_hero）。"""
    db_mission = Mission.model_validate(mission.model_dump(exclude={"hero_ids"}))
    if mission.hero_ids:
        heroes = session.exec(
            select(Hero).where(Hero.id.in_(mission.hero_ids))
        ).all()
        db_mission.heroes = heroes
    session.add(db_mission)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Mission name already exists"
        )
    session.refresh(db_mission)
    return db_mission


@router.patch("/{mission_id}", response_model=MissionRead)
def update_mission(mission_id: int, mission: MissionCreate, session: SessionDep) -> Mission:
    """部分更新任务（PATCH），hero_ids 为空表示不修改关联。"""
    db_mission = session.exec(
        select(Mission)
        .where(Mission.id == mission_id)
        .options(selectinload(Mission.heroes))
    ).first()
    if not db_mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found"
        )
    mission_data = mission.model_dump(exclude={"hero_ids"}, exclude_unset=True)
    db_mission.sqlmodel_update(mission_data)
    if mission.hero_ids:
        heroes = session.exec(
            select(Hero).where(Hero.id.in_(mission.hero_ids))
        ).all()
        db_mission.heroes = heroes
    session.add(db_mission)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Mission name already exists"
        )
    session.refresh(db_mission)
    return db_mission


@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mission(mission_id: int, session: SessionDep) -> None:
    """删除任务（中间表 mission_hero 关联行随之级联删除）。"""
    db_mission = session.get(Mission, mission_id)
    if not db_mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found"
        )
    session.delete(db_mission)
    session.commit()
