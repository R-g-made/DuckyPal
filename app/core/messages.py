# Текстовые сообщения бота

MAIN_MENU = (
    '<a href="https://i.ibb.co/SwVQtQCx/Main-v1.png">&#8203;</a>'
    "Привет, я утя <tg-emoji emoji-id=\"5350726942335214142\">👋</tg-emoji>, я помогу тебе контролировать твое питания!\n\n"
    "<blockquote>У тебя осталось <b>{attempts} попытки</b> сегодня</blockquote>\n\n"
    "<b>{points} баллов</b> <tg-emoji emoji-id=\"5368646692650395057\">😊</tg-emoji> | Ранг: <b>{league_name}</b> <tg-emoji emoji-id=\"5357272691537650628\">🥇</tg-emoji>"
    "{multiplier_text}"
)

OFFER_X2 = (
    "Хочешь получить <b>x2 бонус</b> на 1 блюдо? <tg-emoji emoji-id=\"5354972139550189594\">🎁</tg-emoji>\n"
    "<blockquote>Поставь напоминание на следующий прием пищи,это займет не больше 20 секунд, готовы?</blockquote>"
)

OFFER_GENERIC = (
    "Хочешь получить <b>x{multiplier} бонус</b> на 1 блюдо? <tg-emoji emoji-id=\"5354972139550189594\">🎁</tg-emoji>\n"
    "<blockquote>Поставь напоминание на следующий прием пищи,это займет не больше 20 секунд, готовы?</blockquote>"
)

# Анализ фото
ANALYSIS_PROCESSING = "Анализирую фото <tg-emoji emoji-id=\"5372889128201395415\">📕</tg-emoji>\n <blockquote>Это может занять до 1 минуты!</blockquote>"
ANALYSIS_ERROR = (
    "Извините, у меня не получилось разглядеть фотку <tg-emoji emoji-id=\"5352805654966870268\">👎</tg-emoji>!\n"
    "<blockquote>Ты можешь отправить ее снова</blockquote>"
)
ANALYSIS_NOT_FOOD = (
    "{comment}\n"
    "<blockquote>Пожалуйста, отправь фото именно еды <tg-emoji emoji-id=\"5372833199137266697\">🔍</tg-emoji></blockquote>"
)
ANALYSIS_RESULTS = (
    "{comment}\n\n"
    "<blockquote>"
    "<i>БЖУ и Калории:</i>\n"
    "Белки: {proteins}г\n"
    "Жиры: {fats}г\n"
    "Углеводы: {carbs}г\n"
    "Калорийность: {calories} ккал"
    "</blockquote>\n \n"
    "<blockquote>Ты получил <b>{final_points} баллов</b>{bonus_text} <tg-emoji emoji-id=\"5368646692650395057\">😊</tg-emoji></blockquote>"
)

# Гастро-ферма
FARM_MAIN = (
    '<a href="https://i.ibb.co/xd3PHG1/Gastro-farm-v1.png">&#8203;</a>'
    "Привет, это твоя гастро-ферма!\n \n"
    "<blockquote>Текущий доход: <b>{hourly_income} <tg-emoji emoji-id=\"5368646692650395057\">😊</tg-emoji> / час</b></blockquote>\n"
    "<blockquote>Доступно: <b>{available_points} баллов <tg-emoji emoji-id=\"5368646692650395057\">😊</tg-emoji></b></blockquote>\n\n"
    "<i>Забирать награду можно раз в 8 часов!</i>"
)
FARM_CARD_INFO = (
    "<b>{food}</b>\n\n"
    "<blockquote>Доходность <b>{income} <tg-emoji emoji-id=\"5368646692650395057\">😊</tg-emoji>/час</b></blockquote>\n\n"
    "<i>ты можешь добавить это карточку в свою ферму!</i>"
)
FARM_SLOT_SELECT = "Выберите слот для размещения карточки:"
FARM_ADDED_SUCCESS = "Карточка добавлена в гастроферму!"

# Лидерборд
LEADERBOARD_TITLE = (
    '<a href="https://i.ibb.co/ynbt8H4s/Leaderboard-v1.png">&#8203;</a>'
    "<tg-emoji emoji-id=\"5357272691537650628\">🥇</tg-emoji> Текущая лига:<b> {league_name}</b>\n\n"
    "<blockquote>До смены лиги осталось: <b>{time_left}</b></blockquote>\n\n"
    "<i>Топ-3 переходят в следующую лигу,4-e место остается, 5-е место понижается.</i>"
)

# Инвайты
INVITE_TEXT = (
    '<a href="https://i.ibb.co/svjVCRVd/Invite-v1.png">&#8203;</a>'
    "Зарабатывай очки вместе с друзьями!\n\n"
    "<blockquote>"
    "Награда за каждого друга:\n \n"
    "- <b>{bonus_points} <tg-emoji emoji-id=\"5368646692650395057\">😊</tg-emoji></b>баллов сразу!\n"
    "- <b>x2 баллов</b> на 12 часов <tg-emoji emoji-id=\"5350614323997745915\">🚘</tg-emoji>"
    "</blockquote>"
)

