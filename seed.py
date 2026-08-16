"""演示数据填充脚本（幂等）：插入团队、英雄（约 20 条）、任务与中间表数据。

用法：uv run python seed.py
重复运行不会产生重复数据（按 name / name+secret_name 判断已存在）。
"""

from sqlmodel import Session, select

from app.database import engine
from app.models import Hero, Mission, MissionHeroLink, Team

# 英雄与所属团队：(name, secret_name, age, team_name)
# 新团队会自动创建，已有团队按 name 复用；age 需满足 HeroRead 的 ≤150 校验
HEROES: list[tuple[str, str, int, str]] = [
    ("Thor", "Thor Odinson", 35, "Avengers"),
    ("Hulk", "Bruce Banner", 49, "Avengers"),
    ("Hawkeye", "Clint Barton", 45, "Avengers"),
    ("Black Widow", "Natasha Romanoff", 38, "Avengers"),
    ("Captain America", "Steve Rogers", 105, "Avengers"),
    ("Storm", "Ororo Munroe", 32, "X-Men"),
    ("Jean Grey", "Jean Grey-Summers", 30, "X-Men"),
    ("Cyclops", "Scott Summers", 34, "X-Men"),
    ("Beast", "Hank McCoy", 35, "X-Men"),
    ("Wonder Woman", "Diana Prince", 35, "Justice League"),
    ("Flash", "Barry Allen", 29, "Justice League"),
    ("Aquaman", "Arthur Curry", 35, "Justice League"),
    ("Thing", "Ben Grimm", 40, "Fantastic Four"),
    ("Human Torch", "Johnny Storm", 28, "Fantastic Four"),
    ("Invisible Woman", "Sue Storm", 34, "Fantastic Four"),
    ("Spider-Man", "Peter Parker", 25, "Spider-Verse"),
    ("Miles Morales", "Miles Morales", 17, "Spider-Verse"),
    ("Spider-Gwen", "Gwen Stacy", 19, "Spider-Verse"),
    ("Doctor Strange", "Stephen Strange", 50, "Mystic Arts"),
    ("Wong", "Wong", 45, "Mystic Arts"),
]

# 任务与关联英雄：(name, location, [hero names])
MISSIONS: list[tuple[str, str, list[str]]] = [
    ("Alien Invasion", "New York", ["Thor", "Hulk", "Spider-Man", "Captain America"]),
    ("Dimension War", "Sanctum", ["Doctor Strange", "Wong", "Scarlet Witch"]),
    ("Ocean Threat", "Atlantis", ["Aquaman", "Wonder Woman", "Flash"]),
    ("Mutant Rescue", "Genosha", ["Storm", "Cyclops", "Jean Grey", "Beast"]),
]


def seed() -> None:
    with Session(engine) as session:
        # 团队：不存在则创建，按 name 缓存复用
        teams: dict[str, Team] = {}
        for _, _, _, team_name in HEROES:
            if team_name not in teams:
                team = session.exec(select(Team).where(Team.name == team_name)).first()
                if not team:
                    team = Team(name=team_name, headquarters="Unknown")
                    session.add(team)
                    session.commit()
                    session.refresh(team)
                teams[team_name] = team

        # 英雄：name+secret_name 均相同则视为已存在
        heroes: dict[str, Hero] = {}
        for name, secret_name, age, team_name in HEROES:
            hero = session.exec(
                select(Hero).where(Hero.name == name, Hero.secret_name == secret_name)
            ).first()
            if not hero:
                hero = Hero(name=name, secret_name=secret_name, age=age, team_id=teams[team_name].id)
                session.add(hero)
                session.commit()
                session.refresh(hero)
            heroes[name] = hero

        # 任务与中间表关联：任务按 name 幂等，link 按 (mission_id, hero_id) 幂等
        for name, location, hero_names in MISSIONS:
            mission = session.exec(select(Mission).where(Mission.name == name)).first()
            if not mission:
                mission = Mission(name=name, location=location)
                session.add(mission)
                session.commit()
                session.refresh(mission)
            for hero_name in hero_names:
                hero = heroes.get(hero_name)
                if not hero:
                    continue
                exists = session.exec(
                    select(MissionHeroLink).where(
                        MissionHeroLink.mission_id == mission.id,
                        MissionHeroLink.hero_id == hero.id,
                    )
                ).first()
                if not exists:
                    session.add(MissionHeroLink(mission_id=mission.id, hero_id=hero.id))
        session.commit()

        # 统计输出
        print(f"teams:     {len(session.exec(select(Team)).all())}")
        print(f"heroes:    {len(session.exec(select(Hero)).all())}")
        print(f"missions:  {len(session.exec(select(Mission)).all())}")
        print(f"links:     {len(session.exec(select(MissionHeroLink)).all())}")


if __name__ == "__main__":
    seed()
