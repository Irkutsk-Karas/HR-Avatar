# services/gigachat_client.py
import requests
import json
import os
import base64
from datetime import datetime, timedelta
from config import Config


class GigaChatClient:
    def __init__(self):
        self.config = Config()
        self.access_token = None
        self.token_expires_at = None
        self._get_access_token()

    def _get_basic_auth(self):
        """Создание Basic Auth заголовка"""
        credentials = f"{self.config.GIGACHAT_CLIENT_ID}:{self.config.GIGACHAT_CLIENT_SECRET}"
        return base64.b64encode(credentials.encode()).decode()

    def _get_access_token(self):
        """Получение access token с кэшированием"""
        # Проверка кэша
        if os.path.exists(self.config.TOKEN_CACHE_FILE):
            try:
                with open(self.config.TOKEN_CACHE_FILE, 'r') as f:
                    token_data = json.load(f)
                    expires_at = datetime.fromisoformat(token_data['expires_at'])
                    if expires_at > datetime.now():
                        self.access_token = token_data['access_token']
                        return
            except:
                pass

        # Запрос нового токена
        self._request_new_token()

    def _request_new_token(self):
        """Запрос нового access token"""
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'Authorization': f'Basic {self._get_basic_auth()}',
            'RqUID': self.config.GIGACHAT_CLIENT_ID,
        }

        data = {'scope': self.config.GIGACHAT_SCOPE}

        try:
            response = requests.post(
                self.config.GIGACHAT_AUTH_URL,
                headers=headers,
                data=data,
                verify=False,
                timeout=30
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 1800)

                # Сохранение в кэш
                cache_data = {
                    'access_token': self.access_token,
                    'expires_at': (datetime.now() + timedelta(seconds=expires_in - 300)).isoformat()
                }

                with open(self.config.TOKEN_CACHE_FILE, 'w') as f:
                    json.dump(cache_data, f)

            else:
                print(f"Ошибка авторизации: {response.status_code}")
                self.access_token = None

        except Exception as e:
            print(f"Ошибка при получении токена: {e}")
            self.access_token = None

    def get_chat_response(self, messages, temperature=0.7, max_tokens=1024):
        """Получение ответа от GigaChat"""
        if not self.access_token:
            print("Не удалось получить access token")
            return None

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }

        payload = {
            'model': 'GigaChat',
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }

        try:
            response = requests.post(
                f"{self.config.GIGACHAT_API_URL}/chat/completions",
                headers=headers,
                json=payload,
                verify=False,
                timeout=60
            )

            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            else:
                print(f"Ошибка API: {response.status_code}")
                return None

        except Exception as e:
            print(f"Ошибка при запросе к GigaChat: {e}")
            return None

    def extract_skills_from_text(self, text):
        """Извлечение навыков из текста"""
        prompt = f"""
        Извлеки технические навыки из текста. Верни ТОЛЬКО JSON: {{"skills": ["skill1", "skill2"]}}

        Текст: {text[:2000]}
        """

        messages = [
            {"role": "system", "content": "Ты эксперт по анализу резюме. Отвечай только JSON."},
            {"role": "user", "content": prompt}
        ]

        response = self.get_chat_response(messages, temperature=0.3)

        if response:
            try:
                # Очистка ответа
                json_str = response.strip()
                if '```json' in json_str:
                    json_str = json_str.split('```json')[1].split('```')[0].strip()

                data = json.loads(json_str)
                return data.get('skills', [])
            except:
                return self._fallback_skill_extraction(text)

        return self._fallback_skill_extraction(text)

    def _fallback_skill_extraction(self, text):
        """Резервный метод извлечения навыков"""
        common_skills = ["Python", "Java", "SQL", "JavaScript", "Linux", "Docker",
                         "Kubernetes", "AWS", "Git", "React", "PostgreSQL", "MongoDB"]

        found_skills = []
        for skill in common_skills:
            if skill.lower() in text.lower():
                found_skills.append(skill)
        return found_skills