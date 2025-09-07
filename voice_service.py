# services/voice_service.py
import speech_recognition as sr
import pyttsx3
import time
from config import Config
import os
import json
import threading
from datetime import datetime

# Vosk для оффлайн распознавания
try:
    from vosk import Model, KaldiRecognizer
    import pyaudio

    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False


class VoiceService:
    def __init__(self):
        self.config = Config()
        self.tts_engine = None
        self.vosk_model = None
        self.audio = None
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Улучшенные настройки для лучшего распознавания
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

        self._setup_voice()
        self._setup_vosk()

    def _setup_vosk(self):
        """Настройка Vosk для оффлайн распознавания"""
        if VOSK_AVAILABLE and os.path.exists(self.config.VOSK_MODEL_PATH):
            try:
                self.vosk_model = Model(self.config.VOSK_MODEL_PATH)
                self.audio = pyaudio.PyAudio()
                print("✅ Vosk модель загружена")
            except Exception as e:
                print(f"❌ Ошибка загрузки Vosk модели: {e}")

    def _setup_voice(self):
        """Настройка голосового синтеза"""
        try:
            self.tts_engine = pyttsx3.init()
            voices = self.tts_engine.getProperty('voices')

            # Поиск русского голоса
            russian_voices = [v for v in voices if 'russian' in v.name.lower() or 'ru' in v.id.lower()]
            if russian_voices:
                self.tts_engine.setProperty('voice', russian_voices[0].id)

            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)

        except Exception as e:
            print(f"❌ Ошибка инициализации TTS: {e}")
            self.tts_engine = None

    def text_to_speech(self, text):
        """Озвучивание текста"""
        print(f"🗣️  HR-аватар: {text}")

        if not self.tts_engine:
            return

        try:
            # Создаем новый движок для каждого вызова чтобы избежать ошибок
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"❌ Ошибка синтеза речи: {e}")

    def speech_to_text_vosk(self, timeout=15):
        """Оффлайн распознавание через Vosk с pyaudio"""
        if not self.vosk_model or not self.audio:
            return None

        try:
            # Настройка аудиопотока с улучшенными параметрами
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=4096,
                input_device_index=None
            )

            recognizer = KaldiRecognizer(self.vosk_model, 16000)

            print(f"🎤 Слушаю... Говорите сейчас ({timeout} секунд)")

            # Записываем указанное время
            start_time = time.time()
            audio_data = b""

            while time.time() - start_time < timeout:
                try:
                    data = stream.read(4096, exception_on_overflow=False)
                    audio_data += data

                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text = result.get('text', '').strip()
                        if text and len(text) > 3:
                            stream.stop_stream()
                            stream.close()
                            return text

                except Exception as e:
                    print(f"⚠️ Ошибка чтения аудио: {e}")
                    continue

            # Если время вышло, пытаемся получить результат
            try:
                result = json.loads(recognizer.Result())
                text = result.get('text', '').strip()
                if text and len(text) > 3:
                    return text

                # Пробуем partial result
                partial_result = json.loads(recognizer.PartialResult())
                partial_text = partial_result.get('partial', '').strip()
                if partial_text and len(partial_text) > 3:
                    return partial_text

            except:
                pass

            stream.stop_stream()
            stream.close()

            return None

        except Exception as e:
            print(f"❌ Ошибка Vosk распознавания: {e}")
            return None

    def speech_to_text_google(self, timeout=15):
        """Распознавание через Google Speech Recognition с улучшенными настройками"""
        try:
            with self.microphone as source:
                # Предварительная калибровка для уменьшения шума
                print("🔧 Калибровка микрофона...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2)

                print(f"🎤 Слушаю... Говорите сейчас ({timeout} секунд)")

                # Увеличиваем время записи и паузы
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=timeout
                )

            # Пробуем распознать
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            return text

        except sr.UnknownValueError:
            print("❌ Речь не распознана")
            return None
        except sr.RequestError as e:
            print(f"❌ Ошибка сервиса Google: {e}")
            return None
        except Exception as e:
            print(f"❌ Ошибка записи: {e}")
            return None

    def speech_to_text(self, timeout=15):
        """Распознавание речи в текст с улучшенными настройками"""
        print(f"🎤 Запись началась... Говорите в течение {timeout} секунд")

        # Сначала пробуем Vosk
        if VOSK_AVAILABLE and self.vosk_model:
            text = self.speech_to_text_vosk(timeout)
            if text:
                print(f"✅ Vosk распознано: {text}")
                return text
            else:
                print("⚠️ Vosk не распознал речь, пробуем Google...")

        # Затем пробуем Google
        text = self.speech_to_text_google(timeout)
        if text:
            print(f"✅ Google распознано: {text}")
            return text

        print("❌ Не удалось распознать речь")
        return None

    def __del__(self):
        """Очистка ресурсов"""
        if self.audio:
            self.audio.terminate()