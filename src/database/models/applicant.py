from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from typing import Dict
from .database import Base
from utils.encryption import encryption


class ApplicantProfile(Base):
    __tablename__ = "applicant_profiles"

    applicant_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    address = Column(Text, nullable=True)
    phone_number = Column(Text, nullable=True)
    is_encrypted = Column(Boolean, default=False,
                          nullable=False)  # New encryption flag

    # Relationship to applicant details
    details = relationship("ApplicantDetail", back_populates="profile")

    def encrypt_data(self) -> 'ApplicantProfile':
        """Return a new instance with encrypted data"""
        if self.is_encrypted:
            return self  # Already encrypted

        encrypted_profile = ApplicantProfile(
            applicant_id=self.applicant_id,
            first_name=encryption.encrypt(self.first_name or ""),
            last_name=encryption.encrypt(self.last_name or ""),
            date_of_birth=self.date_of_birth,  # Don't encrypt dates
            address=encryption.encrypt(self.address or ""),
            phone_number=encryption.encrypt(self.phone_number or ""),
            is_encrypted=True
        )
        return encrypted_profile

    def decrypt_data(self) -> 'ApplicantProfile':
        """Return a new instance with decrypted data"""
        if not self.is_encrypted:
            return self  # Already decrypted

        decrypted_profile = ApplicantProfile(
            applicant_id=self.applicant_id,
            first_name=encryption.decrypt(self.first_name or ""),
            last_name=encryption.decrypt(self.last_name or ""),
            date_of_birth=self.date_of_birth,
            address=encryption.decrypt(self.address or ""),
            phone_number=encryption.decrypt(self.phone_number or ""),
            is_encrypted=False
        )
        return decrypted_profile

    def get_display_data(self) -> 'ApplicantProfile':
        """Get data ready for display (decrypted if needed)"""
        return self.decrypt_data() if self.is_encrypted else self

    def to_dict(self) -> Dict:
        """
        Convert model instance to dictionary.
        Ensures that the data is decrypted before being sent out.
        """
        # Get the display-ready (decrypted) version of the profile first.
        display_profile = self.get_display_data()

        return {
            'applicant_id': display_profile.applicant_id,
            'first_name': display_profile.first_name,
            'last_name': display_profile.last_name,
            'date_of_birth': display_profile.date_of_birth,
            'address': display_profile.address,
            'phone_number': display_profile.phone_number,
            # We report the original encryption state of the object in the DB.
            'is_encrypted': self.is_encrypted
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ApplicantProfile':
        """Create model instance from dictionary"""
        return cls(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            date_of_birth=data.get('date_of_birth'),
            address=data.get('address'),
            phone_number=data.get('phone_number'),
            is_encrypted=False
        )

    def __repr__(self):
        return f"<ApplicantProfile(id={self.applicant_id}, name='{self.first_name} {self.last_name}')>"


class ApplicantDetail(Base):
    __tablename__ = "applicant_details"

    detail_id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey(
        'applicant_profiles.applicant_id'), nullable=False)
    application_role = Column(String(100), nullable=True)
    cv_path = Column(Text, nullable=False)

    # Relationship to applicant profile
    profile = relationship("ApplicantProfile", back_populates="details")

    def to_dict(self) -> Dict:
        """Convert model instance to dictionary"""
        return {
            'detail_id': self.detail_id,
            'applicant_id': self.applicant_id,
            'application_role': self.application_role,
            'cv_path': self.cv_path
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ApplicantDetail':
        """Create model instance from dictionary"""
        return cls(
            applicant_id=data.get('applicant_id'),
            application_role=data.get('application_role'),
            cv_path=data.get('cv_path', '')
        )

    def __repr__(self):
        return f"<ApplicantDetail(id={self.detail_id}, applicant_id={self.applicant_id}, role='{self.application_role}')>"
