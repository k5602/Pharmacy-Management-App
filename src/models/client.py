"""
Client Model
Defines the client/patient data model and operations for the Pharmacy Management System
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, Text, Date, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property
from loguru import logger

from .base import BaseModel, BaseRepository, get_database_manager
from utils.validators import validate_phone, validate_email
from enum import Enum


class Gender(Enum):
    """Gender enumeration"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class BloodType(Enum):
    """Blood type enumeration"""
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class ActivityLevel(Enum):
    """Activity level enumeration"""
    SEDENTARY = "sedentary"
    LIGHT = "light"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Client(BaseModel):
    """
    Client/Patient model representing pharmacy clients
    """
    __tablename__ = "clients"

    # Personal Information
    client_pharmacy_id = Column(String(20), unique=True, nullable=False, index=True)
    client_name = Column(String(100), nullable=False, index=True)
    age = Column(Integer, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)  # 'male', 'female', 'other'

    # Contact Information
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    emergency_phone = Column(String(20), nullable=True)

    # Professional Information
    job = Column(String(100), nullable=True)
    work_effort = Column(String(50), nullable=True)  # 'light', 'moderate', 'heavy'

    # Medical Information
    diseases = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    medications = Column(Text, nullable=True)
    previous_attempts = Column(Text, nullable=True)
    current_treatment = Column(Text, nullable=True)
    medical_notes = Column(Text, nullable=True)

    # Visit Information
    visit_purpose = Column(Text, nullable=True)
    follow_up_date = Column(Date, nullable=True)
    last_visit_date = Column(Date, nullable=True)
    visit_count = Column(Integer, default=0)

    # Status and Preferences
    preferred_language = Column(String(10), default='ar')  # 'ar', 'en'
    consent_data_processing = Column(Boolean, default=False)
    consent_marketing = Column(Boolean, default=False)

    # Relationships
    diet_records = relationship("DietRecord", back_populates="client", cascade="all, delete-orphan")
    notes = relationship("ClientNote", back_populates="client", cascade="all, delete-orphan")

    @hybrid_property
    def full_display_name(self) -> str:
        """Get formatted display name with ID"""
        return f"{self.client_name} (ID: {self.client_pharmacy_id})"

    @hybrid_property
    def calculated_age(self) -> Optional[int]:
        """Calculate age from date of birth if available"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return self.age

    @hybrid_property
    def next_follow_up_days(self) -> Optional[int]:
        """Days until next follow-up appointment"""
        if self.follow_up_date:
            delta = self.follow_up_date - date.today()
            return delta.days
        return None

    @hybrid_property
    def is_follow_up_due(self) -> bool:
        """Check if follow-up is due within 7 days"""
        if self.follow_up_date:
            return self.next_follow_up_days <= 7
        return False

    def update_last_visit(self) -> None:
        """Update last visit date and increment visit count"""
        self.last_visit_date = date.today()
        self.visit_count = (self.visit_count or 0) + 1
        self.updated_at = datetime.utcnow()

    def get_latest_diet_record(self):
        """Get the most recent diet record"""
        if self.diet_records:
            return max(self.diet_records, key=lambda x: x.created_at)
        return None

    def get_bmi_history(self) -> List[Dict[str, Any]]:
        """Get BMI history from diet records"""
        history = []
        for record in sorted(self.diet_records, key=lambda x: x.created_at):
            if record.bmi:
                history.append({
                    'date': record.created_at.date(),
                    'bmi': record.bmi,
                    'weight': record.current_weight,
                    'height': record.height
                })
        return history

    def get_weight_progression(self) -> List[Dict[str, Any]]:
        """Get weight progression from diet records"""
        progression = []
        for record in sorted(self.diet_records, key=lambda x: x.created_at):
            if record.current_weight:
                progression.append({
                    'date': record.created_at.date(),
                    'weight': record.current_weight,
                    'previous_weight': record.previous_weight
                })
        return progression

    def to_dict(self) -> Dict[str, Any]:
        """Convert client to dictionary with additional computed fields"""
        data = super().to_dict()
        data.update({
            'full_display_name': self.full_display_name,
            'calculated_age': self.calculated_age,
            'next_follow_up_days': self.next_follow_up_days,
            'is_follow_up_due': self.is_follow_up_due,
            'latest_bmi': None,
            'latest_weight': None
        })

        latest_diet = self.get_latest_diet_record()
        if latest_diet:
            data['latest_bmi'] = latest_diet.bmi
            data['latest_weight'] = latest_diet.current_weight

        return data

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, pharmacy_id='{self.client_pharmacy_id}', name='{self.client_name}')>"


class ClientNote(BaseModel):
    """
    Client notes model for storing rich text notes about clients
    """
    __tablename__ = "client_notes"

    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default='general')  # 'general', 'medical', 'diet', 'follow_up'
    is_private = Column(Boolean, default=False)
    tags = Column(String(500), nullable=True)  # Comma-separated tags

    # Relationships
    client = relationship("Client", back_populates="notes")

    def get_tags_list(self) -> List[str]:
        """Get tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    def set_tags_list(self, tags: List[str]) -> None:
        """Set tags from a list"""
        self.tags = ', '.join(tags) if tags else None

    def __repr__(self) -> str:
        return f"<ClientNote(id={self.id}, client_id={self.client_id}, type='{self.note_type}')>"


