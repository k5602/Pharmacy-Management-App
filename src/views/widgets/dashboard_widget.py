"""
Dashboard Widget Module

This module provides the DashboardWidget class that displays an overview
of the pharmacy management system with key statistics, recent activities,
and quick actions for efficient workflow management.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QGroupBox,
    QScrollArea, QListWidget, QListWidgetItem,
    QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QTextEdit
)
from PyQt6.QtCore import (
    pyqtSignal, Qt, QTimer, QThread, QObject
)
from PyQt6.QtGui import QFont, QPixmap, QIcon, QColor

from .base_widget import BaseWidget
from controllers.client import ClientController
from controllers.diet import DietController
from controllers.report import ReportController
from controllers.auth import AuthController


class DashboardWidget(BaseWidget):
    """
    Main dashboard widget providing system overview and quick actions.

    Features:
    - Key performance indicators (KPIs)
    - Recent client activities
    - Upcoming appointments and follow-ups
    - Quick action buttons
    - System notifications
    - Statistics charts
    """

    # Signals
    quick_action_triggered = pyqtSignal(str, dict)  # action_name, parameters
    client_selected = pyqtSignal(int)               # client_id
    appointment_selected = pyqtSignal(int)          # appointment_id
    notification_clicked = pyqtSignal(str, dict)    # notification_type, data

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Controllers
        self.client_controller = ClientController()
        self.diet_controller = DietController()
        self.report_controller = ReportController()
        self.auth_controller = AuthController()

        # Initialize controllers
        self.client_controller.initialize()
        self.diet_controller.initialize()
        self.report_controller.initialize()
        self.auth_controller.initialize()

        # Dashboard data
        self.dashboard_data = {}
        self.current_user = None

        # UI components
        self.kpi_widgets = {}
        self.recent_activities_list = None
        self.upcoming_appointments_list = None
        self.notifications_list = None
        self.quick_action_buttons = {}

        # Refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(300000)  # Refresh every 5 minutes

        self._setup_ui()
        self._connect_signals()
        self.refresh_data()

    def _setup_ui(self):
        """Setup the main dashboard interface."""
        # Use inherited layout from BaseWidget
        main_layout = self.layout()
        if main_layout is None:
            main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Header with welcome message
        header_layout = self._create_header()
        main_layout.addLayout(header_layout)

        # Main content area
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(content_splitter)

        # Left panel: KPIs and Quick Actions
        left_panel = self._create_left_panel()
        content_splitter.addWidget(left_panel)

        # Center panel: Recent Activities and Charts
        center_panel = self._create_center_panel()
        content_splitter.addWidget(center_panel)

        # Right panel: Appointments and Notifications
        right_panel = self._create_right_panel()
        content_splitter.addWidget(right_panel)

        # Set splitter proportions
        content_splitter.setStretchFactor(0, 1)  # Left panel
        content_splitter.setStretchFactor(1, 2)  # Center panel (larger)
        content_splitter.setStretchFactor(2, 1)  # Right panel

    def _create_header(self) -> QHBoxLayout:
        """Create the dashboard header with welcome message and user info."""
        layout = QHBoxLayout()

        # Welcome message
        welcome_label = QLabel()
        welcome_label.setObjectName("welcomeLabel")
        font = welcome_label.font()
        font.setPointSize(18)
        font.setBold(True)
        welcome_label.setFont(font)
        self._update_welcome_message(welcome_label)

        # Current date/time
        self.datetime_label = QLabel()
        self.datetime_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._update_datetime()

        # Update datetime every minute
        datetime_timer = QTimer(self)
        datetime_timer.timeout.connect(self._update_datetime)
        datetime_timer.start(60000)  # Update every minute

        layout.addWidget(welcome_label)
        layout.addStretch()
        layout.addWidget(self.datetime_label)

        return layout

    def _create_left_panel(self) -> QWidget:
        """Create the left panel with KPIs and quick actions."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # KPI Cards
        kpi_group = QGroupBox("المؤشرات الرئيسية" if self._is_rtl else "Key Performance Indicators")
        kpi_layout = QGridLayout(kpi_group)

        # Total Clients KPI
        self.kpi_widgets['total_clients'] = self._create_kpi_card(
            "إجمالي العملاء" if self._is_rtl else "Total Clients",
            "0", "#4CAF50"
        )
        kpi_layout.addWidget(self.kpi_widgets['total_clients'], 0, 0)

        # Active Clients KPI
        self.kpi_widgets['active_clients'] = self._create_kpi_card(
            "العملاء النشطون" if self._is_rtl else "Active Clients",
            "0", "#2196F3"
        )
        kpi_layout.addWidget(self.kpi_widgets['active_clients'], 0, 1)

        # This Week Appointments KPI
        self.kpi_widgets['week_appointments'] = self._create_kpi_card(
            "مواعيد هذا الأسبوع" if self._is_rtl else "This Week Appointments",
            "0", "#FF9800"
        )
        kpi_layout.addWidget(self.kpi_widgets['week_appointments'], 1, 0)

        # Reports Generated KPI
        self.kpi_widgets['reports_generated'] = self._create_kpi_card(
            "التقارير المُنشأة" if self._is_rtl else "Reports Generated",
            "0", "#9C27B0"
        )
        kpi_layout.addWidget(self.kpi_widgets['reports_generated'], 1, 1)

        layout.addWidget(kpi_group)

        # Quick Actions
        actions_group = QGroupBox("الإجراءات السريعة" if self._is_rtl else "Quick Actions")
        actions_layout = QVBoxLayout(actions_group)

        # Action buttons
        action_buttons = [
            ("new_client", "عميل جديد" if self._is_rtl else "New Client", "#4CAF50"),
            ("new_appointment", "موعد جديد" if self._is_rtl else "New Appointment", "#2196F3"),
            ("diet_plan", "خطة غذائية" if self._is_rtl else "Diet Plan", "#FF9800"),
            ("generate_report", "إنشاء تقرير" if self._is_rtl else "Generate Report", "#9C27B0"),
            ("backup_data", "نسخ احتياطي" if self._is_rtl else "Backup Data", "#795548"),
            ("user_management", "إدارة المستخدمين" if self._is_rtl else "User Management", "#607D8B")
        ]

        for action_id, action_text, color in action_buttons:
            btn = QPushButton(action_text)
            btn.setMinimumHeight(40)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background-color: {self._darken_color(color)};
                }}
                QPushButton:pressed {{
                    background-color: {self._darken_color(color, 0.8)};
                }}
            """)
            btn.clicked.connect(lambda checked, aid=action_id: self._handle_quick_action(aid))
            actions_layout.addWidget(btn)
            self.quick_action_buttons[action_id] = btn

        layout.addWidget(actions_group)
        layout.addStretch()

        return widget

    def _create_center_panel(self) -> QWidget:
        """Create the center panel with recent activities and charts."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Recent Activities
        activities_group = QGroupBox("الأنشطة الحديثة" if self._is_rtl else "Recent Activities")
        activities_layout = QVBoxLayout(activities_group)

        self.recent_activities_list = QListWidget()
        self.recent_activities_list.setMaximumHeight(200)
        self.recent_activities_list.itemDoubleClicked.connect(self._handle_activity_click)
        activities_layout.addWidget(self.recent_activities_list)

        # Refresh button
        refresh_activities_btn = QPushButton("تحديث" if self._is_rtl else "Refresh")
        refresh_activities_btn.clicked.connect(self._refresh_activities)
        activities_layout.addWidget(refresh_activities_btn)

        layout.addWidget(activities_group)

        # Statistics Charts (Placeholder)
        charts_group = QGroupBox("الإحصائيات والرسوم البيانية" if self._is_rtl else "Statistics & Charts")
        charts_layout = QVBoxLayout(charts_group)

        # Chart tabs or sections would go here
        charts_placeholder = QLabel("قريباً - رسوم بيانية تفاعلية" if self._is_rtl else "Coming Soon - Interactive Charts")
        charts_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        charts_placeholder.setMinimumHeight(250)
        charts_placeholder.setStyleSheet("""
            QLabel {
                border: 2px dashed #cccccc;
                border-radius: 10px;
                color: #888888;
                font-size: 14pt;
                font-style: italic;
            }
        """)
        charts_layout.addWidget(charts_placeholder)

        layout.addWidget(charts_group)

        # System Status
        status_group = QGroupBox("حالة النظام" if self._is_rtl else "System Status")
        status_layout = QGridLayout(status_group)

        # Database status
        status_layout.addWidget(QLabel("قاعدة البيانات:" if self._is_rtl else "Database:"), 0, 0)
        self.db_status_label = QLabel("متصل" if self._is_rtl else "Connected")
        self.db_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        status_layout.addWidget(self.db_status_label, 0, 1)

        # Last backup
        status_layout.addWidget(QLabel("آخر نسخة احتياطية:" if self._is_rtl else "Last Backup:"), 1, 0)
        self.backup_status_label = QLabel("غير محدد" if self._is_rtl else "Not specified")
        status_layout.addWidget(self.backup_status_label, 1, 1)

        # Storage usage
        status_layout.addWidget(QLabel("استخدام التخزين:" if self._is_rtl else "Storage Usage:"), 2, 0)
        self.storage_progress = QProgressBar()
        self.storage_progress.setRange(0, 100)
        self.storage_progress.setValue(35)  # Example value
        status_layout.addWidget(self.storage_progress, 2, 1)

        layout.addWidget(status_group)

        return widget

    def _create_right_panel(self) -> QWidget:
        """Create the right panel with appointments and notifications."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Upcoming Appointments
        appointments_group = QGroupBox("المواعيد القادمة" if self._is_rtl else "Upcoming Appointments")
        appointments_layout = QVBoxLayout(appointments_group)

        self.upcoming_appointments_list = QListWidget()
        self.upcoming_appointments_list.setMaximumHeight(200)
        self.upcoming_appointments_list.itemDoubleClicked.connect(self._handle_appointment_click)
        appointments_layout.addWidget(self.upcoming_appointments_list)

        # Add appointment button
        add_appointment_btn = QPushButton("إضافة موعد" if self._is_rtl else "Add Appointment")
        add_appointment_btn.clicked.connect(lambda: self._handle_quick_action("new_appointment"))
        appointments_layout.addWidget(add_appointment_btn)

        layout.addWidget(appointments_group)

        # System Notifications
        notifications_group = QGroupBox("الإشعارات" if self._is_rtl else "Notifications")
        notifications_layout = QVBoxLayout(notifications_group)

        self.notifications_list = QListWidget()
        self.notifications_list.setMaximumHeight(200)
        self.notifications_list.itemClicked.connect(self._handle_notification_click)
        notifications_layout.addWidget(self.notifications_list)

        # Clear notifications button
        clear_notifications_btn = QPushButton("مسح الإشعارات" if self._is_rtl else "Clear Notifications")
        clear_notifications_btn.clicked.connect(self._clear_notifications)
        notifications_layout.addWidget(clear_notifications_btn)

        layout.addWidget(notifications_group)

        # Today's Summary
        summary_group = QGroupBox("ملخص اليوم" if self._is_rtl else "Today's Summary")
        summary_layout = QVBoxLayout(summary_group)

        self.summary_text = QTextEdit()
        self.summary_text.setMaximumHeight(150)
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)

        layout.addWidget(summary_group)

        layout.addStretch()

        return widget

    def _create_kpi_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a KPI card widget."""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.Box)
        card.setStyleSheet(f"""
            QFrame {{
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                padding: 10px;
            }}
            QFrame:hover {{
                border: 2px solid {color};
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = title_label.font()
        font.setPointSize(9)
        title_label.setFont(font)
        title_label.setStyleSheet("color: #666666;")

        # Value
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = value_label.font()
        font.setPointSize(24)
        font.setBold(True)
        value_label.setFont(font)
        value_label.setStyleSheet(f"color: {color};")

        layout.addWidget(title_label)
        layout.addWidget(value_label)

        # Store reference to value label for updates
        setattr(card, 'value_label', value_label)
        setattr(card, 'title_label', title_label)

        return card

    def _darken_color(self, color_hex: str, factor: float = 0.9) -> str:
        """Darken a hex color by a factor."""
        color = QColor(color_hex)
        h, s, v, a = color.getHsv()
        v = int(v * factor)
        color.setHsv(h, s, v, a)
        return color.name()

    def _update_welcome_message(self, label: QLabel):
        """Update the welcome message based on current user."""
        current_hour = datetime.now().hour

        if self._is_rtl:
            if 5 <= current_hour < 12:
                greeting = "صباح الخير"
            elif 12 <= current_hour < 17:
                greeting = "مساء الخير"
            else:
                greeting = "مساء الخير"

            if self.current_user:
                message = f"{greeting}، {self.current_user.get('first_name', 'المستخدم')}"
            else:
                message = f"{greeting}"
        else:
            if 5 <= current_hour < 12:
                greeting = "Good Morning"
            elif 12 <= current_hour < 17:
                greeting = "Good Afternoon"
            else:
                greeting = "Good Evening"

            if self.current_user:
                message = f"{greeting}, {self.current_user.get('first_name', 'User')}"
            else:
                message = f"{greeting}"

        label.setText(message)

    def _update_datetime(self):
        """Update the date/time display."""
        now = datetime.now()
        if self._is_rtl:
            date_str = now.strftime("%A، %d %B %Y")
            time_str = now.strftime("%I:%M %p")
        else:
            date_str = now.strftime("%A, %B %d, %Y")
            time_str = now.strftime("%I:%M %p")

        self.datetime_label.setText(f"{date_str}\n{time_str}")

    def _connect_signals(self):
        """Connect widget signals to handlers."""
        pass

    def _handle_quick_action(self, action_id: str):
        """Handle quick action button clicks."""
        action_data = {
            'timestamp': datetime.now(),
            'user_id': self.current_user.get('id') if self.current_user else None
        }

        self.quick_action_triggered.emit(action_id, action_data)

    def _handle_activity_click(self, item: QListWidgetItem):
        """Handle recent activity item clicks."""
        # Extract activity data from item
        activity_data = item.data(Qt.ItemDataRole.UserRole)
        if activity_data and 'client_id' in activity_data:
            self.client_selected.emit(activity_data['client_id'])

    def _handle_appointment_click(self, item: QListWidgetItem):
        """Handle appointment item clicks."""
        # Extract appointment data from item
        appointment_data = item.data(Qt.ItemDataRole.UserRole)
        if appointment_data and 'appointment_id' in appointment_data:
            self.appointment_selected.emit(appointment_data['appointment_id'])

    def _handle_notification_click(self, item: QListWidgetItem):
        """Handle notification item clicks."""
        notification_data = item.data(Qt.ItemDataRole.UserRole)
        if notification_data:
            self.notification_clicked.emit(
                notification_data.get('type', 'info'),
                notification_data
            )

    def _refresh_activities(self):
        """Refresh the recent activities list."""
        try:
            self.recent_activities_list.clear()

            # Add placeholder activities for now
            activities = [
                "مرحباً بنظام إدارة الصيدلية" if self._is_rtl else "Welcome to Pharmacy Management System",
                "النظام جاهز للاستخدام" if self._is_rtl else "System ready for use",
                "يمكنك الآن إضافة العملاء" if self._is_rtl else "You can now add clients"
            ]

            for activity_text in activities:
                item = QListWidgetItem(activity_text)
                self.recent_activities_list.addItem(item)

        except Exception as e:
            print(f"Activities refresh error: {str(e)}")  # Simple error logging

    def _clear_notifications(self):
        """Clear all notifications."""
        self.notifications_list.clear()

    def refresh_data(self):
        """Refresh all dashboard data."""
        try:
            # Update KPIs
            self._update_kpis()

            # Update recent activities
            self._refresh_activities()

            # Update appointments
            self._update_appointments()

            # Update notifications
            self._update_notifications()

            # Update today's summary
            self._update_today_summary()

            # Update system status
            self._update_system_status()

        except Exception as e:
            self.show_error(f"خطأ في تحديث البيانات: {str(e)}" if self._is_rtl else f"Error refreshing data: {str(e)}")

    def _update_kpis(self):
        """Update KPI values."""
        try:
            # Get client statistics
            client_stats = self.client_controller.get_client_statistics()

            # Total clients
            total_clients = client_stats.get('total_clients', 0)
            self.kpi_widgets['total_clients'].value_label.setText(str(total_clients))

            # Active clients - use total for now
            active_clients = total_clients  # Fallback to total clients
            self.kpi_widgets['active_clients'].value_label.setText(str(active_clients))

            # This week appointments - placeholder
            week_appointments = 0  # Placeholder value
            self.kpi_widgets['week_appointments'].value_label.setText(str(week_appointments))

            # Reports generated this month - placeholder
            reports_count = 0  # Placeholder value
            self.kpi_widgets['reports_generated'].value_label.setText(str(reports_count))

        except Exception as e:
            # Set default values if statistics can't be loaded
            self.kpi_widgets['total_clients'].value_label.setText("0")
            self.kpi_widgets['active_clients'].value_label.setText("0")
            self.kpi_widgets['week_appointments'].value_label.setText("0")
            self.kpi_widgets['reports_generated'].value_label.setText("0")
            print(f"KPI update error: {str(e)}")  # Simple error logging

    def _update_appointments(self):
        """Update upcoming appointments list."""
        try:
            self.upcoming_appointments_list.clear()

            # Add placeholder text for appointments
            placeholder_text = "لا توجد مواعيد مجدولة" if self._is_rtl else "No scheduled appointments"
            item = QListWidgetItem(placeholder_text)
            self.upcoming_appointments_list.addItem(item)

        except Exception as e:
            print(f"Appointments update error: {str(e)}")  # Simple error logging

    def _update_notifications(self):
        """Update system notifications."""
        try:
            self.notifications_list.clear()

            # Add welcome notification
            welcome_text = "مرحباً! النظام جاهز للاستخدام" if self._is_rtl else "Welcome! System is ready to use"
            item = QListWidgetItem(welcome_text)
            self.notifications_list.addItem(item)

        except Exception as e:
            print(f"Notifications update error: {str(e)}")  # Simple error logging

    def _update_today_summary(self):
        """Update today's summary text."""
        try:
            today = date.today()

            # Create simple summary with placeholder data
            if self._is_rtl:
                summary = f"""ملخص اليوم - {today.strftime('%d/%m/%Y')}

عملاء جدد: 0
مواعيد: 0
سجلات غذائية: 0

الحالة: النظام يعمل بشكل طبيعي
"""
            else:
                summary = f"""Today's Summary - {today.strftime('%m/%d/%Y')}

New Clients: 0
Appointments: 0
Diet Records: 0

Status: System operating normally
"""

            self.summary_text.setPlainText(summary)

        except Exception as e:
            print(f"Summary update error: {str(e)}")  # Simple error logging

    def _update_system_status(self):
        """Update system status indicators."""
        try:
            # Simple status check - assume connected for now
            self.db_status_label.setText("متصل" if self._is_rtl else "Connected")
            self.db_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

            # Update last backup time (placeholder)
            self.backup_status_label.setText("أمس" if self._is_rtl else "Yesterday")

            # Update storage usage (placeholder - would calculate actual usage)
            self.storage_progress.setValue(35)

        except Exception as e:
            print(f"System status update error: {str(e)}")  # Simple error logging

    def set_current_user(self, user_data: Dict[str, Any]):
        """Set the current user for personalized dashboard."""
        self.current_user = user_data
        # Update welcome message
        welcome_label = self.findChild(QLabel, "welcomeLabel")
        if welcome_label:
            self._update_welcome_message(welcome_label)

    def handle_user_login(self, user_data: Dict[str, Any]):
        """Handle user login event."""
        self.set_current_user(user_data)
        self.refresh_data()

    def handle_user_logout(self):
        """Handle user logout event."""
        self.current_user = None
        # Reset dashboard to default state
        welcome_label = self.findChild(QLabel, "welcomeLabel")
        if welcome_label:
            self._update_welcome_message(welcome_label)
