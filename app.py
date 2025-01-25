import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTabWidget, QRadioButton, QGroupBox, QFormLayout,
                             QMessageBox, QTextEdit, QScrollArea, QDateEdit, QComboBox, QMenuBar, QAction,
                             QFileDialog, QDateTimeEdit, QDialog, QDialogButtonBox, QCompleter, QTableWidget, QTableWidgetItem, QSizePolicy,QToolBar, QAction,QCheckBox)
from PyQt5.QtCore import Qt, QDate, QTimer,QPropertyAnimation,QSize,QSettings,QFile, QTextStream
from PyQt5.QtGui import QIcon, QFont,QTextListFormat,QDoubleValidator,QPalette
import subprocess
import platform
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display
from weasyprint import HTML, CSS
import os

   
   
def prepare_arabic_text(self, text):
        """Reshapes and reorders Arabic text for correct display."""
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        return bidi_text

def resource_path(relative_path):
    """Get the absolute path to a resource within the 'resources' folder."""
    try:
        # PyInstaller stores files in a temporary folder _MEIPASS when packaged
        base_path = sys._MEIPASS
    except AttributeError:
        # Fallback to current directory for development environment
        base_path = os.path.abspath(".")

    # Construct full path
    full_path = os.path.join(base_path, 'resources', relative_path)

    # Only return the path if the file or directory exists, otherwise return None
    if os.path.exists(full_path):
        return full_path
    else:
        return None

# Example for loading fonts and styles:
font_regular = resource_path("fonts/NotoSansArabic-Regular.ttf")
font_bold = resource_path("fonts/NotoSansArabic-Bold.ttf")
stylesheet_light = resource_path("styles/light_styles.qss")
stylesheet_dark = resource_path("styles/dark_styles.qss")

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        # Initialize settings for saving credentials
        self.settings = QSettings("YourAppName", "LoginSettings")
        # Create layout
        layout = QVBoxLayout()

        # Username and Password fields
        self.username_input = QLineEdit(self)
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        # "Remember Me" checkbox
        self.remember_checkbox = QCheckBox("Remember me", self)

        # Login Button
        login_button = QPushButton("Login", self)
        login_button.clicked.connect(self.check_login)

        # Add widgets to layout
        layout.addWidget(QLabel("Please log in"))
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.remember_checkbox)
        layout.addWidget(login_button)

        self.setLayout(layout)
        self.load_credentials()

    def check_login(self):
        """Check the login credentials."""
        username = self.username_input.text()
        password = self.password_input.text()

        if username == "admin" and password == "a2024":
            if self.remember_checkbox.isChecked():
                self.save_credentials(username, password)
            else:
                self.clear_credentials()

            self.accept()  # Close the dialog if login is successful
        else:
            QMessageBox.warning(self, "Error", "Invalid username or password")
    def save_credentials(self, username, password):
        """Save the username and password using QSettings."""
        self.settings.setValue("username", username)
        self.settings.setValue("password", password)
        self.settings.setValue("remember", True)

    def load_credentials(self):
        """Load saved username and password if 'Remember me' was checked."""
        remember = self.settings.value("remember", False, type=bool)
        if remember:
            username = self.settings.value("username", "")
            password = self.settings.value("password", "")
            self.username_input.setText(username)
            self.password_input.setText(password)
            self.remember_checkbox.setChecked(True)

    def clear_credentials(self):
        """Clear saved username and password."""
        self.settings.remove("username")
        self.settings.remove("password")
        self.settings.setValue("remember", False)



        
