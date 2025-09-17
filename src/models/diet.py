"""
Diet Model
Defines the nutrition and diet tracking data model for the Pharmacy Management System
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import Column, Integer, String, Text, Date, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Session
from sqlalchemy.ext.hybrid import hybrid_property
from enum import Enum

from .base import BaseModel, BaseRepository, get_database_manager


class WeightCategory(str, Enum):
    """Weight category enumeration"""
    CHILDREN = "صغار"
    ADULTS = "كبار"


class WeightCondition(str, Enum):
    """Weight condition enumeration"""
    OBESITY = "سمنة"
    UNDERWEIGHT = "نحافة"
    NORMAL = "طبيعي"
    LOSE_WEIGHT = "lose_weight"
    GAIN_WEIGHT = "gain_weight"
    MAINTAIN_WEIGHT = "maintain_weight"


class BMICategory(str, Enum):
    """BMI category enumeration"""
    UNDERWEIGHT = "نقص الوزن"
    NORMAL = "طبيعي"
    OVERWEIGHT = "زيادة الوزن"
    OBESE_CLASS_1 = "سمنة درجة أولى"
    OBESE_CLASS_2 = "سمنة درجة ثانية"
    OBESE_CLASS_3 = "سمنة مفرطة"


class ActivityLevel(str, Enum):
    """Physical activity level enumeration"""
    SEDENTARY = "قليل الحركة"
    LIGHT = "نشاط خفيف"
    MODERATE = "نشاط متوسط"
    ACTIVE = "نشاط عالي"
    VERY_ACTIVE = "نشاط مكثف"


class MealType(str, Enum):
    """Meal type enumeration"""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACKS = "snacks"


class DietGoal(str, Enum):
    """Diet goal enumeration"""
    WEIGHT_LOSS = "weight_loss"
    WEIGHT_GAIN = "weight_gain"
    WEIGHT_MAINTENANCE = "weight_maintenance"
    MUSCLE_BUILDING = "muscle_building"


class DietRecord(BaseModel):
    """
    Diet record model representing nutrition and body measurements
    """
    __tablename__ = "diet_records"

    # Foreign key to client
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)

    # Body measurements
    height = Column(Float, nullable=True)  # in cm
    current_weight = Column(Float, nullable=True)  # in kg
    previous_weight = Column(Float, nullable=True)  # in kg
    target_weight = Column(Float, nullable=True)  # in kg

    # Body composition
    fat_percentage = Column(Float, nullable=True)
    muscle_percentage = Column(Float, nullable=True)
    water_percentage = Column(Float, nullable=True)
    mineral_percentage = Column(Float, nullable=True)
    bone_density = Column(Float, nullable=True)

    # Calculated values
    bmi = Column(Float, nullable=True)
    bmr = Column(Float, nullable=True)  # Basal Metabolic Rate
    daily_calories = Column(Float, nullable=True)  # Recommended daily calories

    # Categories
    weight_category = Column(String(20), nullable=True)  # WeightCategory enum
    weight_condition = Column(String(20), nullable=True)  # WeightCondition enum
    bmi_category = Column(String(30), nullable=True)  # BMICategory enum
    activity_level = Column(String(20), nullable=True)  # ActivityLevel enum

    # Vital signs
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    blood_sugar = Column(Float, nullable=True)

    # Diet goals
    weight_goal = Column(String(50), nullable=True)  # "lose", "gain", "maintain"
    target_date = Column(Date, nullable=True)
    weekly_goal_kg = Column(Float, nullable=True)

    # Notes
    measurement_notes = Column(Text, nullable=True)
    progress_notes = Column(Text, nullable=True)

    # Relationships
    client = relationship("Client", back_populates="diet_records")
    meal_plans = relationship("MealPlan", back_populates="diet_record", cascade="all, delete-orphan")

    @hybrid_property
    def weight_change(self) -> Optional[float]:
        """Calculate weight change from previous measurement"""
        if self.current_weight and self.previous_weight:
            return self.current_weight - self.previous_weight
        return None

    @hybrid_property
    def weight_change_percentage(self) -> Optional[float]:
        """Calculate weight change percentage"""
        if self.current_weight and self.previous_weight and self.previous_weight > 0:
            return ((self.current_weight - self.previous_weight) / self.previous_weight) * 100
        return None

    @hybrid_property
    def progress_to_goal(self) -> Optional[float]:
        """Calculate progress towards target weight (percentage)"""
        if all([self.current_weight, self.previous_weight, self.target_weight]):
            total_change_needed = abs(self.target_weight - self.previous_weight)
            current_change = abs(self.current_weight - self.previous_weight)
            if total_change_needed > 0:
                return (current_change / total_change_needed) * 100
        return None

    @hybrid_property
    def is_healthy_bmi(self) -> bool:
        """Check if BMI is in healthy range"""
        if self.bmi:
            return 18.5 <= self.bmi < 25
        return False

    def calculate_bmi(self) -> Optional[float]:
        """Calculate BMI from height and weight"""
        if self.height and self.current_weight and self.height > 0:
            height_m = self.height / 100  # Convert cm to meters
            bmi = self.current_weight / (height_m ** 2)
            self.bmi = round(bmi, 2)
            self.bmi_category = self._get_bmi_category(self.bmi)
            return self.bmi
        return None

    def calculate_bmr(self, gender: str = 'male', age: int = 30) -> Optional[float]:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation"""
        if self.height and self.current_weight:
            if gender.lower() == 'female':
                bmr = (10 * self.current_weight) + (6.25 * self.height) - (5 * age) - 161
            else:  # male
                bmr = (10 * self.current_weight) + (6.25 * self.height) - (5 * age) + 5

            self.bmr = round(bmr, 2)
            return self.bmr
        return None

    def calculate_daily_calories(self) -> Optional[float]:
        """Calculate recommended daily calories based on BMR and activity level"""
        if not self.bmr:
            return None

        activity_multipliers = {
            ActivityLevel.SEDENTARY: 1.2,
            ActivityLevel.LIGHT: 1.375,
            ActivityLevel.MODERATE: 1.55,
            ActivityLevel.ACTIVE: 1.725,
            ActivityLevel.VERY_ACTIVE: 1.9
        }

        multiplier = activity_multipliers.get(self.activity_level, 1.4)
        self.daily_calories = round(self.bmr * multiplier, 2)
        return self.daily_calories

    def _get_bmi_category(self, bmi: float) -> str:
        """Get BMI category based on BMI value"""
        if bmi < 18.5:
            return BMICategory.UNDERWEIGHT
        elif 18.5 <= bmi < 25:
            return BMICategory.NORMAL
        elif 25 <= bmi < 30:
            return BMICategory.OVERWEIGHT
        elif 30 <= bmi < 35:
            return BMICategory.OBESE_CLASS_1
        elif 35 <= bmi < 40:
            return BMICategory.OBESE_CLASS_2
        else:
            return BMICategory.OBESE_CLASS_3

    def get_diet_recommendations(self) -> Dict[str, str]:
        """Get diet recommendations based on BMI and goals"""
        recommendations = {
            'suggestions': '',
            'advice': '',
            'foods_to_include': '',
            'foods_to_avoid': ''
        }

        if not self.bmi:
            return recommendations

        if self.bmi < 18.5:
            recommendations['suggestions'] = (
                "• زيادة السعرات الحرارية بشكل معتدل\n"
                "• تناول وجبات صغيرة متكررة\n"
                "• التركيز على البروتينات الصحية\n"
                "• تناول المكسرات والأفوكادو"
            )
            recommendations['advice'] = (
                "• من المهم زيادة الوزن بشكل صحي\n"
                "• استشر أخصائي تغذية لتخطيط نظام غذائي مناسب"
            )
            recommendations['foods_to_include'] = (
                "البروتينات: اللحوم، الأسماك، البيض، البقوليات\n"
                "الكربوهيدرات: الأرز البني، الخبز الكامل، الشوفان\n"
                "الدهون الصحية: المكسرات، الأفوكادو، زيت الزيتون"
            )

        elif 18.5 <= self.bmi < 25:
            recommendations['suggestions'] = (
                "• الحفاظ على نظام غذائي متوازن\n"
                "• تناول الفواكه والخضروات بكميات كافية\n"
                "• ممارسة الرياضة بانتظام"
            )
            recommendations['advice'] = (
                "• حافظ على وزنك الحالي من خلال اتباع نمط حياة صحي\n"
                "• متابعة الفحوصات الدورية لضمان الصحة العامة"
            )

        elif 25 <= self.bmi < 30:
            recommendations['suggestions'] = (
                "• تقليل تناول الدهون المشبعة والسكريات\n"
                "• زيادة تناول الألياف والخضروات\n"
                "• ممارسة التمارين الرياضية بانتظام"
            )
            recommendations['advice'] = (
                "• العمل على فقدان الوزن الزائد لتحسين الصحة\n"
                "• استشر أخصائي تغذية لوضع خطة غذائية مناسبة"
            )
            recommendations['foods_to_avoid'] = (
                "الأطعمة المقلية، الحلويات، المشروبات الغازية\n"
                "الوجبات السريعة، الأطعمة المصنعة"
            )

        else:  # BMI >= 30
            recommendations['suggestions'] = (
                "• اتباع نظام غذائي منخفض السعرات والدهون\n"
                "• زيادة النشاط البدني بشكل منتظم\n"
                "• تناول وجبات متوازنة تحتوي على البروتين والخضروات"
            )
            recommendations['advice'] = (
                "• من الضروري فقدان الوزن لتقليل مخاطر الأمراض المزمنة\n"
                "• استشر طبيب أو أخصائي تغذية لوضع خطة شاملة"
            )

        return recommendations

    def to_dict(self) -> Dict[str, Any]:
        """Convert diet record to dictionary with calculated fields"""
        data = super().to_dict()
        data.update({
            'weight_change': self.weight_change,
            'weight_change_percentage': self.weight_change_percentage,
            'progress_to_goal': self.progress_to_goal,
            'is_healthy_bmi': self.is_healthy_bmi,
            'diet_recommendations': self.get_diet_recommendations()
        })
        return data

    def __repr__(self) -> str:
        return f"<DietRecord(id={self.id}, client_id={self.client_id}, bmi={self.bmi})>"


