# services/resume_parser.py
import pdfplumber
import docx
from sentence_transformers import SentenceTransformer, util
import torch
from .gigachat_client import GigaChatClient
from config import Config


class ResumeParser:
    def __init__(self):
        self.giga_client = GigaChatClient()
        self.skill_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.config = Config()

    def extract_text(self, file_path):
        """Извлечение текста из PDF или DOCX"""
        text = ""
        try:
            if file_path.endswith('.pdf'):
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        if page.extract_text():
                            text += page.extract_text() + "\n"
            elif file_path.endswith('.docx'):
                doc = docx.Document(file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
        except Exception as e:
            print(f"Ошибка чтения файла: {e}")
        return text

    def parse_resume(self, resume_text, vacancy_requirements):
        """Анализ резюме и расчет соответствия вакансии"""
        # Извлечение навыков
        skills = self.giga_client.extract_skills_from_text(resume_text)

        # Расчет соответствия
        match_score = self._calculate_match_score(skills, vacancy_requirements)

        return {
            "skills": skills,
            "match_score": match_score,
            "recommendation": "Пригласить на собеседование" if match_score > 50 else "Рассмотреть дополнительно"
        }

    def _calculate_match_score(self, candidate_skills, required_skills):
        """Расчет соответствия навыков"""
        if not candidate_skills or not required_skills:
            return 0.0

        try:
            # Преобразование навыков в эмбеддинги
            candidate_embeddings = self.skill_model.encode(candidate_skills, convert_to_tensor=True)
            required_embeddings = self.skill_model.encode(required_skills, convert_to_tensor=True)

            # Расчет косинусного сходства
            cos_scores = util.pytorch_cos_sim(required_embeddings, candidate_embeddings)
            max_scores = cos_scores.max(dim=1)[0]

            score = max_scores.mean().item() * 100
            return round(score, 2)

        except Exception as e:
            print(f"Ошибка расчета эмбеддингов: {e}")
            # Простой расчет
            matched_skills = [skill for skill in required_skills if skill in candidate_skills]
            if not required_skills:
                return 0.0
            score = (len(matched_skills) / len(required_skills)) * 100
            return round(score, 2)