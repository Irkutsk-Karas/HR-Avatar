# services/analyzer.py
from .gigachat_client import GigaChatClient
import json
import re


class InterviewAnalyzer:
    def __init__(self):
        self.giga_client = GigaChatClient()

    def analyze_interview(self, conversation_history, required_skills, vacancy_name="Разработчик"):
        """Анализ результатов собеседования"""
        conversation_text = self._format_conversation(conversation_history)

        analysis_prompt = f"""
        Проанализируй техническое собеседование и составь детальный отчет для HR.

        ТРЕБОВАНИЯ ВАКАНСИИ:
        Должность: {vacancy_name}
        Ключевые навыки: {', '.join(required_skills)}

        ТЕКСТ СОБЕСЕДОВАНИЯ:
        {conversation_text[:3000]}  # Ограничиваем длину

        СГЕНЕРИРУЙ ОТЧЕТ В ФОРМАТЕ JSON:
        {{
            "overall_score": 85,  # Общая оценка 0-100
            "strengths": ["навык1", "навык2", "навык3"],
            "weaknesses": ["недостаток1", "недостаток2"], 
            "skill_assessment": {{
                "Python": "confirmed",
                "Django": "partial",
                "PostgreSQL": "missing"
            }},
            "recommendation": "hire",  # hire/reject/дополнительное интервью
            "feedback": "Развернутая обратная связь для кандидата"
        }}

        Будь объективным и профессиональным. Учитывай технические навыки, soft skills, логичность ответов.
        """

        messages = [
            {
                "role": "system",
                "content": "Ты Senior HR-аналитик и технический рекрутер. Анализируешь собеседования и даешь экспертную оценку."
            },
            {
                "role": "user",
                "content": analysis_prompt
            }
        ]

        response = self.giga_client.get_chat_response(messages, temperature=0.3)

        try:
            # Извлекаем JSON из ответа
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self._generate_fallback_analysis(conversation_text)

        except Exception as e:
            print(f"❌ Ошибка анализа результатов: {e}")
            return self._generate_fallback_analysis(conversation_text)

    def _format_conversation(self, history):
        """Форматирование диалога"""
        formatted = []
        for msg in history:
            role = "ИНТЕРВЬЮЕР" if msg["role"] == "assistant" else "КАНДИДАТ"
            formatted.append(f"{role}: {msg['content']}")
        return "\n".join(formatted)

    def _generate_fallback_analysis(self, conversation_text):
        """Резервный анализ если AI не сработал"""
        return {
            "overall_score": 65,
            "strengths": ["Коммуникативные навыки", "Техническая грамотность"],
            "weaknesses": ["Недостаточный практический опыт", "Требуется дополнительная проверка"],
            "skill_assessment": {},
            "recommendation": "additional_interview",
            "feedback": "Кандидат демонстрирует базовые знания, но требуется дополнительная техническая проверка навыков."
        }