class ClientRepository(BaseRepository):
    """
    Repository class for client data operations
    """

    def __init__(self):
        super().__init__(get_database_manager(), Client)

    def create_client(self, **kwargs) -> Optional[Client]:
        """Create a new client with validation"""
        try:
            # Validate phone number if provided
            if 'phone' in kwargs and kwargs['phone']:
                if not validate_phone(kwargs['phone']):
                    raise ValueError("Invalid phone number format")

            # Validate email if provided
            if 'email' in kwargs and kwargs['email']:
                if not validate_email(kwargs['email']):
                    raise ValueError("Invalid email format")

            # Generate pharmacy ID if not provided
            if 'client_pharmacy_id' not in kwargs or not kwargs['client_pharmacy_id']:
                kwargs['client_pharmacy_id'] = self.generate_pharmacy_id()

            # Calculate age from date of birth if provided
            if 'date_of_birth' in kwargs and kwargs['date_of_birth'] and 'age' not in kwargs:
                dob = kwargs['date_of_birth']
                if isinstance(dob, str):
                    dob = datetime.strptime(dob, '%Y-%m-%d').date()
                today = date.today()
                kwargs['age'] = today.year - dob.year - (
                    (today.month, today.day) < (dob.month, dob.day)
                )

            return self.create(**kwargs)

        except Exception as e:
            raise ValueError(f"Failed to create client: {str(e)}")

    def generate_pharmacy_id(self) -> str:
        """Generate the next available pharmacy ID"""
        with self.db_manager.get_session() as session:
            try:
                # Get the highest existing pharmacy ID
                result = session.query(Client.client_pharmacy_id).filter(
                    Client.client_pharmacy_id.regexp(r'^\d+$')
                ).order_by(Client.client_pharmacy_id.desc()).first()

                if result and result[0]:
                    max_id = int(result[0])
                    new_id = max_id + 1
                else:
                    new_id = 1

                # Format as 5-digit ID with leading zeros
                return f"{new_id:05d}"

            except Exception:
                # Fallback: use timestamp-based ID
                return datetime.now().strftime("%Y%m%d%H%M%S")

    def search_clients(self, search_term: str, limit: int = 50) -> List[Client]:
        """Search clients by name or pharmacy ID"""
        with self.db_manager.get_session() as session:
            try:
                search_term = f"%{search_term}%"
                return session.query(Client).filter(
                    Client.is_active == True,
                    (Client.client_name.ilike(search_term) |
                     Client.client_pharmacy_id.like(search_term))
                ).limit(limit).all()

            except Exception as e:
                logger.error(f"Failed to search clients: {e}")
                return []

    def get_by_pharmacy_id(self, pharmacy_id: str) -> Optional[Client]:
        """Get client by pharmacy ID"""
        with self.db_manager.get_session() as session:
            try:
                return session.query(Client).filter(
                    Client.client_pharmacy_id == pharmacy_id,
                    Client.is_active == True
                ).first()
            except Exception as e:
                logger.error(f"Failed to get client by pharmacy ID: {e}")
                return None

    def get_clients_with_upcoming_followups(self, days_ahead: int = 7) -> List[Client]:
        """Get clients with follow-up appointments in the next N days"""
        with self.db_manager.get_session() as session:
            try:
                target_date = date.today() + timedelta(days=days_ahead)
                return session.query(Client).filter(
                    Client.is_active == True,
                    Client.follow_up_date <= target_date,
                    Client.follow_up_date >= date.today()
                ).order_by(Client.follow_up_date).all()

            except Exception as e:
                logger.error(f"Failed to get upcoming follow-ups: {e}")
                return []

    def get_clients_by_criteria(self, criteria: Dict[str, Any]) -> List[Client]:
        """Get clients based on multiple criteria"""
        with self.db_manager.get_session() as session:
            try:
                query = session.query(Client).filter(Client.is_active == True)

                # Age range filter
                if 'min_age' in criteria and criteria['min_age']:
                    query = query.filter(Client.age >= criteria['min_age'])
                if 'max_age' in criteria and criteria['max_age']:
                    query = query.filter(Client.age <= criteria['max_age'])

                # Gender filter
                if 'gender' in criteria and criteria['gender']:
                    query = query.filter(Client.gender == criteria['gender'])

                # Work effort filter
                if 'work_effort' in criteria and criteria['work_effort']:
                    query = query.filter(Client.work_effort == criteria['work_effort'])

                # Date range filter
                if 'from_date' in criteria and criteria['from_date']:
                    query = query.filter(Client.created_at >= criteria['from_date'])
                if 'to_date' in criteria and criteria['to_date']:
                    query = query.filter(Client.created_at <= criteria['to_date'])

                return query.all()

            except Exception as e:
                logger.error(f"Failed to get clients by criteria: {e}")
                return []

    def get_client_statistics(self) -> Dict[str, Any]:
        """Get client statistics"""
        with self.db_manager.get_session() as session:
            try:
                total_clients = session.query(Client).filter(Client.is_active == True).count()

                # Gender distribution
                gender_stats = session.query(
                    Client.gender,
                    session.query(Client).filter(
                        Client.is_active == True,
                        Client.gender == Client.gender
                    ).count()
                ).filter(Client.is_active == True).group_by(Client.gender).all()

                # Age distribution
                age_ranges = [
                    (0, 18, 'children'),
                    (18, 35, 'young_adults'),
                    (35, 55, 'adults'),
                    (55, 100, 'seniors')
                ]

                age_distribution = {}
                for min_age, max_age, label in age_ranges:
                    count = session.query(Client).filter(
                        Client.is_active == True,
                        Client.age >= min_age,
                        Client.age < max_age
                    ).count()
                    age_distribution[label] = count

                # Recent clients (last 30 days)
                thirty_days_ago = datetime.now() - timedelta(days=30)
                recent_clients = session.query(Client).filter(
                    Client.is_active == True,
                    Client.created_at >= thirty_days_ago
                ).count()

                # Upcoming follow-ups
                upcoming_followups = len(self.get_clients_with_upcoming_followups())

                return {
                    'total_clients': total_clients,
                    'gender_distribution': dict(gender_stats),
                    'age_distribution': age_distribution,
                    'recent_clients': recent_clients,
                    'upcoming_followups': upcoming_followups
                }

            except Exception as e:
                logger.error(f"Failed to get client statistics: {e}")
                return {}

    def update_client(self, client_id: int, **kwargs) -> Optional[Client]:
        """Update client with validation"""
        try:
            # Validate phone number if provided
            if 'phone' in kwargs and kwargs['phone']:
                if not validate_phone(kwargs['phone']):
                    raise ValueError("Invalid phone number format")

            # Validate email if provided
            if 'email' in kwargs and kwargs['email']:
                if not validate_email(kwargs['email']):
                    raise ValueError("Invalid email format")

            return self.update(client_id, **kwargs)

        except Exception as e:
            raise ValueError(f"Failed to update client: {str(e)}")


