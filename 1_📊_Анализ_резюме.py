# pages/1_📊_Анализ_резюме.py
import streamlit as st
import sys
import os

# Добавляем путь для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services import ResumeParser
from config import Config


def main():
    st.title("📊 Детальный анализ резюме")

    # Ваш старый код анализа здесь
    config = Config()
    parser = ResumeParser()

    if st.button("🔄 Обновить анализ"):
        with st.spinner("Анализируем..."):
            resume_text = parser.extract_text(config.RESUME_PATH)
            # ... остальной анализ


if __name__ == "__main__":
    main()