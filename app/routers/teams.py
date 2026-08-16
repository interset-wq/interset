"""团队路由：演示 SQLModel Relationship 关联查询（selectinload 预加载避免 N+1）。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.database import get_session
from app.models import Team
from app.schemas import PaginatedTeams, TeamCreate, TeamRead, TeamUpdate

router = APIRouter(prefix="/teams", tags=["teams"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=PaginatedTeams)
def read_teams(
    session: SessionDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    """分页查询团队，返回当前页数据与总条数。"""
    total = session.exec(select(func.count()).select_from(Team)).one()
    teams = session.exec(
        select(Team)
        .options(selectinload(Team.heroes))
        .order_by(Team.id)
        .offset(offset)
        .limit(limit)
    ).all()
    return {"items": teams, "total": total}


@router.get("/{team_id}", response_model=TeamRead)
def read_team(team_id: int, session: SessionDep) -> Team:
    """按 id 查询团队及其成员。"""
    team = session.exec(
        select(Team).where(Team.id == team_id).options(selectinload(Team.heroes))
    ).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    return team


@router.post("", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(team: TeamCreate, session: SessionDep) -> Team:
    """创建团队（name 唯一，重名返回 409）。"""
    db_team = Team.model_validate(team)
    session.add(db_team)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Team name already exists"
        )
    session.refresh(db_team)
    return db_team


@router.patch("/{team_id}", response_model=TeamRead)
def update_team(team_id: int, team: TeamUpdate, session: SessionDep) -> Team:
    """部分更新团队（PATCH）。"""
    db_team = session.get(Team, team_id)
    if not db_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    team_data = team.model_dump(exclude_unset=True)
    db_team.sqlmodel_update(team_data)
    session.add(db_team)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Team name already exists"
        )
    session.refresh(db_team)
    return db_team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: int, session: SessionDep) -> None:
    """删除团队（其成员 hero.team_id 置为 NULL，由外键 ON DELETE SET NULL 保证）。"""
    db_team = session.get(Team, team_id)
    if not db_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    session.delete(db_team)
    session.commit()