class MealPlan(BaseModel):
    """
    Meal plan model representing daily meal planning
    """
    __tablename__ = "meal_plans"

    # Foreign key to diet record
    diet_record_id = Column(Integer, ForeignKey("diet_records.id"), nullable=False)

    # Meal information
    meal_date = Column(Date, nullable=False, default=date.today)
    breakfast = Column(Text, nullable=True)
    morning_snack = Column(Text, nullable=True)
    lunch = Column(Text, nullable=True)
    afternoon_snack = Column(Text, nullable=True)
    dinner = Column(Text, nullable=True)
    evening_snack = Column(Text, nullable=True)

    # Nutritional information (optional)
    total_calories = Column(Float, nullable=True)
    total_protein = Column(Float, nullable=True)
    total_carbs = Column(Float, nullable=True)
    total_fat = Column(Float, nullable=True)
    total_fiber = Column(Float, nullable=True)

    # Compliance and notes
    compliance_score = Column(Integer, nullable=True)  # 1-10 scale
    notes = Column(Text, nullable=True)
    is_followed = Column(Boolean, default=False)

    # Relationships
    diet_record = relationship("DietRecord", back_populates="meal_plans")

    @hybrid_property
    def meal_count(self) -> int:
        """Count non-empty meals"""
        meals = [self.breakfast, self.morning_snack, self.lunch,
                self.afternoon_snack, self.dinner, self.evening_snack]
        return len([meal for meal in meals if meal and meal.strip()])

    @hybrid_property
    def is_complete_plan(self) -> bool:
        """Check if meal plan has at least main meals"""
        main_meals = [self.breakfast, self.lunch, self.dinner]
        return all(meal and meal.strip() for meal in main_meals)

    def get_meals_dict(self) -> Dict[str, str]:
        """Get all meals as a dictionary"""
        return {
            'breakfast': self.breakfast or '',
            'morning_snack': self.morning_snack or '',
            'lunch': self.lunch or '',
            'afternoon_snack': self.afternoon_snack or '',
            'dinner': self.dinner or '',
            'evening_snack': self.evening_snack or ''
        }

    def update_meals(self, meals: Dict[str, str]) -> None:
        """Update meals from dictionary"""
        for meal_type, content in meals.items():
            if hasattr(self, meal_type):
                setattr(self, meal_type, content)

    def calculate_nutrition_totals(self) -> Dict[str, float]:
        """Calculate total nutrition (placeholder for future food database integration)"""
        # This would integrate with a food database in the future
        return {
            'calories': self.total_calories or 0,
            'protein': self.total_protein or 0,
            'carbs': self.total_carbs or 0,
            'fat': self.total_fat or 0,
            'fiber': self.total_fiber or 0
        }

    def __repr__(self) -> str:
        return f"<MealPlan(id={self.id}, diet_record_id={self.diet_record_id}, date={self.meal_date})>"


