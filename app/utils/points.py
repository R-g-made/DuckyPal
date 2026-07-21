import random
from app.database.models import League

def get_league_multiplier(league: League) -> float:
    """
    Returns multiplier based on league level (1x to 5x).
    """
    multipliers = {
        League.BEGINNER: 1.0,
        League.GOURMET: 2.0,
        League.DIET_MASTER: 3.0,
        League.QUALITY_CONNOISSEUR: 4.0,
        League.GASTRO_EXPERT: 5.0
    }
    return multipliers.get(league, 1.0)

def calculate_points(base_score: int, health_multiplier: float, league: League) -> dict:
    """
    Calculates points based on the formula:
    Base Score * Health Multiplier * Luck Multiplier * League Multiplier
    """
    # 1. Base Score (0-100) - from AI
    
    # 2. Health Multiplier (0.5x - 2x) - from AI (already 0.7-2.0, adjusting to requested range if needed)
    
    # 3. Luck Multiplier (1x - 5x) - Randomly generated
    # Using weighted random to make 5x rare
    luck_multiplier = random.choices(
        [1.0, 2.0, 3.0, 4.0, 5.0], 
        weights=[50, 25, 15, 7, 3], 
        k=1
    )[0]
    
    # 4. League Multiplier (1x - 5x)
    league_multiplier = get_league_multiplier(league)
    
    total_points = float(base_score) * health_multiplier * luck_multiplier * league_multiplier
    
    return {
        "total": round(total_points, 2),
        "luck_multiplier": luck_multiplier,
        "league_multiplier": league_multiplier,
        "base_score": base_score,
        "health_multiplier": health_multiplier
    }

def calculate_new_farm_card_income(active_cards: list) -> float:
    """
    Вычисляет доходность новой карточки для гастро-фермы ОДИН РАЗ.
    Formula: Avg(Existing Cards) * Luck Multiplier (0.1x - 5x)
    Если нет карточек, Avg = 30.
    """
    # 1. Calculate Average
    if not active_cards:
        avg_value = 30.0
    else:
        avg_value = sum(card.points_per_hour for card in active_cards) / len(active_cards)
    
    # 2. Luck Multiplier (0.1x - 5x)
    luck_multiplier = random.choices(
        [0.1, 0.5, 1.0, 2.0, 5.0],
        weights=[20, 30, 35, 10, 5],
        k=1
    )[0]
    
    return round(avg_value * luck_multiplier, 2)


def calculate_total_farm_income(active_cards: list) -> dict:
    """
    Вычисляет текущий общий почасовой доход всех активных карточек.
    """
    total_income = sum(card.points_per_hour for card in active_cards)
    return {
        "hourly_income": round(total_income, 2),
        "avg_value": total_income / len(active_cards) if active_cards else 0.0
    }


# Для обратной совместимости
calculate_farm_income = calculate_total_farm_income
