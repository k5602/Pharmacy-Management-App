"""
Diet Management Widget Module

This module provides the DietWidget class for managing diet records,
meal planning, nutrition tracking, and dietary recommendations.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QDateEdit, QGroupBox,
    QTabWidget, QScrollArea, QFrame,
    QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QProgressBar,
    QSlider, QCalendarWidget, QListWidget,
    QListWidgetItem, QSplitter
)
from PyQt6.QtCore import (
    pyqtSignal, QDate, Qt, QTimer,
    QThread, QObject
)
from PyQt6.QtGui import QPixmap, QFont, QColor

from .base_widget import BaseWidget
from controllers.diet import DietController
from utils.validation import NutritionValidation
from models.diet import DietRecord, MealType, DietGoal


class DietWidget(BaseWidget):
    """
    Widget for managing diet records and nutrition tracking.

    Features:
    - Daily meal planning and tracking
    - Nutrition calculations and analysis
    - Calorie and macronutrient monitoring
    - Weight progress tracking
    - Dietary recommendations
    - Meal history and patterns
    """

    # Signals
    diet_record_saved = pyqtSignal(dict)    # diet_data
    meal_added = pyqtSignal(str, dict)      # meal_type, meal_data
    nutrition_calculated = pyqtSignal(dict) # nutrition_summary
    weight_updated = pyqtSignal(float)      # new_weight
    goal_progress_updated = pyqtSignal(float) # progress_percentage

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Controllers and validation
        self.diet_controller = DietController()
        self.diet_controller.initialize()
        self.nutrition_validation = NutritionValidation

        # Current state
        self.current_client_id: Optional[int] = None
        self.current_date = date.today()
        self.current_diet_record: Optional[DietRecord] = None

        # UI components
        self.tab_widget = None
        self.meal_widgets = {}
        self.nutrition_display = None
        self.calendar_widget = None

        # Meal tracking data
        self.daily_meals = {
            'breakfast': [],
            'lunch': [],
            'dinner': [],
            'snacks': []
        }

        self._setup_ui()
        self._connect_signals()
        self._load_today_data()

    def _setup_ui(self):
        """Setup the main user interface."""
        # Use inherited layout from BaseWidget
        main_layout = self.layout()
        if main_layout is None:
            main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Header with date selection and actions
        header_layout = self._create_header()
        main_layout.addLayout(header_layout)

        # Tab widget for different views
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Daily Tracking Tab
        self._create_daily_tracking_tab()

        # Meal Planning Tab
        self._create_meal_planning_tab()

        # Nutrition Analysis Tab
        self._create_nutrition_analysis_tab()

        # Weight Progress Tab
        self._create_weight_progress_tab()

        # Goals & Recommendations Tab
        self._create_goals_tab()

    def _create_header(self) -> QHBoxLayout:
        """Create the header with date selection and action buttons."""
        layout = QHBoxLayout()

        # Date navigation
        prev_day_btn = QPushButton("◀")
        prev_day_btn.setMaximumWidth(30)
        prev_day_btn.clicked.connect(self._previous_day)

        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.dateChanged.connect(self._on_date_changed)

        next_day_btn = QPushButton("▶")
        next_day_btn.setMaximumWidth(30)
        next_day_btn.clicked.connect(self._next_day)

        today_btn = QPushButton("اليوم" if self._is_rtl else "Today")
        today_btn.clicked.connect(self._go_to_today)

        # Action buttons
        self.save_btn = QPushButton("حفظ" if self._is_rtl else "Save")
        self.save_btn.clicked.connect(self._save_diet_record)

        self.copy_btn = QPushButton("نسخ من يوم آخر" if self._is_rtl else "Copy from Day")
        self.copy_btn.clicked.connect(self._copy_from_day)

        self.generate_report_btn = QPushButton("تقرير غذائي" if self._is_rtl else "Nutrition Report")
        self.generate_report_btn.clicked.connect(self._generate_nutrition_report)

        # Layout
        layout.addWidget(QLabel("التاريخ:" if self._is_rtl else "Date:"))
        layout.addWidget(prev_day_btn)
        layout.addWidget(self.date_edit)
        layout.addWidget(next_day_btn)
        layout.addWidget(today_btn)
        layout.addStretch()
        layout.addWidget(self.save_btn)
        layout.addWidget(self.copy_btn)
        layout.addWidget(self.generate_report_btn)

        return layout

    def _create_daily_tracking_tab(self):
        """Create the daily meal tracking tab."""
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Meal tracking
        meal_widget = self._create_meal_tracking_widget()
        splitter.addWidget(meal_widget)

        # Right side: Nutrition summary
        nutrition_widget = self._create_nutrition_summary_widget()
        splitter.addWidget(nutrition_widget)

        splitter.setStretchFactor(0, 2)  # Meal tracking takes more space
        splitter.setStretchFactor(1, 1)

        self.tab_widget.addTab(splitter, "التتبع اليومي" if self._is_rtl else "Daily Tracking")

    def _create_meal_tracking_widget(self) -> QWidget:
        """Create the meal tracking widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Meal sections
        meal_types = [
            ('breakfast', "الإفطار" if self._is_rtl else "Breakfast"),
            ('lunch', "الغداء" if self._is_rtl else "Lunch"),
            ('dinner', "العشاء" if self._is_rtl else "Dinner"),
            ('snacks', "الوجبات الخفيفة" if self._is_rtl else "Snacks")
        ]

        for meal_id, meal_name in meal_types:
            meal_group = self._create_meal_group(meal_id, meal_name)
            layout.addWidget(meal_group)
            self.meal_widgets[meal_id] = meal_group

        layout.addStretch()
        return widget

    def _create_meal_group(self, meal_id: str, meal_name: str) -> QGroupBox:
        """Create a meal tracking group."""
        group = QGroupBox(meal_name)
        layout = QVBoxLayout(group)

        # Meal items list
        meal_list = QListWidget()
        meal_list.setMaximumHeight(120)
        layout.addWidget(meal_list)

        # Add meal controls
        controls_layout = QHBoxLayout()

        food_input = QLineEdit()
        food_input.setPlaceholderText(
            "اسم الطعام" if self._is_rtl else "Food name"
        )

        quantity_input = QDoubleSpinBox()
        quantity_input.setRange(0.1, 1000.0)
        quantity_input.setValue(100.0)
        quantity_input.setSuffix(" g")

        add_btn = QPushButton("إضافة" if self._is_rtl else "Add")
        add_btn.clicked.connect(lambda: self._add_food_item(meal_id, food_input, quantity_input, meal_list))

        controls_layout.addWidget(food_input, 1)
        controls_layout.addWidget(quantity_input)
        controls_layout.addWidget(add_btn)

        layout.addLayout(controls_layout)

        # Store references for easier access
        setattr(group, 'meal_list', meal_list)
        setattr(group, 'food_input', food_input)
        setattr(group, 'quantity_input', quantity_input)

        return group

    def _create_nutrition_summary_widget(self) -> QWidget:
        """Create the nutrition summary widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Daily targets vs actual
        targets_group = QGroupBox("الأهداف اليومية" if self._is_rtl else "Daily Targets")
        targets_layout = QVBoxLayout(targets_group)

        # Calories
        self.calories_progress = self._create_nutrition_progress("السعرات الحرارية" if self._is_rtl else "Calories", "kcal", 2000)
        targets_layout.addWidget(self.calories_progress)

        # Protein
        self.protein_progress = self._create_nutrition_progress("البروتين" if self._is_rtl else "Protein", "g", 150)
        targets_layout.addWidget(self.protein_progress)

        # Carbs
        self.carbs_progress = self._create_nutrition_progress("الكربوهيدرات" if self._is_rtl else "Carbohydrates", "g", 250)
        targets_layout.addWidget(self.carbs_progress)

        # Fats
        self.fat_progress = self._create_nutrition_progress("الدهون" if self._is_rtl else "Fats", "g", 67)
        targets_layout.addWidget(self.fat_progress)

        # Fiber
        self.fiber_progress = self._create_nutrition_progress("الألياف" if self._is_rtl else "Fiber", "g", 25)
        targets_layout.addWidget(self.fiber_progress)

        layout.addWidget(targets_group)

        # Water intake
        water_group = QGroupBox("شرب الماء" if self._is_rtl else "Water Intake")
        water_layout = QVBoxLayout(water_group)

        self.water_slider = QSlider(Qt.Orientation.Horizontal)
        self.water_slider.setRange(0, 12)  # 0-12 glasses
        self.water_slider.setValue(8)
        self.water_slider.valueChanged.connect(self._update_water_display)

        self.water_label = QLabel("8 أكواب" if self._is_rtl else "8 glasses")
        self.water_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        water_layout.addWidget(self.water_label)
        water_layout.addWidget(self.water_slider)

        layout.addWidget(water_group)

        # Meal distribution chart placeholder
        distribution_group = QGroupBox("توزيع الوجبات" if self._is_rtl else "Meal Distribution")
        distribution_layout = QVBoxLayout(distribution_group)
        distribution_layout.addWidget(QLabel("قريباً - رسم بياني" if self._is_rtl else "Coming Soon - Chart"))

        layout.addWidget(distribution_group)

        layout.addStretch()
        return widget

    def _create_nutrition_progress(self, name: str, unit: str, target: float) -> QWidget:
        """Create a nutrition progress widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header_layout = QHBoxLayout()
        name_label = QLabel(name)
        value_label = QLabel(f"0 / {target} {unit}")
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        header_layout.addWidget(value_label)

        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setRange(0, int(target))
        progress_bar.setValue(0)

        layout.addLayout(header_layout)
        layout.addWidget(progress_bar)

        # Store references
        setattr(widget, 'value_label', value_label)
        setattr(widget, 'progress_bar', progress_bar)
        setattr(widget, 'target', target)
        setattr(widget, 'unit', unit)

        return widget

    def _create_meal_planning_tab(self):
        """Create the meal planning tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Weekly calendar view
        calendar_group = QGroupBox("مخطط الوجبات الأسبوعي" if self._is_rtl else "Weekly Meal Planner")
        calendar_layout = QVBoxLayout(calendar_group)

        # Calendar widget
        self.calendar_widget = QCalendarWidget()
        self.calendar_widget.setMaximumHeight(300)
        self.calendar_widget.clicked.connect(self._on_calendar_date_clicked)
        calendar_layout.addWidget(self.calendar_widget)

        layout.addWidget(calendar_group)

        # Meal templates
        templates_group = QGroupBox("قوالب الوجبات" if self._is_rtl else "Meal Templates")
        templates_layout = QGridLayout(templates_group)

        # Template buttons
        template_names = [
            "وجبة صحية متوازنة" if self._is_rtl else "Balanced Healthy Meal",
            "وجبة قليلة الكربوهيدرات" if self._is_rtl else "Low-Carb Meal",
            "وجبة عالية البروتين" if self._is_rtl else "High-Protein Meal",
            "وجبة نباتية" if self._is_rtl else "Vegetarian Meal"
        ]

        for i, template_name in enumerate(template_names):
            btn = QPushButton(template_name)
            btn.clicked.connect(lambda checked, name=template_name: self._apply_meal_template(name))
            templates_layout.addWidget(btn, i // 2, i % 2)

        layout.addWidget(templates_group)

        # Shopping list
        shopping_group = QGroupBox("قائمة التسوق" if self._is_rtl else "Shopping List")
        shopping_layout = QVBoxLayout(shopping_group)

        self.shopping_list = QListWidget()
        shopping_layout.addWidget(self.shopping_list)

        generate_list_btn = QPushButton("إنشاء قائمة التسوق" if self._is_rtl else "Generate Shopping List")
        generate_list_btn.clicked.connect(self._generate_shopping_list)
        shopping_layout.addWidget(generate_list_btn)

        layout.addWidget(shopping_group)

        self.tab_widget.addTab(widget, "تخطيط الوجبات" if self._is_rtl else "Meal Planning")

    def _create_nutrition_analysis_tab(self):
        """Create the nutrition analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Analysis period selection
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("فترة التحليل:" if self._is_rtl else "Analysis Period:"))

        self.analysis_period_combo = QComboBox()
        periods = [
            "أسبوع واحد" if self._is_rtl else "1 Week",
            "أسبوعين" if self._is_rtl else "2 Weeks",
            "شهر واحد" if self._is_rtl else "1 Month",
            "3 أشهر" if self._is_rtl else "3 Months"
        ]
        self.analysis_period_combo.addItems(periods)
        period_layout.addWidget(self.analysis_period_combo)

        analyze_btn = QPushButton("تحليل" if self._is_rtl else "Analyze")
        analyze_btn.clicked.connect(self._analyze_nutrition)
        period_layout.addWidget(analyze_btn)

        period_layout.addStretch()
        layout.addLayout(period_layout)

        # Analysis results
        results_group = QGroupBox("نتائج التحليل" if self._is_rtl else "Analysis Results")
        results_layout = QVBoxLayout(results_group)

        # Average daily intake
        avg_group = QGroupBox("المتوسط اليومي" if self._is_rtl else "Daily Average")
        avg_layout = QGridLayout(avg_group)

        nutrients = [
            ("calories", "السعرات", "Calories", "kcal"),
            ("protein", "البروتين", "Protein", "g"),
            ("carbs", "الكربوهيدرات", "Carbohydrates", "g"),
            ("fat", "الدهون", "Fat", "g"),
            ("fiber", "الألياف", "Fiber", "g")
        ]

        self.avg_labels = {}
        for i, (key, ar_name, en_name, unit) in enumerate(nutrients):
            name = ar_name if self._is_rtl else en_name
            label = QLabel(f"{name}:")
            value_label = QLabel(f"0 {unit}")
            avg_layout.addWidget(label, i, 0)
            avg_layout.addWidget(value_label, i, 1)
            self.avg_labels[key] = value_label

        results_layout.addWidget(avg_group)

        # Trends and recommendations
        trends_group = QGroupBox("الاتجاهات والتوصيات" if self._is_rtl else "Trends & Recommendations")
        trends_layout = QVBoxLayout(trends_group)

        self.trends_text = QTextEdit()
        self.trends_text.setMaximumHeight(150)
        self.trends_text.setReadOnly(True)
        trends_layout.addWidget(self.trends_text)

        results_layout.addWidget(trends_group)

        layout.addWidget(results_group)

        layout.addStretch()

        self.tab_widget.addTab(widget, "تحليل التغذية" if self._is_rtl else "Nutrition Analysis")

    def _create_weight_progress_tab(self):
        """Create the weight progress tracking tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Weight entry
        entry_group = QGroupBox("تسجيل الوزن" if self._is_rtl else "Weight Entry")
        entry_layout = QGridLayout(entry_group)

        entry_layout.addWidget(QLabel("التاريخ:" if self._is_rtl else "Date:"), 0, 0)
        self.weight_date_edit = QDateEdit()
        self.weight_date_edit.setDate(QDate.currentDate())
        self.weight_date_edit.setCalendarPopup(True)
        entry_layout.addWidget(self.weight_date_edit, 0, 1)

        entry_layout.addWidget(QLabel("الوزن (كغ):" if self._is_rtl else "Weight (kg):"), 0, 2)
        self.weight_input = QDoubleSpinBox()
        self.weight_input.setRange(20.0, 300.0)
        self.weight_input.setSuffix(" kg")
        entry_layout.addWidget(self.weight_input, 0, 3)

        add_weight_btn = QPushButton("إضافة" if self._is_rtl else "Add")
        add_weight_btn.clicked.connect(self._add_weight_entry)
        entry_layout.addWidget(add_weight_btn, 0, 4)

        layout.addWidget(entry_group)

        # Weight history table
        history_group = QGroupBox("تاريخ الوزن" if self._is_rtl else "Weight History")
        history_layout = QVBoxLayout(history_group)

        self.weight_table = QTableWidget()
        self.weight_table.setColumnCount(4)
        headers = ["التاريخ", "الوزن", "التغيير", "ملاحظات"] if self._is_rtl else ["Date", "Weight", "Change", "Notes"]
        self.weight_table.setHorizontalHeaderLabels(headers)
        self.weight_table.horizontalHeader().setStretchLastSection(True)
        history_layout.addWidget(self.weight_table)

        layout.addWidget(history_group)

        # Progress summary
        summary_group = QGroupBox("ملخص التقدم" if self._is_rtl else "Progress Summary")
        summary_layout = QGridLayout(summary_group)

        self.start_weight_label = QLabel("0 kg")
        self.current_weight_label = QLabel("0 kg")
        self.total_change_label = QLabel("0 kg")
        self.target_weight_label = QLabel("0 kg")

        summary_layout.addWidget(QLabel("الوزن الأولي:" if self._is_rtl else "Starting Weight:"), 0, 0)
        summary_layout.addWidget(self.start_weight_label, 0, 1)
        summary_layout.addWidget(QLabel("الوزن الحالي:" if self._is_rtl else "Current Weight:"), 0, 2)
        summary_layout.addWidget(self.current_weight_label, 0, 3)

        summary_layout.addWidget(QLabel("إجمالي التغيير:" if self._is_rtl else "Total Change:"), 1, 0)
        summary_layout.addWidget(self.total_change_label, 1, 1)
        summary_layout.addWidget(QLabel("الوزن المستهدف:" if self._is_rtl else "Target Weight:"), 1, 2)
        summary_layout.addWidget(self.target_weight_label, 1, 3)

        layout.addWidget(summary_group)

        self.tab_widget.addTab(widget, "تقدم الوزن" if self._is_rtl else "Weight Progress")

    def _create_goals_tab(self):
        """Create the goals and recommendations tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Current goals
        goals_group = QGroupBox("الأهداف الحالية" if self._is_rtl else "Current Goals")
        goals_layout = QGridLayout(goals_group)

        goals_layout.addWidget(QLabel("هدف النظام الغذائي:" if self._is_rtl else "Diet Goal:"), 0, 0)
        self.goal_combo = QComboBox()
        goal_options = [
            "إنقاص الوزن" if self._is_rtl else "Weight Loss",
            "زيادة الوزن" if self._is_rtl else "Weight Gain",
            "المحافظة على الوزن" if self._is_rtl else "Weight Maintenance",
            "بناء العضلات" if self._is_rtl else "Muscle Building"
        ]
        self.goal_combo.addItems(goal_options)
        goals_layout.addWidget(self.goal_combo, 0, 1)

        goals_layout.addWidget(QLabel("السعرات المستهدفة:" if self._is_rtl else "Target Calories:"), 0, 2)
        self.target_calories_input = QSpinBox()
        self.target_calories_input.setRange(1000, 5000)
        self.target_calories_input.setValue(2000)
        self.target_calories_input.setSuffix(" kcal")
        goals_layout.addWidget(self.target_calories_input, 0, 3)

        update_goals_btn = QPushButton("تحديث الأهداف" if self._is_rtl else "Update Goals")
        update_goals_btn.clicked.connect(self._update_goals)
        goals_layout.addWidget(update_goals_btn, 1, 0, 1, 4)

        layout.addWidget(goals_group)

        # Progress tracking
        progress_group = QGroupBox("تتبع التقدم" if self._is_rtl else "Progress Tracking")
        progress_layout = QVBoxLayout(progress_group)

        self.goal_progress_bar = QProgressBar()
        self.goal_progress_bar.setRange(0, 100)
        self.goal_progress_label = QLabel("0% مكتمل" if self._is_rtl else "0% Complete")

        progress_layout.addWidget(self.goal_progress_label)
        progress_layout.addWidget(self.goal_progress_bar)

        layout.addWidget(progress_group)

        # AI Recommendations
        recommendations_group = QGroupBox("التوصيات الذكية" if self._is_rtl else "AI Recommendations")
        recommendations_layout = QVBoxLayout(recommendations_group)

        self.recommendations_text = QTextEdit()
        self.recommendations_text.setMaximumHeight(200)
        self.recommendations_text.setReadOnly(True)
        recommendations_layout.addWidget(self.recommendations_text)

        refresh_recommendations_btn = QPushButton("تحديث التوصيات" if self._is_rtl else "Refresh Recommendations")
        refresh_recommendations_btn.clicked.connect(self._generate_recommendations)
        recommendations_layout.addWidget(refresh_recommendations_btn)

        layout.addWidget(recommendations_group)

        layout.addStretch()

        self.tab_widget.addTab(widget, "الأهداف والتوصيات" if self._is_rtl else "Goals & Recommendations")

    def _connect_signals(self):
        """Connect widget signals to handlers."""
        self.data_changed.connect(self._on_data_changed)

    def _load_today_data(self):
        """Load today's diet data."""
        self._load_diet_data(self.current_date)

    def _load_diet_data(self, target_date: date):
        """Load diet data for a specific date."""
        if not self.current_client_id:
            return

        try:
            # Load diet record for the date
            diet_record = self.diet_controller.get_diet_record_by_date(
                self.current_client_id, target_date
            )

            if diet_record:
                self.current_diet_record = diet_record
                self._populate_meals_from_record(diet_record)
            else:
                self.current_diet_record = None
                self._clear_all_meals()

            self._update_nutrition_summary()

        except Exception as e:
            self.show_error(f"خطأ في تحميل البيانات: {str(e)}" if self._is_rtl else f"Error loading data: {str(e)}")

    def _populate_meals_from_record(self, diet_record: DietRecord):
        """Populate meal widgets from diet record."""
        # Clear existing meals
        self._clear_all_meals()

        # Add meals from record
        for meal in diet_record.meals:
            meal_type = meal.meal_type.value.lower()
            if meal_type in self.meal_widgets:
                meal_list = getattr(self.meal_widgets[meal_type], 'meal_list')

                for food_item in meal.food_items:
                    item_text = f"{food_item.name} - {food_item.quantity}g"
                    meal_list.addItem(QListWidgetItem(item_text))

        # Update water intake
        if hasattr(diet_record, 'water_intake'):
            self.water_slider.setValue(diet_record.water_intake or 8)

    def _clear_all_meals(self):
        """Clear all meal lists."""
        for meal_widget in self.meal_widgets.values():
            meal_list = getattr(meal_widget, 'meal_list')
            meal_list.clear()

    def _update_nutrition_summary(self):
        """Update the nutrition summary display."""
        if not self.current_client_id:
            return

        try:
            # Calculate nutrition for current date
            nutrition = self.diet_controller.calculate_daily_nutrition(
                self.current_client_id, self.current_date
            )

            # Update progress bars
            self._update_nutrition_progress(self.calories_progress, nutrition.get('calories', 0))
            self._update_nutrition_progress(self.protein_progress, nutrition.get('protein', 0))
            self._update_nutrition_progress(self.carbs_progress, nutrition.get('carbohydrates', 0))
            self._update_nutrition_progress(self.fat_progress, nutrition.get('fat', 0))
            self._update_nutrition_progress(self.fiber_progress, nutrition.get('fiber', 0))

            self.nutrition_calculated.emit(nutrition)

        except Exception as e:
            self.show_error(f"خطأ في حساب التغذية: {str(e)}" if self._is_rtl else f"Error calculating nutrition: {str(e)}")

    def _update_nutrition_progress(self, widget: QWidget, current_value: float):
        """Update a nutrition progress widget."""
        target = getattr(widget, 'target')
        unit = getattr(widget, 'unit')
        value_label = getattr(widget, 'value_label')
        progress_bar = getattr(widget, 'progress_bar')

        value_label.setText(f"{current_value:.1f} / {target} {unit}")
        progress_bar.setValue(int(current_value))

        # Color coding based on percentage
        percentage = (current_value / target) * 100
        if percentage < 50:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #ff6b6b; }")
        elif percentage < 80:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #ffa726; }")
        elif percentage <= 110:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #4caf50; }")
        else:
            progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #ff9800; }")

    def _update_water_display(self, glasses: int):
        """Update water intake display."""
        self.water_label.setText(f"{glasses} أكواب" if self._is_rtl else f"{glasses} glasses")

    def _previous_day(self):
        """Navigate to previous day."""
        current_date = self.date_edit.date().toPython()
        previous_date = current_date - timedelta(days=1)
        self.date_edit.setDate(QDate.fromString(previous_date.isoformat(), Qt.DateFormat.ISODate))

    def _next_day(self):
        """Navigate to next day."""
        current_date = self.date_edit.date().toPython()
        next_date = current_date + timedelta(days=1)
        self.date_edit.setDate(QDate.fromString(next_date.isoformat(), Qt.DateFormat.ISODate))

    def _go_to_today(self):
        """Navigate to today."""
        self.date_edit.setDate(QDate.currentDate())

    def _on_date_changed(self, date: QDate):
        """Handle date change."""
        self.current_date = date.toPython()
        self._load_diet_data(self.current_date)

    def _on_calendar_date_clicked(self, date: QDate):
        """Handle calendar date click."""
        self.date_edit.setDate(date)

    def _add_food_item(self, meal_type: str, food_input: QLineEdit, quantity_input: QDoubleSpinBox, meal_list: QListWidget):
        """Add a food item to a meal."""
        food_name = food_input.text().strip()
        if not food_name:
            self.show_warning("يرجى إدخال اسم الطعام" if self._is_rtl else "Please enter food name")
            return

        quantity = quantity_input.value()
        item_text = f"{food_name} - {quantity}g"

        meal_list.addItem(QListWidgetItem(item_text))
        food_input.clear()
        quantity_input.setValue(100.0)

        # Add to daily meals data
        if meal_type not in self.daily_meals:
            self.daily_meals[meal_type] = []

        self.daily_meals[meal_type].append({
            'name': food_name,
            'quantity': quantity
        })

        # Emit signal
        self.meal_added.emit(meal_type, {
            'name': food_name,
            'quantity': quantity
        })

        # Update nutrition summary
        self._update_nutrition_summary()

    def _save_diet_record(self):
        """Save the current diet record."""
        if not self.current_client_id:
            self.show_warning("يرجى تحديد عميل أولاً" if self._is_rtl else "Please select a client first")
            return

        try:
            # Collect all meal data
            all_meals = []
            for meal_type, meal_widget in self.meal_widgets.items():
                meal_list = getattr(meal_widget, 'meal_list')

                food_items = []
                for i in range(meal_list.count()):
                    item_text = meal_list.item(i).text()
                    # Parse item text to get name and quantity
                    parts = item_text.split(' - ')
                    if len(parts) == 2:
                        name = parts[0]
                        quantity_str = parts[1].replace('g', '')
                        try:
                            quantity = float(quantity_str)
                            food_items.append({
                                'name': name,
                                'quantity': quantity
                            })
                        except ValueError:
                            continue

                if food_items:
                    all_meals.append({
                        'meal_type': meal_type.upper(),
                        'food_items': food_items
                    })

            # Save diet record
            diet_data = {
                'client_id': self.current_client_id,
                'date': self.current_date,
                'meals': all_meals,
                'water_intake': self.water_slider.value(),
                'notes': ""
            }

            if self.current_diet_record:
                # Update existing record
                diet_record = self.diet_controller.update_diet_record(
                    self.current_diet_record.id, diet_data
                )
            else:
                # Create new record
                diet_record = self.diet_controller.create_diet_record(diet_data)

            self.current_diet_record = diet_record
            self.diet_record_saved.emit(diet_data)
            self.show_information("تم حفظ السجل الغذائي بنجاح" if self._is_rtl else "Diet record saved successfully")

        except Exception as e:
            self.show_error(f"خطأ في حفظ السجل: {str(e)}" if self._is_rtl else f"Error saving record: {str(e)}")

    def _copy_from_day(self):
        """Copy meals from another day."""
        # TODO: Implement copy from day dialog
        pass

    def _generate_nutrition_report(self):
        """Generate nutrition report."""
        if not self.current_client_id:
            self.show_warning("يرجى تحديد عميل أولاً" if self._is_rtl else "Please select a client first")
            return

        # TODO: Implement report generation
        pass

    def _apply_meal_template(self, template_name: str):
        """Apply a meal template."""
        # TODO: Implement meal templates
        pass

    def _generate_shopping_list(self):
        """Generate shopping list from meal plans."""
        # TODO: Implement shopping list generation
        pass

    def _analyze_nutrition(self):
        """Analyze nutrition for selected period."""
        if not self.current_client_id:
            self.show_warning("يرجى تحديد عميل أولاً" if self._is_rtl else "Please select a client first")
            return

        # TODO: Implement nutrition analysis
        pass

    def _add_weight_entry(self):
        """Add a weight entry."""
        if not self.current_client_id:
            self.show_warning("يرجى تحديد عميل أولاً" if self._is_rtl else "Please select a client first")
            return

        weight_date = self.weight_date_edit.date().toPython()
        weight = self.weight_input.value()

        try:
            # Add weight entry through diet controller
            self.diet_controller.add_weight_entry(
                self.current_client_id, weight_date, weight
            )

            self.weight_updated.emit(weight)
            self.show_information("تم إضافة الوزن بنجاح" if self._is_rtl else "Weight added successfully")
            self._refresh_weight_table()

        except Exception as e:
            self.show_error(f"خطأ في إضافة الوزن: {str(e)}" if self._is_rtl else f"Error adding weight: {str(e)}")

    def _refresh_weight_table(self):
        """Refresh the weight history table."""
        # TODO: Implement weight table refresh
        pass

    def _update_goals(self):
        """Update diet goals."""
        if not self.current_client_id:
            self.show_warning("يرجى تحديد عميل أولاً" if self._is_rtl else "Please select a client first")
            return

        # TODO: Implement goals update
        pass

    def _generate_recommendations(self):
        """Generate AI recommendations."""
        if not self.current_client_id:
            self.show_warning("يرجى تحديد عميل أولاً" if self._is_rtl else "Please select a client first")
            return

        try:
            recommendations = self.diet_controller.get_dietary_recommendations(
                self.current_client_id
            )

            recommendations_text = "\n".join(recommendations) if recommendations else (
                "لا توجد توصيات متاحة حالياً" if self._is_rtl else "No recommendations available"
            )

            self.recommendations_text.setPlainText(recommendations_text)

        except Exception as e:
            self.show_error(f"خطأ في إنشاء التوصيات: {str(e)}" if self._is_rtl else f"Error generating recommendations: {str(e)}")

    def _on_data_changed(self, field_name: str, value: Any):
        """Handle data changes."""
        # Auto-save or mark as modified
        pass

    def set_client(self, client_id: int):
        """Set the current client for diet tracking."""
        self.current_client_id = client_id
        self._load_diet_data(self.current_date)

    def refresh_data(self):
        """Refresh all widget data."""
        self._load_diet_data(self.current_date)
        self._refresh_weight_table()
