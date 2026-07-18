from google import genai
from PIL import Image
import io
import logging
from config import GEMINI_API_KEY

# Initialize the client (using the new google-genai SDK)
client = genai.Client(api_key=GEMINI_API_KEY)

async def analyze_food_image(image_bytes: bytes, roast_mode: bool = False) -> str:
    """
    Analyzes an image using Gemini to identify food and estimate calories.
    """
    try:
        # Load image from bytes
        img = Image.open(io.BytesIO(image_bytes))
        
        if roast_mode:
            role_prompt = """
            Ты - саркастичный и очень острый на язык диетолог. Твоя задача - высмеять ("прожарить") выбор еды пользователя, 
            используя черный юмор, сарказм и иронию. Будь дерзким, но не переходи границы приличия.
            """
        else:
            role_prompt = """
            Ты - дружелюбный и профессиональный эксперт-диетолог. Твоя задача - поддержать пользователя и дать полезную информацию.
            """

        prompt = f"""
        {role_prompt}
        Проанализируй это фото еды.
        Твой ответ ДОЛЖЕН СТРОГО соответствовать следующему формату:

        [Твой краткий комментарий о блюде в выбранном стиле]

        <blockquote>
        - Белков: [значение]г
        - Жиров: [значение]г
        - Углеводов: [значение]г
        - Калорийность: [значение] ккал
        </blockquote>

        Правила:
        1. В блоке <blockquote> перечисли только БЖУ и общую калорийность.
        2. Если на фото нет еды, напиши: "Похоже, на фото нет еды. Пожалуйста, отправь фото своего блюда!" без блока blockquote.
        3. Используй русский язык.
        """
        
        # Используем gemini-2.0-flash-lite
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, img]
        )
        
        if not response.text:
            return "Не удалось получить текст ответа от ИИ. Попробуйте другое фото."
            
        return response.text
    except Exception as e:
        logging.error(f"Gemini API Error: {e}")
        return f"Ошибка при анализе изображения: {str(e)}"
