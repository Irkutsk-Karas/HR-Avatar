# services/__init__.py
"""
Пакет services - сервисные модули для HR-Аватара
"""

import os
import sys

# Добавляем путь к корневой директории проекта
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Версия пакета
__version__ = "1.0.0"
__author__ = "HR-Avatar Team"

# Импорты для удобного доступа
from .gigachat_client import GigaChatClient
from .resume_parser import ResumeParser
from .interview_agent import InterviewAgent
from .analyzer import InterviewAnalyzer
from .voice_service import VoiceService

# Экспортируемые объекты
__all__ = [
    'GigaChatClient',
    'ResumeParser',
    'InterviewAgent',
    'InterviewAnalyzer',
    'VoiceService'
]