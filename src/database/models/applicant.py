from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
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
            'phone_number': self.phone_number
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

    # Relationship to applicant profile
    profile = relationship("ApplicantProfile", back_populates="details")

    def to_dict(self) -> Dict:
        """Convert model instance to dictionary"""
        return {
            'detail_id': self.detail_id,
            'applicant_id': self.applicant_id,
            'applicant_role': self.applicant_role,
            'cv_path': self.cv_path
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ApplicantDetail':
        """Create model instance from dictionary"""
        return cls(
            applicant_id=data.get('applicant_id'),
            applicant_role=data.get('applicant_role'),
            cv_path=data.get('cv_path', '')
        )

    def __repr__(self):
        return f"<ApplicantDetail(id={self.detail_id}, applicant_id={self.applicant_id}, role='{self.applicant_role}')>"