class ClientNoteRepository(BaseRepository):
    """
    Repository class for client notes operations
    """

    def __init__(self):
        super().__init__(get_database_manager(), ClientNote)

    def get_notes_for_client(self, client_id: int, note_type: Optional[str] = None) -> List[ClientNote]:
        """Get all notes for a specific client"""
        with self.db_manager.get_session() as session:
            try:
                query = session.query(ClientNote).filter(
                    ClientNote.client_id == client_id,
                    ClientNote.is_active == True
                )

                if note_type:
                    query = query.filter(ClientNote.note_type == note_type)

                return query.order_by(ClientNote.created_at.desc()).all()

            except Exception as e:
                logger.error(f"Failed to get notes for client {client_id}: {e}")
                return []

    def create_note(self, client_id: int, content: str, **kwargs) -> Optional[ClientNote]:
        """Create a new note for a client"""
        try:
            kwargs['client_id'] = client_id
            kwargs['content'] = content
            return self.create(**kwargs)
        except Exception as e:
            raise ValueError(f"Failed to create note: {str(e)}")

    def search_notes(self, search_term: str, client_id: Optional[int] = None) -> List[ClientNote]:
        """Search notes by content"""
        with self.db_manager.get_session() as session:
            try:
                search_term = f"%{search_term}%"
                query = session.query(ClientNote).filter(
                    ClientNote.is_active == True,
                    (ClientNote.content.ilike(search_term) |
                     ClientNote.title.ilike(search_term) |
                     ClientNote.tags.ilike(search_term))
                )

                if client_id:
                    query = query.filter(ClientNote.client_id == client_id)

                return query.order_by(ClientNote.created_at.desc()).all()

            except Exception as e:
                logger.error(f"Failed to search notes: {e}")
                return []