class ClientSelectionDialog(QDialog):
    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle("العملاء المسجلين")

        # Fetch all registered clients from the database
        cur = self.main_window.conn.cursor()
        cur.execute("SELECT client_pharmacy_id, client_name FROM general_info")
        self.clients = cur.fetchall()

        # Create a table to display client data
        self.table = QTableWidget()
        self.table.setRowCount(len(self.clients))
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["رقم العميل", "اسم العميل"])  # "Client ID", "Client Name"

        # Populate the table with client data
        for i, (client_id, client_name) in enumerate(self.clients):
            self.table.setItem(i, 0, QTableWidgetItem(str(client_id)))  # Client ID
            self.table.setItem(i, 1, QTableWidgetItem(client_name))  # Client Name

        # Allow selection of rows
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        # Layout and buttons
        layout = QVBoxLayout()
        layout.addWidget(self.table)

        # Add a "Select Client" button to choose a client and load their data
        select_button = QPushButton("اختيار العميل")  # "Select Client"
        select_button.clicked.connect(self.select_client)
        layout.addWidget(select_button)

        # Set layout
        self.setLayout(layout)

    def keyPressEvent(self, event):
        """Handle the Enter key to select the client."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.select_client()

    def select_client(self):
        """Handle the event when a client is selected."""
        selected_row = self.table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "خطأ", "يرجى اختيار عميل.")  # "Please select a client."
            return

        # Get the selected client's ID and name
        client_id = self.table.item(selected_row, 0).text()
        client_name = self.table.item(selected_row, 1).text()

        # Close the dialog after selection
        self.accept()

        # Populate the form with the selected client's data
        self.main_window.populate_client_by_id(client_id)
    


class RandomPDFDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("توليد PDF عشوائي")
        self.setMinimumSize(400, 300)

        # Layout for the dialog
        layout = QVBoxLayout()

        # Form layout for the 5 meals
        form_layout = QFormLayout()
        self.random_breakfast_input = QLineEdit()
        self.random_lunch_input = QLineEdit()
        self.random_dinner_input = QLineEdit()
        self.random_snack1_input = QLineEdit()
        self.random_snack2_input = QLineEdit()

        form_layout.addRow("الإفطار:", self.random_breakfast_input)
        form_layout.addRow("الغداء:", self.random_lunch_input)
        form_layout.addRow("العشاء:", self.random_dinner_input)
        form_layout.addRow("وجبة خفيفة 1:", self.random_snack1_input)
        form_layout.addRow("وجبة خفيفة 2:", self.random_snack2_input)

        # Button to generate random PDF
        generate_pdf_button = QPushButton("توليد PDF")
        generate_pdf_button.clicked.connect(self.confirm_generate_pdf)

        # Add widgets to layout
        layout.addLayout(form_layout)
        layout.addWidget(generate_pdf_button)

        # Set layout
        self.setLayout(layout)

    def confirm_generate_pdf(self):
        """Shows a confirmation prompt to the user before generating the PDF."""
        confirmation = QMessageBox.question(
            self,
            "تأكيد",
            "هل تريد توليد PDF بهذه الوجبات؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirmation == QMessageBox.Yes:
            self.generate_random_pdf()

    def generate_random_pdf(self):
        """Generates a random PDF with the entered 5 meals using WeasyPrint."""
        # Get the meal data from the text inputs
        breakfast = self.random_breakfast_input.text().strip()
        lunch = self.random_lunch_input.text().strip()
        dinner = self.random_dinner_input.text().strip()
        snack1 = self.random_snack1_input.text().strip()
        snack2 = self.random_snack2_input.text().strip()

        # Define the PDF file path
        pdf_output, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ PDF عشوائي",
            f"random_meals_{datetime.now().strftime('%Y-%m-%d')}.pdf",  # Default file name: random_meals_date.pdf
            "PDF Files (*.pdf)"
        )

        if not pdf_output:
            return

        # Generate HTML content
        html_content = self.build_html_content(breakfast, lunch, dinner, snack1, snack2)

        # Define paths to fonts inside resources/fonts
        font_path_regular = resource_path(os.path.join('fonts', 'NotoSansArabic-Regular.ttf'))
        font_path_bold = resource_path(os.path.join('fonts', 'NotoSansArabic-Bold.ttf'))

        # Debugging: Print font paths
        print(f"Regular Font Path: {font_path_regular}")
        print(f"Bold Font Path: {font_path_bold}")

        # Check if font files exist
        fonts_exist = True
        missing_fonts = []
        if not font_path_regular:
            fonts_exist = False
            missing_fonts.append('NotoSansArabic-Regular.ttf')
        if not font_path_bold:
            fonts_exist = False
            missing_fonts.append('NotoSansArabic-Bold.ttf')

        if not fonts_exist:
            missing = ', '.join(missing_fonts)
            QMessageBox.warning(
                self,
                "خطأ",
                f"لم يتم العثور على ملفات الخطوط المطلوبة في مجلد الموارد: {missing}."
            )
            return

        # Define CSS for styling
        css = CSS(string=f"""
            @font-face {{
                font-family: 'NotoSansArabic';
                src: url('file://{font_path_regular}') format('truetype');
                font-weight: normal;
                font-style: normal;
            }}
            @font-face {{
                font-family: 'NotoSansArabic';
                src: url('file://{font_path_bold}') format('truetype');
                font-weight: bold;
                font-style: normal;
            }}
            body {{
                font-family: 'NotoSansArabic', sans-serif;
                direction: rtl;
                text-align: right;
                padding: 50px;
            }}
            h1 {{
                font-size: 24px;
                text-align: center;
            }}
            h2 {{
                font-size: 20px;
                margin-top: 30px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            th, td {{
                border: 1px solid #000;
                padding: 8px;
                font-size: 14px;
            }}
            th {{
                background-color: #f2f2f2;
            }}
        """)

        # Generate PDF
        try:
            HTML(string=html_content).write_pdf(pdf_output, stylesheets=[css])
            QMessageBox.information(self, "تم الحفظ", f"تم حفظ التقرير إلى {pdf_output}")  # Report saved successfully
            self.accept()  # Close the dialog after successful PDF generation
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في حفظ التقرير: {e}")  # Failed to save report

    def build_html_content(self, breakfast, lunch, dinner, snack1, snack2):
        """Builds the HTML content for the PDF."""
        title = "تقرير غذائي مخصص"
        meals_title = "وجبات اليوم"
        meals = [
            ("الإفطار", breakfast),
            ("الغداء", lunch),
            ("العشاء", dinner),
            ("وجبة خفيفة 1", snack1),
            ("وجبة خفيفة 2", snack2),
        ]

        # Construct HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
        </head>
        <body>
            <h1>{title}</h1>
            <h2>{meals_title}</h2>
            <table>
                <thead>
                    <tr>
                        <th>الوجبة</th>
                        <th>التفاصيل</th>
                    </tr>
                </thead>
                <tbody>
        """

        for meal_name, meal_detail in meals:
            html += f"""
                    <tr>
                        <td>{meal_name}</td>
                        <td>{meal_detail}</td>
                    </tr>
            """

        html += """
                </tbody>
            </table>
        </body>
        </html>
        """

        return html
class MainWindow(QMainWindow):
    def __init__(self):

        # Show login dialog before initializing the main window
        login_dialog = LoginDialog()
        if login_dialog.exec_() == QDialog.Accepted:
                super().__init__()  
                #self.init_ui()  
        else:
            sys.exit()  # Exit if the login is not successful
    
    
        # Initialize dark mode state based on system theme
        self.load_stylesheet()          
        self.current_client_id = None  # To track the current client being edited
        # Set up the database
        self.conn = sqlite3.connect("pharmacy.db")
        self.create_tables()
        #self.add_missing_columns()
        self.update_general_info_table()  # Call this to ensure 'age' column exists        
         # Initialize cache for client search results
        self.client_cache = {}
        self.cached_stylesheet_light = None
        self.cached_stylesheet_dark = None
        self.dark_mode = False


        self.setWindowTitle("Dr.Abaza Pharmacy")
        self.setGeometry(100, 100, 1200, 800)
        # Set the window icon
        icon_path = resource_path('app_icon.ico')
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        else:
            print("Icon file not found.")

        # Initialize dark mode state
        #self.dark_mode = self.detect_system_theme()
        # Apply RTL layout to the whole application
        self.setLayoutDirection(Qt.RightToLeft)
    


        # Load the QSS file
        self.load_stylesheet()
                
        # Initialize dark mode state
        # Main layout to hold menu bar and main widget
        main_layout = QVBoxLayout()

        # Menu Bar for File, Edit, and View
        self.menu_bar = self.menuBar()
        self.create_menu()

         # Search bar for client name or ID
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("بحث عن العميل برقم العميل أو اسم العميل")
         # Connect the Enter key to trigger search
        self.search_input.returnPressed.connect(self.search_client) 
        # Trigger search on button click
        search_button = QPushButton("بحث")
        search_button.clicked.connect(self.search_client)

        # Initialize autocomplete
        self.init_autocomplete() 
        # Add the search bar at the top of the main window
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("البحث:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)

        main_layout.addLayout(search_layout)

        # Tabs 
        self.tabs = QTabWidget()
        self.general_info_tab = QWidget()
        self.diet_tab = QWidget()
        self.notes_tab = QWidget()

        self.tabs.addTab(self.general_info_tab, "معلومات عامة")
        self.tabs.addTab(self.diet_tab, "الحمية")
        self.tabs.addTab(self.notes_tab, "الملاحظات")
    
        
        main_layout.addWidget(self.tabs)
        
        


        # Set main layout
        main_widget = QWidget()
        main_widget.setLayout(main_layout)


        # Create a scroll area and set the main widget inside it
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(main_widget)  

        # Set the scroll area as the central widget of the main window
        self.setCentralWidget(scroll_area)

        # Initialize tabs
        self.init_general_info_tab()
        self.init_diet_tab()
        self.init_notes_tab()
        # Add BMI calculation on pressing Enter in Current Weight
        self.current_weight_input.returnPressed.connect(self.calculate_bmi)
        #reminder
        self.check_follow_up_dates()

    def detect_system_theme(self):
        if platform.system() == 'Windows':
            try:
                settings = QSettings("HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize", QSettings.NativeFormat)
                is_light_mode = settings.value("AppsUseLightTheme", 1)
                return 'light' if is_light_mode == 1 else 'dark'
            except KeyError:
                return 'light'
        else:
            return 'light'  # non-windows

    def load_stylesheet(self):
        """Loads and applies the QSS stylesheet to the application."""
        try:
            system_theme = self.detect_system_theme()
            
            # Cache light and dark stylesheets
            if system_theme == 'light':
                if not self.cached_stylesheet_light:
                    with open(stylesheet_light, "r", encoding='utf-8') as file:
                        self.cached_stylesheet_light = file.read()
                self.setStyleSheet(self.cached_stylesheet_light)
            else:
                if not self.cached_stylesheet_dark:
                    with open(stylesheet_dark, "r", encoding='utf-8') as file:
                        self.cached_stylesheet_dark = file.read()
                self.setStyleSheet(self.cached_stylesheet_dark)
        except Exception as e:
            print(f"Error loading stylesheet: {e}")




    def open_random_pdf_window(self):
        """Opens the dialog for generating a random PDF with 5 meals."""
        dialog = RandomPDFDialog(self)
        dialog.exec_()

    
    def set_custom_font(self):
        arabic_font = QFont("NotoSansArabic-Regular", 12)  # Use a font that supports Arabic, like Arial or Noto Sans Arabic
        self.diet_suggestions_text.setFont(arabic_font)
        self.general_advice_text.setFont(arabic_font)
    
    def refresh_autocomplete(self):
        """Refreshes the autocomplete list with current client names and IDs."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT client_name FROM general_info")
            client_names = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT client_pharmacy_id FROM general_info")
            client_ids = [row[0] for row in cur.fetchall()]
            self.completer.model().setStringList(client_names + client_ids)
        except Exception as e:
            print(f"Error refreshing autocomplete: {e}")

    def setup_database(self):
        """Checks if the database exists and sets up a new one if it doesn't."""
        db_path = "pharmacy.db"
        db_exists = os.path.exists(db_path)

        # Connect to the database (or create it if it does not exist)
        self.conn = sqlite3.connect(db_path)

        # If the database file didn't exist, create the necessary tables
        if not db_exists:
            self.create_tables()

    def create_tables(self):
        try:    
            cur = self.conn.cursor()
            cur.execute('''CREATE TABLE IF NOT EXISTS general_info (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_name TEXT,
                        client_pharmacy_id TEXT UNIQUE,  -- Make this field unique
                        age INTEGER,
                        job TEXT,
                        address TEXT,
                        phone TEXT,
                        work_effort TEXT,
                        diseases TEXT,
                        previous_attempts TEXT,
                        current_treatment TEXT,
                        visit_purpose TEXT,
                        follow_up_date TEXT)''')


            cur.execute('''CREATE TABLE IF NOT EXISTS diet_info (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            client_id INTEGER,
                            height REAL,
                            fat_percentage REAL,
                            muscle_percentage REAL,
                            water_percentage REAL,
                            mineral_percentage REAL,
                            current_weight REAL,
                            previous_weight REAL,
                            weight_category TEXT,
                            weight_condition TEXT,
                            breakfast TEXT,
                            lunch TEXT,
                            dinner TEXT,
                            snack_1 TEXT,
                            snack_2 TEXT,
                            bmi REAL,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(client_id) REFERENCES general_info(id))''')

            cur.execute('''CREATE TABLE IF NOT EXISTS notes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            client_id INTEGER,
                            client_notes TEXT,
                            FOREIGN KEY(client_id) REFERENCES general_info(id))''')

            
            self.conn.commit()
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Database Error", f"Error creating tables: {e}")



    def show_registered_clients(self):
        """Opens a new window to display all registered clients with their names and IDs."""
        dialog = ClientSelectionDialog(self, main_window=self)
        dialog.exec_()

    def update_general_info_table(self):
        """Adds the age column to the general_info table if it doesn't exist."""
        cur = self.conn.cursor()
        try:
            cur.execute('''ALTER TABLE general_info ADD COLUMN age INTEGER''')
        except sqlite3.OperationalError:
            print("Column 'age' already exists, skipping ALTER.")

   
    def generate_client_id(self):
        """Generates the next available client pharmacy ID."""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT MAX(CAST(client_pharmacy_id AS INTEGER)) FROM general_info")
            max_id = cur.fetchone()[0]
            new_id = (int(max_id) + 1) if max_id else 1
            if new_id > 10000:
                QMessageBox.warning(self, "خطأ", "تم الوصول إلى الحد الأقصى لعدد العملاء.")  # Maximum number of clients reached.
                return
            self.client_pharmacy_id_input.setText(f"{new_id:05d}")  # Format as 5-digit ID
        except sqlite3.Error as e:
            QMessageBox.warning(self, "خطأ", f"فشل في توليد رقم العميل: {e}")  # Failed to generate client ID

    
    def new_client(self):
        """Creates a new client in the database."""
        self.clear_all_fields()
        self.generate_client_id()  # Generate the next available client ID
        QMessageBox.information(self, "عميل جديد", "يمكنك الآن إدخال بيانات العميل الجديد.")



    def generate_client_id_on_name_change(self):
        """Generate a client pharmacy ID dynamically when the name changes."""
        if self.client_name_input.text():  # Only generate if there is some name
            cur = self.conn.cursor()
            cur.execute("SELECT MAX(CAST(client_pharmacy_id AS INTEGER)) FROM general_info")
            max_id = cur.fetchone()[0]
            new_id = (int(max_id) + 1) if max_id else 1
            if new_id > 10000:
                QMessageBox.warning(self, "خطأ", "تم الوصول إلى الحد الأقصى لعدد العملاء.")
                return
            self.client_pharmacy_id_input.setText(f"{new_id:05d}")  # Update the ID input field


    def populate_client_by_id(self, client_id):
        """Populates the client data in the form based on the selected client ID."""
        cur = self.conn.cursor()
        cur.execute('''SELECT * FROM general_info WHERE client_pharmacy_id = ?''', (client_id,))
        client = cur.fetchone()

        if client:
            self.current_client_id = client_id  # Set the current client ID for tracking
            self.populate_client_info(client)  # Populate all fields using existing method
        else:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على بيانات العميل.")  # "Client data not found."



    def create_menu(self):
        """Creates the File, Edit, and View menu with options."""
        # File Menu
        file_menu = self.menu_bar.addMenu("ملف")  # File -> ملف

        # Save Client action
        save_action = QAction("حفظ", self)  # Save -> حفظ
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_diet_info)
        file_menu.addAction(save_action)

        # New Client action
        new_client_action = QAction("عميل جديد", self)  # New Client -> عميل جديد
        new_client_action.triggered.connect(self.new_client)
        file_menu.addAction(new_client_action)
        new_client_action.setShortcut("Ctrl+N")

        
        # Clear All Fields action
        clear_fields_action = QAction("مسح جميع الحقول", self)  # Clear All Fields -> مسح جميع الحقول
        clear_fields_action.setShortcut("Ctrl+L")
        clear_fields_action.triggered.connect(self.clear_all_fields)  # Connect the action to clear_all_fields
        file_menu.addAction(clear_fields_action)

        # Remove Client action
        remove_client_action = QAction("حذف عميل", self)  # Remove Client -> حذف عميل
        remove_client_action.triggered.connect(self.remove_client)
        file_menu.addAction(remove_client_action)
        remove_client_action.setShortcut("Ctrl+D")

        export_data_action = QAction("تصدير البيانات", self)
        export_data_action.triggered.connect(self.export_data)
        file_menu.addAction(export_data_action)


        # Edit Menu -> تعديل
        edit_menu = self.menu_bar.addMenu("تعديل")

        # Save Database action
        save_db_action = QAction("حفظ قاعدة البيانات", self)  # Save Database -> حفظ قاعدة البيانات
        save_db_action.triggered.connect(self.save_database)
        edit_menu.addAction(save_db_action)

        # Load Database action
        load_db_action = QAction("تحميل قاعدة البيانات", self)  # Load Database -> تحميل قاعدة البيانات
        load_db_action.triggered.connect(self.load_database)
        edit_menu.addAction(load_db_action)

        # View Menu -> العرض
        view_menu = self.menu_bar.addMenu("العرض")

        # Generate PDF Report
        pdf_report_action = QAction("تقرير PDF", self)  # PDF Report -> تقرير PDF
        pdf_report_action.triggered.connect(self.generate_pdf_report)
        view_menu.addAction(pdf_report_action)
        # Generate Random PDF action
        random_pdf_action = QAction("توليد PDF عشوائي", self)  # Random PDF -> توليد PDF عشوائي
        random_pdf_action.triggered.connect(self.open_random_pdf_window)
        view_menu.addAction(random_pdf_action)

        # Toggle Dark Mode
        toggle_theme_action = QAction("تبديل الوضع الداكن", self)  # Toggle Dark Mode
        toggle_theme_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(toggle_theme_action)
        
        # Clients Menu -> العملاء
        clients_menu = self.menu_bar.addMenu("العملاء")  # "Clients" menu

        # Show Registered Clients action -> عرض العملاء المسجلين
        show_clients_action = QAction("عرض العملاء المسجلين", self)
        show_clients_action.triggered.connect(self.show_registered_clients)
        clients_menu.addAction(show_clients_action)
        show_clients_action.setShortcut("Ctrl+P")

    def fetch_clients(self):
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT client_pharmacy_id, client_name FROM general_info")
            return cur.fetchall()
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Database Error", f"Error fetching clients: {e}")
            return []


    def get_diet_suggestions_and_advice(self, bmi):
        try:
            bmi = float(bmi)
        except ValueError:
            return "", ""  # Handle invalid input

        if bmi < 18.5:
            suggestions = (
                "• زيادة السعرات الحرارية بشكل معتدل.\n"
                "• تناول وجبات صغيرة متكررة.\n"
                "• التركيز على البروتينات الصحية مثل اللحوم والأسماك.\n"
                "• تناول المكسرات والأفوكادو."
            )
            advice = (
                "• من المهم زيادة الوزن بشكل صحي لتجنب نقص العناصر الغذائية.\n"
                "• استشر أخصائي تغذية لتخطيط نظام غذائي مناسب."
            )
        elif 18.5 <= bmi < 25:
            suggestions = (
                "• الحفاظ على نظام غذائي متوازن.\n"
                "• تناول الفواكه والخضروات بكميات كافية.\n"
                "• ممارسة الرياضة بانتظام."
            )
            advice = (
                "• حافظ على وزنك الحالي من خلال اتباع نمط حياة صحي.\n"
                "• متابعة الفحوصات الدورية لضمان الصحة العامة."
            )
        elif 25 <= bmi < 30:
            suggestions = (
                "• تقليل تناول الدهون المشبعة والسكريات.\n"
                "• زيادة تناول الألياف مثل الحبوب الكاملة والخضروات.\n"
                "• ممارسة التمارين الرياضية بانتظام."
            )
            advice = (
                "• العمل على فقدان الوزن الزائد لتحسين الصحة.\n"
                "• استشر أخصائي تغذية لوضع خطة غذائية مناسبة."
            )
        else:
            suggestions = (
                "• اتباع نظام غذائي منخفض السعرات والدهون.\n"
                "• زيادة النشاط البدني بشكل منتظم.\n"
                "• تناول وجبات متوازنة تحتوي على البروتين والخضروات."
            )
            advice = (
                "• من الضروري فقدان الوزن لتقليل مخاطر الأمراض المزمنة.\n"
                "• استشر طبيب أو أخصائي تغذية لوضع خطة شاملة."
            )

        # Return the plain suggestions and advice text
        return suggestions, advice

    def export_data(self):
        """Exports general info data to a CSV file."""
        export_path, _ = QFileDialog.getSaveFileName(self, "تصدير البيانات", "", "CSV Files (*.csv)")
        
        if not export_path:
            return

        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM general_info")
            data = cur.fetchall()
            headers = [description[0] for description in cur.description]

            # Writing to CSV
            with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(data)
            
            QMessageBox.information(self, "تم التصدير", f"تم تصدير البيانات إلى {export_path}")

        except (IOError, PermissionError) as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تصدير البيانات: {e}")


    def remove_client(self):
        """Removes the current client from the database."""
        client_id = self.get_current_client_id()
        if not client_id:
            QMessageBox.warning(self, "خطأ", "لم يتم تحديد عميل للحذف.")  # No client selected
            return

        reply = QMessageBox.question(self, "تأكيد الحذف", "هل أنت متأكد أنك تريد حذف هذا العميل؟",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                cur = self.conn.cursor()
                # Delete from diet_info
                cur.execute('DELETE FROM diet_info WHERE client_id = ?', (client_id,))
                # Delete from notes
                cur.execute('DELETE FROM notes WHERE client_id = ?', (client_id,))
                # Delete from general_info
                cur.execute('DELETE FROM general_info WHERE id = ?', (client_id,))
                self.conn.commit()
                QMessageBox.information(self, "تم الحذف", "تم حذف العميل بنجاح.")
                self.clear_all_fields()
                self.refresh_autocomplete()
            except Exception as e:
                QMessageBox.warning(self, "خطأ", f"فشل في حذف العميل: {e}")

    
    def save_diet_info(self):
        """Saves the current client's general info, diet info, and notes to the database.
        If the client exists, it updates the data; otherwise, it creates a new record."""

        try:
            # 1. Validate and save general info
            client_id = self._save_general_info()
            if client_id is None:
                return

            # 2. Process and save diet info
            if not self._save_diet_info(client_id):
                return

            # 3. Save notes
            self._save_notes(client_id)

        except Exception as e:
            QMessageBox.warning(self, "خطأ غير متوقع", f"حدث خطأ غير متوقع: {str(e)}")

    def _save_general_info(self):
        """Helper method to save general client information."""
        try:
            # Retrieve and sanitize input data
            client_data = {
                'name': self.client_name_input.text().strip(),
                'pharmacy_id': self.client_pharmacy_id_input.text().strip(),
                'age': self.age_input.text().strip(),
                'job': self.job_input.text().strip(),
                'address': self.address_input.text().strip(),
                'phone': self.phone_input.text().strip(),
                'work_effort': self.work_effort_input.text().strip(),
                'diseases': self.diseases_input.text().strip(),
                'previous_attempts': self.previous_attempts_input.text().strip(),
                'current_treatment': self.current_treatment_input.text().strip(),
                'visit_purpose': self.visit_purpose_input.text().strip(),
                'follow_up_date': self.follow_up_date_input.date().toString('yyyy-MM-dd')
            }

            # Validate required fields
            required_fields = ['name', 'age', 'phone', 'address', 'visit_purpose']
            if not all(client_data[field] for field in required_fields):
                QMessageBox.warning(self, "خطأ", "يرجى ملء جميع الحقول المطلوبة.")
                return None

            try:
                client_data['age'] = int(client_data['age'])
            except ValueError:
                QMessageBox.warning(self, "خطأ", "يرجى إدخال عمر صحيح.")
                return None

            cur = self.conn.cursor()
            
            # Check if client exists
            cur.execute('''SELECT id FROM general_info WHERE client_name = ? OR client_pharmacy_id = ?''',
                    (client_data['name'], client_data['pharmacy_id']))
            existing_client = cur.fetchone()

            if existing_client:
                client_id = existing_client[0]
                cur.execute('''UPDATE general_info 
                            SET client_name = ?, client_pharmacy_id = ?, age = ?, job = ?, 
                                address = ?, phone = ?, work_effort = ?, diseases = ?, 
                                previous_attempts = ?, current_treatment = ?, visit_purpose = ?, 
                                follow_up_date = ?
                            WHERE id = ?''',
                        (*[client_data[k] for k in client_data.keys()], client_id))
            else:
                cur.execute('''INSERT INTO general_info 
                            (client_name, client_pharmacy_id, age, job, address, phone, 
                            work_effort, diseases, previous_attempts, current_treatment, 
                            visit_purpose, follow_up_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        tuple(client_data.values()))
                client_id = cur.lastrowid

            self.conn.commit()
            return client_id

        except sqlite3.Error as e:
            QMessageBox.warning(self, "خطأ في قاعدة البيانات", f"حدث خطأ أثناء حفظ البيانات العامة: {str(e)}")
            return None

    def _save_diet_info(self, client_id):
        """Helper method to save diet information only if changes are detected."""
        try:
            # Get current measurements
            measurements = self._get_measurements()
            if not measurements:
                return False

            # Get current meals from the input fields
            current_meals = {
                'breakfast': self.breakfast_input.text().strip(),
                'lunch': self.lunch_input.text().strip(),
                'dinner': self.dinner_input.text().strip(),
                'snack_1': self.snack1_input.text().strip(),
                'snack_2': self.snack2_input.text().strip()
            }

            cur = self.conn.cursor()

            # Fetch the latest saved meals for the client
            cur.execute('''
                SELECT breakfast, lunch, dinner, snack_1, snack_2 
                FROM diet_info 
                WHERE client_id = ? 
                ORDER BY timestamp DESC LIMIT 1
            ''', (client_id,))
            last_meals = cur.fetchone()

            # Check if the current meal inputs differ from the latest saved meals
            if last_meals:
                last_meals = tuple("" if meal is None else meal for meal in last_meals)
                if tuple(current_meals.values()) == last_meals:
                    print("No changes detected in meal data. Skipping save.")
                    return False


            # Fetch the latest record for the previous weight
            cur.execute('''SELECT current_weight FROM diet_info 
                        WHERE client_id = ? 
                        ORDER BY timestamp DESC LIMIT 1''', (client_id,))
            last_record = cur.fetchone()

            if last_record:
                previous_weight = float(last_record[0]) if last_record and last_record[0] is not None else measurements['current_weight']
                self.previous_weight_input.setText(str(previous_weight))
            else:
                previous_weight = measurements['current_weight']

            # Calculate BMI
            bmi = None
            if measurements['height'] and measurements['current_weight']:
                bmi = round(measurements['current_weight'] / ((measurements['height'] / 100) ** 2), 2)
                self.bmi_display.setText(str(bmi))
                self.update_bmi_color(bmi)

            # Insert new diet info into the database since changes were detected
            cur.execute('''INSERT INTO diet_info 
                        (client_id, height, fat_percentage, muscle_percentage, 
                        water_percentage, mineral_percentage, current_weight, 
                        previous_weight, weight_category, weight_condition, 
                        breakfast, lunch, dinner, snack_1, snack_2, bmi, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
                        (client_id, measurements['height'], measurements['fat_percentage'],
                        measurements['muscle_percentage'], measurements['water_percentage'],
                        measurements['mineral_percentage'], measurements['current_weight'],
                        previous_weight,
                        "صغار" if self.radio_small.isChecked() else "كبار",
                        "سمنة" if self.obesity_checkbox.isChecked() else "نحافة",
                        current_meals['breakfast'], current_meals['lunch'], current_meals['dinner'],
                        current_meals['snack_1'], current_meals['snack_2'], bmi))

            self.conn.commit()
            self.update_meal_log(client_id)
            QMessageBox.information(self, "تم الحفظ", "تم حفظ بيانات الحمية بنجاح!")
            return True

        except sqlite3.Error as e:
            QMessageBox.warning(self, "خطأ في قاعدة البيانات", f"حدث خطأ أثناء حفظ بيانات الحمية: {str(e)}")
            return False


    def update_meal_log(self, client_id):
        """Updates the meal log display with the latest meals."""
        try:
            cur = self.conn.cursor()
            
            # Fetch all meal records for this client, ordered by timestamp
            cur.execute('''
                SELECT 
                    strftime('%Y-%m-%d %H:%M', timestamp) as formatted_time,
                    breakfast, lunch, dinner, snack_1, snack_2
                FROM diet_info 
                WHERE client_id = ? 
                ORDER BY timestamp DESC
                LIMIT 10
            ''', (client_id,))
            
            meals = cur.fetchall()
            
            # Clear the existing meal log
            self.clear_past_meals()
  
            
            # Format and display each meal record
            for meal in meals:
                timestamp, breakfast, lunch, dinner, snack1, snack2 = meal
                
                meal_text = (
                    f"=== {timestamp} ===\n"
                    f"الفطور: {breakfast}\n"
                    f"الغداء: {lunch}\n"
                    f"العشاء: {dinner}\n"
                )
                
                if snack1:
                    meal_text += f"وجبة خفيفة 1: {snack1}\n"
                if snack2:
                    meal_text += f"وجبة خفيفة 2: {snack2}\n"
                    
                meal_text += "\n"  # Add extra newline for spacing between records
                
                label = QLabel(meal_text)   
                label.setWordWrap(True)     
                self.past_meals_layout.addWidget(label)  


        except sqlite3.Error as e:
            QMessageBox.warning(self, "خطأ", 
                            f"حدث خطأ أثناء تحديث سجل الوجبات: {str(e)}")        

    def _get_measurements(self):
        """Helper method to get and validate measurements."""
        try:
            measurements = {
                'height': self.height_input.text().strip(),
                'current_weight': self.current_weight_input.text().strip(),
                'fat_percentage': self.fat_percentage_input.text().strip(),
                'muscle_percentage': self.muscle_percentage_input.text().strip(),
                'water_percentage': self.water_percentage_input.text().strip(),
                'mineral_percentage': self.mineral_percentage_input.text().strip(),
                'previous_weight': self.previous_weight_input.text().strip()
            }

            # Convert string values to float where needed
            for key in measurements:
                measurements[key] = float(measurements[key]) if measurements[key] else None

            return measurements

        except ValueError:
            QMessageBox.warning(self, "خطأ", "يرجى إدخال قيم صحيحة للوزن والقياسات.")
            return None

    def _save_notes(self, client_id):
        """Helper method to save client notes."""
        try:
            notes = self.notes_input.toHtml().strip()
            if notes:
                cur = self.conn.cursor()
                cur.execute('''INSERT INTO notes (client_id, client_notes) 
                            VALUES (?, ?)''', (client_id, notes))
                self.conn.commit()

        except sqlite3.Error as e:
            QMessageBox.warning(self, "خطأ في قاعدة البيانات", 
                            f"حدث خطأ أثناء حفظ الملاحظات: {str(e)}")

    def save_database(self):
        """Saves the current database to a file using VACUUM INTO or fallback to file copy."""
        try:
            # Get save location from user
            db_path, _ = QFileDialog.getSaveFileName(
                self, 
                "حفظ قاعدة البيانات",  # Save Database
                f"nutrition_backup_{QDate.currentDate().toString('yyyy-MM-dd')}.db",  # Default filename with date
                "SQLite Database (*.db)"
            )
            
            if not db_path:
                return
                
            # Ensure file extension is .db
            if not db_path.endswith('.db'):
                db_path += '.db'
                
            # Commit any pending changes
            self.conn.commit()
            
            try:
                # Try VACUUM INTO first (faster and more reliable)
                self.conn.execute(f"VACUUM INTO '{db_path}'")
            except sqlite3.OperationalError:
                # Fallback to file copy if VACUUM INTO is not supported
                import shutil
                current_db_path = os.path.join(os.path.dirname(__file__), 'nutrition.db')
                shutil.copy2(current_db_path, db_path)
                
            QMessageBox.information(
                self, 
                "نجاح",  # Success
                f"تم حفظ قاعدة البيانات بنجاح إلى:\n{db_path}"  # Database saved successfully to:
            )
                
        except sqlite3.Error as e:
            QMessageBox.critical(
                self, 
                "خطأ في قاعدة البيانات",  # Database Error
                f"فشل في حفظ قاعدة البيانات:\n{str(e)}"  # Failed to save database
            )
        except OSError as e:
            QMessageBox.critical(
                self, 
                "خطأ في النظام",  # System Error
                f"فشل في الوصول إلى الملف:\n{str(e)}"  # Failed to access file
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "خطأ غير متوقع",  # Unexpected Error
                f"حدث خطأ غير متوقع أثناء حفظ قاعدة البيانات:\n{str(e)}"  # An unexpected error occurred while saving the database
            )


    
    def load_database(self):
        """Loads an existing database."""
        db_path, _ = QFileDialog.getOpenFileName(self, "تحميل قاعدة البيانات", "", "SQLite Database (*.db)")  # Load Database
        if db_path:
            try:
                self.conn.close()  # Close the current connection
                self.conn = sqlite3.connect(db_path)
                QMessageBox.information(self, "تم تحميل قاعدة البيانات", f"تم تحميل قاعدة البيانات من {db_path}")  # Database loaded
                self.create_tables()  # Ensure tables exist
            except sqlite3.Error as e:
                QMessageBox.warning(self, "خطأ", f"فشل في تحميل قاعدة البيانات: {e}")  # Failed to load database



    def register_fonts(self):
        """Registers Arabic-supporting fonts with ReportLab."""
        try:
            regular_font_path = resource_path('fonts/NotoSansArabic-Regular.ttf')
            bold_font_path = resource_path('fonts/NotoSansArabic-Bold.ttf')

            pdfmetrics.registerFont(TTFont('NotoSansArabic-Regular', regular_font_path))
            pdfmetrics.registerFont(TTFont('NotoSansArabic-Bold', bold_font_path))
        except Exception as e:
            QMessageBox.warning(self, "خطأ", f"فشل في تسجيل الخطوط: {e}")  # Failed to register fonts




    def generate_pdf_report(self):
        """Generates a PDF report of the current client's data with Arabic support using WeasyPrint."""
        client_id = self.get_current_client_id()
        if not client_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على العميل.")  # Error: Client not found
            return

        cur = self.conn.cursor()
        cur.execute('''SELECT * FROM general_info WHERE id = ?''', (client_id,))
        client_data = cur.fetchone()

        cur.execute('''SELECT * FROM diet_info WHERE client_id = ? ORDER BY timestamp DESC LIMIT 1''', (client_id,))
        diet_data = cur.fetchone()

        #client_data = self.get_client_data(client_id)
        #diet_data = self.get_diet_data(client_id)

        if not client_data or not isinstance(client_data[1], str):  # Adjust the check to ensure client name is valid
            QMessageBox.warning(self, "خطأ", "لا توجد بيانات عامة للعميل أو الاسم غير صالح.")  # No general data for client or invalid name
            return

        # Extract and sanitize client_name
        client_name = client_data[1].strip()  # Ensure the name is a string and strip any leading/trailing spaces
        today_date = datetime.now().strftime("%Y-%m-%d_%H-%M")  # Get today's date in YYYY-MM-DD format
        safe_client_name = client_name.replace(" ", "_")  # Replace spaces with underscores in the client name

        # Define PDF file path using the client's name and today's date
        pdf_output, _ = QFileDialog.getSaveFileName(
            self, 
            "حفظ تقرير PDF", 
            f"{safe_client_name}_{today_date}.pdf",  # Default file name: client_name_date.pdf
            "PDF Files (*.pdf)"
        )
        
        if not pdf_output:
            return

        # Define paths to fonts inside resources/fonts
        font_path_regular = resource_path(os.path.join('fonts', 'NotoSansArabic-Regular.ttf'))
        font_path_bold = resource_path(os.path.join('fonts', 'NotoSansArabic-Bold.ttf'))

        # Debugging: Print font paths (Consider using logging in production)
        print(f"Regular Font Path: {font_path_regular}")
        print(f"Bold Font Path: {font_path_bold}")

        # Check if font files exist
        fonts_exist = True
        missing_fonts = []
        if not font_path_regular:
            fonts_exist = False
            missing_fonts.append('NotoSansArabic-Regular.ttf')
        if not font_path_bold:
            fonts_exist = False
            missing_fonts.append('NotoSansArabic-Bold.ttf')

        if not fonts_exist:
            missing = ', '.join(missing_fonts)
            QMessageBox.warning(
                self,
                "خطأ",
                f"لم يتم العثور على ملفات الخطوط المطلوبة في مجلد الموارد: {missing}."
            )
            return

        # Build HTML content
        html_content = self.build_html_report(client_data, diet_data)

        # Define CSS for styling
        css = CSS(string=f"""
            @font-face {{
                font-family: 'NotoSansArabic';
                src: url('file://{font_path_regular}') format('truetype');
                font-weight: normal;
                font-style: normal;
            }}
            @font-face {{
                font-family: 'NotoSansArabic';
                src: url('file://{font_path_bold}') format('truetype');
                font-weight: bold;
                font-style: normal;
            }}
            @page {{
                size: A4;
                margin: 15mm;  /* Reduced margins to fit more content */
            }}
            body {{
                font-family: 'NotoSansArabic', sans-serif;
                direction: rtl;
                text-align: right;
                padding: 0;
                font-size: 12px;  /* Reduced base font size */
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                font-size: 10px;  /* Small font for follow-up date */
            }}
            h1 {{
                font-size: 20px;  /* Reduced font size */
                text-align: center;
                margin-bottom: 10px;
            }}
            h2 {{
                font-size: 16px;  /* Reduced font size */
                margin-top: 20px;
                margin-bottom: 8px;
                font-weight: bold;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 15px;
                font-size: 12px;  /* Reduced font size */
            }}
            th, td {{
                border: 1px solid #000;
                padding: 6px;  /* Reduced padding */
            }}
            th {{
                background-color: #f2f2f2;
                text-align: right;
                font-weight: bold;
            }}
            .section-title {{
                margin-top: 20px;
                margin-bottom: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            .content {{
                margin-bottom: 15px;
                font-size: 12px;
            }}
            /* Additional CSS to handle table direction */
            .left-to-right-table {{
                direction: rtl;
                margin-left: auto;  /* Align table to the right */
            }}
            /* Ensure images (if any) do not overflow */
            img {{
                max-width: 100%;
                height: auto;
            }}
            /* Avoid page breaks inside tables */
            table, tr, td, th {{
                page-break-inside: avoid;
            }}
            /* Control page breaks between sections */
            .section {{
                page-break-after: avoid;
                page-break-inside: avoid;
            }}
        """)

        # Generate PDF using WeasyPrint
        try:
            html_content = self.build_html_report(client_data, diet_data)
            HTML(string=html_content).write_pdf(pdf_output)
            QMessageBox.information(self, "تم الحفظ", f"تم حفظ التقرير إلى {pdf_output}")
        except IOError as e:
            QMessageBox.warning(self, "خطأ", f"فشل في حفظ التقرير: {e}")
        except Exception as e:
            QMessageBox.warning(self, "خطأ غير متوقع", f"حدث خطأ غير متوقع: {e}")
    def build_html_report(self, client_data, diet_data):
        """Constructs the HTML content for the PDF report."""
        title = "تقرير طبي"
        general_info_title = "تفاصيل شخصية"
        diet_info_title = "معلومات الحمية"
        meals_section_title = "وجبات النظام الغذائي"
        suggestions_title = "اقتراحات النظام الغذائي"

        # General Info Data
        general_info = {
            "الاسم": client_data[1],
            "رقم العميل بالصيدلية": client_data[2],
            "العمر": client_data[3],
            "رقم الهاتف": client_data[6],
            "العنوان": client_data[5],
            "الأمراض": client_data[8]
        }
        follow_up_date = client_data[12]

        # Diet Info Data
        if diet_data:
            diet_info = {
                "الطول": diet_data[2],
                "نسبة الدهون": diet_data[3],
                "نسبة العضلات": diet_data[4],
                "نسبة الماء": diet_data[5],
                "نسبة المعادن": diet_data[6],
                "الوزن الحالي": diet_data[7],
                "الوزن السابق": diet_data[8],
                "BMI": diet_data[16]
            }
            meals_info = {
                "الإفطار": diet_data[11],
                "الغداء": diet_data[12],
                "العشاء": diet_data[13],
                "وجبة خفيفة 1": diet_data[14],
                "وجبة خفيفة 2": diet_data[15]
            }
            suggestions, advice = self.get_diet_suggestions_and_advice(diet_data[16])
        else:
            diet_info, meals_info, suggestions, advice = {}, {}, "", ""

        # Build HTML Content
        html = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{
                    font-family: 'NotoSansArabic', sans-serif;
                    direction: rtl;
                    text-align: right;
                    padding: 20px;
                    font-size: 14px;
                }}
                h1, h2 {{
                    text-align: center;
                    margin-bottom: 10px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 15px;
                }}
                th, td {{
                    border: 1px solid #000;
                    padding: 8px;
                    text-align: right;
                    vertical-align: top;
                }}
                th {{
                    background-color: #f2f2f2;
                    width: 20%; 
                }}
                td {{
                    width: 80%; 
                    word-wrap: break-word;
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <h2>{general_info_title}</h2>
            <table>
                {"".join(f"<tr><th>{self.escape_html(key)}</th><td>{self.escape_html(str(value))}</td></tr>" for key, value in general_info.items())}
            </table>

            <h2>{diet_info_title}</h2>
            <table>
                {"".join(f"<tr><th>{self.escape_html(key)}</th><td>{self.escape_html(str(value))}</td></tr>" for key, value in diet_info.items())}
            </table>

            <h2>{meals_section_title}</h2>
            <table>
                {"".join(f"<tr><th>{self.escape_html(key)}</th><td>{self.escape_html(str(value))}</td></tr>" for key, value in meals_info.items())}
            </table>

            <h2>{suggestions_title}</h2>
            <p>{self.escape_html(suggestions)}</p>
            <p>{self.escape_html(advice)}</p>
        </body>
        </html>
        """
        return html


    def escape_html(self, text):
        """Escapes HTML special characters in text."""
        import html
        return html.escape(text)

        

    def get_diet_suggestions_and_advice(self, bmi):
        """
        Returns diet suggestions and advice based on BMI.
        This is a placeholder function. Replace it with your actual implementation.
        """
        try:
            bmi = float(bmi)
        except (ValueError, TypeError):
            return ("", "")
        
        if bmi < 18.5:
            suggestions = "زيادة الوزن من خلال تناول الأطعمة الغنية بالسعرات الحرارية."
            advice = "يُفضل استشارة أخصائي تغذية لوضع خطة غذائية مناسبة."
        elif 18.5 <= bmi < 24.9:
            suggestions = "الحفاظ على الوزن الحالي من خلال نظام غذائي متوازن."
            advice = "استمرار على تناول الأطعمة الصحية والمتنوعة."
        elif 25 <= bmi < 29.9:
            suggestions = "فقدان الوزن من خلال تقليل السعرات الحرارية وزيادة النشاط البدني."
            advice = "ممارسة الرياضة بانتظام واتباع نظام غذائي منخفض الدهون."
        else:
            suggestions = "فقدان الوزن بشكل كبير من خلال نظام غذائي صارم وبرنامج رياضي."
            advice = "استشارة طبيب أو أخصائي تغذية لوضع خطة مناسبة وآمنة."
        
        return suggestions, advice

    def toggle_dark_mode(self):
        """Toggles between light and dark mode."""
        if self.dark_mode:
            stylesheet_path = resource_path("styles/light_styles.qss")
        else:
            stylesheet_path = resource_path("styles/dark_styles.qss")
        
        try:
            with open(stylesheet_path, "r", encoding='utf-8') as file:
                stylesheet = file.read()
            self.setStyleSheet(stylesheet)
            self.dark_mode = not self.dark_mode  # Toggle the state
        except Exception as e:
            print(f"Error loading stylesheet: {e}")



    def init_general_info_tab(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.tabs.setMinimumWidth(500)  # Ensure main tab widget has a minimum width
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Expand to fill available space
        self.client_name_input = QLineEdit()
        self.client_pharmacy_id_input = QLineEdit()
        self.client_name_input.textChanged.connect(self.generate_client_id_on_name_change)
        self.client_pharmacy_id_input.setReadOnly(True)
        self.age_input = QLineEdit()
        self.job_input = QLineEdit()
        self.address_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.work_effort_input = QLineEdit()
        self.diseases_input = QLineEdit()
        self.previous_attempts_input = QLineEdit()
        self.current_treatment_input = QLineEdit()
        self.visit_purpose_input = QLineEdit()
        self.follow_up_date_input = QDateEdit()
        self.follow_up_date_input.setDate(QDate.currentDate())
        self.bmi_display = QLineEdit()
        self.bmi_display.setReadOnly(False)  # Make the BMI field read-only
        
        form_layout.addRow("اسم العميل:", self.client_name_input)
        form_layout.addRow("رقم العميل بالصيدلية:", self.client_pharmacy_id_input)
        form_layout.addRow("العمر:", self.age_input)
        form_layout.addRow("الوظيفة:", self.job_input)
        form_layout.addRow("العنوان:", self.address_input)
        form_layout.addRow("رقم التليفون:", self.phone_input)
        form_layout.addRow("المجهود في العمل:", self.work_effort_input)
        form_layout.addRow("الأمراض:", self.diseases_input)
        form_layout.addRow("المحاولات السابقة:", self.previous_attempts_input)
        form_layout.addRow("العلاج الحالي:", self.current_treatment_input)
        form_layout.addRow("الغرض من الزيارة:", self.visit_purpose_input)
        form_layout.addRow("تاريخ المتابعة:", self.follow_up_date_input)
        form_layout.addRow("BMI:", self.bmi_display)
        layout.addLayout(form_layout)
        self.general_info_tab.setLayout(layout)

    def init_diet_tab(self):
        diet_tabs = QTabWidget()

        # Main Diet Information Tab
        diet_info_tab = QWidget()
        diet_info_layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.height_input = QLineEdit()
        self.fat_percentage_input = QLineEdit()
        self.muscle_percentage_input = QLineEdit()
        self.water_percentage_input = QLineEdit()
        self.mineral_percentage_input = QLineEdit()

        # Align previous weight and current weight next to each other
        weight_layout = QHBoxLayout()
        self.previous_weight_input = QLineEdit()
        self.previous_weight_input.setReadOnly(True)
        self.current_weight_input = QLineEdit()
        weight_layout.addWidget(QLabel("الوزن السابق:"))
        weight_layout.addWidget(self.previous_weight_input)
        weight_layout.addWidget(QLabel("الوزن الحالي:"))
        weight_layout.addWidget(self.current_weight_input)

        form_layout.addRow("الطول:", self.height_input)
        form_layout.addRow("نسبة الدهون:", self.fat_percentage_input)
        form_layout.addRow("نسبة العضلات:", self.muscle_percentage_input)
        form_layout.addRow("نسبة الماء:", self.water_percentage_input)
        form_layout.addRow("نسبة المعادن:", self.mineral_percentage_input)

        diet_info_layout.addLayout(form_layout)
        diet_info_layout.addLayout(weight_layout)

        # Radio buttons for weight category and additional conditions (side by side)
        condition_layout = QHBoxLayout()
        self.weight_category_group = QGroupBox("فئة الوزن")
        radio_layout = QHBoxLayout()
        self.radio_small = QRadioButton("صغار")
        self.radio_adult = QRadioButton("كبار")
        radio_layout.addWidget(self.radio_small)
        radio_layout.addWidget(self.radio_adult)
        self.weight_category_group.setLayout(radio_layout)

        self.weight_condition_group = QGroupBox("حالة الوزن")
        condition_sub_layout = QHBoxLayout()
        self.obesity_checkbox = QRadioButton("سمنة")
        self.thinness_checkbox = QRadioButton("نحافة")
        condition_sub_layout.addWidget(self.obesity_checkbox)
        condition_sub_layout.addWidget(self.thinness_checkbox)
        self.weight_condition_group.setLayout(condition_sub_layout)

        condition_layout.addWidget(self.weight_category_group)
        condition_layout.addWidget(self.weight_condition_group)

        diet_info_layout.addLayout(condition_layout)

        diet_info_tab.setLayout(diet_info_layout)

        # Meals Tab (Breakfast, Lunch, Dinner, Snacks) with 10 past records
        meals_tab = QWidget()
        meals_layout = QVBoxLayout()

        meal_form_layout = QFormLayout()
        self.breakfast_input = QLineEdit()
        self.lunch_input = QLineEdit()
        self.dinner_input = QLineEdit()
        self.snack1_input = QLineEdit()
        self.snack2_input = QLineEdit()

        meal_form_layout.addRow("الإفطار:", self.breakfast_input)
        meal_form_layout.addRow("الغداء:", self.lunch_input)
        meal_form_layout.addRow("العشاء:", self.dinner_input)
        meal_form_layout.addRow("الوجبة الخفيفة 1:", self.snack1_input)
        meal_form_layout.addRow("الوجبة الخفيفة 2:", self.snack2_input)

        meals_layout.addLayout(meal_form_layout)

        # Add a scrollable area to display past 10 meals
        self.past_meals_area = QScrollArea()
        self.past_meals_widget = QWidget()
        self.past_meals_layout = QVBoxLayout()
        self.past_meals_widget.setLayout(self.past_meals_layout)
        self.past_meals_area.setWidgetResizable(True)
        self.past_meals_area.setWidget(self.past_meals_widget)
        meals_layout.addWidget(QLabel("سجل الوجبات السابقة:"))
        meals_layout.addWidget(self.past_meals_area)

        meals_tab.setLayout(meals_layout)

        # Remove the BMI Tab
        # If you decide to keep BMI calculation, you can integrate it differently

        # Add both tabs (Diet Info and Meals) to the Diet section
        diet_tabs.addTab(diet_info_tab, "معلومات الحمية")
        diet_tabs.addTab(meals_tab, "الوجبات")
        # Remove or comment out the BMI tab
        # diet_tabs.addTab(bmi_tab, "حساب BMI")
        self.diet_suggestions_text = QTextEdit()
        self.diet_suggestions_text.setReadOnly(True)
        self.general_advice_text = QTextEdit()
        self.general_advice_text.setReadOnly(True)
        self.set_custom_font()
         # **Set RTL alignment for the text**
        self.diet_suggestions_text.setAlignment(Qt.AlignRight)  
        self.general_advice_text.setAlignment(Qt.AlignRight)    
        
        # **Set Right-to-Left layout direction**
        self.diet_suggestions_text.setLayoutDirection(Qt.RightToLeft) 
        self.general_advice_text.setLayoutDirection(Qt.RightToLeft)    

        # Add the tabs to the main diet tab layout
        main_diet_layout = QVBoxLayout()
        main_diet_layout.addWidget(diet_tabs)

        self.diet_tab.setLayout(main_diet_layout)
        diet_info_layout.addWidget(QLabel("اقتراحات النظام الغذائي:"))
        diet_info_layout.addWidget(self.diet_suggestions_text)
        diet_info_layout.addWidget(QLabel("نصائح عامة:"))
        diet_info_layout.addWidget(self.general_advice_text)
        #self.diet_tab.setLayout(layout)             

        
    def load_past_meals(self):
        """Loads past meals for the current client and displays them on separate lines."""
        client_id = self.get_current_client_id()
        if not client_id:
            return

        cur = self.conn.cursor()
        cur.execute('''SELECT breakfast, lunch, dinner, snack_1, snack_2 
                    FROM diet_info WHERE client_id = ? ORDER BY timestamp DESC LIMIT 10''', (client_id,))
        meals = cur.fetchall()

        self.clear_past_meals()  # Clear previous entries

        # Display each set of meals on separate lines for better readability
        for meal in meals:
            meal_label = QLabel(f"""
            الإفطار: {meal[0] if meal[0] else 'لا يوجد'}\n
            الغداء: {meal[1] if meal[1] else 'لا يوجد'}\n
            العشاء: {meal[2] if meal[2] else 'لا يوجد'}\n
            وجبة خفيفة 1: {meal[3] if meal[3] else 'لا يوجد'}\n
            وجبة خفيفة 2: {meal[4] if meal[4] else 'لا يوجد'}
            """)
            meal_label.setWordWrap(True)
            self.past_meals_layout.addWidget(meal_label)




    def clear_past_meals(self):
        """Clears all widgets from the past meals layout."""
        while self.past_meals_layout.count() > 0:
            item = self.past_meals_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()


    def init_autocomplete(self):
        """Initializes the autocomplete feature for the search input."""
        try:
            self.completer = QCompleter([], self)
            self.completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.completer.setCompletionMode(QCompleter.PopupCompletion)
            self.search_input.setCompleter(self.completer)
            self.refresh_autocomplete()
        except Exception as e:
            print(f"Error during autocomplete initialization: {e}")
            QMessageBox.warning(self, "خطأ", f"فشل في تهيئة البحث التلقائي: {e}")


  


    def init_autosave(self):
        """Initializes autosave timer."""
        self.autosave_timer = QTimer(self)
        self.form_changed = False
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(300000)  # Autosave every 5 minutes

    def autosave(self):
        """Autosaves data if changes were made."""
        if self.form_changed:
            self.save_diet_info()
            self.form_changed = False


    def closeEvent(self, event):
        """Ensure the database connection is closed when the window is closed."""
        if self.conn:
            self.conn.close()
        event.accept()

    
    def apply_stylesheet(self):
        if self.dark_mode:
            dark_stylesheet = """
                QMainWindow { background-color: #2b2b2b; color: white; }
                QLabel, QLineEdit, QPushButton, QTextEdit, QRadioButton, QGroupBox, QMenuBar, QMenu { color: white; }
                QLineEdit, QTextEdit { background-color: #3c3c3c; }
                QPushButton { background-color: #444444; }
                QTabWidget::pane { border: 1px solid #444444; }
            """
            self.setStyleSheet(dark_stylesheet)
        else:
            self.setStyleSheet("")  # Reset to light mode


    def calculate_bmi(self):
        """Calculates BMI and updates the suggestions and advice."""
        height_text = self.height_input.text().strip()
        weight_text = self.current_weight_input.text().strip()
        
        # Validation: Ensure both inputs are non-empty
        if not height_text or not weight_text:
            self.bmi_display.clear()
            self.diet_suggestions_text.clear()
            self.general_advice_text.clear()
            QMessageBox.warning(self, "Input Error", "يرجى إدخال الطول والوزن.")
            return
        
        try:
            height = float(height_text) / 100  # Convert height to meters
            weight = float(weight_text)
            
            # Validation: Ensure height and weight are positive
            if height <= 0 or weight <= 0:
                raise ValueError("الطول والوزن لابد ان يكونوا قيم صحيحة")
            
            # Calculate BMI
            bmi = round(weight / (height ** 2), 2)
            self.bmi_display.setText(f"{bmi}")
            
            # Provide diet suggestions based on BMI
            suggestions, advice = self.get_diet_suggestions_and_advice(bmi)
            self.diet_suggestions_text.setText(suggestions)
            self.general_advice_text.setText(advice)
        
        except ValueError:
            QMessageBox.warning(self, "Input Error", "يرجى إدخال قيم رقمية صحيحة للطول والوزن.")
            self.bmi_display.clear()
            self.diet_suggestions_text.clear()
            self.general_advice_text.clear()

    
    def update_bmi_color(self, bmi):
        if bmi < 18.5:
            self.bmi_display.setStyleSheet("background-color: yellow;")
        elif 18.5 <= bmi < 25:
            self.bmi_display.setStyleSheet("background-color: green;")
        elif 25 <= bmi < 30:
            self.bmi_display.setStyleSheet("background-color: orange;")
        else:
            self.bmi_display.setStyleSheet("background-color: red;")


    def save_bmi(self, bmi):
        """Saves the calculated BMI into the SQLite database and updates the past 10 BMI list."""
        client_id = self.get_current_client_id()
        if not client_id:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على العميل.")  # Error: Client not found
            return

        cur = self.conn.cursor()
        # Retrieve the latest diet_info ID for the client
        cur.execute('''SELECT id FROM diet_info WHERE client_id = ? ORDER BY timestamp DESC LIMIT 1''', (client_id,))
        result = cur.fetchone()

        if result:
            diet_id = result[0]
            cur.execute('''UPDATE diet_info SET bmi = ? WHERE id = ?''', (bmi, diet_id))
            self.conn.commit()
            #self.load_past_bmis()
        else:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على بيانات الحمية للعميل.")  # No diet data

    



    def init_notes_tab(self):
        layout = QVBoxLayout()

        # Create a formatting toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(16, 16))  # Set icon size as needed

        # Bold action
        bold_icon_path = resource_path('resources/icons/bold.png')
        bold_action = QAction(QIcon(bold_icon_path), 'Bold', self)
        bold_action.triggered.connect(self.make_bold)
        toolbar.addAction(bold_action)

        # Italic action
        italic_icon_path = resource_path('resources/icons/italic.png')
        italic_action = QAction(QIcon(italic_icon_path), 'Italic', self)
        italic_action.triggered.connect(self.make_italic)
        toolbar.addAction(italic_action)

        # Underline action
        underline_icon_path = resource_path('resources/icons/underline.png')
        underline_action = QAction(QIcon(underline_icon_path), 'Underline', self)
        underline_action.triggered.connect(self.make_underline)
        toolbar.addAction(underline_action)

        # Bullet List action
        bullet_icon_path = resource_path('resources/icons/bullet.png')
        bullet_action = QAction(QIcon(bullet_icon_path), 'Bullet List', self)
        bullet_action.triggered.connect(self.insert_bullet_list)
        toolbar.addAction(bullet_action)

        # Add toolbar to layout
        layout.addWidget(toolbar)

        # Rich text edit
        self.notes_input = QTextEdit()
        # Remove fixed height to allow it to expand
        self.notes_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.notes_input)

        # Set the layout for the notes tab
        self.notes_tab.setLayout(layout)
        self.notes_input.setLayoutDirection(Qt.RightToLeft)
        self.notes_input.setAlignment(Qt.AlignRight)


    def make_bold(self):
        fmt = self.notes_input.currentCharFormat()
        if fmt.fontWeight() == QFont.Bold:
            fmt.setFontWeight(QFont.Normal)
        else:
            fmt.setFontWeight(QFont.Bold)
        self.notes_input.setCurrentCharFormat(fmt)

    def make_italic(self):
        fmt = self.notes_input.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.notes_input.setCurrentCharFormat(fmt)

    def make_underline(self):
        fmt = self.notes_input.currentCharFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        self.notes_input.setCurrentCharFormat(fmt)

    def insert_bullet_list(self):
        cursor = self.notes_input.textCursor()
        cursor.insertList(QTextListFormat.ListDisc)


    def search_client(self):
        search_term = self.search_input.text().strip()
        if not search_term:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال اسم العميل أو رقم العميل")
            return
        cur = self.conn.cursor()
        # Use LIKE operator for partial matching
        cur.execute('''SELECT * FROM general_info WHERE client_pharmacy_id LIKE ? OR client_name LIKE ?''',
                    (f'%{search_term}%', f'%{search_term}%'))
        client = cur.fetchone()
        if client:
            self.populate_client_info(client)
        else:
            QMessageBox.warning(self, "لم يتم العثور", "لم يتم العثور على العميل")


    def check_follow_up_dates(self):
        today = datetime.today().date()
        upcoming_clients = []
        cur = self.conn.cursor()
        cur.execute('''SELECT client_name, follow_up_date FROM general_info''')
        for client_name, follow_up_date in cur.fetchall():
            if follow_up_date:
                follow_up = datetime.strptime(follow_up_date, '%Y-%m-%d').date()
                delta = (follow_up - today).days
                if 0 <= delta <= 7:
                    upcoming_clients.append((client_name, follow_up_date))
        if upcoming_clients:
            message = "العملاء الذين لديهم مواعيد متابعة خلال الأسبوع القادم:\n"
            for name, date in upcoming_clients:
                message += f"- {name}: {date}\n"
            QMessageBox.information(self, "تذكير المتابعة", message)


    def populate_client_info(self, client):
        """Populate the tabs with client data."""
        try:
            # Print the entire client tuple for debugging
            print(f"Client Data: {client}")

            # Unpack client data based on the database schema
            (id_, name, pharmacy_id, age, job, address, phone, work_effort, diseases, 
            previous_attempts, current_treatment, visit_purpose, follow_up_date) = client

            # Populate general info fields
            self.client_name_input.setText(name)
            self.client_pharmacy_id_input.setText(pharmacy_id)
            self.age_input.setText(str(age) if age is not None else "")
            self.job_input.setText(job if job else "")
            self.address_input.setText(address if address else "")
            self.phone_input.setText(phone if phone else "")
            self.work_effort_input.setText(work_effort if work_effort else "")
            self.diseases_input.setText(diseases if diseases else "")
            self.previous_attempts_input.setText(previous_attempts if previous_attempts else "")
            self.current_treatment_input.setText(current_treatment if current_treatment else "")
            self.visit_purpose_input.setText(visit_purpose if visit_purpose else "")
            if follow_up_date:
                self.follow_up_date_input.setDate(QDate.fromString(follow_up_date, 'yyyy-MM-dd'))
            else:
                self.follow_up_date_input.setDate(QDate.currentDate())

            self.search_input.clear()

            # Populate diet info, notes, etc., as needed
            self.populate_diet_info(id_)
            self.populate_notes(id_)
            #self.load_past_bmis()
            self.load_past_meals()

        except Exception as e:
            print(f"Error populating client info: {e}")
            QMessageBox.warning(self, "Error", f"Failed to populate client info: {e}")
            return  # Exit the method if there's an error


    def populate_diet_info(self, client_id):
        """Populate diet information for the client."""
        try:
            cur = self.conn.cursor()
            cur.execute('''SELECT * FROM diet_info WHERE client_id = ? ORDER BY timestamp DESC LIMIT 1''', (client_id,))
            diet = cur.fetchone()
            if diet:
                (_, _, height, fat_percentage, muscle_percentage, water_percentage, mineral_percentage, 
                current_weight, previous_weight, weight_category, weight_condition, breakfast, 
                lunch, dinner, snack_1, snack_2, bmi, _) = diet

                self.height_input.setText(str(height) if height is not None else "")
                self.fat_percentage_input.setText(str(fat_percentage) if fat_percentage is not None else "")
                self.muscle_percentage_input.setText(str(muscle_percentage) if muscle_percentage is not None else "")
                self.water_percentage_input.setText(str(water_percentage) if water_percentage is not None else "")
                self.mineral_percentage_input.setText(str(mineral_percentage) if mineral_percentage is not None else "")
                self.previous_weight_input.setText(str(previous_weight) if previous_weight is not None else "")
                self.current_weight_input.setText(str(current_weight) if current_weight is not None else "")
                self.breakfast_input.setText(breakfast if breakfast else "")
                self.lunch_input.setText(lunch if lunch else "")
                self.dinner_input.setText(dinner if dinner else "")
                self.snack1_input.setText(snack_1 if snack_1 else "")
                self.snack2_input.setText(snack_2 if snack_2 else "")
                self.bmi_display.setText(str(bmi) if bmi is not None else "")

                # Set weight category radio buttons
                if weight_category == "صغار":
                    self.radio_small.setChecked(True)
                elif weight_category == "كبار":
                    self.radio_adult.setChecked(True)
                else:
                    self.radio_small.setChecked(False)
                    self.radio_adult.setChecked(False)

                # Set weight condition radio buttons
                if weight_condition == "سمنة":
                    self.obesity_checkbox.setChecked(True)
                    self.thinness_checkbox.setChecked(False)
                elif weight_condition == "نحافة":
                    self.obesity_checkbox.setChecked(False)
                    self.thinness_checkbox.setChecked(True)
                else:
                    self.obesity_checkbox.setChecked(False)
                    self.thinness_checkbox.setChecked(False)
                
                # Get suggestions and advice based on BMI
                suggestions, advice = self.get_diet_suggestions_and_advice(bmi)
                self.diet_suggestions_text.setText(suggestions)
                self.general_advice_text.setText(advice)
        except Exception as e:
            print(f"Error populating diet info: {e}")
            QMessageBox.warning(self, "خطأ", f"فشل في جلب بيانات الحمية: {e}")


    def populate_notes(self, client_id):
        """Populate notes for the client."""
        try:
            cur = self.conn.cursor()
            cur.execute('''SELECT client_notes FROM notes WHERE client_id = ? ORDER BY id DESC LIMIT 1''', (client_id,))
            notes = cur.fetchone()
            if notes and notes[0]:
                self.notes_input.setHtml(notes[0])
            else:
                self.notes_input.setText("")
        except Exception as e:
            print(f"Error populating notes: {e}")
            QMessageBox.warning(self, "خطأ", f"فشل في جلب الملاحظات: {e}")


    def get_current_client_id(self):
        """Returns the current client ID from the general info tab."""
        client_name = self.client_name_input.text()
        client_pharmacy_id = self.client_pharmacy_id_input.text()
        cur = self.conn.cursor()
        cur.execute('''SELECT id FROM general_info WHERE client_name = ? OR client_pharmacy_id = ?''', (client_name, client_pharmacy_id))
        result = cur.fetchone()
        if result:
            return result[0]
        return None

    def clear_all_fields(self):
        """Clears all input fields in the application."""
        # Clear general info fields
        self.client_name_input.clear()
        self.client_pharmacy_id_input.clear()
        self.age_input.clear()
        self.job_input.clear()
        self.address_input.clear()
        self.phone_input.clear()
        self.work_effort_input.clear()
        self.diseases_input.clear()
        self.previous_attempts_input.clear()
        self.current_treatment_input.clear()
        self.visit_purpose_input.clear()
        self.follow_up_date_input.setDate(QDate.currentDate())

        # Clear diet info fields
        self.height_input.clear()
        self.fat_percentage_input.clear()
        self.muscle_percentage_input.clear()
        self.water_percentage_input.clear()
        self.mineral_percentage_input.clear()
        self.previous_weight_input.clear()
        self.current_weight_input.clear()
        # Extract the text from each QLabel in the layout
        meal_log_content = []
        for i in range(self.past_meals_layout.count()):
            item = self.past_meals_layout.itemAt(i).widget()
            if isinstance(item, QLabel):
                meal_log_content.append(item.text())

    

        # Restore the meal logs
        self.clear_past_meals()  # Clear the past meals layout
        for meal_text in meal_log_content:
            label = QLabel(meal_text)
            label.setWordWrap(True)
            self.past_meals_layout.addWidget(label)
        self.past_meals_layout.addStretch()

        # Clear weight category and condition
        self.radio_small.setAutoExclusive(False)
        self.radio_small.setChecked(False)
        self.radio_small.setAutoExclusive(True)

        self.radio_adult.setAutoExclusive(False)
        self.radio_adult.setChecked(False)
        self.radio_adult.setAutoExclusive(True)

        self.obesity_checkbox.setAutoExclusive(False)
        self.obesity_checkbox.setChecked(False)
        self.obesity_checkbox.setAutoExclusive(True)

        self.thinness_checkbox.setAutoExclusive(False)
        self.thinness_checkbox.setChecked(False)
        self.thinness_checkbox.setAutoExclusive(True)

        # Clear meal info
        self.breakfast_input.clear()
        self.lunch_input.clear()
        self.dinner_input.clear()
        self.snack1_input.clear()
        self.snack2_input.clear()

        # Clear BMI
        self.bmi_display.clear()

        # Clear notes
        self.notes_input.clear()

        # Clear past meals 
        for i in reversed(range(self.past_meals_layout.count())):
            widget = self.past_meals_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
