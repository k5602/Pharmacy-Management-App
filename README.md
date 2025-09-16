# Pharmacy Management Nutrition System v2.0

A comprehensive, modern pharmacy management application with advanced nutrition tracking capabilities, built with PyQt6 and following MVC architecture principles.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.5+-green.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🌟 Features

### 🏥 Client Management

- **Comprehensive Client Profiles**: Store detailed personal, medical, and contact information
- **Unique Pharmacy ID System**: Auto-generated 5-digit client identification
- **Advanced Search & Filtering**: Find clients by name, ID, age range, medical conditions
- **Follow-up Scheduling**: Automated reminders for client appointments
- **Medical History Tracking**: Complete medical background and current treatments

### 🍎 Nutrition & Diet Tracking

- **BMI Calculation & Monitoring**: Automatic BMI calculation with health categorization
- **Body Composition Analysis**: Track fat, muscle, water, and mineral percentages
- **Meal Planning System**: Comprehensive 6-meal daily planning (breakfast, snacks, lunch, dinner)
- **Weight Progression Tracking**: Visual weight change monitoring over time
- **Personalized Diet Recommendations**: AI-powered suggestions based on BMI and health goals
- **Nutritional Goal Setting**: Weight targets with progress tracking

### 📊 Analytics & Reporting

- **Interactive Dashboard**: Real-time client statistics and health metrics
- **Professional PDF Reports**: Arabic-supported reports with custom templates
- **Progress Charts**: Visual representation of client health improvements
- **Statistical Analysis**: Population health metrics and trend analysis
- **Export Capabilities**: CSV, Excel, and PDF export options

### 🔐 Security & User Management

- **Multi-User Authentication**: Role-based access control (Admin, Nutritionist, Assistant)
- **Encrypted Data Storage**: Secure client information protection
- **Session Management**: Automatic timeout and security policies
- **Audit Trail**: Complete logging of all system operations
- **GDPR Compliance**: Data protection and privacy features

### 🌍 Arabic Language Support

- **Complete RTL Support**: Right-to-left text direction throughout the application
- **Arabic Font Integration**: Beautiful Arabic typography with NotoSansArabic fonts
- **Localized Interface**: All UI elements in Arabic
- **Arabic PDF Generation**: Professional Arabic reports with proper text shaping

### 🎨 Modern User Interface

- **Dark/Light Themes**: Toggle between modern theme options
- **Responsive Design**: Adaptive layout for different screen sizes
- **Intuitive Navigation**: Tab-based interface with keyboard shortcuts
- **Rich Text Editor**: Formatted notes with Arabic support
- **Progress Indicators**: Real-time feedback for long operations

## 🏗️ Architecture

### MVC Design Pattern

```
pharmacy_management_v2/
├── src/
│   ├── models/          # Data models and database operations
│   ├── views/           # User interface components
│   ├── controllers/     # Business logic and coordination
│   ├── utils/           # Helper functions and utilities
│   ├── services/        # External service integrations
│   └── config/          # Configuration management
├── resources/           # Application assets
│   ├── fonts/          # Arabic and international fonts
│   ├── icons/          # UI icons and graphics
│   ├── styles/         # QSS stylesheets
│   ├── images/         # Application images
│   └── templates/      # Report and email templates
├── tests/              # Unit and integration tests
├── docs/               # Documentation
└── config/             # Configuration files
```

### Technology Stack

- **GUI Framework**: PyQt6 with modern widgets and styling
- **Database**: SQLAlchemy ORM with SQLite backend
- **Configuration**: Pydantic for settings management
- **PDF Generation**: WeasyPrint with Arabic text support
- **Logging**: Loguru for comprehensive logging
- **Testing**: pytest with Qt testing extensions
- **Security**: cryptography and bcrypt for data protection

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- At least 500MB free disk space

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/pharmacy-management-v2.git
cd pharmacy-management-v2

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

### Development Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies including development tools
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Run with debugging
python src/main.py --debug
```

## 📖 Usage

### First Run

1. **Launch Application**: Run `python src/main.py`
2. **Login**: Use default credentials (admin/admin2024) - **Change immediately!**
3. **Setup**: Configure your preferences in Settings menu
4. **Add Clients**: Start adding client information through the "New Client" button

### Daily Workflow

1. **Search Clients**: Use the search bar to find existing clients
2. **Update Information**: Add new measurements, notes, and meal plans
3. **Generate Reports**: Create professional PDF reports for clients
4. **Follow-up Management**: Check and schedule follow-up appointments
5. **Analytics Review**: Monitor client progress through the dashboard

### Key Features Usage

#### Client Management

- **Add New Client**: File → New Client (Ctrl+N)
- **Search**: Use the search bar with client name or ID
- **Edit Information**: Click on any client field to edit
- **Delete Client**: Edit → Delete Client (Ctrl+D)

#### Diet Tracking

- **BMI Calculation**: Enter height and weight - BMI calculates automatically
- **Meal Planning**: Use the Diet tab to plan daily meals
- **Progress Tracking**: View weight history in the Analytics tab
- **Recommendations**: Get AI-powered diet suggestions based on BMI

#### Report Generation

- **Client Report**: View → PDF Report
- **Custom Reports**: View → Custom PDF Report
- **Analytics Dashboard**: View → Analytics Dashboard
- **Export Data**: File → Export Data

## ⚙️ Configuration

### Settings File

The application stores settings in:

- **Windows**: `%APPDATA%\PharmacyManagement\settings.json`
- **macOS**: `~/Library/Application Support/PharmacyManagement/settings.json`
- **Linux**: `~/.config/PharmacyManagement/settings.json`

### Key Configuration Options

```json
{
  "ui": {
    "default_theme": "light",
    "default_language": "ar",
    "rtl_support": true,
    "default_font_family": "NotoSansArabic"
  },
  "database": {
    "auto_backup": true,
    "backup_interval_hours": 24,
    "max_backups": 7
  },
  "security": {
    "session_timeout_minutes": 60,
    "max_login_attempts": 3,
    "require_strong_passwords": true
  }
}
```

## 🔧 Development

### Project Structure

```
src/
├── main.py              # Application entry point
├── models/
│   ├── base.py          # Base model and database classes
│   ├── client.py        # Client data models
│   └── diet.py          # Diet and nutrition models
├── views/
│   ├── main_window.py   # Main application window
│   ├── dialogs/         # Modal dialogs
│   ├── components/      # Reusable UI components
│   └── widgets/         # Custom widgets
├── controllers/
│   ├── base.py          # Base controller class
│   ├── client_controller.py
│   ├── diet_controller.py
│   └── app_controller.py
├── utils/
│   ├── validators.py    # Data validation functions
│   ├── formatters.py    # Text and data formatting
│   └── resource_manager.py # Resource loading
└── config/
    └── settings.py      # Configuration management