class DietRepository(BaseRepository):
    """
    Repository class for diet record operations
    """

    def __init__(self):
        super().__init__(get_database_manager(), DietRecord)

    def create_diet_record(self, client_id: int, **kwargs) -> Optional[DietRecord]:
        """Create a new diet record with calculations"""
        try:
            kwargs['client_id'] = client_id

            # Get previous weight if not provided
            if 'previous_weight' not in kwargs:
                latest_record = self.get_latest_for_client(client_id)
                if latest_record and latest_record.current_weight:
                    kwargs['previous_weight'] = latest_record.current_weight

            diet_record = self.create(**kwargs)

            # Calculate BMI and other metrics
            if diet_record.height and diet_record.current_weight:
                diet_record.calculate_bmi()

            # Update the record
            self.update(diet_record.id,
                       bmi=diet_record.bmi,
                       bmi_category=diet_record.bmi_category)

            return diet_record

        except Exception as e:
            raise ValueError(f"Failed to create diet record: {str(e)}")

    def get_latest_for_client(self, client_id: int) -> Optional[DietRecord]:
        """Get the latest diet record for a client"""
        with self.db_manager.get_session() as session:
            try:
                return session.query(DietRecord).filter(
                    DietRecord.client_id == client_id,
                    DietRecord.is_active == True
                ).order_by(DietRecord.created_at.desc()).first()

            except Exception as e:
                self.logger.error(f"Failed to get latest diet record: {e}")
                return None

    def get_records_for_client(self, client_id: int, limit: int = 10) -> List[DietRecord]:
        """Get diet records for a client"""
        with self.db_manager.get_session() as session:
            try:
                return session.query(DietRecord).filter(
                    DietRecord.client_id == client_id,
                    DietRecord.is_active == True
                ).order_by(DietRecord.created_at.desc()).limit(limit).all()

            except Exception as e:
                self.logger.error(f"Failed to get diet records: {e}")
                return []

    def get_weight_history(self, client_id: int) -> List[Dict[str, Any]]:
        """Get weight history for a client"""
        records = self.get_records_for_client(client_id, limit=50)
        history = []

        for record in reversed(records):  # Oldest to newest
            if record.current_weight:
                history.append({
                    'date': record.created_at.date(),
                    'weight': record.current_weight,
                    'bmi': record.bmi,
                    'weight_change': record.weight_change
                })

        return history

    def get_bmi_statistics(self) -> Dict[str, Any]:
        """Get BMI statistics across all active clients"""
        with self.db_manager.get_session() as session:
            try:
                # Get latest diet record for each client
                subquery = session.query(
                    DietRecord.client_id,
                    session.query(DietRecord.id).filter(
                        DietRecord.client_id == DietRecord.client_id,
                        DietRecord.is_active == True
                    ).order_by(DietRecord.created_at.desc()).limit(1).as_scalar().label('latest_id')
                ).subquery()

                latest_records = session.query(DietRecord).join(
                    subquery, DietRecord.id == subquery.c.latest_id
                ).filter(DietRecord.bmi.isnot(None)).all()

                if not latest_records:
                    return {}

                bmis = [record.bmi for record in latest_records]

                # Calculate statistics
                total_count = len(bmis)
                avg_bmi = sum(bmis) / total_count

                # Category counts
                categories = {}
                for record in latest_records:
                    category = record.bmi_category or 'Unknown'
                    categories[category] = categories.get(category, 0) + 1

                return {
                    'total_records': total_count,
                    'average_bmi': round(avg_bmi, 2),
                    'min_bmi': min(bmis),
                    'max_bmi': max(bmis),
                    'category_distribution': categories
                }

            except Exception as e:
                self.logger.error(f"Failed to get BMI statistics: {e}")
                return {}


