from sqlalchemy import Column, Integer, String, Text, DateTime, func
from typing import Dict, List, Optional
import json
from .database import Base


class Applicant(Base):
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    cv_file_path = Column(String(500), nullable=False)
    txt_file_path = Column(String(500), nullable=True)
    extracted_text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    skills = Column(Text, nullable=True)
    highlights = Column(Text, nullable=True)
    accomplishments = Column(Text, nullable=True)
    work_experience = Column(Text, nullable=True)
    education = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(),
                        onupdate=func.current_timestamp())

    def to_dict(self) -> Dict:
        """Convert model instance to dictionary"""        # Parse JSON fields
        skills = []
        highlights = []
        accomplishments = []
        work_experience = []
        education = []

        try:
            if self.skills:
                skills = json.loads(self.skills) if isinstance(
                    self.skills, str) else self.skills
        except (json.JSONDecodeError, TypeError):
            skills = []

        try:
            if self.highlights:
                highlights = json.loads(self.highlights) if isinstance(
                    self.highlights, str) else self.highlights
        except (json.JSONDecodeError, TypeError):
            highlights = []

        try:
            if self.accomplishments:
                accomplishments = json.loads(self.accomplishments) if isinstance(
                    self.accomplishments, str) else self.accomplishments
        except (json.JSONDecodeError, TypeError):
            accomplishments = []

        try:
            if self.work_experience:
                work_experience = json.loads(self.work_experience) if isinstance(
                    self.work_experience, str) else self.work_experience
        except (json.JSONDecodeError, TypeError):
            work_experience = []

        try:
            if self.education:
                education = json.loads(self.education) if isinstance(
                    self.education, str) else self.education
        except (json.JSONDecodeError, TypeError):
            education = []

        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'cv_file_path': self.cv_file_path,
            'txt_file_path': self.txt_file_path,
            'extracted_text': self.extracted_text,
            'summary': self.summary,
            'skills': skills,
            'highlights': highlights,
            'accomplishments': accomplishments,
            'work_experience': work_experience,
            'education': education,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Applicant':
        """Create model instance from dictionary"""        # Convert lists/dicts to JSON strings
        skills_json = json.dumps(
            data.get('skills', [])) if data.get('skills') else None
        highlights_json = json.dumps(
            data.get('highlights', [])) if data.get('highlights') else None
        accomplishments_json = json.dumps(
            data.get('accomplishments', [])) if data.get('accomplishments') else None
        work_exp_json = json.dumps(data.get('work_experience', [])) if data.get(
            'work_experience') else None
        education_json = json.dumps(
            data.get('education', [])) if data.get('education') else None

        return cls(
            name=data.get('name', ''),
            email=data.get('email'),
            phone=data.get('phone'),
            cv_file_path=data.get('cv_file_path', ''),
            txt_file_path=data.get('txt_file_path'),
            extracted_text=data.get('extracted_text'),
            summary=data.get('summary'),
            skills=skills_json,
            highlights=highlights_json,
            accomplishments=accomplishments_json,
            work_experience=work_exp_json,
            education=education_json
        )

    def __repr__(self):
        return f"<Applicant(id={self.id}, name='{self.name}', email='{self.email}')>"
