"""
Report Controller
Handles PDF report generation, health reports, follow-up tracking and document management
for the Pharmacy Management System
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from pathlib import Path
import json
from PyQt6.QtCore import pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QPixmap, QPainter, QFont
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from loguru import logger

from .base import BaseController
from models.client import Client, ClientRepository
from models.diet import DietRecord, MealPlan, DietRepository, MealPlanRepository
from utils.validation import ReportValidator
from utils.resource_manager import get_resource_manager


class ReportGenerationThread(QThread):
    """Thread for generating reports in the background"""

    report_progress = pyqtSignal(int, str)  # progress, status
    report_completed = pyqtSignal(str, dict)  # file_path, metadata
    report_failed = pyqtSignal(str)  # error message

    def __init__(self, report_data, output_path, report_type):
        super().__init__()
        self.report_data = report_data
        self.output_path = output_path
        self.report_type = report_type

    def run(self):
        """Run report generation in background thread"""
        try:
            self.report_progress.emit(10, "Initializing report generation...")

            if self.report_type == "client_profile":
                self._generate_client_profile_report()
            elif self.report_type == "diet_progress":
                self._generate_diet_progress_report()
            elif self.report_type == "follow_up":
                self._generate_follow_up_report()
            elif self.report_type == "nutrition_summary":
                self._generate_nutrition_summary_report()
            else:
                raise ValueError(f"Unknown report type: {self.report_type}")

            self.report_progress.emit(100, "Report generation completed")
            self.report_completed.emit(str(self.output_path), self.report_data.get('metadata', {}))

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            self.report_failed.emit(str(e))

    def _generate_client_profile_report(self):
        """Generate client profile report"""
        self.report_progress.emit(30, "Generating client profile...")
        # Implementation would go here
        self.report_progress.emit(90, "Finalizing client profile report...")

    def _generate_diet_progress_report(self):
        """Generate diet progress report"""
        self.report_progress.emit(30, "Analyzing diet progress...")
        # Implementation would go here
        self.report_progress.emit(90, "Finalizing diet progress report...")

    def _generate_follow_up_report(self):
        """Generate follow-up report"""
        self.report_progress.emit(30, "Compiling follow-up data...")
        # Implementation would go here
        self.report_progress.emit(90, "Finalizing follow-up report...")

    def _generate_nutrition_summary_report(self):
        """Generate nutrition summary report"""
        self.report_progress.emit(30, "Calculating nutrition metrics...")
        # Implementation would go here
        self.report_progress.emit(90, "Finalizing nutrition summary...")


class ReportController(BaseController):
    """Controller for report generation and document management"""

    # Specific signals for report operations
    report_generation_started = pyqtSignal(str, dict)  # report_type, metadata
    report_generation_progress = pyqtSignal(int, str)  # progress, status
    report_generated = pyqtSignal(str, str)  # report_type, file_path
    report_generation_failed = pyqtSignal(str, str)  # report_type, error
    report_printed = pyqtSignal(str)  # file_path
    report_exported = pyqtSignal(str, str)  # format, file_path

    def __init__(self, parent=None):
        super().__init__(parent)
        self.client_repo = None
        self.diet_repo = None
        self.meal_plan_repo = None
        self.report_validator = ReportValidator()
        self.resource_manager = None
        self._generation_threads = []  # Track active generation threads
        self._report_templates = {}
        self._report_history = []

    def _do_initialize(self) -> bool:
        """Initialize the report controller"""
        try:
            # Initialize repositories
            self.client_repo = ClientRepository()
            self.diet_repo = DietRepository()
            self.meal_plan_repo = MealPlanRepository()
            self.resource_manager = get_resource_manager()

            # Load report templates
            self._load_report_templates()

            # Set up reports directory
            self._setup_reports_directory()

            logger.info("ReportController initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize ReportController: {e}")
            return False

    def _load_report_templates(self) -> None:
        """Load report templates from resources"""
        try:
            templates_path = self.resource_manager.get_template_path("reports")
            if templates_path and templates_path.exists():
                for template_file in templates_path.glob("*.json"):
                    try:
                        with open(template_file, 'r', encoding='utf-8') as f:
                            template_data = json.load(f)
                            template_name = template_file.stem
                            self._report_templates[template_name] = template_data
                    except Exception as e:
                        logger.warning(f"Failed to load template {template_file}: {e}")

            # Load default templates if none found
            if not self._report_templates:
                self._create_default_templates()

        except Exception as e:
            logger.error(f"Error loading report templates: {e}")
            self._create_default_templates()

    def _create_default_templates(self) -> None:
        """Create default report templates"""
        self._report_templates = {
            "client_profile": {
                "title": "Client Profile Report",
                "sections": ["personal_info", "medical_history", "current_status", "recommendations"],
                "format": "A4",
                "orientation": "portrait"
            },
            "diet_progress": {
                "title": "Diet Progress Report",
                "sections": ["current_metrics", "weight_history", "meal_compliance", "recommendations"],
                "format": "A4",
                "orientation": "portrait"
            },
            "follow_up": {
                "title": "Follow-up Report",
                "sections": ["visit_summary", "progress_assessment", "plan_updates", "next_steps"],
                "format": "A4",
                "orientation": "portrait"
            },
            "nutrition_summary": {
                "title": "Nutrition Summary Report",
                "sections": ["nutrition_analysis", "meal_plans", "compliance_tracking", "goals"],
                "format": "A4",
                "orientation": "portrait"
            }
        }

    def _setup_reports_directory(self) -> None:
        """Set up reports directory structure"""
        try:
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)

            # Create subdirectories for different report types
            for report_type in ["client_profiles", "diet_progress", "follow_ups", "nutrition_summaries"]:
                (reports_dir / report_type).mkdir(exist_ok=True)

        except Exception as e:
            logger.error(f"Error setting up reports directory: {e}")

    # ==================== Report Generation ====================

    def generate_client_profile_report(self, client_id: str,
                                     include_sections: List[str] = None,
                                     custom_options: Dict[str, Any] = None) -> bool:
        """
        Generate a comprehensive client profile report

        Args:
            client_id: Client ID
            include_sections: Specific sections to include
            custom_options: Custom report options

        Returns:
            bool: True if generation started successfully
        """
        try:
            # Validate client exists
            client = self.client_repo.get_by_id(client_id)
            if not client:
                self.emit_error("Client Not Found", f"Client with ID {client_id} not found")
                return False

            # Prepare report data
            report_data = self._prepare_client_profile_data(client, include_sections, custom_options)

            # Validate report data
            validation_result = self.report_validator.validate_client_report_data(report_data)
            if not validation_result['is_valid']:
                error_msg = "; ".join(validation_result['errors'])
                self.emit_error("Validation Error", f"Report data validation failed: {error_msg}")
                return False

            # Generate output file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"client_profile_{client.pharmacy_id}_{timestamp}.pdf"
            output_path = Path("reports/client_profiles") / filename

            # Start background generation
            return self._start_report_generation("client_profile", report_data, output_path)

        except Exception as e:
            logger.error(f"Error generating client profile report: {e}")
            self.emit_error("Report Generation Error", f"Failed to generate client profile report: {str(e)}")
            return False

    def generate_diet_progress_report(self, client_id: str,
                                    date_range: Tuple[date, date] = None,
                                    custom_options: Dict[str, Any] = None) -> bool:
        """
        Generate a diet progress report for a client

        Args:
            client_id: Client ID
            date_range: Optional date range (start_date, end_date)
            custom_options: Custom report options

        Returns:
            bool: True if generation started successfully
        """
        try:
            # Validate client exists
            client = self.client_repo.get_by_id(client_id)
            if not client:
                self.emit_error("Client Not Found", f"Client with ID {client_id} not found")
                return False

            # Prepare report data
            report_data = self._prepare_diet_progress_data(client, date_range, custom_options)

            # Validate report data
            validation_result = self.report_validator.validate_diet_report_data(report_data)
            if not validation_result['is_valid']:
                error_msg = "; ".join(validation_result['errors'])
                self.emit_error("Validation Error", f"Report data validation failed: {error_msg}")
                return False

            # Generate output file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"diet_progress_{client.pharmacy_id}_{timestamp}.pdf"
            output_path = Path("reports/diet_progress") / filename

            # Start background generation
            return self._start_report_generation("diet_progress", report_data, output_path)

        except Exception as e:
            logger.error(f"Error generating diet progress report: {e}")
            self.emit_error("Report Generation Error", f"Failed to generate diet progress report: {str(e)}")
            return False

    def generate_follow_up_report(self, client_id: str,
                                visit_date: date = None,
                                custom_options: Dict[str, Any] = None) -> bool:
        """
        Generate a follow-up visit report

        Args:
            client_id: Client ID
            visit_date: Visit date (defaults to today)
            custom_options: Custom report options

        Returns:
            bool: True if generation started successfully
        """
        try:
            # Validate client exists
            client = self.client_repo.get_by_id(client_id)
            if not client:
                self.emit_error("Client Not Found", f"Client with ID {client_id} not found")
                return False

            if visit_date is None:
                visit_date = date.today()

            # Prepare report data
            report_data = self._prepare_follow_up_data(client, visit_date, custom_options)

            # Generate output file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"follow_up_{client.pharmacy_id}_{timestamp}.pdf"
            output_path = Path("reports/follow_ups") / filename

            # Start background generation
            return self._start_report_generation("follow_up", report_data, output_path)

        except Exception as e:
            logger.error(f"Error generating follow-up report: {e}")
            self.emit_error("Report Generation Error", f"Failed to generate follow-up report: {str(e)}")
            return False

    def generate_nutrition_summary_report(self, client_id: str,
                                        period_days: int = 30,
                                        custom_options: Dict[str, Any] = None) -> bool:
        """
        Generate a nutrition summary report

        Args:
            client_id: Client ID
            period_days: Number of days to include in summary
            custom_options: Custom report options

        Returns:
            bool: True if generation started successfully
        """
        try:
            # Validate client exists
            client = self.client_repo.get_by_id(client_id)
            if not client:
                self.emit_error("Client Not Found", f"Client with ID {client_id} not found")
                return False

            # Prepare report data
            report_data = self._prepare_nutrition_summary_data(client, period_days, custom_options)

            # Generate output file path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"nutrition_summary_{client.pharmacy_id}_{timestamp}.pdf"
            output_path = Path("reports/nutrition_summaries") / filename

            # Start background generation
            return self._start_report_generation("nutrition_summary", report_data, output_path)

        except Exception as e:
            logger.error(f"Error generating nutrition summary report: {e}")
            self.emit_error("Report Generation Error", f"Failed to generate nutrition summary report: {str(e)}")
            return False

    def _start_report_generation(self, report_type: str, report_data: Dict[str, Any],
                               output_path: Path) -> bool:
        """
        Start background report generation

        Args:
            report_type: Type of report to generate
            report_data: Report data
            output_path: Output file path

        Returns:
            bool: True if started successfully
        """
        try:
            # Create generation thread
            generation_thread = ReportGenerationThread(report_data, output_path, report_type)

            # Connect signals
            generation_thread.report_progress.connect(self.report_generation_progress.emit)
            generation_thread.report_completed.connect(self._on_report_completed)
            generation_thread.report_failed.connect(self._on_report_failed)
            generation_thread.finished.connect(lambda: self._cleanup_thread(generation_thread))

            # Track thread and start generation
            self._generation_threads.append(generation_thread)
            generation_thread.start()

            # Emit generation started signal
            metadata = {
                'client_id': report_data.get('client', {}).get('id'),
                'generation_time': datetime.now().isoformat(),
                'output_path': str(output_path)
            }
            self.report_generation_started.emit(report_type, metadata)

            self.emit_status(f"Started generating {report_type} report...")
            return True

        except Exception as e:
            logger.error(f"Error starting report generation: {e}")
            return False

    @pyqtSlot(str, dict)
    def _on_report_completed(self, file_path: str, metadata: Dict[str, Any]) -> None:
        """Handle completed report generation"""
        try:
            # Add to report history
            report_record = {
                'file_path': file_path,
                'generation_time': datetime.now().isoformat(),
                'metadata': metadata
            }
            self._report_history.append(report_record)

            # Emit success signals
            report_type = metadata.get('report_type', 'unknown')
            self.report_generated.emit(report_type, file_path)
            self.emit_success("Report Generated", f"Report saved to: {file_path}")
            self.emit_data_changed("report_generated", {
                "file_path": file_path,
                "report_type": report_type
            })

        except Exception as e:
            logger.error(f"Error handling completed report: {e}")

    @pyqtSlot(str)
    def _on_report_failed(self, error_message: str) -> None:
        """Handle failed report generation"""
        try:
            self.emit_error("Report Generation Failed", error_message)
            self.report_generation_failed.emit("unknown", error_message)
        except Exception as e:
            logger.error(f"Error handling failed report: {e}")

    def _cleanup_thread(self, thread: ReportGenerationThread) -> None:
        """Clean up completed generation thread"""
        try:
            if thread in self._generation_threads:
                self._generation_threads.remove(thread)
            thread.deleteLater()
        except Exception as e:
            logger.error(f"Error cleaning up generation thread: {e}")

    # ==================== Data Preparation Methods ====================

    def _prepare_client_profile_data(self, client: Client,
                                   include_sections: List[str] = None,
                                   custom_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Prepare data for client profile report

        Args:
            client: Client instance
            include_sections: Sections to include
            custom_options: Custom options

        Returns:
            dict: Prepared report data
        """
        try:
            # Get latest diet record
            latest_diet_record = self.diet_repo.get_latest_for_client(client.id)

            # Get BMI history
            bmi_history = client.get_bmi_history(10)

            # Get recent meal plans
            recent_meal_plans = self.meal_plan_repo.get_recent_meal_plans(client.id, 14)

            report_data = {
                'client': {
                    'id': client.id,
                    'pharmacy_id': client.pharmacy_id,
                    'full_name': client.full_display_name,
                    'age': client.calculated_age,
                    'gender': client.gender,
                    'phone': client.phone_number,
                    'email': client.email,
                    'address': client.address,
                    'registration_date': client.created_at.date() if client.created_at else None,
                    'last_visit': client.last_visit_date,
                    'next_follow_up': client.next_follow_up
                },
                'medical_info': {
                    'medical_conditions': client.medical_conditions,
                    'allergies': client.allergies,
                    'current_medications': client.current_medications,
                    'emergency_contact': client.emergency_contact
                },
                'current_status': {},
                'bmi_history': bmi_history,
                'recent_meal_plans': [plan.to_dict() for plan in recent_meal_plans],
                'template': self._report_templates.get('client_profile', {}),
                'generation_options': custom_options or {},
                'include_sections': include_sections or ['personal_info', 'medical_history', 'current_status']
            }

            # Add current status if latest diet record exists
            if latest_diet_record:
                report_data['current_status'] = {
                    'current_weight': latest_diet_record.current_weight,
                    'target_weight': latest_diet_record.target_weight,
                    'height': latest_diet_record.height,
                    'bmi': latest_diet_record.calculate_bmi(),
                    'bmi_category': latest_diet_record._get_bmi_category(),
                    'activity_level': latest_diet_record.activity_level,
                    'weight_goal': latest_diet_record.weight_goal,
                    'record_date': latest_diet_record.record_date
                }

            return report_data

        except Exception as e:
            logger.error(f"Error preparing client profile data: {e}")
            return {}

    def _prepare_diet_progress_data(self, client: Client,
                                  date_range: Tuple[date, date] = None,
                                  custom_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Prepare data for diet progress report

        Args:
            client: Client instance
            date_range: Date range for the report
            custom_options: Custom options

        Returns:
            dict: Prepared report data
        """
        try:
            if date_range is None:
                end_date = date.today()
                start_date = end_date - timedelta(days=30)
                date_range = (start_date, end_date)

            # Get diet records in date range
            diet_records = self.diet_repo.get_records_for_client(client.id)
            filtered_records = [
                record for record in diet_records
                if date_range[0] <= record.record_date <= date_range[1]
            ]

            # Get weight history
            weight_history = self.diet_repo.get_weight_history(client.id, date_range[0], date_range[1])

            # Get meal plans in date range
            meal_plans = self.meal_plan_repo.get_recent_meal_plans(client.id, (date_range[1] - date_range[0]).days)

            # Calculate progress metrics
            progress_metrics = self._calculate_progress_metrics(filtered_records, weight_history)

            report_data = {
                'client': {
                    'id': client.id,
                    'pharmacy_id': client.pharmacy_id,
                    'full_name': client.full_display_name
                },
                'date_range': {
                    'start_date': date_range[0].isoformat(),
                    'end_date': date_range[1].isoformat(),
                    'period_days': (date_range[1] - date_range[0]).days
                },
                'diet_records': [record.to_dict() for record in filtered_records],
                'weight_history': weight_history,
                'meal_plans': [plan.to_dict() for plan in meal_plans],
                'progress_metrics': progress_metrics,
                'template': self._report_templates.get('diet_progress', {}),
                'generation_options': custom_options or {}
            }

            return report_data

        except Exception as e:
            logger.error(f"Error preparing diet progress data: {e}")
            return {}

    def _prepare_follow_up_data(self, client: Client, visit_date: date,
                              custom_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Prepare data for follow-up report

        Args:
            client: Client instance
            visit_date: Visit date
            custom_options: Custom options

        Returns:
            dict: Prepared report data
        """
        try:
            # Get latest diet record
            latest_diet_record = self.diet_repo.get_latest_for_client(client.id)

            # Get recent progress
            previous_visit_date = client.last_visit_date or (visit_date - timedelta(days=30))
            progress_data = self._get_progress_since_last_visit(client.id, previous_visit_date, visit_date)

            report_data = {
                'client': {
                    'id': client.id,
                    'pharmacy_id': client.pharmacy_id,
                    'full_name': client.full_display_name
                },
                'visit_info': {
                    'visit_date': visit_date.isoformat(),
                    'previous_visit_date': previous_visit_date.isoformat() if previous_visit_date else None,
                    'days_since_last_visit': (visit_date - previous_visit_date).days if previous_visit_date else None
                },
                'current_status': latest_diet_record.to_dict() if latest_diet_record else {},
                'progress_data': progress_data,
                'recommendations': self._generate_follow_up_recommendations(client, latest_diet_record),
                'template': self._report_templates.get('follow_up', {}),
                'generation_options': custom_options or {}
            }

            return report_data

        except Exception as e:
            logger.error(f"Error preparing follow-up data: {e}")
            return {}

    def _prepare_nutrition_summary_data(self, client: Client, period_days: int,
                                      custom_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Prepare data for nutrition summary report

        Args:
            client: Client instance
            period_days: Number of days to include
            custom_options: Custom options

        Returns:
            dict: Prepared report data
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=period_days)

            # Get nutrition data
            meal_plans = self.meal_plan_repo.get_recent_meal_plans(client.id, period_days)
            diet_records = self.diet_repo.get_records_for_client(client.id)

            # Calculate nutrition metrics
            nutrition_metrics = self._calculate_nutrition_metrics(meal_plans, diet_records)

            report_data = {
                'client': {
                    'id': client.id,
                    'pharmacy_id': client.pharmacy_id,
                    'full_name': client.full_display_name
                },
                'summary_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'period_days': period_days
                },
                'meal_plans': [plan.to_dict() for plan in meal_plans],
                'nutrition_metrics': nutrition_metrics,
                'compliance_analysis': self._analyze_meal_plan_compliance(meal_plans),
                'recommendations': self._generate_nutrition_recommendations(nutrition_metrics),
                'template': self._report_templates.get('nutrition_summary', {}),
                'generation_options': custom_options or {}
            }

            return report_data

        except Exception as e:
            logger.error(f"Error preparing nutrition summary data: {e}")
            return {}

    # ==================== Analysis Helper Methods ====================

    def _calculate_progress_metrics(self, diet_records: List[DietRecord],
                                  weight_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate progress metrics from diet records and weight history"""
        try:
            if not weight_history or len(weight_history) < 2:
                return {}

            latest_weight = weight_history[0]['weight']
            initial_weight = weight_history[-1]['weight']
            weight_change = latest_weight - initial_weight

            # Calculate BMI change
            if diet_records:
                latest_record = diet_records[0]
                initial_record = diet_records[-1]
                bmi_change = latest_record.calculate_bmi() - initial_record.calculate_bmi()
            else:
                bmi_change = 0

            return {
                'weight_change': round(weight_change, 2),
                'weight_change_percentage': round((weight_change / initial_weight) * 100, 1) if initial_weight > 0 else 0,
                'bmi_change': round(bmi_change, 2),
                'total_days': len(weight_history),
                'average_weekly_change': round((weight_change / len(weight_history)) * 7, 2) if len(weight_history) > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error calculating progress metrics: {e}")
            return {}

    def _get_progress_since_last_visit(self, client_id: str, previous_date: date,
                                     current_date: date) -> Dict[str, Any]:
        """Get progress data since last visit"""
        try:
            # Get weight history between visits
            weight_history = self.diet_repo.get_weight_history(client_id, previous_date, current_date)

            # Get meal plan compliance
            meal_plans = self.meal_plan_repo.get_recent_meal_plans(client_id, (current_date - previous_date).days)

            compliance_rate = self._calculate_compliance_rate(meal_plans)

            return {
                'weight_history': weight_history,
                'meal_plan_compliance': compliance_rate,
                'total_meal_plans': len(meal_plans),
                'days_tracked': len(weight_history)
            }

        except Exception as e:
            logger.error(f"Error getting progress since last visit: {e}")
            return {}

    def _calculate_nutrition_metrics(self, meal_plans: List[MealPlan],
                                   diet_records: List[DietRecord]) -> Dict[str, Any]:
        """Calculate comprehensive nutrition metrics"""
        try:
            if not meal_plans:
                return {}

            # Calculate average water intake
            water_intakes = [plan.water_intake for plan in meal_plans if plan.water_intake > 0]
            avg_water_intake = sum(water_intakes) / len(water_intakes) if water_intakes else 0

            # Calculate meal frequency
            total_meals = sum(plan.meal_count for plan in meal_plans)
            avg_meals_per_day = total_meals / len(meal_plans) if meal_plans else 0

            # Calculate compliance rate
            compliance_rate = self._calculate_compliance_rate(meal_plans)

            return {
                'average_water_intake': round(avg_water_intake, 0),
                'average_meals_per_day': round(avg_meals_per_day, 1),
                'compliance_rate': compliance_rate,
                'total_plan_days': len(meal_plans),
                'plans_followed': sum(1 for plan in meal_plans if plan.is_followed)
            }

        except Exception as e:
            logger.error(f"Error calculating nutrition metrics: {e}")
            return {}

    def _calculate_compliance_rate(self, meal_plans: List[MealPlan]) -> float:
        """Calculate meal plan compliance rate"""
        if not meal_plans:
            return 0.0

        followed_plans = sum(1 for plan in meal_plans if plan.is_followed)
        return round((followed_plans / len(meal_plans)) * 100, 1)

    def _analyze_meal_plan_compliance(self, meal_plans: List[MealPlan]) -> Dict[str, Any]:
        """Analyze meal plan compliance patterns"""
        try:
            if not meal_plans:
                return {}

            total_plans = len(meal_plans)
            followed_plans = sum(1 for plan in meal_plans if plan.is_followed)
            compliance_rate = (followed_plans / total_plans) * 100

            # Analyze compliance by day of week (if date information available)
            weekly_compliance = {}
            for plan in meal_plans:
                if hasattr(plan, 'plan_date') and plan.plan_date:
                    day_name = plan.plan_date.strftime("%A")
                    if day_name not in weekly_compliance:
                        weekly_compliance[day_name] = {'total': 0, 'followed': 0}
                    weekly_compliance[day_name]['total'] += 1
                    if plan.is_followed:
                        weekly_compliance[day_name]['followed'] += 1

            return {
                'overall_compliance_rate': round(compliance_rate, 1),
                'total_plans': total_plans,
                'followed_plans': followed_plans,
                'weekly_patterns': weekly_compliance
            }

        except Exception as e:
            logger.error(f"Error analyzing meal plan compliance: {e}")
            return {}

    def _generate_follow_up_recommendations(self, client: Client,
                                          latest_diet_record: Optional[DietRecord]) -> List[str]:
        """Generate follow-up recommendations"""
        recommendations = []

        if latest_diet_record:
            # BMI-based recommendations
            bmi = latest_diet_record.calculate_bmi()
            if bmi < 18.5:
                recommendations.append("Focus on healthy weight gain through increased caloric intake")
            elif bmi > 25:
                recommendations.append("Continue with weight management plan and regular exercise")

            # Activity level recommendations
            if latest_diet_record.activity_level == "sedentary":
                recommendations.append("Gradually increase physical activity level")

        # Medical condition considerations
        if client.medical_conditions:
            recommendations.append("Continue monitoring medical conditions and medication adherence")

        # Default recommendations
        if not recommendations:
            recommendations = [
                "Maintain current healthy lifestyle habits",
                "Schedule regular follow-up visits",
                "Continue tracking daily meals and water intake"
            ]

        return recommendations

    def _generate_nutrition_recommendations(self, nutrition_metrics: Dict[str, Any]) -> List[str]:
        """Generate nutrition-specific recommendations"""
        recommendations = []

        if nutrition_metrics.get('compliance_rate', 0) < 80:
            recommendations.append("Improve meal plan adherence for better results")

        if nutrition_metrics.get('average_water_intake', 0) < 2000:
            recommendations.append("Increase daily water intake to at least 2 liters")

        if nutrition_metrics.get('average_meals_per_day', 0) < 3:
            recommendations.append("Ensure at least 3 balanced meals per day")

        return recommendations or ["Continue with current nutrition plan"]

    # ==================== Report Management ====================

    def get_report_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get report generation history

        Args:
            limit: Maximum number of records to return

        Returns:
            List[dict]: Report history records
        """
        try:
            return self._report_history[-limit:] if self._report_history else []
        except Exception as e:
            logger.error(f"Error getting report history: {e}")
            return []

    def delete_report(self, file_path: str) -> bool:
        """
        Delete a generated report file

        Args:
            file_path: Path to the report file

        Returns:
            bool: True if successful
        """
        try:
            report_file = Path(file_path)
            if report_file.exists():
                report_file.unlink()

                # Remove from history
                self._report_history = [
                    record for record in self._report_history
                    if record.get('file_path') != file_path
                ]

                self.emit_success("Report Deleted", f"Report file deleted: {file_path}")
                self.emit_data_changed("report_deleted", {"file_path": file_path})
                return True
            else:
                self.emit_error("File Not Found", f"Report file not found: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Error deleting report: {e}")
            self.emit_error("Deletion Error", f"Failed to delete report: {str(e)}")
            return False

    def print_report(self, file_path: str) -> bool:
        """
        Print a generated report

        Args:
            file_path: Path to the report file

        Returns:
            bool: True if printing started successfully
        """
        try:
            if not Path(file_path).exists():
                self.emit_error("File Not Found", f"Report file not found: {file_path}")
                return False

            # Create printer and show print dialog
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            print_dialog = QPrintDialog(printer)

            if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
                # TODO: Implement actual PDF printing
                self.emit_success("Print Started", f"Printing report: {file_path}")
                self.report_printed.emit(file_path)
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Error printing report: {e}")
            self.emit_error("Print Error", f"Failed to print report: {str(e)}")
            return False

    def export_report(self, file_path: str, export_format: str,
                     export_path: str = None) -> bool:
        """
        Export a report to different format

        Args:
            file_path: Source report file path
            export_format: Target format (pdf, html, txt)
            export_path: Optional custom export path

        Returns:
            bool: True if successful
        """
        try:
            if not Path(file_path).exists():
                self.emit_error("File Not Found", f"Source file not found: {file_path}")
                return False

            if export_path is None:
                source_path = Path(file_path)
                export_path = source_path.with_suffix(f".{export_format}")

            # TODO: Implement format conversion logic
            # For now, just copy the file if it's the same format
            if export_format.lower() == "pdf":
                import shutil
                shutil.copy2(file_path, export_path)

                self.emit_success("Export Complete", f"Report exported to: {export_path}")
                self.report_exported.emit(export_format, str(export_path))
                return True
            else:
                self.emit_error("Format Not Supported", f"Export format '{export_format}' not yet supported")
                return False

        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            self.emit_error("Export Error", f"Failed to export report: {str(e)}")
            return False

    # ==================== Utility Methods ====================

    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available report templates"""
        return self._report_templates.copy()

    def cancel_active_generations(self) -> None:
        """Cancel all active report generations"""
        try:
            for thread in self._generation_threads:
                if thread.isRunning():
                    thread.terminate()
                    thread.wait()

            self._generation_threads.clear()
            self.emit_status("All report generations cancelled")

        except Exception as e:
            logger.error(f"Error cancelling report generations: {e}")

    def cleanup(self) -> None:
        """Clean up controller resources"""
        try:
            # Cancel any active report generations
            self.cancel_active_generations()

            # Clean up repositories
            self.client_repo = None
            self.diet_repo = None
            self.meal_plan_repo = None
            self.resource_manager = None

            # Clear data
            self._report_templates.clear()
            self._report_history.clear()

            super().cleanup()
            logger.info("ReportController cleaned up successfully")

        except Exception as e:
            logger.error(f"Error during ReportController cleanup: {e}")
