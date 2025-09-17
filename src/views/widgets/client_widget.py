"""
Client Management Widget Module

This module provides the ClientWidget class for managing client information,
including demographics, medical history, BMI calculations, and follow-up tracking.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QDateEdit, QGroupBox,
    QTabWidget, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QProgressBar
)
from PyQt6.QtCore import (
    pyqtSignal, QDate, Qt, QTimer,
    QThread, QObject
)
from PyQt6.QtGui import QPixmap, QFont

from .base_widget import BaseWidget
from controllers.client import ClientController
from utils.validation import ClientValidation
from models.client import Client, Gender, BloodType, ActivityLevel


class ClientWidget(BaseWidget):
    """
    Widget for managing client information and operations.

    Features:
    - Client information form (demographics, medical data)
    - BMI calculation and health metrics
    - Medical history tracking
    - Follow-up scheduling
    - Client search and filtering
    - Data export capabilities
    """

    # Signals
    client_selected = pyqtSignal(int)  # client_id
    client_saved = pyqtSignal(dict)    # client_data
    client_deleted = pyqtSignal(int)   # client_id
    bmi_calculated = pyqtSignal(float, str)  # bmi_value, category

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Controllers and validation
        self.client_controller = ClientController()
        self.client_controller.initialize()
        self.client_validation = ClientValidation

        # Current client
        self.current_client: Optional[Client] = None
        self._is_editing = False

        # UI components
        self.tab_widget = None
        self.client_form = None
        self.medical_form = None
        self.history_table = None
        self.search_widget = None

        # Form fields
        self.form_fields = {}

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the main user interface."""
        # Use inherited layout from BaseWidget
        main_layout = self.layout()
        if main_layout is None:
            main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header with search and actions
        header_layout = self._create_header()
        main_layout.addLayout(header_layout)

        # Tab widget for different views
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Client Information Tab
        self._create_client_info_tab()

        # Medical History Tab
        self._create_medical_history_tab()

        # Follow-up Tab
        self._create_followup_tab()

        # Statistics Tab
        self._create_statistics_tab()

    def _create_header(self) -> QHBoxLayout:
        """Create the header with search and action buttons."""
        layout = QHBoxLayout()

        # Search section
        search_label = QLabel("البحث عن العميل:" if self._is_rtl else "Search Client:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "اسم العميل، رقم الهاتف، أو المعرف" if self._is_rtl
            else "Client name, phone, or ID"
        )
        self.search_edit.textChanged.connect(self._on_search_changed)

        # Action buttons
        self.new_client_btn = QPushButton("عميل جديد" if self._is_rtl else "New Client")
        self.new_client_btn.clicked.connect(self._new_client)

        self.save_btn = QPushButton("حفظ" if self._is_rtl else "Save")
        self.save_btn.clicked.connect(self._save_client)
        self.save_btn.setEnabled(False)

        self.delete_btn = QPushButton("حذف" if self._is_rtl else "Delete")
        self.delete_btn.clicked.connect(self._delete_client)
        self.delete_btn.setEnabled(False)

        self.export_btn = QPushButton("تصدير" if self._is_rtl else "Export")
        self.export_btn.clicked.connect(self._export_client_data)

        # Layout
        layout.addWidget(search_label)
        layout.addWidget(self.search_edit, 1)
        layout.addStretch()
        layout.addWidget(self.new_client_btn)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.delete_btn)
        layout.addWidget(self.export_btn)

        return layout

    def _create_client_info_tab(self):
        """Create the main client information tab."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)

        # Personal Information Group
        personal_group = self._create_personal_info_group()
        layout.addWidget(personal_group)

        # Contact Information Group
        contact_group = self._create_contact_info_group()
        layout.addWidget(contact_group)

        # Medical Information Group
        medical_group = self._create_medical_info_group()
        layout.addWidget(medical_group)

        # BMI Calculation Group
        bmi_group = self._create_bmi_group()
        layout.addWidget(bmi_group)

        layout.addStretch()

        scroll_area.setWidget(main_widget)
        self.tab_widget.addTab(scroll_area, "معلومات العميل" if self._is_rtl else "Client Info")

    def _create_personal_info_group(self) -> QGroupBox:
        """Create personal information form group."""
        group = QGroupBox("المعلومات الشخصية" if self._is_rtl else "Personal Information")
        layout = QGridLayout(group)

        # Name fields
        layout.addWidget(QLabel("الاسم الأول:" if self._is_rtl else "First Name:"), 0, 0)
        self.first_name_edit = QLineEdit()
        layout.addWidget(self.first_name_edit, 0, 1)
        self.add_field_widget("first_name", self.first_name_edit)

        layout.addWidget(QLabel("اسم العائلة:" if self._is_rtl else "Last Name:"), 0, 2)
        self.last_name_edit = QLineEdit()
        layout.addWidget(self.last_name_edit, 0, 3)
        self.add_field_widget("last_name", self.last_name_edit)

        # Date of birth
        layout.addWidget(QLabel("تاريخ الميلاد:" if self._is_rtl else "Date of Birth:"), 1, 0)
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDate(QDate.currentDate().addYears(-25))
        layout.addWidget(self.birth_date_edit, 1, 1)

        # Gender
        layout.addWidget(QLabel("الجنس:" if self._is_rtl else "Gender:"), 1, 2)
        self.gender_combo = QComboBox()
        self.gender_combo.addItems([
            "ذكر" if self._is_rtl else "Male",
            "أنثى" if self._is_rtl else "Female"
        ])
        layout.addWidget(self.gender_combo, 1, 3)
        self.add_field_widget("gender", self.gender_combo)

        # ID Number
        layout.addWidget(QLabel("رقم الهوية:" if self._is_rtl else "ID Number:"), 2, 0)
        self.id_number_edit = QLineEdit()
        layout.addWidget(self.id_number_edit, 2, 1)
        self.add_field_widget("id_number", self.id_number_edit)

        # Occupation
        layout.addWidget(QLabel("المهنة:" if self._is_rtl else "Occupation:"), 2, 2)
        self.occupation_edit = QLineEdit()
        layout.addWidget(self.occupation_edit, 2, 3)
        self.add_field_widget("occupation", self.occupation_edit)

        return group

    def _create_contact_info_group(self) -> QGroupBox:
        """Create contact information form group."""
        group = QGroupBox("معلومات الاتصال" if self._is_rtl else "Contact Information")
        layout = QGridLayout(group)

        # Phone
        layout.addWidget(QLabel("رقم الهاتف:" if self._is_rtl else "Phone:"), 0, 0)
        self.phone_edit = QLineEdit()
        layout.addWidget(self.phone_edit, 0, 1)
        self.add_field_widget("phone", self.phone_edit)

        # Email
        layout.addWidget(QLabel("البريد الإلكتروني:" if self._is_rtl else "Email:"), 0, 2)
        self.email_edit = QLineEdit()
        layout.addWidget(self.email_edit, 0, 3)
        self.add_field_widget("email", self.email_edit)

        # Address
        layout.addWidget(QLabel("العنوان:" if self._is_rtl else "Address:"), 1, 0)
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        layout.addWidget(self.address_edit, 1, 1, 1, 3)
        self.add_field_widget("address", self.address_edit)

        return group

    def _create_medical_info_group(self) -> QGroupBox:
        """Create medical information form group."""
        group = QGroupBox("المعلومات الطبية" if self._is_rtl else "Medical Information")
        layout = QGridLayout(group)

        # Blood Type
        layout.addWidget(QLabel("فصيلة الدم:" if self._is_rtl else "Blood Type:"), 0, 0)
        self.blood_type_combo = QComboBox()
        blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        self.blood_type_combo.addItems(blood_types)
        layout.addWidget(self.blood_type_combo, 0, 1)
        self.add_field_widget("blood_type", self.blood_type_combo)

        # Activity Level
        layout.addWidget(QLabel("مستوى النشاط:" if self._is_rtl else "Activity Level:"), 0, 2)
        self.activity_combo = QComboBox()
        activities = [
            "مستقر" if self._is_rtl else "Sedentary",
            "نشاط خفيف" if self._is_rtl else "Light",
            "نشاط متوسط" if self._is_rtl else "Moderate",
            "نشاط عالي" if self._is_rtl else "High",
            "نشاط مكثف" if self._is_rtl else "Very High"
        ]
        self.activity_combo.addItems(activities)
        layout.addWidget(self.activity_combo, 0, 3)
        self.add_field_widget("activity_level", self.activity_combo)

        # Medical Conditions
        layout.addWidget(QLabel("الحالات الطبية:" if self._is_rtl else "Medical Conditions:"), 1, 0)
        self.medical_conditions_edit = QTextEdit()
        self.medical_conditions_edit.setMaximumHeight(60)
        layout.addWidget(self.medical_conditions_edit, 1, 1, 1, 3)
        self.add_field_widget("medical_conditions", self.medical_conditions_edit)

        # Medications
        layout.addWidget(QLabel("الأدوية:" if self._is_rtl else "Medications:"), 2, 0)
        self.medications_edit = QTextEdit()
        self.medications_edit.setMaximumHeight(60)
        layout.addWidget(self.medications_edit, 2, 1, 1, 3)
        self.add_field_widget("medications", self.medications_edit)

        # Allergies
        layout.addWidget(QLabel("الحساسية:" if self._is_rtl else "Allergies:"), 3, 0)
        self.allergies_edit = QTextEdit()
        self.allergies_edit.setMaximumHeight(60)
        layout.addWidget(self.allergies_edit, 3, 1, 1, 3)
        self.add_field_widget("allergies", self.allergies_edit)

        return group

    def _create_bmi_group(self) -> QGroupBox:
        """Create BMI calculation group."""
        group = QGroupBox("حساب مؤشر كتلة الجسم" if self._is_rtl else "BMI Calculation")
        layout = QGridLayout(group)

        # Height
        layout.addWidget(QLabel("الطول (سم):" if self._is_rtl else "Height (cm):"), 0, 0)
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(50.0, 250.0)
        self.height_spin.setSuffix(" cm")
        self.height_spin.setValue(170.0)
        layout.addWidget(self.height_spin, 0, 1)
        self.add_field_widget("height", self.height_spin)

        # Weight
        layout.addWidget(QLabel("الوزن (كغ):" if self._is_rtl else "Weight (kg):"), 0, 2)
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(20.0, 300.0)
        self.weight_spin.setSuffix(" kg")
        self.weight_spin.setValue(70.0)
        layout.addWidget(self.weight_spin, 0, 3)
        self.add_field_widget("weight", self.weight_spin)

        # Calculate button
        self.calculate_bmi_btn = QPushButton("احسب مؤشر كتلة الجسم" if self._is_rtl else "Calculate BMI")
        self.calculate_bmi_btn.clicked.connect(self._calculate_bmi)
        layout.addWidget(self.calculate_bmi_btn, 1, 0, 1, 2)

        # BMI Result
        self.bmi_result_label = QLabel("مؤشر كتلة الجسم:" if self._is_rtl else "BMI:")
        layout.addWidget(self.bmi_result_label, 1, 2, 1, 2)

        # Auto-calculate when values change
        self.height_spin.valueChanged.connect(self._auto_calculate_bmi)
        self.weight_spin.valueChanged.connect(self._auto_calculate_bmi)

        return group

    def _create_medical_history_tab(self):
        """Create medical history tracking tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("السجل الطبي" if self._is_rtl else "Medical History"))
        header_layout.addStretch()

        add_record_btn = QPushButton("إضافة سجل" if self._is_rtl else "Add Record")
        add_record_btn.clicked.connect(self._add_medical_record)
        header_layout.addWidget(add_record_btn)

        layout.addLayout(header_layout)

        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        headers = ["التاريخ", "النوع", "الوصف", "الملاحظات"] if self._is_rtl else ["Date", "Type", "Description", "Notes"]
        self.history_table.setHorizontalHeaderLabels(headers)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.history_table)

        self.tab_widget.addTab(widget, "السجل الطبي" if self._is_rtl else "Medical History")

    def _create_followup_tab(self):
        """Create follow-up scheduling tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Follow-up form
        form_group = QGroupBox("جدولة المتابعة" if self._is_rtl else "Schedule Follow-up")
        form_layout = QGridLayout(form_group)

        # Date
        form_layout.addWidget(QLabel("تاريخ المتابعة:" if self._is_rtl else "Follow-up Date:"), 0, 0)
        self.followup_date_edit = QDateEdit()
        self.followup_date_edit.setCalendarPopup(True)
        self.followup_date_edit.setDate(QDate.currentDate().addDays(7))
        form_layout.addWidget(self.followup_date_edit, 0, 1)

        # Type
        form_layout.addWidget(QLabel("نوع المتابعة:" if self._is_rtl else "Follow-up Type:"), 0, 2)
        self.followup_type_combo = QComboBox()
        followup_types = [
            "استشارة غذائية" if self._is_rtl else "Nutrition Consultation",
            "فحص طبي" if self._is_rtl else "Medical Checkup",
            "متابعة الوزن" if self._is_rtl else "Weight Follow-up",
            "مراجعة الأدوية" if self._is_rtl else "Medication Review"
        ]
        self.followup_type_combo.addItems(followup_types)
        form_layout.addWidget(self.followup_type_combo, 0, 3)

        # Notes
        form_layout.addWidget(QLabel("ملاحظات:" if self._is_rtl else "Notes:"), 1, 0)
        self.followup_notes_edit = QTextEdit()
        self.followup_notes_edit.setMaximumHeight(60)
        form_layout.addWidget(self.followup_notes_edit, 1, 1, 1, 3)

        # Schedule button
        schedule_btn = QPushButton("جدولة المتابعة" if self._is_rtl else "Schedule Follow-up")
        schedule_btn.clicked.connect(self._schedule_followup)
        form_layout.addWidget(schedule_btn, 2, 0, 1, 4)

        layout.addWidget(form_group)

        # Upcoming follow-ups table
        upcoming_group = QGroupBox("المتابعات القادمة" if self._is_rtl else "Upcoming Follow-ups")
        upcoming_layout = QVBoxLayout(upcoming_group)

        self.followup_table = QTableWidget()
        self.followup_table.setColumnCount(4)
        headers = ["التاريخ", "النوع", "الحالة", "الملاحظات"] if self._is_rtl else ["Date", "Type", "Status", "Notes"]
        self.followup_table.setHorizontalHeaderLabels(headers)
        self.followup_table.horizontalHeader().setStretchLastSection(True)
        upcoming_layout.addWidget(self.followup_table)

        layout.addWidget(upcoming_group)

        self.tab_widget.addTab(widget, "المتابعة" if self._is_rtl else "Follow-up")

    def _create_statistics_tab(self):
        """Create client statistics and analytics tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Statistics cards
        stats_layout = QGridLayout()

        # BMI History Card
        bmi_card = self._create_stat_card("تاريخ مؤشر كتلة الجسم" if self._is_rtl else "BMI History", "0.0")
        stats_layout.addWidget(bmi_card, 0, 0)

        # Weight Progress Card
        weight_card = self._create_stat_card("تقدم الوزن" if self._is_rtl else "Weight Progress", "0 kg")
        stats_layout.addWidget(weight_card, 0, 1)

        # Visit Count Card
        visit_card = self._create_stat_card("عدد الزيارات" if self._is_rtl else "Visit Count", "0")
        stats_layout.addWidget(visit_card, 0, 2)

        # Last Visit Card
        last_visit_card = self._create_stat_card("آخر زيارة" if self._is_rtl else "Last Visit", "N/A")
        stats_layout.addWidget(last_visit_card, 0, 3)

        layout.addLayout(stats_layout)

        # Charts placeholder
        charts_group = QGroupBox("الرسوم البيانية" if self._is_rtl else "Charts")
        charts_layout = QVBoxLayout(charts_group)
        charts_layout.addWidget(QLabel("قريباً - رسوم بيانية تفاعلية" if self._is_rtl else "Coming Soon - Interactive Charts"))
        layout.addWidget(charts_group)

        layout.addStretch()

        self.tab_widget.addTab(widget, "الإحصائيات" if self._is_rtl else "Statistics")

    def _create_stat_card(self, title: str, value: str) -> QGroupBox:
        """Create a statistics card widget."""
        card = QGroupBox(title)
        layout = QVBoxLayout(card)

        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = value_label.font()
        font.setPointSize(16)
        font.setBold(True)
        value_label.setFont(font)

        layout.addWidget(value_label)
        return card

    def _connect_signals(self):
        """Connect widget signals to handlers."""
        # Field change signals
        self.data_changed.connect(self._on_data_changed)

        # Validation signals
        self.validation_error.connect(self._on_validation_error)

    def _on_search_changed(self, text: str):
        """Handle search text changes."""
        # TODO: Implement client search
        pass

    def _new_client(self):
        """Create a new client."""
        self.current_client = None
        self._is_editing = True
        self.clear_all_fields()
        self.clear_all_errors()
        self.save_btn.setEnabled(True)
        self.delete_btn.setEnabled(False)

    def _save_client(self):
        """Save the current client."""
        if not self.validate_all_fields():
            self.show_error("يرجى تصحيح الأخطاء قبل الحفظ" if self._is_rtl else "Please fix errors before saving")
            return

        try:
            client_data = self._get_client_data()

            if self.current_client:
                # Update existing client
                client = self.client_controller.update_client(self.current_client.id, client_data)
            else:
                # Create new client
                client = self.client_controller.create_client(client_data)

            self.current_client = client
            self._is_editing = False
            self.save_btn.setEnabled(False)
            self.delete_btn.setEnabled(True)

            self.client_saved.emit(client_data)
            self.show_information("تم حفظ بيانات العميل بنجاح" if self._is_rtl else "Client data saved successfully")

        except Exception as e:
            self.show_error(f"خطأ في حفظ البيانات: {str(e)}" if self._is_rtl else f"Error saving data: {str(e)}")

    def _delete_client(self):
        """Delete the current client."""
        if not self.current_client:
            return

        reply = self.ask_question(
            "تأكيد الحذف" if self._is_rtl else "Confirm Delete",
            "هل أنت متأكد من حذف هذا العميل؟" if self._is_rtl else "Are you sure you want to delete this client?"
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.client_controller.delete_client(self.current_client.id)
                self.client_deleted.emit(self.current_client.id)
                self._new_client()
                self.show_information("تم حذف العميل بنجاح" if self._is_rtl else "Client deleted successfully")
            except Exception as e:
                self.show_error(f"خطأ في حذف العميل: {str(e)}" if self._is_rtl else f"Error deleting client: {str(e)}")

    def _export_client_data(self):
        """Export client data."""
        # TODO: Implement data export
        pass

    def _calculate_bmi(self):
        """Calculate and display BMI."""
        height = self.height_spin.value() / 100  # Convert to meters
        weight = self.weight_spin.value()

        if height > 0 and weight > 0:
            bmi = self.client_controller.calculate_bmi(weight, height)
            category = self.client_controller.get_bmi_category(bmi)

            result_text = f"BMI: {bmi:.1f} ({category})"
            self.bmi_result_label.setText(result_text)

            self.bmi_calculated.emit(bmi, category)

    def _auto_calculate_bmi(self):
        """Auto-calculate BMI when height or weight changes."""
        # Use a timer to avoid excessive calculations
        if not hasattr(self, '_bmi_timer'):
            self._bmi_timer = QTimer()
            self._bmi_timer.setSingleShot(True)
            self._bmi_timer.timeout.connect(self._calculate_bmi)

        self._bmi_timer.start(500)  # 500ms delay

    def _add_medical_record(self):
        """Add a new medical record."""
        # TODO: Implement medical record dialog
        pass

    def _schedule_followup(self):
        """Schedule a follow-up appointment."""
        if not self.current_client:
            self.show_warning("يرجى تحديد عميل أولاً" if self._is_rtl else "Please select a client first")
            return

        # TODO: Implement follow-up scheduling
        pass

    def _get_client_data(self) -> Dict[str, Any]:
        """Get client data from form fields."""
        return {
            'first_name': self.first_name_edit.text(),
            'last_name': self.last_name_edit.text(),
            'birth_date': self.birth_date_edit.date().toPython(),
            'gender': Gender.MALE if self.gender_combo.currentIndex() == 0 else Gender.FEMALE,
            'id_number': self.id_number_edit.text(),
            'phone': self.phone_edit.text(),
            'email': self.email_edit.text(),
            'address': self.address_edit.toPlainText(),
            'occupation': self.occupation_edit.text(),
            'blood_type': self.blood_type_combo.currentText(),
            'activity_level': self._get_activity_level(),
            'height': self.height_spin.value(),
            'weight': self.weight_spin.value(),
            'medical_conditions': self.medical_conditions_edit.toPlainText(),
            'medications': self.medications_edit.toPlainText(),
            'allergies': self.allergies_edit.toPlainText()
        }

    def _get_activity_level(self) -> ActivityLevel:
        """Convert activity combo selection to ActivityLevel enum."""
        index = self.activity_combo.currentIndex()
        levels = [
            ActivityLevel.SEDENTARY,
            ActivityLevel.LIGHT,
            ActivityLevel.MODERATE,
            ActivityLevel.HIGH,
            ActivityLevel.VERY_HIGH
        ]
        return levels[index] if index < len(levels) else ActivityLevel.SEDENTARY

    def _set_client_data(self, client: Client):
        """Set form fields from client data."""
        self.first_name_edit.setText(client.first_name)
        self.last_name_edit.setText(client.last_name)
        self.birth_date_edit.setDate(QDate.fromString(client.birth_date.isoformat(), Qt.DateFormat.ISODate))
        self.gender_combo.setCurrentIndex(0 if client.gender == Gender.MALE else 1)
        self.id_number_edit.setText(client.id_number or "")
        self.phone_edit.setText(client.phone or "")
        self.email_edit.setText(client.email or "")
        self.address_edit.setPlainText(client.address or "")
        self.occupation_edit.setText(client.occupation or "")

        # Set blood type
        blood_type_index = self.blood_type_combo.findText(client.blood_type or "")
        if blood_type_index >= 0:
            self.blood_type_combo.setCurrentIndex(blood_type_index)

        # Set activity level
        activity_index = self._get_activity_index(client.activity_level)
        self.activity_combo.setCurrentIndex(activity_index)

        self.height_spin.setValue(client.height or 170.0)
        self.weight_spin.setValue(client.weight or 70.0)
        self.medical_conditions_edit.setPlainText(client.medical_conditions or "")
        self.medications_edit.setPlainText(client.medications or "")
        self.allergies_edit.setPlainText(client.allergies or "")

        # Calculate BMI
        self._calculate_bmi()

    def _get_activity_index(self, activity_level: ActivityLevel) -> int:
        """Convert ActivityLevel enum to combo box index."""
        level_map = {
            ActivityLevel.SEDENTARY: 0,
            ActivityLevel.LIGHT: 1,
            ActivityLevel.MODERATE: 2,
            ActivityLevel.HIGH: 3,
            ActivityLevel.VERY_HIGH: 4
        }
        return level_map.get(activity_level, 0)

    def _on_data_changed(self, field_name: str, value: Any):
        """Handle data changes in form fields."""
        if not self._is_editing:
            self._is_editing = True
            self.save_btn.setEnabled(True)

    def _on_validation_error(self, field_name: str, error_message: str):
        """Handle validation errors."""
        self.show_field_error(field_name, error_message)

    def validate_field(self, field_name: str) -> bool:
        """Validate a specific field."""
        value = self.get_field_value(field_name)

        try:
            if field_name == "first_name":
                self.client_validation.validate_name(value, "First name")
            elif field_name == "last_name":
                self.client_validation.validate_name(value, "Last name")
            elif field_name == "phone":
                if value:  # Phone is optional
                    self.client_validation.validate_phone(value)
            elif field_name == "email":
                if value:  # Email is optional
                    self.client_validation.validate_email(value)
            elif field_name == "id_number":
                if value:  # ID number is optional
                    self.client_validation.validate_id_number(value)

            self.clear_field_error(field_name)
            return True

        except ValueError as e:
            self.show_field_error(field_name, str(e))
            return False

    def load_client(self, client_id: int):
        """Load a specific client."""
        try:
            client = self.client_controller.get_client(client_id)
            if client:
                self.current_client = client
                self._set_client_data(client)
                self._is_editing = False
                self.save_btn.setEnabled(False)
                self.delete_btn.setEnabled(True)
                self.client_selected.emit(client_id)
            else:
                self.show_error("العميل غير موجود" if self._is_rtl else "Client not found")
        except Exception as e:
            self.show_error(f"خطأ في تحميل بيانات العميل: {str(e)}" if self._is_rtl else f"Error loading client: {str(e)}")

    def refresh_data(self):
        """Refresh the widget data."""
        if self.current_client:
            self.load_client(self.current_client.id)
