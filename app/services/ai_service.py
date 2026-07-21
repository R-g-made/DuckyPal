import io
import logging
import json
from PIL import Image
from google import genai
from app.core.config import settings

class AIService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-2.5-flash"

    async def analyze_food_image(self, image_bytes: bytes) -> dict:
        """
        Analyzes an image using Gemini to identify food, estimate calories,
        and provide a score and health multiplier.
        Returns a dictionary (JSON-like).
        """
        try:
            # Load image from bytes
            img = Image.open(io.BytesIO(image_bytes))
            
            prompt = self._get_analysis_prompt()
            
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=[prompt, img],
                config={
                    'response_mime_type': 'application/json'
                }
            )
            
            if not response.text:
                raise ValueError("Empty response from AI")
                
            return json.loads(response.text)
        except Exception as e:
            logging.error(f"Gemini API Error: {e}")
            return {
                "error": True,
                "message": f"Ошибка при анализе изображения: {str(e)}"
            }

    def _get_analysis_prompt(self) -> str:
        return """
        Ты - профессиональный эксперт-диетолог с отличным чувством юмора. Твоя задача - проанализировать фото еды и вернуть результат СТРОГО в формате JSON.
        
        Твой ответ должен содержать следующие поля:
        1. "comment": ОЧЕНЬ краткий (СТРОГО 1 короткое предложение) комментарий. В этом предложении ты должен похвалить самого ЧЕЛОВЕКА (его вкус, дисциплину, выбор или внешность), а не саму еду. Будь очень дружелюбным.
        2. "food_name": Очень краткое название блюда (1-3 слова, например "Цезарь с курицей" или "Борщ"), для использования в меню.
        3. "proteins": Количество белков в граммах (число).
        4. "fats": Количество жиров в граммах (число).
        5. "carbs": Количество углеводов в граммах (число).
        6. "calories": Общая калорийность (число).
        7. "food_score": Оценка ПОЛЕЗНОСТИ еды от 1 до 100 (насколько это здоровая и качественная еда для организма).
        8. "health_multiplier": Коэффициент полезности от 0.7 до 2.0 (где 2.0 - суперфуд, а 0.7 - вредный фастфуд).
        9. "is_food": Boolean (true если на фото еда, false если нет).

        Если на фото нет еды, заполни поля нулями, а в comment напиши вежливую просьбу прислать фото блюда.
        Язык ответа: Русский.
        """

ai_service = AIService()