class MealPlanRepository(BaseRepository):
    """
    Repository class for meal plan operations
    """

    def __init__(self):
        super().__init__(get_database_manager(), MealPlan)

    def create_meal_plan(self, diet_record_id: int, **kwargs) -> Optional[MealPlan]:
        """Create a new meal plan"""
        try:
            kwargs['diet_record_id'] = diet_record_id
            return self.create(**kwargs)
        except Exception as e:
            raise ValueError(f"Failed to create meal plan: {str(e)}")

    def get_meal_plans_for_diet_record(self, diet_record_id: int) -> List[MealPlan]:
        """Get meal plans for a diet record"""
        with self.db_manager.get_session() as session:
            try:
                return session.query(MealPlan).filter(
                    MealPlan.diet_record_id == diet_record_id,
                    MealPlan.is_active == True
                ).order_by(MealPlan.meal_date.desc()).all()

            except Exception as e:
                self.logger.error(f"Failed to get meal plans: {e}")
                return []

    def get_recent_meal_plans(self, client_id: int, days: int = 7) -> List[MealPlan]:
        """Get recent meal plans for a client"""
        with self.db_manager.get_session() as session:
            try:
                cutoff_date = date.today() - datetime.timedelta(days=days)

                return session.query(MealPlan).join(DietRecord).filter(
                    DietRecord.client_id == client_id,
                    MealPlan.is_active == True,
                    MealPlan.meal_date >= cutoff_date
                ).order_by(MealPlan.meal_date.desc()).all()

            except Exception as e:
                self.logger.error(f"Failed to get recent meal plans: {e}")
                return []

    def update_meal_plan_compliance(self, meal_plan_id: int,
                                  compliance_score: int,
                                  notes: str = None) -> bool:
        """Update meal plan compliance"""
        try:
            update_data = {
                'compliance_score': compliance_score,
                'is_followed': compliance_score >= 7  # Consider followed if score >= 7
            }
            if notes:
                update_data['notes'] = notes

            result = self.update(meal_plan_id, **update_data)
            return result is not None

        except Exception as e:
            self.logger.error(f"Failed to update meal plan compliance: {e}")
            return False
