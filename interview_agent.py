# services/interview_agent.py
from .gigachat_client import GigaChatClient
import random


class InterviewAgent:
    def __init__(self, vacancy_name, required_skills):
        self.giga_client = GigaChatClient()
        self.vacancy_name = vacancy_name
        self.required_skills = required_skills
        self.conversation_history = []
        self.question_count = 0
        self.max_questions = 15

    def start_interview(self):
        """Начало собеседования"""
        welcome_message = f"""
        Добро пожаловать на собеседование на позицию {self.vacancy_name}!

        Я - HR-аватар, буду задавать вам вопросы по техническим и профессиональным компетенциям.
        Отвечайте максимально подробно и честно.

        Давайте начнем!
        """

        print(f"HR-аватар: {welcome_message.strip()}")
        self.conversation_history.append({
            "role": "assistant",
            "content": welcome_message.strip()
        })

        # Первый вопрос
        first_question = self._get_base_question()
        print(f"HR-аватар: {first_question}")
        self.conversation_history.append({
            "role": "assistant",
            "content": first_question
        })

    def process_answer(self, answer):
        """Обработка ответа кандидата"""
        if not answer or len(answer.strip()) < 3:
            print("HR-аватар: Пожалуйста, ответьте более развернуто.")
            return True

        # Добавляем ответ кандидата
        self.conversation_history.append({
            "role": "user",
            "content": answer.strip()
        })

        self.question_count += 1

        # Проверяем лимит вопросов
        if self.question_count >= self.max_questions:
            return False

        # Генерируем следующий вопрос
        next_question = self._generate_next_question()
        if next_question:
            print(f"HR-аватар: {next_question}")
            self.conversation_history.append({
                "role": "assistant",
                "content": next_question
            })
            return True

        return False

    def _get_base_questions(self):
        """Базовые вопросы для разных позиций"""
        base_questions = {
            "Python Разработчик": [
                "Расскажите о вашем опыте работы с Python.",
                "Какие фреймворки Django/Flask/FastAPI вы использовали?",
                "Какой у вас опыт работы с базами данных?",
                "Опишите самый сложный технический проект.",
                "Как вы тестируете свой код?",
                "Какой опыт работы с Docker и Kubernetes?",
                "Расскажите о вашем опыте работы в команде.",
                "Как вы решаете сложные технические проблемы?",
                "Почему вы хотите работать именно в нашей компании?",
                "Какие ваши карьерные цели на ближайшие 2-3 года?"
            ],
            "Data Scientist": [
                "Расскажите о вашем опыте в машинном обучении.",
                "Какие библиотеки для анализа данных вы используете?",
                "Опишите процесс работы над ML проектом.",
                "Как вы оцениваете качество моделей?",
                "Какой опыт работы с большими данными?"
            ]
        }

        return base_questions.get(self.vacancy_name, [
            "Расскажите о вашем профессиональном опыте.",
            "Какие технологии и инструменты вы используете?",
            "Опишите ваш последний проект.",
            "Как вы решаете сложные задачи?",
            "Почему вы interested в этой позиции?"
        ])

    def _get_base_question(self):
        """Получение базового вопроса"""
        questions = self._get_base_questions()
        return random.choice(questions)

    def _generate_next_question(self):
        """Генерация адаптивного вопроса"""
        # Первые 3 вопроса - базовые
        if self.question_count < 3:
            return self._get_base_question()

        # Адаптивные вопросы через GigaChat
        prompt = self._build_adaptive_prompt()
        response = self.giga_client.get_chat_response(prompt, temperature=0.7)

        if response:
            return self._clean_response(response)

        # Fallback вопрос
        return "Расскажите подробнее о вашем опыте работы."

    def _build_adaptive_prompt(self):
        """Построение промпта для адаптивного вопроса"""
        history_text = "\n".join([
            f"{'Интервьюер' if msg['role'] == 'assistant' else 'Кандидат'}: {msg['content']}"
            for msg in self.conversation_history[-6:]
        ])

        prompt = f"""
        Ты - опытный технический рекрутер. Проводишь собеседование на {self.vacancy_name}.

        ТРЕБУЕМЫЕ НАВЫКИ: {', '.join(self.required_skills)}

        ИСТОРИЯ ДИАЛОГА:
        {history_text}

        Сгенерируй следующий вопрос который:
        1. Будет релевантен предыдущим ответам кандидата
        2. Касается технических навыков или опыта работы  
        3. Поможет лучше оценить соответствие требованиям
        4. Будет конкретным и профессиональным

        Верни ТОЛЬКО текст вопроса без дополнительных объяснений.
        """

        return [
            {
                "role": "system",
                "content": "Ты экспертный IT-рекрутер с глубоким пониманием технических навыков."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

    def _clean_response(self, response):
        """Очистка ответа от лишнего текста"""
        response = response.strip()
        # Убираем кавычки если есть
        if response.startswith('"') and response.endswith('"'):
            response = response[1:-1]
        # Убираем маркеры формата
        response = response.replace("**", "").replace("*", "")
        return response

    def end_interview(self):
        """Завершение собеседования"""
        thank_you_message = """
        Благодарим вас за ответы! На этом собеседование завершено.

        Ваши результаты будут проанализированы, и мы свяжемся с вами 
        в ближайшее время для обратной связи.

        Хорошего дня!
        """

        print(f"HR-аватар: {thank_you_message.strip()}")
        self.conversation_history.append({
            "role": "assistant",
            "content": thank_you_message.strip()
        })

        return self.conversation_history

    def get_progress(self):
        """Получение прогресса собеседования"""
        return self.question_count

    def get_conversation_text(self):
        """Получение текста диалога"""
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history])