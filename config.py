# config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # GigaChat настройки
    GIGACHAT_CLIENT_ID = "cbf73482-95d9-4134-ba0b-0e31ad62dcfe"
    GIGACHAT_CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET", "")
    GIGACHAT_SCOPE = "GIGACHAT_API_PERS"
    GIGACHAT_AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1"

    # Пути к файлам
    DATA_DIR = "data"
    VACANCIES_DIR = os.path.join(DATA_DIR, "vacancies")
    RESUME_PATH = os.path.join(DATA_DIR, "resume.pdf")
    VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "models/vosk-model-small-ru-0.22")

    # Настройки
    MAX_QUESTIONS = 8
    MIN_MATCH_SCORE = 30
    VOICE_RECORD_DURATION = 15
    TOKEN_CACHE_FILE = "gigachat_token.json"
    FONT_FAMILY = "Verdana, sans-serif"
    PRIMARY_COLOR = "#2E86AB"
    SECONDARY_COLOR = "#A23B72"

    VOICE_RECORD_DURATION = 15  # Увеличили до 15 секунд
    SAMPLE_RATE = 16000
    AUDIO_BUFFER_SIZE = 4096  # Увеличили буфер
    ENERGY_THRESHOLD = 300  # Понизили порог чувствительности
    PAUSE_THRESHOLD = 1.0  # Увеличили паузу для конца фразы

    # Настройки Vosk
    VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "models/vosk-model-small-ru-0.22")

    def __init__(self):
        # Создаем необходимые директории
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.VACANCIES_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(self.VOSK_MODEL_PATH), exist_ok=True)

        # Проверяем аудиоустройства
        self._check_audio_devices()

    def _check_audio_devices(self):
        """Проверяет доступные аудиоустройства"""
        try:
            import pyaudio
            audio = pyaudio.PyAudio()
            info = audio.get_default_input_device_info()
            print(f"✅ Аудиоустройство: {info.get('name', 'Unknown')}")
            audio.terminate()

        except:
            print("⚠️ Не удалось проверить аудиоустройства")

    def __init__(self):
        # Создаем необходимые директории для Streamlit
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.VACANCIES_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(self.VOSK_MODEL_PATH), exist_ok=True)