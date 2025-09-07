# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import base64
import sys
import os
import time
import threading

# Добавляем путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импорты из services
from services import ResumeParser, InterviewAgent, InterviewAnalyzer, VoiceService
from config import Config

# Настройка страницы
st.set_page_config(
    page_title="HR Avatar 🤖",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Стили
st.markdown("""
<style>
    /* Основные стили */
    .main {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Заголовки */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Comic Sans MS', cursive, sans-serif;
        color: #2E86AB;
    }

    /* Кнопки */
    .stButton>button {
        font-family: 'Verdana', sans-serif;
        border-radius: 20px;
        border: 2px solid #2E86AB;
        background: linear-gradient(45deg, #2E86AB, #A23B72);
        color: white;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(46, 134, 171, 0.4);
    }

    /* Карточки сообщений */
    .user-message {
        background: linear-gradient(135deg, #E8F4F8, #D1E8F2);
        padding: 15px;
        border-radius: 20px;
        margin: 10px 0;
        border-left: 5px solid #2E86AB;
        font-family: 'Verdana', sans-serif;
    }

    .assistant-message {
        background: linear-gradient(135deg, #F8E8F4, #F2D1E8);
        padding: 15px;
        border-radius: 20px;
        margin: 10px 0;
        border-left: 5px solid #A23B72;
        font-family: 'Verdana', sans-serif;
    }

    /* Прогресс бар */
    .progress-container {
        background: #F0F0F0;
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
    }

    .progress-bar {
        height: 20px;
        background: linear-gradient(45deg, #2E86AB, #A23B72);
        border-radius: 10px;
        transition: width 0.3s ease;
    }

    /* Таблицы и графики */
    .plotly-graph-div {
        font-family: 'Verdana', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)


class AppUtils:
    """Вспомогательные утилиты"""

    @staticmethod
    def ensure_directory_exists(path):
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def save_uploaded_file(uploaded_file, save_dir="data"):
        AppUtils.ensure_directory_exists(save_dir)
        file_path = os.path.join(save_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path

    @staticmethod
    def create_skills_chart(skills_list):
        if not skills_list:
            return None

        # Берем топ-10 навыков
        top_skills = skills_list[:10]

        # Создаем DataFrame с градиентом цветов
        skills_df = pd.DataFrame({
            'Навык': top_skills,
            'Уровень': range(len(top_skills), 0, -1)  # Обратный порядок для красивого градиента
        })

        # Создаем график с русскими подписями
        fig = px.bar(skills_df,
                     x='Уровень',
                     y='Навык',
                     orientation='h',
                     title="🏆 Топ-10 навыков из вашего резюме",
                     color='Уровень',
                     color_continuous_scale='Blues')

        # Русские подписи и стилизация - совместимость со старыми версиями Plotly
        fig['layout'].update(
            font=dict(family='Verdana', size=12),
            xaxis=dict(title="", showticklabels=False),
            yaxis=dict(title="Навыки"),
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )

        return fig

    @staticmethod
    def create_score_gauge(score, title="Общая оценка"):
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"},
                    {'range': [80, 100], 'color': "lightgreen"}
                ]
            }
        ))
        return fig


# Инициализация состояния сессии
def init_session_state():
    # Этапы процесса
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1

    # Данные
    if 'resume_analysis' not in st.session_state:
        st.session_state.resume_analysis = None
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []
    if 'interview_results' not in st.session_state:
        st.session_state.interview_results = None
    if 'agent' not in st.session_state:
        st.session_state.agent = None

    # Голосовой режим
    if 'is_recording' not in st.session_state:
        st.session_state.is_recording = False
    if 'last_voice_text' not in st.session_state:
        st.session_state.last_voice_text = ""
    if 'voice_status' not in st.session_state:
        st.session_state.voice_status = ""
    if 'recording_start_time' not in st.session_state:
        st.session_state.recording_start_time = 0
    if 'processing_audio' not in st.session_state:
        st.session_state.processing_audio = False
    if 'recognition_quality' not in st.session_state:
        st.session_state.recognition_quality = ""


# Главная функция
def main():
    init_session_state()
    utils = AppUtils()

    st.title("🤖 HR Avatar - AI система собеседований")
    st.markdown("---")

    # Прогресс бар этапов
    col1, col2, col3 = st.columns(3)
    with col1:
        step1_class = "active-tab" if st.session_state.current_step >= 1 else "disabled-tab"
        st.markdown(f'<div class="{step1_class}">📊 1. Анализ резюме</div>', unsafe_allow_html=True)
    with col2:
        step2_class = "active-tab" if st.session_state.current_step >= 2 else "disabled-tab"
        st.markdown(f'<div class="{step2_class}">🎤 2. Собеседование</div>', unsafe_allow_html=True)
    with col3:
        step3_class = "active-tab" if st.session_state.current_step >= 3 else "disabled-tab"
        st.markdown(f'<div class="{step3_class}">📈 3. Результаты</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Боковая панель
    with st.sidebar:
        st.header("⚙️ Настройки")

        vacancy_options = {
            "Python Разработчик": ["Python", "Django", "PostgreSQL", "Docker", "Git"],
            "Data Scientist": ["Python", "ML", "Pandas", "SQL", "Statistics"],
            "DevOps Engineer": ["Docker", "Kubernetes", "AWS", "Linux", "CI/CD"]
        }

        selected_vacancy = st.selectbox(
            "🎯 Выберите вакансию:",
            list(vacancy_options.keys()),
            key="vacancy_select"
        )

        interview_mode = st.radio(
            "🎤 Режим собеседования:",
            ["Текстовый", "Голосовой"],
            key="interview_mode"
        )

        uploaded_file = st.file_uploader(
            "📄 Загрузите резюме (PDF или DOCX):",
            type=["pdf", "docx"],
            key="resume_uploader"
        )

        if st.button("🔄 Начать заново", key="restart_button"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            init_session_state()
            st.rerun()

    # Отображение текущего этапа
    if st.session_state.current_step == 1:
        show_resume_analysis(uploaded_file, vacancy_options, selected_vacancy, utils)
    elif st.session_state.current_step == 2:
        show_interview_interface(selected_vacancy, vacancy_options, interview_mode, utils)
    elif st.session_state.current_step == 3:
        show_results(utils)


def show_resume_analysis(uploaded_file, vacancy_options, selected_vacancy, utils):
    st.header("📊 Анализ резюме")

    if uploaded_file is None:
        st.info("📁 Загрузите резюме для начала анализа")
        return

    with st.spinner("🔍 Анализируем резюме..."):
        try:
            # Сохраняем и анализируем файл
            file_path = utils.save_uploaded_file(uploaded_file)
            parser = ResumeParser()
            resume_text = parser.extract_text(file_path)
            analysis = parser.parse_resume(resume_text, vacancy_options[selected_vacancy])

            st.session_state.resume_analysis = analysis

            # Визуализация
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Соответствие вакансии", f"{analysis['match_score']}%")
            with col2:
                status = "✅ Подходит" if analysis['match_score'] > 50 else "⚠️ На рассмотрение"
                st.metric("Рекомендация", status)
            with col3:
                st.metric("Навыков найдено", len(analysis['skills']))

            # График навыков
            if analysis['skills']:
                fig = utils.create_skills_chart(analysis['skills'])
                st.plotly_chart(fig, use_container_width=True)

            # Кнопка перехода к собеседованию
            if st.button("➡️ Перейти к собеседованию", type="primary"):
                st.session_state.current_step = 2
                st.rerun()

        except Exception as e:
            st.error(f"❌ Ошибка анализа: {str(e)}")


def show_interview_interface(vacancy_name, vacancy_options, interview_mode, utils):
    st.header("🎤 Проведение собеседования")

    if st.session_state.resume_analysis is None:
        st.warning("⚠️ Сначала проанализируйте резюме")
        return

    # Максимальное количество вопросов
    MAX_QUESTIONS = 8
    current_questions = len([msg for msg in st.session_state.conversation if msg[0] == "assistant"])

    # Прогресс бар собеседования
    st.info(f"📊 Прогресс: {current_questions}/{MAX_QUESTIONS} вопросов")

    # Визуальный прогресс бар
    progress_percent = min(current_questions / MAX_QUESTIONS * 100, 100)
    progress_html = f"""
    <div class="progress-container">
        <div class="progress-bar" style="width: {progress_percent}%"></div>
    </div>
    """
    st.markdown(progress_html, unsafe_allow_html=True)

    # Предупреждение о количестве вопросов
    if current_questions == 0:
        st.success(f"💡 Вам будет задано {MAX_QUESTIONS} вопросов. Отвечайте максимально подробно!")
    elif current_questions < MAX_QUESTIONS:
        st.info(f"💡 Осталось вопросов: {MAX_QUESTIONS - current_questions}")

    # Инициализация агента
    if st.session_state.agent is None:
        st.session_state.agent = InterviewAgent(vacancy_name, vacancy_options[vacancy_name])
        st.session_state.agent.start_interview()
        welcome_msg = st.session_state.agent.conversation_history[-1]["content"]
        st.session_state.conversation.append(("assistant", welcome_msg))
        current_questions += 1  # Увеличиваем счетчик после добавления приветствия

    # Отображение диалога
    st.subheader("💬 Диалог")
    for i, (role, message) in enumerate(st.session_state.conversation):
        if role == "assistant":
            st.markdown(f'<div class="assistant-message"><b>🤖 HR-аватар:</b> {message}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="user-message"><b>👤 Кандидат:</b> {message}</div>',
                        unsafe_allow_html=True)

    # Статус голосового ввода
    if st.session_state.voice_status:
        st.info(st.session_state.voice_status)

    # Поле ввода
    st.subheader("📝 Ваш ответ")

    if current_questions >= MAX_QUESTIONS:
        st.success("🎉 Вы ответили на все вопросы!")
        if st.button("✅ Завершить собеседование и перейти к результатам",
                     type="primary"):
            st.session_state.current_step = 3
            st.rerun()
        return

    if interview_mode == "Текстовый":
        user_input = st.text_area("💬 Введите ваш ответ:",
                                  height=100,
                                  placeholder="Напишите ваш ответ здесь...")

        if st.button("📤 Отправить ответ", type="primary") and user_input:
            success = process_user_input(user_input)
            if success:
                st.rerun()
            else:
                st.warning("🎉 Вы ответили на все вопросы! Нажмите 'Завершить собеседование'")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            user_input = st.text_area("✍️ Или введите текст вручную:",
                                      height=100,
                                      placeholder="Или напишите ответ здесь...")
        with col2:
            if st.button("🎤 Запись голоса", type="secondary",
                         disabled=st.session_state.is_recording):
                st.session_state.is_recording = True
                st.session_state.voice_status = "⏺️ Запись началась... Говорите сейчас!"
                st.session_state.recording_start_time = time.time()
                st.rerun()

        if user_input and st.button("📤 Отправить ответ", type="primary"):
            success = process_user_input(user_input)
            if success:
                st.rerun()
            else:
                st.warning("🎉 Вы ответили на все вопросы! Нажмите 'Завершить собеседование'")

    # Обработка голосовой записи
    if st.session_state.is_recording:
        with st.spinner("🎤 Идет запись... Говорите сейчас"):
            voice_service = VoiceService()
            voice_text = voice_service.speech_to_text(timeout=15)

            st.session_state.is_recording = False
            if voice_text:
                st.session_state.last_voice_text = voice_text
                st.session_state.voice_status = "✅ Запись распознана!"
                st.rerun()
            else:
                st.session_state.voice_status = "❌ Не удалось распознать речь"
                st.rerun()

    # Показать распознанный текст
    if st.session_state.last_voice_text:
        st.success(f"🎤 Распознанная речь: **{st.session_state.last_voice_text}**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Использовать этот текст", type="primary"):
                success = process_user_input(st.session_state.last_voice_text)
                st.session_state.last_voice_text = ""
                st.session_state.voice_status = ""
                if success:
                    st.rerun()
                else:
                    st.warning("🎉 Вы ответили на все вопросы! Нажмите 'Завершить собеседование'")
        with col2:
            if st.button("🔄 Записать заново", type="secondary"):
                st.session_state.last_voice_text = ""
                st.session_state.voice_status = ""
                st.rerun()

    # Советы по улучшению распознавания
    if interview_mode == "Голосовой":
        with st.expander("💡 Советы для лучшего распознавания:"):
            st.markdown("""
            - 🎤 **Говорите четко и разборчиво**
            - 🔇 **Уберите фоновый шум**
            - 📏 **Держите микрофон на расстоянии 10-15 см ото рта**
            - 🗣️ **Говорите полными предложениями**
            - ⏱️ **Делайте паузы между фразами**
            - 🔧 **Проверьте настройки микрофона в системе**
            """)

    # Кнопка досрочного завершения
    if current_questions > 0 and current_questions < MAX_QUESTIONS:
        if st.button("⏹️ Завершить досрочно", type="secondary"):
            st.session_state.current_step = 3
            st.rerun()


def process_user_input(user_input):
    """Обработка ответа пользователя с проверкой лимита вопросов"""
    MAX_QUESTIONS = 8
    current_questions = len([msg for msg in st.session_state.conversation if msg[0] == "assistant"])

    # Проверяем лимит вопросов
    if current_questions >= MAX_QUESTIONS:
        return False

    # Добавляем ответ пользователя
    st.session_state.conversation.append(("user", user_input))

    # Обработка ответа агентом
    agent = st.session_state.agent
    if agent.process_answer(user_input):
        last_msg = agent.conversation_history[-1]
        if last_msg["role"] == "assistant":
            st.session_state.conversation.append(("assistant", last_msg["content"]))

            # Проверяем не достигли ли лимита
            new_question_count = len([msg for msg in st.session_state.conversation if msg[0] == "assistant"])
            return new_question_count < MAX_QUESTIONS

    return True


def show_results(utils):
    st.header("📈 Результаты собеседования")

    if not st.session_state.conversation:
        st.info("ℹ️ Проведите собеседование чтобы увидеть результаты")
        return

    if st.session_state.interview_results is None and st.session_state.agent:
        with st.spinner("📊 Анализируем результаты собеседования..."):
            try:
                agent = st.session_state.agent
                analyzer = InterviewAnalyzer()
                results = analyzer.analyze_interview(
                    agent.conversation_history,
                    agent.required_skills,
                    agent.vacancy_name
                )
                st.session_state.interview_results = results
            except Exception as e:
                st.error(f"❌ Ошибка анализа: {str(e)}")
                return

    results = st.session_state.interview_results
    if not results:
        return

    # Визуализация результатов
    st.success("🎉 Собеседование завершено! Вот результаты:")

    col1, col2 = st.columns(2)

    with col1:
        # Общая оценка
        fig = utils.create_score_gauge(results['overall_score'])
        st.plotly_chart(fig, use_container_width=True)

        # Рекомендация с цветовой индикацией
        recommendation = results.get('recommendation', 'additional_interview')
        if recommendation == 'hire':
            st.success(f"✅ Рекомендация: **Нанять**")
        elif recommendation == 'reject':
            st.error(f"❌ Рекомендация: **Отказать**")
        else:
            st.warning(f"⚠️ Рекомендация: **Дополнительное собеседование**")

    with col2:
        # Сильные стороны
        if results.get('strengths'):
            st.subheader("✅ Сильные стороны:")
            for i, strength in enumerate(results['strengths'][:5], 1):
                st.markdown(f"{i}. {strength}")

        # Области развития
        if results.get('weaknesses'):
            st.subheader("📈 Области развития:")
            for i, weakness in enumerate(results['weaknesses'][:5], 1):
                st.markdown(f"{i}. {weakness}")

    # Детальная обратная связь
    st.subheader("💬 Детальная обратная связь")
    if results.get('feedback'):
        st.info(results['feedback'])
    else:
        st.info("Кандидат показал хорошие результаты. Рекомендуется к найму.")

    # Статистика собеседования
    st.subheader("📊 Статистика")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Всего вопросов", len([m for m in st.session_state.conversation if m[0] == "assistant"]))
    with col2:
        st.metric("Всего ответов", len([m for m in st.session_state.conversation if m[0] == "user"]))
    with col3:
        st.metric("Длительность", f"~{len(st.session_state.conversation) * 2} мин")

    # Кнопка нового собеседования
    if st.button("🔄 Начать новое собеседование", type="primary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        init_session_state()
        st.rerun()


if __name__ == "__main__":
    main()