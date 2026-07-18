from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Enum, ForeignKey, Float
from datetime import datetime
import enum
from app.database.connection import Base

class ActionType(str, enum.Enum):
    GASTRO_FARM = "gastro_farm"
    LEADERBOARD = "leaderboard"
    SUBSCRIPTION = "subscription"
    INVITE_FRIENDS = "invite_friends"
    FAQ = "faq"
    SUPPORT = "support"
    START = "start"
    PHOTO_ANALYSIS = "photo_analysis"

class PushType(str, enum.Enum):
    REMINDER = "reminder"
    PROMO = "promo"
    SYSTEM = "system"
    ACHIEVEMENT = "achievement"

class InviteType(str, enum.Enum):
    AD = "ad"
    FRIEND = "friend"

class League(str, enum.Enum):
    BEGINNER = "Начинающий едок"
    GOURMET = "Гурман"
    DIET_MASTER = "Мастер рациона"
    QUALITY_CONNOISSEUR = "Знаток качества"
    GASTRO_EXPERT = "Гастро-эксперт"

class AttributionType(str, enum.Enum):
    PUSH = "push"
    AD = "ad"
    FRIEND = "friend"
    DIRECT = "direct"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    language_code = Column(String, nullable=True)
    is_premium = Column(Boolean, default=False)
    is_bot = Column(Boolean, default=False)
    
    # Stats
    total_photos = Column(Integer, default=0)
    points = Column(Float, default=1500.0)
    
    # Limits & Recharge
    analysis_attempts = Column(Integer, default=3) # Current available attempts
    last_recharge_at = Column(DateTime, default=datetime.utcnow) # Last time an attempt was used/recharged
    last_farm_claim_at = Column(DateTime, nullable=True) # Last time farm points were claimed
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(Date, nullable=True)
    last_photo_at = Column(DateTime, nullable=True)
    
    is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"

class UserAction(Base):
    __tablename__ = "user_actions"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, index=True)
    action_type = Column(Enum(ActionType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserAction(telegram_id={self.telegram_id}, action_type={self.action_type})>"

class PushNotification(Base):
    __tablename__ = "push_notifications"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, ForeignKey("users.telegram_id"), index=True)
    push_type = Column(String) # 'farm', 'leaderboard', 'attempts'
    message_text = Column(String)
    sent_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PushNotification(user={self.telegram_id}, type={self.push_type})>"

class Invite(Base):
    __tablename__ = "invites"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, index=True, unique=True) # The invited user
    invite_type = Column(Enum(InviteType), nullable=False)
    referrer_id = Column(String, nullable=False) # Can be TG ID or Ad ID
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Invite(telegram_id={self.telegram_id}, type={self.invite_type}, from={self.referrer_id})>"

class UserVisit(Base):
    __tablename__ = "user_visits"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, index=True)
    visit_time = Column(DateTime, default=datetime.utcnow)
    
    attribution_type = Column(Enum(AttributionType), nullable=False)
    attribution_id = Column(Integer, nullable=True) # ID from push_notifications or invites

    def __repr__(self):
        return f"<UserVisit(telegram_id={self.telegram_id}, type={self.attribution_type})>"

class PhotoAnalysis(Base):
    __tablename__ = "photo_analyses"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # AI Results & Description
    description = Column(String, nullable=True) # Текстовое описание фотографии
    file_path = Column(String, nullable=True)   # Ссылка на файл (путь в проекте)
    result_text = Column(String, nullable=True) # Full JSON summary
    
    # Points
    points_earned = Column(Float, default=0.0)  # Количество поинтов за фото
    food_score = Column(Integer, default=0)
    health_multiplier = Column(Float, default=1.0)
    
    # Links
    trigger_card_id = Column(Integer, ForeignKey("farm_cards.id"), nullable=True) # Связь с карточкой
    
    # Attribution
    attribution_type = Column(Enum(AttributionType), nullable=False)
    attribution_id = Column(Integer, nullable=True) # ID from push_notifications or invites

    def __repr__(self):
        return f"<PhotoAnalysis(telegram_id={self.telegram_id}, points={self.points_earned})>"

class FarmCard(Base):
    __tablename__ = "farm_cards"

    id = Column(Integer, primary_key=True, index=True) # Уникальный внутренний ID
    telegram_id = Column(Integer, ForeignKey("users.telegram_id"), index=True)
    food_name = Column(String, nullable=True)    # Краткое наименование еды
    points_per_hour = Column(Float, default=0.0) # Сколько поинтов приносит владельцу
    is_active = Column(Boolean, default=True)    # Флаг активности
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<FarmCard(id={self.id}, owner={self.telegram_id}, active={self.is_active})>"

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Group(id={self.id})>"

class UserLeague(Base):
    __tablename__ = "user_leagues"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, ForeignKey("users.telegram_id"), index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True)
    league = Column(Enum(League), default=League.BEGINNER)
    points = Column(Float, default=0.0) # Points within the current league/group
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserLeague(telegram_id={self.telegram_id}, group={self.group_id}, league={self.league})>"

class BotLeague(Base):
    __tablename__ = "bot_leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True)
    league = Column(Enum(League), default=League.BEGINNER)
    points = Column(Float, default=0.0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<BotLeague(name={self.name}, group={self.group_id}, league={self.league})>"

class UserMultiplier(Base):
    __tablename__ = "user_multipliers"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, ForeignKey("users.telegram_id"), index=True)
    multiplier = Column(Float, default=1.0)
    expires_at = Column(DateTime, nullable=True) # Optional for time-based
    uses_left = Column(Integer, nullable=True)   # Optional for usage-based
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<UserMultiplier(telegram_id={self.telegram_id}, multiplier={self.multiplier}, expires_at={self.expires_at}, uses_left={self.uses_left})>"

class UserPushSchedule(Base):
    __tablename__ = "user_push_schedules"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, ForeignKey("users.telegram_id"), index=True, unique=True)
    
    # Время приемов пищи (храним как строки HH:MM)
    meal_1_time = Column(String, nullable=True) # Завтрак
    meal_2_time = Column(String, nullable=True) # Обед
    meal_3_time = Column(String, nullable=True) # Ужин
    
    # Флаги ручной настройки (через онбординг)
    meal_1_manual = Column(Boolean, default=False)
    meal_2_manual = Column(Boolean, default=False)
    meal_3_manual = Column(Boolean, default=False)
    
    # Флаги активности пушей
    is_enabled = Column(Boolean, default=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserPushSchedule(telegram_id={self.telegram_id}, m1={self.meal_1_time}, m2={self.meal_2_time}, m3={self.meal_3_time})>"

class LeaderboardMovement(Base):
    __tablename__ = "leaderboard_movements"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, ForeignKey("users.telegram_id"), index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True)
    old_rank = Column(Integer, nullable=True)
    new_rank = Column(Integer, nullable=False)
    overtook_telegram_id = Column(Integer, nullable=True) # TG ID (или ID бота) того, кого обогнали
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<LeaderboardMovement(user={self.telegram_id}, group={self.group_id}, {self.old_rank}->{self.new_rank})>"

