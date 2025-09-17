"""
Migration Script: Pharmacy Management v1.0 to v2.0
Migrates data from the old monolithic application to the new MVC architecture
"""

import os
import sys
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.models.base import get_database_manager, init_database
from src.models.client import ClientRepository, ClientNoteRepository
from src.models.diet import DietRepository, MealPlanRepository
from src.config.settings import get_settings_manager
from loguru import logger


class V1ToV2Migrator:
    """Handles migration from v1.0 to v2.0 database schema"""

    def __init__(self, v1_db_path: str, backup_dir: Optional[str] = None):
        self.v1_db_path = v1_db_path
        self.backup_dir = backup_dir or "migration_backups"
        self.migration_log = []
        self.errors = []

        # Initialize v2 components
        self.v2_db_manager = get_database_manager()
        self.client_repo = ClientRepository()
        self.diet_repo = DietRepository()
        self.meal_repo = MealPlanRepository()
        self.note_repo = ClientNoteRepository()

    def run_migration(self) -> bool:
        """
        Run the complete migration process

        Returns:
            bool: True if migration successful, False otherwise
        """
        try:
            logger.info("Starting migration from v1.0 to v2.0")

            # Step 1: Validate v1 database
            if not self._validate_v1_database():
                return False

            # Step 2: Create backup
            if not self._create_backup():
                return False

            # Step 3: Initialize v2 database
            if not self._initialize_v2_database():
                return False

            # Step 4: Migrate data
            if not self._migrate_data():
                return False

            # Step 5: Validate migration
            if not self._validate_migration():
                return False

            # Step 6: Create migration report
            self._create_migration_report()

            logger.info("Migration completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self.errors.append(f"Migration failed: {e}")
            return False

    def _validate_v1_database(self) -> bool:
        """Validate the v1 database exists and has expected structure"""
        try:
            if not os.path.exists(self.v1_db_path):
                self.errors.append(f"V1 database not found: {self.v1_db_path}")
                return False

            conn = sqlite3.connect(self.v1_db_path)
            cursor = conn.cursor()

            # Check for expected tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = ['general_info', 'diet_info', 'notes']
            missing_tables = [table for table in expected_tables if table not in tables]

            if missing_tables:
                self.errors.append(f"Missing tables in v1 database: {missing_tables}")
                conn.close()
                return False

            conn.close()
            logger.info("V1 database validation successful")
            return True

        except Exception as e:
            self.errors.append(f"V1 database validation failed: {e}")
            return False

    def _create_backup(self) -> bool:
        """Create backup of v1 database"""
        try:
            backup_dir = Path(self.backup_dir)
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"pharmacy_v1_backup_{timestamp}.db"

            shutil.copy2(self.v1_db_path, backup_file)

            self.migration_log.append(f"Created backup: {backup_file}")
            logger.info(f"Backup created: {backup_file}")
            return True

        except Exception as e:
            self.errors.append(f"Backup creation failed: {e}")
            return False

    def _initialize_v2_database(self) -> bool:
        """Initialize the v2 database schema"""
        try:
            init_database()
            self.migration_log.append("V2 database initialized")
            logger.info("V2 database initialized")
            return True

        except Exception as e:
            self.errors.append(f"V2 database initialization failed: {e}")
            return False

    def _migrate_data(self) -> bool:
        """Migrate all data from v1 to v2"""
        try:
            # Connect to v1 database
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_conn.row_factory = sqlite3.Row  # Access columns by name

            # Migrate in order: clients, diet records, notes
            client_mapping = self._migrate_clients(v1_conn)
            if not client_mapping:
                return False

            self._migrate_diet_records(v1_conn, client_mapping)
            self._migrate_notes(v1_conn, client_mapping)

            v1_conn.close()
            return True

        except Exception as e:
            self.errors.append(f"Data migration failed: {e}")
            return False

    def _migrate_clients(self, v1_conn: sqlite3.Connection) -> Dict[str, int]:
        """
        Migrate client data from general_info table

        Returns:
            Dict mapping v1 pharmacy_id to v2 client_id
        """
        client_mapping = {}

        try:
            cursor = v1_conn.cursor()
            cursor.execute("SELECT * FROM general_info")

            migrated_count = 0
            for row in cursor.fetchall():
                try:
                    # Map v1 fields to v2 structure
                    client_data = {
                        'client_pharmacy_id': row['client_pharmacy_id'],
                        'client_name': row['client_name'],
                        'age': row.get('age'),
                        'job': row.get('job'),
                        'address': row.get('address'),
                        'phone': row.get('phone'),
                        'work_effort': row.get('work_effort'),
                        'diseases': row.get('diseases'),
                        'previous_attempts': row.get('previous_attempts'),
                        'current_treatment': row.get('current_treatment'),
                        'visit_purpose': row.get('visit_purpose'),
                        'follow_up_date': self._convert_date(row.get('follow_up_date'))
                    }

                    # Create client in v2
                    client = self.client_repo.create_client(**client_data)
                    if client:
                        client_mapping[row['client_pharmacy_id']] = client.id
                        migrated_count += 1
                    else:
                        self.errors.append(f"Failed to create client: {row['client_name']}")

                except Exception as e:
                    self.errors.append(f"Error migrating client {row.get('client_name', 'Unknown')}: {e}")

            self.migration_log.append(f"Migrated {migrated_count} clients")
            logger.info(f"Migrated {migrated_count} clients")
            return client_mapping

        except Exception as e:
            self.errors.append(f"Client migration failed: {e}")
            return {}

    def _migrate_diet_records(self, v1_conn: sqlite3.Connection, client_mapping: Dict[str, int]):
        """Migrate diet records from diet_info table"""
        try:
            cursor = v1_conn.cursor()
            cursor.execute("SELECT * FROM diet_info")

            migrated_count = 0
            for row in cursor.fetchall():
                try:
                    # Get v2 client_id from mapping
                    v1_client_id = row['client_id']

                    # Find corresponding pharmacy_id from general_info
                    client_cursor = v1_conn.cursor()
                    client_cursor.execute("SELECT client_pharmacy_id FROM general_info WHERE id = ?", (v1_client_id,))
                    client_result = client_cursor.fetchone()

                    if not client_result:
                        continue

                    pharmacy_id = client_result['client_pharmacy_id']
                    v2_client_id = client_mapping.get(pharmacy_id)

                    if not v2_client_id:
                        continue

                    # Map diet data
                    diet_data = {
                        'height': row.get('height'),
                        'current_weight': row.get('current_weight'),
                        'previous_weight': row.get('previous_weight'),
                        'fat_percentage': row.get('fat_percentage'),
                        'muscle_percentage': row.get('muscle_percentage'),
                        'water_percentage': row.get('water_percentage'),
                        'mineral_percentage': row.get('mineral_percentage'),
                        'bmi': row.get('bmi'),
                        'weight_category': row.get('weight_category'),
                        'weight_condition': row.get('weight_condition')
                    }

                    # Create diet record
                    diet_record = self.diet_repo.create_diet_record(v2_client_id, **diet_data)

                    if diet_record:
                        # Create meal plan if meal data exists
                        meal_data = {
                            'breakfast': row.get('breakfast'),
                            'lunch': row.get('lunch'),
                            'dinner': row.get('dinner'),
                            'snack_1': row.get('snack_1'),
                            'snack_2': row.get('snack_2')
                        }

                        # Only create meal plan if there's actual meal data
                        if any(meal for meal in meal_data.values() if meal and meal.strip()):
                            meal_plan = self.meal_repo.create_meal_plan(diet_record.id, **meal_data)

                        migrated_count += 1

                except Exception as e:
                    self.errors.append(f"Error migrating diet record: {e}")

            self.migration_log.append(f"Migrated {migrated_count} diet records")
            logger.info(f"Migrated {migrated_count} diet records")

        except Exception as e:
            self.errors.append(f"Diet records migration failed: {e}")

    def _migrate_notes(self, v1_conn: sqlite3.Connection, client_mapping: Dict[str, int]):
        """Migrate notes from notes table"""
        try:
            cursor = v1_conn.cursor()
            cursor.execute("SELECT * FROM notes")

            migrated_count = 0
            for row in cursor.fetchall():
                try:
                    # Get v2 client_id from mapping
                    v1_client_id = row['client_id']

                    # Find corresponding pharmacy_id from general_info
                    client_cursor = v1_conn.cursor()
                    client_cursor.execute("SELECT client_pharmacy_id FROM general_info WHERE id = ?", (v1_client_id,))
                    client_result = client_cursor.fetchone()

                    if not client_result:
                        continue

                    pharmacy_id = client_result['client_pharmacy_id']
                    v2_client_id = client_mapping.get(pharmacy_id)

                    if not v2_client_id:
                        continue

                    # Create note
                    note_content = row.get('client_notes', '')
                    if note_content and note_content.strip():
                        note = self.note_repo.create_note(
                            client_id=v2_client_id,
                            content=note_content,
                            title="Migrated from v1.0",
                            note_type="general"
                        )

                        if note:
                            migrated_count += 1

                except Exception as e:
                    self.errors.append(f"Error migrating note: {e}")

            self.migration_log.append(f"Migrated {migrated_count} notes")
            logger.info(f"Migrated {migrated_count} notes")

        except Exception as e:
            self.errors.append(f"Notes migration failed: {e}")

    def _convert_date(self, date_str: str) -> Optional[str]:
        """Convert date string to proper format"""
        if not date_str:
            return None

        try:
            # Try to parse the date and return in ISO format
            from datetime import datetime
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.date().isoformat()
        except:
            return None

    def _validate_migration(self) -> bool:
        """Validate that migration was successful"""
        try:
            # Get counts from v1 database
            v1_conn = sqlite3.connect(self.v1_db_path)
            v1_cursor = v1_conn.cursor()

            v1_cursor.execute("SELECT COUNT(*) FROM general_info")
            v1_client_count = v1_cursor.fetchone()[0]

            v1_cursor.execute("SELECT COUNT(*) FROM diet_info")
            v1_diet_count = v1_cursor.fetchone()[0]

            v1_cursor.execute("SELECT COUNT(*) FROM notes WHERE client_notes IS NOT NULL AND client_notes != ''")
            v1_notes_count = v1_cursor.fetchone()[0]

            v1_conn.close()

            # Get counts from v2 database
            v2_client_count = self.client_repo.count()
            v2_diet_count = self.diet_repo.count()
            v2_notes_count = self.note_repo.count()

            # Compare counts
            validation_results = {
                'clients': (v1_client_count, v2_client_count),
                'diet_records': (v1_diet_count, v2_diet_count),
                'notes': (v1_notes_count, v2_notes_count)
            }

            all_valid = True
            for item_type, (v1_count, v2_count) in validation_results.items():
                if v1_count != v2_count:
                    self.errors.append(f"Count mismatch for {item_type}: v1={v1_count}, v2={v2_count}")
                    all_valid = False
                else:
                    self.migration_log.append(f"✓ {item_type}: {v2_count} records migrated successfully")

            return all_valid

        except Exception as e:
            self.errors.append(f"Migration validation failed: {e}")
            return False

    def _create_migration_report(self):
        """Create a detailed migration report"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            report_file = Path(self.backup_dir) / f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("Pharmacy Management System Migration Report\n")
                f.write("=" * 50 + "\n")
                f.write(f"Migration Date: {timestamp}\n")
                f.write(f"Source Database: {self.v1_db_path}\n")
                f.write(f"Target Database: v2.0\n\n")

                f.write("Migration Log:\n")
                f.write("-" * 20 + "\n")
                for log_entry in self.migration_log:
                    f.write(f"• {log_entry}\n")

                if self.errors:
                    f.write("\nErrors:\n")
                    f.write("-" * 10 + "\n")
                    for error in self.errors:
                        f.write(f"✗ {error}\n")
                else:
                    f.write("\n✓ Migration completed successfully with no errors!\n")

                f.write(f"\nReport saved: {report_file}\n")

            logger.info(f"Migration report created: {report_file}")

        except Exception as e:
            logger.error(f"Failed to create migration report: {e}")


def main():
    """Main migration function"""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate Pharmacy Management v1.0 to v2.0")
    parser.add_argument("--v1-db", required=True, help="Path to v1.0 database file")
    parser.add_argument("--backup-dir", default="migration_backups", help="Backup directory")
    parser.add_argument("--force", action="store_true", help="Force migration even if v2 database exists")

    args = parser.parse_args()

    # Setup logging
    logger.add("migration.log", level="INFO")

    # Check if v2 database already exists
    v2_db_exists = os.path.exists("pharmacy.db")
    if v2_db_exists and not args.force:
        print("V2 database already exists. Use --force to overwrite.")
        sys.exit(1)

    # Run migration
    migrator = V1ToV2Migrator(args.v1_db, args.backup_dir)
    success = migrator.run_migration()

    if success:
        print("✓ Migration completed successfully!")
        print(f"Backup directory: {args.backup_dir}")
        print("You can now run the v2.0 application with your migrated data.")
    else:
        print("✗ Migration failed!")
        print("Check migration.log and the migration report for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
