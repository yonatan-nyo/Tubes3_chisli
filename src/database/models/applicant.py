from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, func
from sqlalchemy.orm import relationship
from typing import Dict
import json
from .database import Base


class ApplicantProfile(Base):
    __tablename__ = "applicant_profiles"

    applicant_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    address = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(),
                        onupdate=func.current_timestamp())

    # Relationship to applicant details
    details = relationship("ApplicantDetail", back_populates="profile")

    def to_dict(self) -> Dict:
        """Convert model instance to dictionary"""
        return {
            'applicant_id': self.applicant_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'date_of_birth': self.date_of_birth,
            'address': self.address,
            'phone_number': self.phone_number,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ApplicantProfile':
        """Create model instance from dictionary"""
        return cls(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            date_of_birth=data.get('date_of_birth'),
            address=data.get('address'),
            phone_number=data.get('phone_number')
        )

    def __repr__(self):
        return f"<ApplicantProfile(id={self.applicant_id}, name='{self.first_name} {self.last_name}')>"


class ApplicantDetail(Base):
    __tablename__ = "applicant_details"

    detail_id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey(
        'applicant_profiles.applicant_id'), nullable=False)
    applicant_role = Column(String(100), nullable=True)
    cv_path = Column(Text, nullable=False)
    txt_file_path = Column(Text, nullable=True)
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

    # Relationship to applicant profile
    profile = relationship("ApplicantProfile", back_populates="details")

    def to_dict(self) -> Dict:
        """Convert model instance to dictionary"""
        # Parse JSON fields
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
            'detail_id': self.detail_id,
            'applicant_id': self.applicant_id,
            'applicant_role': self.applicant_role,
            'cv_path': self.cv_path,
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
    def from_dict(cls, data: Dict) -> 'ApplicantDetail':
        """Create model instance from dictionary"""
        # Convert lists/dicts to JSON strings
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
            applicant_id=data.get('applicant_id'),
            applicant_role=data.get('applicant_role'),
            cv_path=data.get('cv_path', ''),
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
        return f"<ApplicantDetail(id={self.detail_id}, applicant_id={self.applicant_id}, role='{self.applicant_role}')>"
