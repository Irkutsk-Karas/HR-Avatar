# main.py
import os
import json
from services import ResumeParser, InterviewAgent, InterviewAnalyzer, VoiceService
from config import Config
from dotenv import load_dotenv
import speech_recognition as sr

load_dotenv()


def check_microphone():
    """Проверка доступности микрофона"""
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("🔊 Проверка микрофона... Скажите что-нибудь")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=2)
        print("✅ Микрофон работает!")
        return True
    except Exception as e:
        print(f"❌ Проблема с микрофоном: {e}")
        return False


def check_internet():
    """Проверка подключения к интернету"""
    try:
        import requests
        requests.get("https://www.google.com", timeout=5)
        return True
    except:
        return False


def conduct_interview(agent, voice_service=None):
    """Проведение собеседования"""
    print(f"\n🎯 Начало собеседования ({'голосовой' if voice_service else 'текстовый'} режим)...")
    print("Для завершения скажите 'завершить' или введите 'exit'")
    print("-" * 50)

    agent.start_interview()
    question_count = 0
    max_questions = 10

    while question_count < max_questions:
        try:
            if voice_service:
                print("\n🎤 Говорите...")
                answer = voice_service.speech_to_text()
                if not answer:
                    continue
            else:
                answer = input("\n👤 Кандидат: ")

            if not answer.strip():
                continue

            # Проверка команд завершения
            stop_commands = ['завершить', 'закончить', 'выход', 'стоп', 'exit', 'quit']
            if answer.lower() in stop_commands:
                print("Завершение собеседования...")
                break

            # Обработка ответа
            if not agent.process_answer(answer):
                break

            question_count += 1

            # Автоматическое завершение после 10 вопросов
            if question_count >= max_questions:
                print("\n✓ Достигнут лимит вопросов. Завершение...")
                break

        except KeyboardInterrupt:
            print("\n\nСобеседование прервано пользователем.")
            break
        except Exception as e:
            print(f"❌ Ошибка во время собеседования: {e}")
            continue

    return agent.end_interview()


def main():
    print("=== HR-Аватар - Система автоматического собеседования ===")
    print("=" * 60)

    config = Config()

    # 1. Анализ резюме
    print("\n1. 📄 Анализ резюме...")
    parser = ResumeParser()

    resume_text = parser.extract_text(config.RESUME_PATH)
    if not resume_text:
        print("❌ Резюме не найдено. Используем демо-текст.")
        resume_text = """
        Python разработчик с 3 годами опыта. 
        Навыки: Python, Django, Flask, PostgreSQL, Docker, Git, Linux.
        Опыт разработки веб-приложений, REST API, работа в команде.
        """

    vacancy = {
        "name": "Python Разработчик",
        "required_skills": ["Python", "Django", "PostgreSQL", "Docker", "Git", "Linux"]
    }

    analysis = parser.parse_resume(resume_text, vacancy["required_skills"])

    print(f"✅ Навыки кандидата: {', '.join(analysis['skills'][:8])}")
    print(f"📊 Соответствие вакансии: {analysis['match_score']}%")
    print(f"💡 Рекомендация: {analysis['recommendation']}")

    # Решение о допуске к собеседованию
    if analysis['match_score'] < 30:
        print(f"\n❌ Кандидат не соответствует минимальным требованиям.")
        print("Рекомендуется рассмотреть других кандидатов.")
        return

    # 2. Выбор режима собеседования
    print(f"\n2. 🎛️  Выбор режима собеседования")
    print("1. Текстовый режим (клавиатура)")
    print("2. Голосовой режим (микрофон)")

    choice = input("Ваш выбор (1/2): ").strip()

    voice_service = None
    if choice == "2":
        if not check_microphone():
            print("⚠️  Переключаемся на текстовый режим")
            choice = "1"
        else:
            voice_service = VoiceService()

    # 3. Проведение собеседования
    agent = InterviewAgent(vacancy["name"], vacancy["required_skills"])
    conversation = conduct_interview(agent, voice_service)

    # 4. Анализ результатов
    print(f"\n4. 📊 Анализ результатов собеседования...")
    analyzer = InterviewAnalyzer()
    results = analyzer.analyze_interview(
        conversation,
        vacancy["required_skills"],
        vacancy["name"]
    )

    print("\n" + "=" * 60)
    print("🎯 РЕЗУЛЬТАТЫ СОБЕСЕДОВАНИЯ")
    print("=" * 60)
    print(f"🏆 Общая оценка: {results['overall_score']}/100")
    print(f"✅ Сильные стороны: {', '.join(results['strengths'])}")
    print(f"📈 Области развития: {', '.join(results['weaknesses'])}")
    print(f"📋 Рекомендация: {results['recommendation']}")
    print(f"\n💬 Обратная связь: {results['feedback']}")

    # 5. Сохранение результатов
    output_file = "interview_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Результаты сохранены в {output_file}")

    # 6. Персонализированная обратная связь
    if voice_service:
        feedback_summary = f"Ваша оценка {results['overall_score']} из 100. {results['feedback']}"
        voice_service.text_to_speech(feedback_summary)


if __name__ == "__main__":
    main()