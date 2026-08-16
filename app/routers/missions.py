"""任务路由：演示 SQLModel 多对多（M2M）关系与中间表 mission_hero 的查询。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.database import get_session
from app.models import Hero, Mission, MissionHeroLink
from app.schemas import MissionCreate, MissionHeroLinkRead, MissionRead

router = APIRouter(prefix="/missions", tags=["missions"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/links", response_model=list[MissionHeroLinkRead])
def read_mission_hero_links(session: SessionDep) -> list[dict]:
    """返回 mission_hero 中间表的实际数据行（DB 层面），附任务名与英雄名。"""
    rows = session.exec(
        select(MissionHeroLink, Mission.name, Hero.name)
        .join(Mission, Mission.id == MissionHeroLink.mission_id)
        .join(Hero, Hero.id == MissionHeroLink.hero_id)
        .order_by(MissionHeroLink.mission_id, MissionHeroLink.hero_id)
    ).all()
    return [
        {
            "mission_id": link.mission_id,
            "hero_id": link.hero_id,
            "role": link.role,
            "mission_name": mission_name,
            "hero_name": hero_name,
        }
        for link, mission_name, hero_name in rows
    ]


@router.get("", response_model=list[MissionRead])
def read_missions(session: SessionDep) -> list[Mission]:
    """查询所有任务，预加载关联英雄。"""
    missions = session.exec(
        select(Mission).options(selectinload(Mission.heroes)).order_by(Mission.id)
    ).all()
    return missions


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
