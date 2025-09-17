"""
Diet Controller
Handles diet record management, meal planning, nutrition tracking, and dietary recommendations
for the Pharmacy Management System
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from PyQt6.QtCore import pyqtSignal
from loguru import logger

from .base import BaseController
from models.diet import (
    DietRecord, MealPlan, DietRepository, MealPlanRepository,
    BMICategory, ActivityLevel, WeightCategory, WeightCondition
)
from models.client import Client, ClientRepository
from utils.validation import MedicalValidator, NutritionValidator


class DietController(BaseController):
    """Controller for diet and nutrition management operations"""

    # Specific signals for diet operations
    diet_record_created = pyqtSignal(dict)  # diet record data
    diet_record_updated = pyqtSignal(dict)  # diet record data
    meal_plan_created = pyqtSignal(dict)    # meal plan data
    meal_plan_updated = pyqtSignal(dict)    # meal plan data
    nutrition_calculated = pyqtSignal(dict)  # nutrition calculation results
    weight_goal_updated = pyqtSignal(dict)   # weight goal progress
    diet_recommendations_generated = pyqtSignal(dict)  # recommendations

    def __init__(self, parent=None):
        super().__init__(parent)
        self.diet_repo = None
        self.meal_plan_repo = None
        self.client_repo = None
        self.medical_validator = MedicalValidator()
        self.nutrition_validator = NutritionValidator()

    def _do_initialize(self) -> bool:
        """Initialize the diet controller"""
        try:
            # Initialize repositories
            self.diet_repo = DietRepository()
            self.meal_plan_repo = MealPlanRepository()
            self.client_repo = ClientRepository()

            logger.info("DietController initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize DietController: {e}")
            return False

    # ==================== Diet Record Operations ====================

    def create_diet_record(self, client_id: str, diet_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new diet record for a client

        Args:
            client_id: Client ID
            diet_data: Dictionary containing diet record information

        Returns:
            str: Diet record ID if successful, None if failed
        """
        try:
            # Validate client exists
            client = self.client_repo.get_by_id(client_id)
            if not client:
                self.emit_error("Client Not Found", f"Client with ID {client_id} not found")
                return None

            # Validate diet data
            validation_result = self.medical_validator.validate_diet_data(diet_data)
            if not validation_result['is_valid']:
                error_msg = "; ".join(validation_result['errors'])
                self.emit_error("Validation Error", f"Diet data validation failed: {error_msg}")
                return None

            validated_data = validation_result['data']

            # Create diet record instance
            diet_record = DietRecord(
                client_id=client_id,
                record_date=validated_data.get('record_date', date.today()),
                current_weight=validated_data['current_weight'],
                target_weight=validated_data.get('target_weight'),
                height=validated_data['height'],
                activity_level=validated_data.get('activity_level', ActivityLevel.SEDENTARY),
                weight_goal=validated_data.get('weight_goal', WeightCondition.MAINTAIN),
                target_date=validated_data.get('target_date'),
                dietary_restrictions=validated_data.get('dietary_restrictions', ''),
                food_preferences=validated_data.get('food_preferences', ''),
                supplements=validated_data.get('supplements', ''),
                water_intake_target=validated_data.get('water_intake_target', 2000),
                notes=validated_data.get('notes', '')
            )

            # Save to database
            record_id = self.diet_repo.create_diet_record(diet_record)

            if record_id:
                # Calculate BMI and recommendations
                bmi_data = self.calculate_nutrition_metrics(record_id)

                self.emit_success("Diet Record Created",
                                f"Diet record created for {client.full_display_name}")
                self.diet_record_created.emit(diet_record.to_dict())
                self.emit_data_changed("diet_record_created", {
                    "client_id": client_id,
                    "record_id": record_id
                })
                return record_id
            else:
                self.emit_error("Creation Failed", "Failed to create diet record in database")
                return None

        except Exception as e:
            self.handle_database_error(e, "creating diet record")
            return None

    def update_diet_record(self, record_id: str, updated_data: Dict[str, Any]) -> bool:
        """
        Update an existing diet record

        Args:
            record_id: Diet record ID to update
            updated_data: Dictionary containing updated diet information

        Returns:
            bool: True if successful
        """
        try:
            # Get existing record
            existing_record = self.get_diet_record_by_id(record_id)
            if not existing_record:
                self.emit_error("Record Not Found", f"Diet record with ID {record_id} not found")
                return False

            # Validate updated data
            validation_result = self.medical_validator.validate_diet_data(updated_data, is_update=True)
            if not validation_result['is_valid']:
                error_msg = "; ".join(validation_result['errors'])
                self.emit_error("Validation Error", f"Update data validation failed: {error_msg}")
                return False

            validated_data = validation_result['data']

            # Update record
            success = self.diet_repo.update_diet_record(record_id, validated_data)

            if success:
                updated_record = self.get_diet_record_by_id(record_id)
                self.emit_success("Diet Record Updated", "Diet record updated successfully")
                self.diet_record_updated.emit(updated_record.to_dict())
                self.emit_data_changed("diet_record_updated", {"record_id": record_id})
                return True
            else:
                self.emit_error("Update Failed", "Failed to update diet record in database")
                return False

        except Exception as e:
            self.handle_database_error(e, "updating diet record")
            return False

    def get_diet_record_by_id(self, record_id: str) -> Optional[DietRecord]:
        """
        Get a diet record by ID

        Args:
            record_id: Diet record ID

        Returns:
            DietRecord: Diet record instance or None
        """
        try:
            return self.diet_repo.get_by_id(record_id)
        except Exception as e:
            logger.error(f"Error getting diet record {record_id}: {e}")
            return None

    def get_latest_diet_record(self, client_id: str) -> Optional[DietRecord]:
        """
        Get the latest diet record for a client

        Args:
            client_id: Client ID

        Returns:
            DietRecord: Latest diet record or None
        """
        try:
            return self.diet_repo.get_latest_for_client(client_id)
        except Exception as e:
            logger.error(f"Error getting latest diet record for client {client_id}: {e}")
            return None

    def get_diet_records_for_client(self, client_id: str, limit: int = 10) -> List[DietRecord]:
        """
        Get diet records for a client

        Args:
            client_id: Client ID
            limit: Maximum number of records to return

        Returns:
            List[DietRecord]: List of diet records
        """
        try:
            return self.diet_repo.get_records_for_client(client_id, limit)
        except Exception as e:
            logger.error(f"Error getting diet records for client {client_id}: {e}")
            return []

    # ==================== Nutrition Calculations ====================

    def calculate_nutrition_metrics(self, record_id: str) -> Dict[str, Any]:
        """
        Calculate comprehensive nutrition metrics for a diet record

        Args:
            record_id: Diet record ID

        Returns:
            dict: Nutrition calculation results
        """
        try:
            diet_record = self.get_diet_record_by_id(record_id)
            if not diet_record:
                return {}

            # Calculate BMI
            bmi = diet_record.calculate_bmi()

            # Calculate BMR (Basal Metabolic Rate)
            bmr = diet_record.calculate_bmr()

            # Calculate daily calorie needs
            daily_calories = diet_record.calculate_daily_calories()

            # Get BMI category and health status
            bmi_category = diet_record._get_bmi_category()

            # Calculate macronutrient distribution
            macros = self._calculate_macronutrient_distribution(daily_calories, diet_record.weight_goal)

            # Calculate weight change timeline
            timeline = self._calculate_weight_change_timeline(diet_record)

            result = {
                'record_id': record_id,
                'bmi': bmi,
                'bmi_category': bmi_category,
                'bmr': bmr,
                'daily_calories': daily_calories,
                'macronutrients': macros,
                'weight_timeline': timeline,
                'calculation_date': datetime.now(),
                'is_healthy_weight': diet_record.is_healthy_bmi(),
                'recommendations': diet_record.get_diet_recommendations()
            }

            # Emit signal
            self.nutrition_calculated.emit(result)

            return result

        except Exception as e:
            logger.error(f"Error calculating nutrition metrics: {e}")
            self.emit_error("Calculation Error", f"Failed to calculate nutrition metrics: {str(e)}")
            return {}

    def _calculate_macronutrient_distribution(self, daily_calories: float,
                                            weight_goal: WeightCondition) -> Dict[str, Any]:
        """
        Calculate recommended macronutrient distribution

        Args:
            daily_calories: Daily calorie target
            weight_goal: Weight goal (lose, gain, maintain)

        Returns:
            dict: Macronutrient breakdown
        """
        try:
            # Base macronutrient ratios (can be customized based on goals)
            if weight_goal == WeightCondition.LOSE_WEIGHT:
                # Higher protein for weight loss
                protein_ratio = 0.30
                carb_ratio = 0.40
                fat_ratio = 0.30
            elif weight_goal == WeightCondition.GAIN_WEIGHT:
                # Balanced for healthy weight gain
                protein_ratio = 0.25
                carb_ratio = 0.45
                fat_ratio = 0.30
            else:  # Maintain weight
                # Standard balanced diet
                protein_ratio = 0.25
                carb_ratio = 0.45
                fat_ratio = 0.30

            # Calculate calories per macronutrient
            protein_calories = daily_calories * protein_ratio
            carb_calories = daily_calories * carb_ratio
            fat_calories = daily_calories * fat_ratio

            # Convert to grams (protein: 4 cal/g, carbs: 4 cal/g, fat: 9 cal/g)
            protein_grams = round(protein_calories / 4, 1)
            carb_grams = round(carb_calories / 4, 1)
            fat_grams = round(fat_calories / 9, 1)

            return {
                'total_calories': daily_calories,
                'protein': {
                    'calories': protein_calories,
                    'grams': protein_grams,
                    'percentage': int(protein_ratio * 100)
                },
                'carbohydrates': {
                    'calories': carb_calories,
                    'grams': carb_grams,
                    'percentage': int(carb_ratio * 100)
                },
                'fat': {
                    'calories': fat_calories,
                    'grams': fat_grams,
                    'percentage': int(fat_ratio * 100)
                }
            }

        except Exception as e:
            logger.error(f"Error calculating macronutrient distribution: {e}")
            return {}

    def _calculate_weight_change_timeline(self, diet_record: DietRecord) -> Dict[str, Any]:
        """
        Calculate realistic weight change timeline

        Args:
            diet_record: Diet record instance

        Returns:
            dict: Weight change timeline
        """
        try:
            current_weight = diet_record.current_weight
            target_weight = diet_record.target_weight
            target_date = diet_record.target_date

            if not target_weight or not target_date:
                return {}

            weight_difference = target_weight - current_weight
            days_to_target = (target_date - date.today()).days

            if days_to_target <= 0:
                return {
                    'status': 'target_date_passed',
                    'message': 'Target date has already passed'
                }

            # Healthy weight loss/gain rates (kg per week)
            healthy_loss_rate = 0.5  # 0.5 kg per week
            healthy_gain_rate = 0.25  # 0.25 kg per week

            if weight_difference < 0:  # Weight loss
                recommended_rate = healthy_loss_rate
                weeks_needed = abs(weight_difference) / recommended_rate
                is_realistic = weeks_needed <= (days_to_target / 7)
            else:  # Weight gain
                recommended_rate = healthy_gain_rate
                weeks_needed = weight_difference / recommended_rate
                is_realistic = weeks_needed <= (days_to_target / 7)

            weekly_target = weight_difference / (days_to_target / 7) if days_to_target > 0 else 0

            return {
                'current_weight': current_weight,
                'target_weight': target_weight,
                'weight_difference': weight_difference,
                'days_to_target': days_to_target,
                'weeks_to_target': round(days_to_target / 7, 1),
                'recommended_weekly_change': round(recommended_rate, 2),
                'required_weekly_change': round(weekly_target, 2),
                'is_realistic': is_realistic,
                'weeks_needed_healthy': round(weeks_needed, 1),
                'recommended_target_date': (date.today() + timedelta(weeks=weeks_needed)).isoformat(),
                'status': 'realistic' if is_realistic else 'aggressive'
            }

        except Exception as e:
            logger.error(f"Error calculating weight change timeline: {e}")
            return {}

    # ==================== Meal Planning ====================

    def create_meal_plan(self, diet_record_id: str, meal_plan_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a meal plan for a diet record

        Args:
            diet_record_id: Diet record ID
            meal_plan_data: Meal plan data

        Returns:
            str: Meal plan ID if successful
        """
        try:
            # Validate diet record exists
            diet_record = self.get_diet_record_by_id(diet_record_id)
            if not diet_record:
                self.emit_error("Diet Record Not Found", f"Diet record with ID {diet_record_id} not found")
                return None

            # Validate meal plan data
            validation_result = self.nutrition_validator.validate_meal_plan_data(meal_plan_data)
            if not validation_result['is_valid']:
                error_msg = "; ".join(validation_result['errors'])
                self.emit_error("Validation Error", f"Meal plan validation failed: {error_msg}")
                return None

            validated_data = validation_result['data']

            # Create meal plan instance
            meal_plan = MealPlan(
                diet_record_id=diet_record_id,
                plan_date=validated_data.get('plan_date', date.today()),
                breakfast=validated_data.get('breakfast', ''),
                morning_snack=validated_data.get('morning_snack', ''),
                lunch=validated_data.get('lunch', ''),
                afternoon_snack=validated_data.get('afternoon_snack', ''),
                dinner=validated_data.get('dinner', ''),
                evening_snack=validated_data.get('evening_snack', ''),
                water_intake=validated_data.get('water_intake', 0),
                notes=validated_data.get('notes', ''),
                is_followed=validated_data.get('is_followed', False)
            )

            # Save to database
            plan_id = self.meal_plan_repo.create_meal_plan(meal_plan)

            if plan_id:
                self.emit_success("Meal Plan Created", "Meal plan created successfully")
                self.meal_plan_created.emit(meal_plan.to_dict())
                self.emit_data_changed("meal_plan_created", {
                    "diet_record_id": diet_record_id,
                    "plan_id": plan_id
                })
                return plan_id
            else:
                self.emit_error("Creation Failed", "Failed to create meal plan in database")
                return None

        except Exception as e:
            self.handle_database_error(e, "creating meal plan")
            return None

    def update_meal_plan(self, plan_id: str, updated_data: Dict[str, Any]) -> bool:
        """
        Update an existing meal plan

        Args:
            plan_id: Meal plan ID
            updated_data: Updated meal plan data

        Returns:
            bool: True if successful
        """
        try:
            # Validate updated data
            validation_result = self.nutrition_validator.validate_meal_plan_data(updated_data, is_update=True)
            if not validation_result['is_valid']:
                error_msg = "; ".join(validation_result['errors'])
                self.emit_error("Validation Error", f"Update data validation failed: {error_msg}")
                return False

            validated_data = validation_result['data']

            # Update meal plan
            success = self.meal_plan_repo.update_meal_plan(plan_id, validated_data)

            if success:
                updated_plan = self.get_meal_plan_by_id(plan_id)
                self.emit_success("Meal Plan Updated", "Meal plan updated successfully")
                self.meal_plan_updated.emit(updated_plan.to_dict())
                self.emit_data_changed("meal_plan_updated", {"plan_id": plan_id})
                return True
            else:
                self.emit_error("Update Failed", "Failed to update meal plan in database")
                return False

        except Exception as e:
            self.handle_database_error(e, "updating meal plan")
            return False

    def get_meal_plan_by_id(self, plan_id: str) -> Optional[MealPlan]:
        """
        Get a meal plan by ID

        Args:
            plan_id: Meal plan ID

        Returns:
            MealPlan: Meal plan instance or None
        """
        try:
            return self.meal_plan_repo.get_by_id(plan_id)
        except Exception as e:
            logger.error(f"Error getting meal plan {plan_id}: {e}")
            return None

    def get_meal_plans_for_diet_record(self, diet_record_id: str, limit: int = 30) -> List[MealPlan]:
        """
        Get meal plans for a diet record

        Args:
            diet_record_id: Diet record ID
            limit: Maximum number of plans to return

        Returns:
            List[MealPlan]: List of meal plans
        """
        try:
            return self.meal_plan_repo.get_meal_plans_for_diet_record(diet_record_id, limit)
        except Exception as e:
            logger.error(f"Error getting meal plans for diet record {diet_record_id}: {e}")
            return []

    def get_recent_meal_plans(self, client_id: str, days: int = 7) -> List[MealPlan]:
        """
        Get recent meal plans for a client

        Args:
            client_id: Client ID
            days: Number of days to look back

        Returns:
            List[MealPlan]: Recent meal plans
        """
        try:
            return self.meal_plan_repo.get_recent_meal_plans(client_id, days)
        except Exception as e:
            logger.error(f"Error getting recent meal plans for client {client_id}: {e}")
            return []

    def update_meal_plan_compliance(self, plan_id: str, compliance_data: Dict[str, bool]) -> bool:
        """
        Update meal plan compliance tracking

        Args:
            plan_id: Meal plan ID
            compliance_data: Dictionary of compliance status for each meal

        Returns:
            bool: True if successful
        """
        try:
            success = self.meal_plan_repo.update_meal_plan_compliance(plan_id, compliance_data)

            if success:
                self.emit_data_changed("meal_plan_compliance_updated", {
                    "plan_id": plan_id,
                    "compliance": compliance_data
                })

            return success

        except Exception as e:
            self.handle_database_error(e, "updating meal plan compliance")
            return False

    # ==================== Diet Recommendations ====================

    def generate_diet_recommendations(self, client_id: str) -> Dict[str, Any]:
        """
        Generate personalized diet recommendations for a client

        Args:
            client_id: Client ID

        Returns:
            dict: Diet recommendations
        """
        try:
            # Get latest diet record
            diet_record = self.get_latest_diet_record(client_id)
            if not diet_record:
                self.emit_error("No Diet Record", "No diet record found for client")
                return {}

            # Get client information
            client = self.client_repo.get_by_id(client_id)
            if not client:
                return {}

            # Generate recommendations based on current status
            recommendations = diet_record.get_diet_recommendations()

            # Add personalized recommendations based on medical conditions
            if client.medical_conditions:
                medical_recommendations = self._get_medical_condition_recommendations(
                    client.medical_conditions, diet_record
                )
                recommendations.update(medical_recommendations)

            # Add allergy considerations
            if client.allergies:
                allergy_considerations = self._get_allergy_considerations(client.allergies)
                recommendations['allergy_considerations'] = allergy_considerations

            # Add current medication interactions
            if client.current_medications:
                medication_considerations = self._get_medication_diet_interactions(client.current_medications)
                recommendations['medication_considerations'] = medication_considerations

            # Emit recommendations signal
            self.diet_recommendations_generated.emit(recommendations)

            return recommendations

        except Exception as e:
            logger.error(f"Error generating diet recommendations: {e}")
            self.emit_error("Recommendation Error", f"Failed to generate recommendations: {str(e)}")
            return {}

    def _get_medical_condition_recommendations(self, medical_conditions: str,
                                             diet_record: DietRecord) -> Dict[str, List[str]]:
        """
        Get diet recommendations based on medical conditions

        Args:
            medical_conditions: Medical conditions string
            diet_record: Diet record instance

        Returns:
            dict: Medical condition-specific recommendations
        """
        recommendations = {
            'medical_recommendations': [],
            'foods_to_avoid': [],
            'foods_to_include': []
        }

        conditions = medical_conditions.lower()

        # Diabetes recommendations
        if any(term in conditions for term in ['diabetes', 'diabetic', 'blood sugar']):
            recommendations['medical_recommendations'].extend([
                'Monitor carbohydrate intake and choose complex carbs',
                'Eat regular, balanced meals to maintain blood sugar',
                'Include fiber-rich foods to help control blood glucose'
            ])
            recommendations['foods_to_avoid'].extend([
                'Refined sugars and sweets',
                'White bread and processed grains',
                'Sugary drinks and fruit juices'
            ])
            recommendations['foods_to_include'].extend([
                'Whole grains and legumes',
                'Non-starchy vegetables',
                'Lean proteins'
            ])

        # Hypertension recommendations
        if any(term in conditions for term in ['hypertension', 'high blood pressure', 'bp']):
            recommendations['medical_recommendations'].extend([
                'Reduce sodium intake to less than 2300mg per day',
                'Follow DASH diet principles',
                'Maintain healthy weight to reduce blood pressure'
            ])
            recommendations['foods_to_avoid'].extend([
                'High-sodium processed foods',
                'Canned soups and sauces',
                'Deli meats and pickled foods'
            ])
            recommendations['foods_to_include'].extend([
                'Potassium-rich fruits and vegetables',
                'Low-fat dairy products',
                'Nuts and seeds (unsalted)'
            ])

        # Heart disease recommendations
        if any(term in conditions for term in ['heart', 'cardiac', 'cardiovascular']):
            recommendations['medical_recommendations'].extend([
                'Limit saturated and trans fats',
                'Include omega-3 fatty acids',
                'Maintain healthy cholesterol levels through diet'
            ])
            recommendations['foods_to_avoid'].extend([
                'Fried and processed foods',
                'High-fat dairy products',
                'Red meat and organ meats'
            ])
            recommendations['foods_to_include'].extend([
                'Fatty fish (salmon, mackerel)',
                'Olive oil and avocados',
                'Oats and barley'
            ])

        return recommendations

    def _get_allergy_considerations(self, allergies: str) -> List[str]:
        """
        Get dietary considerations for allergies

        Args:
            allergies: Allergies string

        Returns:
            List[str]: Allergy considerations
        """
        considerations = []
        allergy_list = allergies.lower()

        common_allergens = {
            'gluten': 'Avoid wheat, barley, rye, and products containing gluten',
            'dairy': 'Avoid milk, cheese, yogurt, and dairy-based products',
            'nuts': 'Carefully check labels for tree nuts and cross-contamination',
            'peanuts': 'Avoid peanuts and peanut-containing products',
            'shellfish': 'Avoid all shellfish and check for cross-contamination',
            'eggs': 'Avoid eggs and egg-containing products',
            'soy': 'Avoid soy products and check processed food labels'
        }

        for allergen, advice in common_allergens.items():
            if allergen in allergy_list:
                considerations.append(advice)

        if not considerations:
            considerations.append('Always read food labels carefully for allergen information')

        return considerations

    def _get_medication_diet_interactions(self, medications: str) -> List[str]:
        """
        Get dietary considerations for medication interactions

        Args:
            medications: Current medications string

        Returns:
            List[str]: Medication interaction considerations
        """
        considerations = []
        med_list = medications.lower()

        # Common medication-diet interactions
        if 'warfarin' in med_list or 'coumadin' in med_list:
            considerations.append('Maintain consistent vitamin K intake from green vegetables')

        if 'metformin' in med_list:
            considerations.append('Take with meals to reduce gastrointestinal side effects')

        if any(term in med_list for term in ['insulin', 'diabetic medication']):
            considerations.append('Coordinate meal timing with medication schedule')

        if 'thyroid' in med_list or 'levothyroxine' in med_list:
            considerations.append('Take thyroid medication on empty stomach, avoid calcium/iron supplements within 4 hours')

        if not considerations:
            considerations.append('Consult healthcare provider about potential food-drug interactions')

        return considerations

    # ==================== Weight Progress Tracking ====================

    def track_weight_progress(self, client_id: str) -> Dict[str, Any]:
        """
        Track weight progress for a client

        Args:
            client_id: Client ID

        Returns:
            dict: Weight progress data
        """
        try:
            # Get weight history
            weight_history = self.diet_repo.get_weight_history(client_id)

            if len(weight_history) < 2:
                return {
                    'status': 'insufficient_data',
                    'message': 'Need at least 2 weight records to track progress'
                }

            # Calculate progress metrics
            latest_record = weight_history[0]
            previous_record = weight_history[1]
            initial_record = weight_history[-1]

            weight_change_recent = latest_record['weight'] - previous_record['weight']
            weight_change_total = latest_record['weight'] - initial_record['weight']

            days_since_start = (latest_record['date'] - initial_record['date']).days
            weekly_average = (weight_change_total / days_since_start * 7) if days_since_start > 0 else 0

            # Determine progress status
            target_weight = latest_record.get('target_weight')
            if target_weight:
                progress_to_goal = self._calculate_progress_to_goal(
                    initial_record['weight'],
                    latest_record['weight'],
                    target_weight
                )
            else:
                progress_to_goal = None

            progress_data = {
                'latest_weight': latest_record['weight'],
                'weight_change_recent': round(weight_change_recent, 2),
                'weight_change_total': round(weight_change_total, 2),
                'weekly_average_change': round(weekly_average, 2),
                'days_tracking': days_since_start,
                'progress_to_goal': progress_to_goal,
                'weight_history': weight_history[:10],  # Last 10 records
                'trend': 'decreasing' if weight_change_recent < 0 else 'increasing' if weight_change_recent > 0 else 'stable'
            }

            # Emit progress signal
            self.weight_goal_updated.emit(progress_data)

            return progress_data

        except Exception as e:
            logger.error(f"Error tracking weight progress for client {client_id}: {e}")
            return {}

    def _calculate_progress_to_goal(self, initial_weight: float, current_weight: float,
                                  target_weight: float) -> Dict[str, Any]:
        """
        Calculate progress towards weight goal

        Args:
            initial_weight: Starting weight
            current_weight: Current weight
            target_weight: Target weight

        Returns:
            dict: Progress calculation
        """
        total_change_needed = target_weight - initial_weight
        current_change = current_weight - initial_weight

        if total_change_needed == 0:
            progress_percentage = 100
        else:
            progress_percentage = min(100, max(0, (current_change / total_change_needed) * 100))

        remaining_change = target_weight - current_weight

        return {
            'progress_percentage': round(progress_percentage, 1),
            'weight_remaining': round(abs(remaining_change), 2),
            'is_on_track': abs(remaining_change) <= abs(total_change_needed) * 0.1,  # Within 10% of goal
            'goal_achieved': abs(remaining_change) <= 0.5  # Within 0.5 kg of goal
        }

    # ==================== Statistics and Analytics ====================

    def get_nutrition_statistics(self, client_id: str = None) -> Dict[str, Any]:
        """
        Get nutrition and diet statistics

        Args:
            client_id: Optional client ID for specific client stats

        Returns:
            dict: Nutrition statistics
        """
        try:
            if client_id:
                # Client-specific statistics
                return self._get_client_nutrition_stats(client_id)
            else:
                # Overall statistics
                return self.diet_repo.get_bmi_statistics()

        except Exception as e:
            logger.error(f"Error getting nutrition statistics: {e}")
            return {}

    def _get_client_nutrition_stats(self, client_id: str) -> Dict[str, Any]:
        """
        Get nutrition statistics for a specific client

        Args:
            client_id: Client ID

        Returns:
            dict: Client nutrition statistics
        """
        try:
            diet_records = self.get_diet_records_for_client(client_id)
            meal_plans = self.get_recent_meal_plans(client_id, 30)

            if not diet_records:
                return {}

            latest_record = diet_records[0]

            # Calculate compliance rate for meal plans
            total_plans = len(meal_plans)
            followed_plans = sum(1 for plan in meal_plans if plan.is_followed)
            compliance_rate = (followed_plans / total_plans * 100) if total_plans > 0 else 0

            # Calculate average water intake
            water_intakes = [plan.water_intake for plan in meal_plans if plan.water_intake > 0]
            avg_water_intake = sum(water_intakes) / len(water_intakes) if water_intakes else 0

            return {
                'total_diet_records': len(diet_records),
                'latest_bmi': latest_record.calculate_bmi(),
                'bmi_category': latest_record._get_bmi_category(),
                'meal_plan_compliance_rate': round(compliance_rate, 1),
                'average_water_intake': round(avg_water_intake, 0),
                'days_tracking': (datetime.now().date() - diet_records[-1].record_date).days,
                'weight_change_trend': self._calculate_weight_trend(diet_records)
            }

        except Exception as e:
            logger.error(f"Error getting client nutrition stats: {e}")
            return {}

    def _calculate_weight_trend(self, diet_records: List[DietRecord]) -> str:
        """
        Calculate weight trend from diet records

        Args:
            diet_records: List of diet records (newest first)

        Returns:
            str: Trend description
        """
        if len(diet_records) < 2:
            return "insufficient_data"

        recent_weights = [record.current_weight for record in diet_records[:3]]

        if len(recent_weights) >= 3:
            # Check trend over last 3 records
            if recent_weights[0] < recent_weights[1] < recent_weights[2]:
                return "decreasing"
            elif recent_weights[0] > recent_weights[1] > recent_weights[2]:
                return "increasing"
            else:
                return "fluctuating"
        else:
            # Compare latest two records
            if recent_weights[0] < recent_weights[1]:
                return "decreasing"
            elif recent_weights[0] > recent_weights[1]:
                return "increasing"
            else:
                return "stable"

    # ==================== Utility Methods ====================

    def refresh_diet_data(self, client_id: str = None) -> None:
        """
        Refresh diet data and emit update signals

        Args:
            client_id: Optional client ID to refresh specific client data
        """
        try:
            if client_id:
                self.emit_data_changed("client_diet_data_refreshed", {"client_id": client_id})
            else:
                self.emit_data_changed("diet_data_refreshed", {})

            self.emit_status("Diet data refreshed")
        except Exception as e:
            logger.error(f"Error refreshing diet data: {e}")

    def cleanup(self) -> None:
        """Clean up controller resources"""
        try:
            super().cleanup()
            # Additional cleanup specific to DietController
            self.diet_repo = None
            self.meal_plan_repo = None
            self.client_repo = None
            logger.info("DietController cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during DietController cleanup: {e}")
