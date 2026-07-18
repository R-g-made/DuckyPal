import random
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.models import Group, UserLeague, League, User, BotLeague, LeaderboardMovement

RUSSIAN_NAMES = [
    "Александр", "Дмитрий", "Максим", "Сергей", "Андрей", "Алексей", "Артём", "Илья", "Кирилл", "Михаил",
    "Никита", "Даниил", "Денис", "Егор", "Иван", "Матвей", "Павел", "Роман", "Тимофей", "Ярослав",
    "Анна", "Мария", "Елена", "Ольга", "Наталья", "Екатерина", "Татьяна", "Ирина", "Светлана", "Анастасия"
]

def get_or_create_open_group(db: Session, league: League = League.BEGINNER):
    """
    Finds a group in a specific league with less than 5 total members (users + bots) 
    or creates a new one and adds 1 initial bot.
    """
    # Find all groups in this league
    groups = db.query(Group).all()
    
    for group in groups:
        user_count = db.query(UserLeague).filter(UserLeague.group_id == group.id, UserLeague.league == league).count()
        bot_count = db.query(BotLeague).filter(BotLeague.group_id == group.id, BotLeague.league == league).count()
        total_count = user_count + bot_count
        
        if 0 < total_count < 5:
            # Verify group league
            first_user = db.query(UserLeague).filter(UserLeague.group_id == group.id).first()
            first_bot = db.query(BotLeague).filter(BotLeague.group_id == group.id).first()
            
            group_league = None
            if first_user: group_league = first_user.league
            elif first_bot: group_league = first_bot.league
            
            if group_league == league:
                return group

    # Create new group and add 1 bot
    new_group = Group()
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    
    generate_bots_for_group(db, new_group.id, league, count=1)
    
    return new_group

def generate_bots_for_group(db: Session, group_id: int, league: League, count: int = 4):
    """
    Generates random bots for a group.
    """
    for _ in range(count):
        bot = BotLeague(
            name=random.choice(RUSSIAN_NAMES),
            group_id=group_id,
            league=league,
            points=random.uniform(1500, 3500)
        )
        db.add(bot)
    db.commit()

def join_league_group(db: Session, telegram_id: int, league: League = League.BEGINNER):
    """
    Assigns a user to a group of 5 people in a specific league.
    """
    # Check if user already in a league/group
    existing = db.query(UserLeague).filter(UserLeague.telegram_id == telegram_id).first()
    if existing:
        return existing
        
    group = get_or_create_open_group(db, league)
    
    # Check if this is a brand new user (first time joining any league)
    # We can check if they have 1500 points and 0 photos
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    initial_points = 0.0
    if user and user.points >= 1500.0 and user.total_photos == 0:
        initial_points = 1500.0

    user_league = UserLeague(
        telegram_id=telegram_id,
        group_id=group.id,
        league=league,
        points=initial_points
    )
    db.add(user_league)
    db.commit()
    db.refresh(user_league)
    return user_league

def get_leaderboard_data(db: Session, group_id: int):
    """
    Returns sorted list of users and bots in a group.
    """
    users = db.query(UserLeague).filter(UserLeague.group_id == group_id).all()
    bots = db.query(BotLeague).filter(BotLeague.group_id == group_id).all()
    
    # Format data for display
    leaderboard = []
    
    for u in users:
        user_info = db.query(User).filter(User.telegram_id == u.telegram_id).first()
        name = user_info.first_name if user_info else "User"
        # Leaderboard shows only points earned in the current league/group
        total_points = u.points
        leaderboard.append({"name": name, "points": total_points, "is_bot": False, "id": u.telegram_id})
        
    for b in bots:
        # Bots already have randomized points starting from 1500
        leaderboard.append({"name": b.name, "points": b.points, "is_bot": True, "id": b.id})
        
    # Sort by points descending
    leaderboard.sort(key=lambda x: x["points"], reverse=True)
    return leaderboard

def update_user_league(db: Session, telegram_id: int, new_league: League, new_group_id: int = None):
    """
    Updates a user's league status and optionally their group.
    """
    user_league = db.query(UserLeague).filter(UserLeague.telegram_id == telegram_id).first()
    if user_league:
        user_league.league = new_league
        if new_group_id:
            user_league.group_id = new_group_id
        user_league.points = 0.0 # Reset points for new league
        db.commit()
        db.refresh(user_league)
    return user_league

