"""
Client Controller
Handles client management, BMI calculations, demographics, and follow-up tracking
for the Pharmacy Management System
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from PyQt6.QtCore import pyqtSignal
from loguru import logger

from .base import BaseController
from models.client import Client, ClientNote, ClientRepository, ClientNoteRepository
from models.diet import DietRecord, DietRepository, BMICategory, WeightCondition
from utils.validation import ClientValidator, MedicalValidator


class ClientController(BaseController):
    """Controller for client management operations"""

    # Specific signals for client operations
    client_created = pyqtSignal(dict)  # client data
    client_updated = pyqtSignal(dict)  # client data
    client_deleted = pyqtSignal(str)   # client_id
    follow_up_due = pyqtSignal(list)   # list of clients due for follow-up
    bmi_calculated = pyqtSignal(dict)  # BMI calculation results

    def __init__(self, parent=None):
        super().__init__(parent)
        self.client_repo = None
        self.note_repo = None
        self.diet_repo = None
        self.client_validator = ClientValidator()
        self.medical_validator = MedicalValidator()

    def _do_initialize(self) -> bool:
        """Initialize the client controller"""
        try:
            # Initialize repositories
            self.client_repo = ClientRepository()
            self.note_repo = ClientNoteRepository()
            self.diet_repo = DietRepository()

            logger.info("ClientController initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize ClientController: {e}")
            return False

    # ==================== Client CRUD Operations ====================

    def create_client(self, client_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new client

        Args:
            client_data: Dictionary containing client information

        Returns:
            str: Client ID if successful, None if failed
        """
        try:
            # Validate input data
            validation_result = self.client_validator.validate_client_data(client_data)
            if not validation_result['is_valid']:
                error_msg = "; ".join(validation_result['errors'])
                self.emit_error("Validation Error", f"Client data validation failed: {error_msg}")
                return None

            validated_data = validation_result['data']

            # Create client instance
            client = Client(
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                phone_number=validated_data['phone_number'],
                birth_date=validated_data.get('birth_date'),
                gender=validated_data.get('gender'),
                email=validated_data.get('email'),
                address=validated_data.get('address'),
                emergency_contact=validated_data.get('emergency_contact'),
                medical_conditions=validated_data.get('medical_conditions', ''),
                allergies=validated_data.get('allergies', ''),
                current_medications=validated_data.get('current_medications', ''),
                notes=validated_data.get('notes', '')
            )

            # Save to database
            client_id = self.client_repo.create_client(client)

            if client_id:
                self.emit_success("Client Created", f"Client {client.full_display_name} created successfully")
                self.client_created.emit(client.to_dict())
                self.emit_data_changed("client_created", {"client_id": client_id})
                return client_id
            else:
                self.emit_error("Creation Failed", "Failed to create client in database")
                return None

        except Exception as e:
            self.handle_database_error(e, "creating client")
            return None

    def update_client(self, client_id: str, updated_data: Dict[str, Any]) -> bool:
        """
        Update an existing client

        Args:
            client_id: Client ID to update
            updated_data: Dictionary containing updated client information

        Returns:
            bool: True if successful
        """
        try:
            # Get existing client
            existing_client = self.get_client_by_id(client_id)
            if not existing_client:
                self.emit_error("Client Not Found", f"Client with ID {client_id} not found")
                return False

            # Validate updated data
            validation_result = self.client_validator.validate_client_data(updated_data, is_update=True)
            if not validation_result['is_valid']:
                error_msg = "; ".join(validation_result['errors'])
                self.emit_error("Validation Error", f"Update data validation failed: {error_msg}")
                return False

            validated_data = validation_result['data']

            # Update client
            success = self.client_repo.update_client(client_id, validated_data)

            if success:
                updated_client = self.get_client_by_id(client_id)
                self.emit_success("Client Updated", f"Client {updated_client.full_display_name} updated successfully")
                self.client_updated.emit(updated_client.to_dict())
                self.emit_data_changed("client_updated", {"client_id": client_id})
                return True
            else:
                self.emit_error("Update Failed", "Failed to update client in database")
                return False

        except Exception as e:
            self.handle_database_error(e, "updating client")
            return False

    def delete_client(self, client_id: str) -> bool:
        """
        Delete a client (soft delete - mark as inactive)

        Args:
            client_id: Client ID to delete

        Returns:
            bool: True if successful
        """
        try:
            # Get client for confirmation
            client = self.get_client_by_id(client_id)
            if not client:
                self.emit_error("Client Not Found", f"Client with ID {client_id} not found")
                return False

            # Perform soft delete
            success = self.client_repo.update_client(client_id, {"is_active": False})

            if success:
                self.emit_success("Client Deleted", f"Client {client.full_display_name} deleted successfully")
                self.client_deleted.emit(client_id)
                self.emit_data_changed("client_deleted", {"client_id": client_id})
                return True
            else:
                self.emit_error("Deletion Failed", "Failed to delete client")
                return False

        except Exception as e:
            self.handle_database_error(e, "deleting client")
            return False

    def get_client_by_id(self, client_id: str) -> Optional[Client]:
        """
        Get a client by ID

        Args:
            client_id: Client ID

        Returns:
            Client: Client instance or None
        """
        try:
            return self.client_repo.get_by_id(client_id)
        except Exception as e:
            logger.error(f"Error getting client {client_id}: {e}")
            return None

    def get_client_by_pharmacy_id(self, pharmacy_id: str) -> Optional[Client]:
        """
        Get a client by pharmacy ID

        Args:
            pharmacy_id: Pharmacy ID

        Returns:
            Client: Client instance or None
        """
        try:
            return self.client_repo.get_by_pharmacy_id(pharmacy_id)
        except Exception as e:
            logger.error(f"Error getting client by pharmacy ID {pharmacy_id}: {e}")
            return None

    def search_clients(self, search_term: str, filters: Dict[str, Any] = None) -> List[Client]:
        """
        Search for clients

        Args:
            search_term: Search term (name, phone, etc.)
            filters: Additional search filters

        Returns:
            List[Client]: List of matching clients
        """
        try:
            if filters is None:
                filters = {}

            # Add default filter for active clients only
            filters.setdefault('is_active', True)

            return self.client_repo.search_clients(search_term, filters)

        except Exception as e:
            logger.error(f"Error searching clients: {e}")
            return []

    def get_all_clients(self, include_inactive: bool = False) -> List[Client]:
        """
        Get all clients

        Args:
            include_inactive: Whether to include inactive clients

        Returns:
            List[Client]: List of all clients
        """
        try:
            filters = {} if include_inactive else {"is_active": True}
            return self.client_repo.get_clients_by_criteria(filters)
        except Exception as e:
            logger.error(f"Error getting all clients: {e}")
            return []

    # ==================== BMI and Health Calculations ====================

    def calculate_bmi(self, weight: float, height: float, client_id: str = None) -> Dict[str, Any]:
        """
        Calculate BMI and related health metrics

        Args:
            weight: Weight in kg
            height: Height in cm
            client_id: Optional client ID for record keeping

        Returns:
            dict: BMI calculation results
        """
        try:
            # Validate input
            validation_result = self.medical_validator.validate_bmi_data({
                'weight': weight,
                'height': height
            })

            if not validation_result['is_valid']:
                error_msg = "; ".join(validation_result['errors'])
                self.emit_error("Validation Error", f"BMI data validation failed: {error_msg}")
                return {}

            # Calculate BMI
            height_m = height / 100  # Convert cm to meters
            bmi = round(weight / (height_m ** 2), 2)

            # Determine BMI category
            if bmi < 18.5:
                category = BMICategory.UNDERWEIGHT
                category_text = "Underweight"
                health_status = "Below normal weight"
            elif 18.5 <= bmi < 25:
                category = BMICategory.NORMAL
                category_text = "Normal"
                health_status = "Healthy weight range"
            elif 25 <= bmi < 30:
                category = BMICategory.OVERWEIGHT
                category_text = "Overweight"
                health_status = "Above normal weight"
            else:
                category = BMICategory.OBESE
                category_text = "Obese"
                health_status = "Significantly above normal weight"

            # Calculate ideal weight range (BMI 18.5-24.9)
            ideal_weight_min = round(18.5 * (height_m ** 2), 1)
            ideal_weight_max = round(24.9 * (height_m ** 2), 1)

            # Calculate weight to lose/gain to reach ideal range
            weight_to_ideal = 0
            if bmi < 18.5:
                weight_to_ideal = round(ideal_weight_min - weight, 1)
            elif bmi > 24.9:
                weight_to_ideal = round(weight - ideal_weight_max, 1)

            result = {
                'bmi': bmi,
                'category': category,
                'category_text': category_text,
                'health_status': health_status,
                'ideal_weight_range': (ideal_weight_min, ideal_weight_max),
                'weight_to_ideal': weight_to_ideal,
                'is_healthy': category == BMICategory.NORMAL,
                'calculation_date': datetime.now(),
                'weight': weight,
                'height': height
            }

            # Emit signal
            self.bmi_calculated.emit(result)

            # Log to client record if client_id provided
            if client_id:
                self.emit_data_changed("bmi_calculated", {
                    "client_id": client_id,
                    "bmi_data": result
                })

            return result

        except Exception as e:
            logger.error(f"Error calculating BMI: {e}")
            self.emit_error("BMI Calculation Error", f"Failed to calculate BMI: {str(e)}")
            return {}

    def get_client_bmi_history(self, client_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get BMI history for a client

        Args:
            client_id: Client ID
            limit: Maximum number of records to return

        Returns:
            List[dict]: BMI history records
        """
        try:
            client = self.get_client_by_id(client_id)
            if not client:
                return []

            return client.get_bmi_history(limit)

        except Exception as e:
            logger.error(f"Error getting BMI history for client {client_id}: {e}")
            return []

    def get_weight_progression(self, client_id: str) -> Dict[str, Any]:
        """
        Get weight progression analysis for a client

        Args:
            client_id: Client ID

        Returns:
            dict: Weight progression data
        """
        try:
            client = self.get_client_by_id(client_id)
            if not client:
                return {}

            return client.get_weight_progression()

        except Exception as e:
            logger.error(f"Error getting weight progression for client {client_id}: {e}")
            return {}

    # ==================== Follow-up Management ====================

    def get_clients_due_for_followup(self, days_ahead: int = 7) -> List[Client]:
        """
        Get clients who are due for follow-up visits

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List[Client]: Clients due for follow-up
        """
        try:
            clients = self.client_repo.get_clients_with_upcoming_followups(days_ahead)

            if clients:
                self.follow_up_due.emit([client.to_dict() for client in clients])

            return clients

        except Exception as e:
            logger.error(f"Error getting clients due for follow-up: {e}")
            return []

    def schedule_follow_up(self, client_id: str, follow_up_date: date, notes: str = "") -> bool:
        """
        Schedule a follow-up for a client

        Args:
            client_id: Client ID
            follow_up_date: Date for follow-up
            notes: Optional notes

        Returns:
            bool: True if successful
        """
        try:
            success = self.client_repo.update_client(client_id, {
                "next_follow_up": follow_up_date,
                "follow_up_notes": notes
            })

            if success:
                client = self.get_client_by_id(client_id)
                self.emit_success("Follow-up Scheduled",
                                f"Follow-up scheduled for {client.full_display_name} on {follow_up_date}")
                self.emit_data_changed("follow_up_scheduled", {
                    "client_id": client_id,
                    "follow_up_date": follow_up_date.isoformat()
                })

            return success

        except Exception as e:
            self.handle_database_error(e, "scheduling follow-up")
            return False

    def complete_follow_up(self, client_id: str, notes: str = "") -> bool:
        """
        Mark a follow-up visit as completed

        Args:
            client_id: Client ID
            notes: Visit notes

        Returns:
            bool: True if successful
        """
        try:
            client = self.get_client_by_id(client_id)
            if not client:
                return False

            # Update last visit date and clear next follow-up
            success = self.client_repo.update_client(client_id, {
                "last_visit_date": datetime.now().date(),
                "next_follow_up": None,
                "follow_up_notes": ""
            })

            # Add completion note if notes provided
            if success and notes:
                self.add_client_note(client_id, f"Follow-up completed: {notes}", "follow_up")

            if success:
                self.emit_success("Follow-up Completed",
                                f"Follow-up completed for {client.full_display_name}")
                self.emit_data_changed("follow_up_completed", {"client_id": client_id})

            return success

        except Exception as e:
            self.handle_database_error(e, "completing follow-up")
            return False

    # ==================== Client Notes Management ====================

    def add_client_note(self, client_id: str, content: str, note_type: str = "general",
                       tags: List[str] = None) -> bool:
        """
        Add a note to a client's record

        Args:
            client_id: Client ID
            content: Note content
            note_type: Type of note (general, medical, follow_up, etc.)
            tags: Optional tags for the note

        Returns:
            bool: True if successful
        """
        try:
            note = ClientNote(
                client_id=client_id,
                content=content,
                note_type=note_type,
                created_by="system",  # TODO: Replace with actual user when auth is implemented
                tags=",".join(tags) if tags else ""
            )

            note_id = self.note_repo.create_note(note)

            if note_id:
                self.emit_data_changed("note_added", {
                    "client_id": client_id,
                    "note_id": note_id
                })
                return True
            else:
                self.emit_error("Note Creation Failed", "Failed to create client note")
                return False

        except Exception as e:
            self.handle_database_error(e, "adding client note")
            return False

    def get_client_notes(self, client_id: str, note_type: str = None,
                        limit: int = 50) -> List[ClientNote]:
        """
        Get notes for a client

        Args:
            client_id: Client ID
            note_type: Optional filter by note type
            limit: Maximum number of notes to return

        Returns:
            List[ClientNote]: Client notes
        """
        try:
            return self.note_repo.get_notes_for_client(client_id, note_type, limit)
        except Exception as e:
            logger.error(f"Error getting notes for client {client_id}: {e}")
            return []

    def search_client_notes(self, search_term: str, client_id: str = None) -> List[ClientNote]:
        """
        Search client notes

        Args:
            search_term: Search term
            client_id: Optional client ID filter

        Returns:
            List[ClientNote]: Matching notes
        """
        try:
            return self.note_repo.search_notes(search_term, client_id)
        except Exception as e:
            logger.error(f"Error searching client notes: {e}")
            return []

    # ==================== Statistics and Analytics ====================

    def get_client_statistics(self) -> Dict[str, Any]:
        """
        Get client statistics and analytics

        Returns:
            dict: Client statistics
        """
        try:
            if self.client_repo is None:
                logger.warning("Client repository not initialized")
                return {}
            return self.client_repo.get_client_statistics()
        except Exception as e:
            logger.error(f"Error getting client statistics: {e}")
            return {}

    def get_age_demographics(self) -> Dict[str, int]:
        """
        Get age demographics of clients

        Returns:
            dict: Age group counts
        """
        try:
            clients = self.get_all_clients()
            age_groups = {
                "Under 18": 0,
                "18-25": 0,
                "26-35": 0,
                "36-45": 0,
                "46-55": 0,
                "56-65": 0,
                "Over 65": 0,
                "Unknown": 0
            }

            for client in clients:
                age = client.calculated_age
                if age is None:
                    age_groups["Unknown"] += 1
                elif age < 18:
                    age_groups["Under 18"] += 1
                elif age <= 25:
                    age_groups["18-25"] += 1
                elif age <= 35:
                    age_groups["26-35"] += 1
                elif age <= 45:
                    age_groups["36-45"] += 1
                elif age <= 55:
                    age_groups["46-55"] += 1
                elif age <= 65:
                    age_groups["56-65"] += 1
                else:
                    age_groups["Over 65"] += 1

            return age_groups

        except Exception as e:
            logger.error(f"Error getting age demographics: {e}")
            return {}

    def get_gender_distribution(self) -> Dict[str, int]:
        """
        Get gender distribution of clients

        Returns:
            dict: Gender counts
        """
        try:
            clients = self.get_all_clients()
            gender_counts = {"Male": 0, "Female": 0, "Other": 0, "Not Specified": 0}

            for client in clients:
                gender = client.gender or "Not Specified"
                if gender in gender_counts:
                    gender_counts[gender] += 1
                else:
                    gender_counts["Other"] += 1

            return gender_counts

        except Exception as e:
            logger.error(f"Error getting gender distribution: {e}")
            return {}

    # ==================== Data Export/Import ====================

    def export_client_data(self, client_ids: List[str] = None,
                          include_notes: bool = True) -> List[Dict[str, Any]]:
        """
        Export client data for backup or transfer

        Args:
            client_ids: Optional list of specific client IDs to export
            include_notes: Whether to include client notes

        Returns:
            List[dict]: Exported client data
        """
        try:
            if client_ids:
                clients = [self.get_client_by_id(cid) for cid in client_ids]
                clients = [c for c in clients if c is not None]
            else:
                clients = self.get_all_clients(include_inactive=True)

            exported_data = []

            for client in clients:
                client_data = client.to_dict()

                if include_notes:
                    notes = self.get_client_notes(client.id)
                    client_data['notes'] = [
                        {
                            'content': note.content,
                            'note_type': note.note_type,
                            'created_at': note.created_at.isoformat(),
                            'tags': note.get_tags_list()
                        }
                        for note in notes
                    ]

                exported_data.append(client_data)

            self.emit_success("Export Complete", f"Exported data for {len(exported_data)} clients")
            return exported_data

        except Exception as e:
            logger.error(f"Error exporting client data: {e}")
            self.emit_error("Export Failed", f"Failed to export client data: {str(e)}")
            return []

    def validate_import_data(self, import_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate data before import

        Args:
            import_data: Data to validate

        Returns:
            dict: Validation results
        """
        try:
            valid_records = []
            invalid_records = []
            errors = []

            for i, record in enumerate(import_data):
                try:
                    validation_result = self.client_validator.validate_client_data(record)
                    if validation_result['is_valid']:
                        valid_records.append(record)
                    else:
                        invalid_records.append({
                            'record_index': i,
                            'record': record,
                            'errors': validation_result['errors']
                        })
                except Exception as e:
                    errors.append(f"Record {i}: {str(e)}")

            return {
                'total_records': len(import_data),
                'valid_records': len(valid_records),
                'invalid_records': len(invalid_records),
                'validation_errors': errors,
                'valid_data': valid_records,
                'invalid_data': invalid_records
            }

        except Exception as e:
            logger.error(f"Error validating import data: {e}")
            return {
                'total_records': 0,
                'valid_records': 0,
                'invalid_records': 0,
                'validation_errors': [str(e)],
                'valid_data': [],
                'invalid_data': []
            }

    # ==================== Utility Methods ====================

    def generate_unique_pharmacy_id(self) -> str:
        """
        Generate a unique pharmacy ID for a new client

        Returns:
            str: Unique pharmacy ID
        """
        try:
            return self.client_repo.generate_pharmacy_id()
        except Exception as e:
            logger.error(f"Error generating pharmacy ID: {e}")
            return f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def refresh_client_data(self) -> None:
        """Refresh all client data and emit update signals"""
        try:
            self.emit_data_changed("clients_refreshed", {})
            self.emit_status("Client data refreshed")
        except Exception as e:
            logger.error(f"Error refreshing client data: {e}")

    def cleanup(self) -> None:
        """Clean up controller resources"""
        try:
            super().cleanup()
            # Additional cleanup specific to ClientController
            self.client_repo = None
            self.note_repo = None
            self.diet_repo = None
            logger.info("ClientController cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during ClientController cleanup: {e}")