# FAQ (Как это работает)
FAQ_PAGES = {
    1: {
        "text": "<b>Хотите стать здоровее? Наш бот вам поможет!</b> \n \nПросто <b>присылайте фото еды</b> — узнавайте её состав и <b>зарабатывайте баллы</b> за пользу.\n \n<b>Наши баллы — это ваш личный индикатор здоровья</b>. \nСобирайте их, чтобы наглядно видеть, как ваш образ жизни становится правильнее и здоровее с каждым днем!",
        "img": "https://i.ibb.co/60kbDg0r/HIV-l2.png"
    },
    2: {
        "text": "<b>Поднимайся в рейтинге и переходи в высшие лиги</b>. \n \nТвой прогресс — это знак высокого уровня дисциплины.\nСоревнуйся с единомышленниками и докажи, что здоровый образ жизни — это про тебя!",
        "img": "https://i.ibb.co/1GjymPnX/HIV-L3.png"
    },
    3: {
        "text": "<b>Твоя еда может приносить доход!</b>\n \nДобавляй свои самые крутые блюда в личную Гастро-ферму. \n \nСобирай собственную <b>коллекцию здорового питания</b> и получай пассивные баллы просто за то, что ты молодец!",
        "img": "https://i.ibb.co/WWn7pZpR/HIV-L4.png"
    }
}

# Тексты для онбординга (копия FAQ для дальнейшего редактирования)
ONBOARDING_PAGES = {
    1: {
        "text": "<b>Добро пожаловать в UtyaPal!</b> 👋\n \nПросто <b>присылайте фото еды</b> — узнавайте её состав и <b>зарабатывайте баллы</b> за пользу.\n \n<b>Наши баллы — это ваш личный индикатор здоровья</b>. \nСобирайте их, чтобы наглядно видеть, как ваш образ жизни становится правильнее и здоровее с каждым днем!",
        "img": "https://i.ibb.co/60kbDg0r/HIV-l2.png"
    },
    2: {
        "text": "<b>Соревнуйтесь с другими!</b> 🥇\n \nПоднимайся в рейтинге и переходи в высшие лиги. Твой прогресс — это знак высокого уровня дисциплины.\n \nДокажи всем, что здоровый образ жизни — это про тебя!",
        "img": "https://i.ibb.co/1GjymPnX/HIV-L3.png"
    },
    3: {
        "text": "<b>Создайте свою Гастро-ферму!</b> 🍎\n \nДобавляй свои самые крутые блюда в личную коллекцию. \n \nПолучай <b>пассивные баллы</b> за каждое здоровое блюдо в твоей коллекции просто за то, что ты молодец!",
        "img": "https://i.ibb.co/WWn7pZpR/HIV-L4.png"
    }
}

# Магазин
SHOP_MAIN = (
    '<a href="https://i.ibb.co/60kbDg0r/HIV-l2.png">&#8203;</a>' # Пока временная картинка
    "Привет, это тайный магазин Ути <tg-emoji emoji-id=\"5350726942335214142\">🕵️‍♂️</tg-emoji>, здесь ты можешь купить разные бонусы!\n\n"
    "<blockquote>До обновления: <b>{time_left}</b></blockquote>"
)
SHOP_PURCHASE_SUCCESS = "Успешная покупка! ✅\n\n<blockquote>Ваш бонус уже начислен.</blockquote>"
SHOP_NOT_ENOUGH_POINTS = "Недостаточно баллов! ❌\n\n<blockquote>Тебе нужно еще {needed} баллов 😊</blockquote>"
SHOP_LIMIT_REACHED = "Лимит покупок исчерпан! ❌\n\n<blockquote>Этот товар можно купить не более 2 раз за 12 часов.</blockquote>"

# Онбординг
ONBOARDING_BONUS_INFO = (
    "<tg-emoji emoji-id=\"5350614323997745915\">🚘</tg-emoji> <b>Бонус x{multiplier} на следующую фотку!</b>\n\n"
    "Чтобы получить его, на какой прием пищи вы хочете поставить напоминание?"
)
ONBOARDING_TIME_PROMPT = (
    "Через сколько ты планируешь этот прием пищи?\n"
    "<blockquote>Я пришлю тебе напоминание за 15 минут до этого времени!</blockquote>"
)
ONBOARDING_SUCCESS_ALERT = "Готово! Бонус x{multiplier} активирован на следующую фотку!"

# Лимиты
LIMITS_REACHED = (
    "<tg-emoji emoji-id=\"5375182043737002931\">❌</tg-emoji> <b>У вас закончились попытки анализа!</b>\n\n"
    "Новая попытка появится через: <b>{time_left}</b>\n"
    "Всего можно накопить до 3 попыток (1 каждые 8 часов)."
)
