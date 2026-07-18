import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Добавляем корневую директорию проекта в путь поиска модулей
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app.database.connection import Base
from app.database.models import User, UserLeague, League, Group, BotLeague
from app.database.crud import league as league_crud

# Используем отдельную базу данных для тестов
TEST_DATABASE_URL = "sqlite:///./test_sql_app.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_league_transition():
    print("--- Запуск теста переходов в лигах ---")
    setup_test_db()
    db = TestingSessionLocal()
    
    # 1. Создаем группу в лиге BEGINNER
    group_beginner = Group()
    db.add(group_beginner)
    db.commit()
    db.refresh(group_beginner)
    
    # Создаем 5 пользователей для этой группы
    # User 1: 1 место (должен перейти в GOURMET)
    db.add(User(telegram_id=1, first_name="User1", points=1500))
    db.add(UserLeague(telegram_id=1, group_id=group_beginner.id, league=League.BEGINNER, points=5000))
    
    # User 2: 2 место (должен перейти в GOURMET)
    db.add(User(telegram_id=2, first_name="User2", points=1500))
    db.add(UserLeague(telegram_id=2, group_id=group_beginner.id, league=League.BEGINNER, points=4000))
    
    # User 3: 3 место (должен перейти в GOURMET)
    db.add(User(telegram_id=3, first_name="User3", points=1500))
    db.add(UserLeague(telegram_id=3, group_id=group_beginner.id, league=League.BEGINNER, points=3000))
    
    # User 4: 4 место (должен ОСТАТЬСЯ в BEGINNER)
    db.add(User(telegram_id=4, first_name="User4", points=1500))
    db.add(UserLeague(telegram_id=4, group_id=group_beginner.id, league=League.BEGINNER, points=2000))
    
    # User 5: 5 место (должен ОСТАТЬСЯ в BEGINNER, так как это низшая лига)
    db.add(User(telegram_id=5, first_name="User5", points=1500))
    db.add(UserLeague(telegram_id=5, group_id=group_beginner.id, league=League.BEGINNER, points=1000))

    # 2. Создаем группу в лиге GOURMET
    group_gourmet = Group()
    db.add(group_gourmet)
    db.commit()
    db.refresh(group_gourmet)
    
    # User 6: 5 место в GOURMET (должен ПЕРЕЙТИ ВНИЗ в BEGINNER)
    db.add(User(telegram_id=6, first_name="User6", points=1500))
    db.add(UserLeague(telegram_id=6, group_id=group_gourmet.id, league=League.GOURMET, points=100))
    
    # Добавим ботов в группу GOURMET, чтобы User 6 был на 5-м месте
    for i in range(4):
        db.add(BotLeague(name=f"Bot{i}", group_id=group_gourmet.id, league=League.GOURMET, points=1000 + i*100))
    
    db.commit()
    
    # 3. Создаем группу в ВЫСШЕЙ лиге (GASTRO_EXPERT)
    group_expert = Group()
    db.add(group_expert)
    db.commit()
    db.refresh(group_expert)
    
    # User 7: 1 место в GASTRO_EXPERT (должен ОСТАТЬСЯ в GASTRO_EXPERT)
    db.add(User(telegram_id=7, first_name="User7", points=1500))
    db.add(UserLeague(telegram_id=7, group_id=group_expert.id, league=League.GASTRO_EXPERT, points=9999))
    
    # Заполняем остаток ботами
    for i in range(4):
        db.add(BotLeague(name=f"ExpertBot{i}", group_id=group_expert.id, league=League.GASTRO_EXPERT, points=1000))
    
    db.commit()
    
    print("Начальное состояние создано. Запуск процесса переходов...")
    
    # Запускаем переходы
    league_crud.process_league_transitions(db)
    
    # Проверяем результаты
    print("\n--- Проверка результатов ---")
    
    # User 1 (был 1-м в BEGINNER) -> GOURMET
    ul1 = db.query(UserLeague).filter(UserLeague.telegram_id == 1).first()
    print(f"User 1: Лига {ul1.league.value}, Очки {ul1.points}")
    assert ul1.league == League.GOURMET
    
    # User 4 (был 4-м в BEGINNER) -> BEGINNER
    ul4 = db.query(UserLeague).filter(UserLeague.telegram_id == 4).first()
    print(f"User 4: Лига {ul4.league.value}, Очки {ul4.points}")
    assert ul4.league == League.BEGINNER
    
    # User 6 (был 5-м в GOURMET) -> BEGINNER
    ul6 = db.query(UserLeague).filter(UserLeague.telegram_id == 6).first()
    print(f"User 6: Лига {ul6.league.value}, Очки {ul6.points}")
    assert ul6.league == League.BEGINNER

    # User 7 (был 1-м в GASTRO_EXPERT) -> GASTRO_EXPERT (никуда выше нельзя)
    ul7 = db.query(UserLeague).filter(UserLeague.telegram_id == 7).first()
    print(f"User 7: Лига {ul7.league.value}, Очки {ul7.points}")
    assert ul7.league == League.GASTRO_EXPERT
    
    # Проверяем, что все пользователи распределены по группам по 5 человек (с учетом ботов)
    all_groups = db.query(Group).all()
    print(f"Всего создано групп: {len(all_groups)}")
    for g in all_groups:
        # Получаем лигу группы (по первому попавшемуся участнику)
        sample_user = db.query(UserLeague).filter(UserLeague.group_id == g.id).first()
        sample_bot = db.query(BotLeague).filter(BotLeague.group_id == g.id).first()
        league_name = sample_user.league.value if sample_user else sample_bot.league.value
        
        users_in_group = db.query(UserLeague).filter(UserLeague.group_id == g.id).count()
        bots_in_group = db.query(BotLeague).filter(BotLeague.group_id == g.id).count()
        print(f"Группа {g.id} ({league_name}): Пользователей {users_in_group}, Ботов {bots_in_group}")
        assert (users_in_group + bots_in_group) == 5

    print("\nВсе тесты пройдены успешно!")
    db.close()

if __name__ == "__main__":
    try:
        test_league_transition()
    finally:
        # Закрываем все соединения перед удалением файла
        engine.dispose()
        # Удаляем тестовую БД после завершения
        if os.path.exists("./test_sql_app.db"):
            try:
                os.remove("./test_sql_app.db")
            except Exception as e:
                print(f"Не удалось удалить тестовую БД: {e}")