```

### Adding New Features

1. **Models**: Add data models in `src/models/`
2. **Views**: Create UI components in `src/views/`
3. **Controllers**: Implement business logic in `src/controllers/`
4. **Tests**: Add tests in `tests/` directory

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_client_model.py

# Run UI tests
pytest tests/ui/
```

### Test Structure

```
tests/
├── unit/               # Unit tests for individual components
├── integration/        # Integration tests
├── ui/                # UI component tests
└── conftest.py        # Test configuration
```

## 📊 Performance

### Optimization Features

- **Lazy Loading**: Large datasets loaded on demand
- **Caching**: Frequently accessed data cached in memory
- **Background Operations**: Heavy operations run in separate threads
- **Database Indexing**: Optimized queries for fast search
- **Resource Management**: Efficient loading and disposal of UI resources

### Performance Metrics

- **Startup Time**: < 3 seconds on modern hardware
- **Search Response**: < 500ms for 10,000+ client records
- **Memory Usage**: < 200MB baseline memory footprint
- **Database Operations**: 50% fewer queries compared to v1.0

## 🛡️ Security

### Data Protection

- **Encryption**: Client data encrypted at rest
- **Secure Authentication**: Password hashing with bcrypt
- **Session Security**: Automatic timeout and secure session management
- **Audit Logging**: Complete trail of all system operations
- **Backup Security**: Encrypted database backups

### Best Practices

- Change default passwords immediately
- Enable automatic backups
- Regular security updates
- Use strong passwords
- Limit user permissions appropriately

## 📚 Documentation

### User Documentation

- **User Guide**: Complete step-by-step usage instructions
- **Video Tutorials**: Screen recordings for common tasks
- **FAQ**: Frequently asked questions and solutions
- **Troubleshooting**: Common issues and resolutions

### Developer Documentation

- **API Reference**: Complete code documentation
- **Architecture Guide**: System design and patterns
- **Contributing Guide**: How to contribute to the project
- **Release Notes**: Version history and changes

## 🤝 Contributing

I welcome contributions for details.

### Development Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards

- Follow PEP 8 style guide
- Add type hints to all functions
- Write comprehensive docstrings
- Include unit tests for new features
- Use meaningful commit messages

## 🐛 Troubleshooting

### Common Issues

#### Application Won't Start

```bash
# Check Python version
python --version

# Verify dependencies
pip list | grep PyQt6

# Check for missing resources
python -c "from src.utils.resource_manager import ResourceManager; rm = ResourceManager(); print(rm.validate_resources())"
```

#### Database Issues

```bash
# Backup current database
python -c "from src.models.base import get_database_manager; get_database_manager().backup_database()"

# Reset database
rm -f ~/.config/PharmacyManagement/pharmacy.db

# Restart application
python src/main.py
```

#### Arabic Text Issues

- Ensure Arabic fonts are installed
- Check system language settings
- Verify UTF-8 encoding support

### Getting Help

- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Join community discussions
- **Support**: Contact support@abazapharmacy.com
- **Documentation**: Check the docs/ folder

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PyQt6**: For the excellent GUI framework
- **SQLAlchemy**: For robust database ORM
- **WeasyPrint**: For PDF generation capabilities
- **Noto Fonts**: For beautiful Arabic typography
- **Contributors**: All developers who contributed to this project

## 📈 Roadmap

### Version 2.1 (Q4 2025)

- [ ] Food database integration
- [ ] Calorie tracking
- [ ] Mobile app companion
- [ ] Cloud synchronization

### Version 2.2 (Q1 2026)

- [ ] Machine learning recommendations
- [ ] Advanced analytics
- [ ] Multi-pharmacy support
- [ ] API for third-party integrations

### Version 3.0 (Q3 2026)

- [ ] Web interface
- [ ] Real-time collaboration
- [ ] Advanced reporting
- [ ] Enterprise features

---

**Dr.Abaza Pharmacy Management System v2.0** - Empowering healthcare through technology 🏥💊