def process_league_transitions(db: Session):
    """
    Synchronous distribution every 3 days.
    1. Collects all users and their next league based on current rank.
    2. Resets all groups and bots.
    3. Re-groups everyone into full groups of 5 (filling with bots where needed).
    """
    leagues_order = list(League)
    user_next_leagues = [] # List of (telegram_id, next_league)
    
    # Step 1: Determine next leagues for all current users
    groups = db.query(Group).all()
    for group in groups:
        leaderboard = get_leaderboard_data(db, group.id)
        if not leaderboard:
            continue
            
        # Fill with bots if needed just to ensure ranks are clear (1-5)
        # However, for transition, we just need the relative order of users vs bots
        for i, entry in enumerate(leaderboard):
            if entry["is_bot"]:
                continue
                
            place = i + 1
            user_league_record = db.query(UserLeague).filter(UserLeague.telegram_id == entry["id"]).first()
            if not user_league_record: continue
            
            current_league = user_league_record.league
            current_league_idx = leagues_order.index(current_league)
            
            next_league = current_league
            if place <= 3: # Up
                if current_league_idx < len(leagues_order) - 1:
                    next_league = leagues_order[current_league_idx + 1]
            elif place == 5: # Down
                if current_league_idx > 0:
                    next_league = leagues_order[current_league_idx - 1]
            
            user_next_leagues.append((entry["id"], next_league))

    # Step 2: Clear old structure
    db.query(BotLeague).delete()
    db.query(UserLeague).delete()
    db.query(Group).delete()
    db.commit()

    # Step 3: Synchronous Re-grouping
    for league in leagues_order:
        # Users for this specific league
        league_users = [u for u in user_next_leagues if u[1] == league]
        
        # Shuffle for variety
        random.shuffle(league_users)
        
        # Group by 5
        for i in range(0, len(league_users), 5):
            chunk = league_users[i:i+5]
            
            new_group = Group()
            db.add(new_group)
            db.commit()
            db.refresh(new_group)
            
            for tg_id, _ in chunk:
                user_league = UserLeague(
                    telegram_id=tg_id,
                    group_id=new_group.id,
                    league=league,
                    points=0.0
                )
                db.add(user_league)
            
            # Fill remaining slots with bots
            needed_bots = 5 - len(chunk)
            if needed_bots > 0:
                generate_bots_for_group(db, new_group.id, league, count=needed_bots)
    
    db.commit()

def get_group_members(db: Session, group_id: int):
    """
    Returns all members of a specific group.
    """
    return db.query(UserLeague).filter(UserLeague.group_id == group_id).all()

def track_leaderboard_movement(db: Session, telegram_id: int):
    """
    Tracks and logs movement in the leaderboard for a user.
    """
    user_league = db.query(UserLeague).filter(UserLeague.telegram_id == telegram_id).first()
    if not user_league:
        return

    # Get current state of leaderboard
    leaderboard = get_leaderboard_data(db, user_league.group_id)
    
    # Find new rank
    new_rank = 0
    for i, entry in enumerate(leaderboard):
        if not entry["is_bot"] and entry["id"] == telegram_id:
            new_rank = i + 1
            break
            
    # Get last known rank from movements table
    last_movement = db.query(LeaderboardMovement).filter(
        LeaderboardMovement.telegram_id == telegram_id,
        LeaderboardMovement.group_id == user_league.group_id
    ).order_by(desc(LeaderboardMovement.created_at)).first()
    
    old_rank = last_movement.new_rank if last_movement else None
    
    # If rank changed (improved), log who we overtook
    if old_rank and new_rank < old_rank:
        movement = LeaderboardMovement(
            telegram_id=telegram_id,
            group_id=user_league.group_id,
            old_rank=old_rank,
            new_rank=new_rank,
            overtook_telegram_id=leaderboard[new_rank]["id"] if len(leaderboard) > new_rank else None
        )
        db.add(movement)
        db.commit()
    elif not old_rank:
        # First time tracking rank in this group
        movement = LeaderboardMovement(
            telegram_id=telegram_id,
            group_id=user_league.group_id,
            old_rank=None,
            new_rank=new_rank
        )
        db.add(movement)
        db.commit()

def add_league_points(db: Session, telegram_id: int, points: float):
    """
    Adds points to user's current league/group score.
    """
    user_league = db.query(UserLeague).filter(UserLeague.telegram_id == telegram_id).first()
    if user_league:
        user_league.points += points
        db.commit()
        db.refresh(user_league)
        
        # Track movement after adding points
        track_leaderboard_movement(db, telegram_id)
        
    return user_league
