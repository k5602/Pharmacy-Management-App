Here's a polished GitHub description for your application with integrated screenshots:

---

# Dr. Abaza Pharmacy Management System

![App Interface](Desktop- 4.png)
*A comprehensive desktop application for managing pharmacy client records, diet plans, and medical notes with Arabic/English support.*

## 🌟 Features

### **Client Management**
- 📝 Store client demographics (name, age, contact info)
- 🆔 Automatic client ID generation
- 🔍 Quick search by name/ID with Arabic autocomplete
- 📅 Follow-up date tracking with reminders

### **Diet & Nutrition Tracking**
- 📊 Body metrics analysis (BMI, fat%, muscle%)
- 🥗 Meal planning with breakfast/lunch/dinner/snacks
- 📈 Weight progress tracking with historical data
- 🧠 AI-powered diet suggestions based on BMI(Planned)

### **Medical Workflow**
- 💊 Medication history tracking
- 🩺 Disease/condition documentation
- 📑 PDF report generation with Arabic typography
- ✏️ Rich text notes with formatting tools

### **Enterprise Features**
- 🔒 Role-based login system
- 🕶️ Light/dark mode switching
- 💾 Database backup/restore functionality
- 📤 CSV data export capabilities

---

## 🖼️ Screenshots

| Client Information | Diet Planning | PDF Reports |
|--------------------|---------------|-------------|
| ![General Info](Desktop- 1.png) | ![Diet Interface](Desktop- 5.png) | ![PDF Report](Desktop- 6.png) |

---

## 🛠️ Technical Stack

```python
Python 3.9+
PyQt5 - Cross-platform GUI
SQLite - Client data storage
WeasyPrint - PDF generation
Arabic-Reshaper - RTL text processing
```

---

## 🚀 Quick Start

1. **Install Requirements**
```bash
pip install -r requirements.txt
```

2. **Run Application**
```bash
python app.py
```

3. **Default Credentials**
```
Username: admin
Password: a2024
```

---

## 📦 Database Structure
```sql
3 Normalized Tables:
- general_info (Client demographics)
- diet_info (Nutrition metrics)
- notes (Medical observations)

ACID Compliant Transactions
Automatic Schema Migration
```

---

## 🌐 Localization Support
- Full Arabic/English bilingual interface
- RTL layout engine
- Noto Sans Arabic font integration
- Culture-sensitive date formatting

---

## 📄 License
MIT License - Free for educational/commercial use

---

**💡 Pro Tip:** Use the dark mode toggle (Ctrl+D) for extended usage sessions!
