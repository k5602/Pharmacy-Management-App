"""
Resource Manager Utility
Manages application resources like fonts, icons, images, and stylesheets
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtCore import QFile, QTextStream
from loguru import logger


class ResourceManager:
    """
    Manages application resources and provides centralized access to assets
    """

    def __init__(self):
        self.base_path = self._get_base_path()
        self.resources_path = self.base_path / "resources"
        self._cached_stylesheets: Dict[str, str] = {}
        self._cached_icons: Dict[str, QIcon] = {}
        self._cached_fonts: Dict[str, QFont] = {}

        # Ensure resources directory exists
        if not self.resources_path.exists():
            logger.warning(f"Resources directory not found: {self.resources_path}")

    def _get_base_path(self) -> Path:
        """
        Get the base path for resources, handling both development and packaged environments
        """
        try:
            # PyInstaller stores files in a temporary folder _MEIPASS when packaged
            base_path = Path(sys._MEIPASS)
        except AttributeError:
            # Fallback to parent directory for development environment
            base_path = Path(__file__).parent.parent.parent

        return base_path

    def get_resource_path(self, relative_path: str) -> Optional[str]:
        """
        Get the absolute path to a resource file

        Args:
            relative_path: Relative path from resources directory

        Returns:
            str: Absolute path if file exists, None otherwise
        """
        full_path = self.resources_path / relative_path

        if full_path.exists():
            return str(full_path)

        logger.warning(f"Resource not found: {relative_path}")
        return None

    def get_font_path(self, font_name: str) -> Optional[str]:
        """
        Get path to a font file

        Args:
            font_name: Font file name

        Returns:
            str: Font file path if exists, None otherwise
        """
        return self.get_resource_path(f"fonts/{font_name}")

    def get_icon_path(self, icon_name: str) -> Optional[str]:
        """
        Get path to an icon file

        Args:
            icon_name: Icon file name

        Returns:
            str: Icon file path if exists, None otherwise
        """
        return self.get_resource_path(f"icons/{icon_name}")

    def get_image_path(self, image_name: str) -> Optional[str]:
        """
        Get path to an image file

        Args:
            image_name: Image file name

        Returns:
            str: Image file path if exists, None otherwise
        """
        return self.get_resource_path(f"images/{image_name}")

    def get_style_path(self, style_name: str) -> Optional[str]:
        """
        Get path to a stylesheet file

        Args:
            style_name: Stylesheet file name

        Returns:
            str: Stylesheet file path if exists, None otherwise
        """
        return self.get_resource_path(f"styles/{style_name}")

    def get_template_path(self, template_name: str) -> Optional[str]:
        """
        Get path to a template file

        Args:
            template_name: Template file name

        Returns:
            str: Template file path if exists, None otherwise
        """
        return self.get_resource_path(f"templates/{template_name}")

    def load_stylesheet(self, style_name: str, use_cache: bool = True) -> Optional[str]:
        """
        Load stylesheet content from file

        Args:
            style_name: Stylesheet file name
            use_cache: Whether to use cached version

        Returns:
            str: Stylesheet content if successful, None otherwise
        """
        # Check cache first
        if use_cache and style_name in self._cached_stylesheets:
            return self._cached_stylesheets[style_name]

        style_path = self.get_style_path(style_name)
        if not style_path:
            return None

        try:
            with open(style_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Cache the content
            if use_cache:
                self._cached_stylesheets[style_name] = content

            return content

        except Exception as e:
            logger.error(f"Failed to load stylesheet {style_name}: {e}")
            return None

    def load_icon(self, icon_name: str, use_cache: bool = True) -> Optional[QIcon]:
        """
        Load icon from file

        Args:
            icon_name: Icon file name
            use_cache: Whether to use cached version

        Returns:
            QIcon: Icon object if successful, None otherwise
        """
        # Check cache first
        if use_cache and icon_name in self._cached_icons:
            return self._cached_icons[icon_name]

        icon_path = self.get_icon_path(icon_name)
        if not icon_path:
            return None

        try:
            icon = QIcon(icon_path)

            if not icon.isNull():
                # Cache the icon
                if use_cache:
                    self._cached_icons[icon_name] = icon
                return icon
            else:
                logger.warning(f"Failed to load icon: {icon_name}")
                return None

        except Exception as e:
            logger.error(f"Error loading icon {icon_name}: {e}")
            return None

    def load_pixmap(self, image_name: str) -> Optional[QPixmap]:
        """
        Load pixmap from image file

        Args:
            image_name: Image file name

        Returns:
            QPixmap: Pixmap object if successful, None otherwise
        """
        image_path = self.get_image_path(image_name)
        if not image_path:
            return None

        try:
            pixmap = QPixmap(image_path)

            if not pixmap.isNull():
                return pixmap
            else:
                logger.warning(f"Failed to load image: {image_name}")
                return None

        except Exception as e:
            logger.error(f"Error loading image {image_name}: {e}")
            return None

    def load_font(self, font_name: str, size: int = 12, use_cache: bool = True) -> Optional[QFont]:
        """
        Load and register font from file

        Args:
            font_name: Font file name
            size: Font size
            use_cache: Whether to use cached version

        Returns:
            QFont: Font object if successful, None otherwise
        """
        cache_key = f"{font_name}_{size}"

        # Check cache first
        if use_cache and cache_key in self._cached_fonts:
            return self._cached_fonts[cache_key]

        font_path = self.get_font_path(font_name)
        if not font_path:
            return None

        try:
            from PyQt6.QtGui import QFontDatabase

            font_db = QFontDatabase()
            font_id = font_db.addApplicationFont(font_path)

            if font_id != -1:
                font_families = font_db.applicationFontFamilies(font_id)
                if font_families:
                    font = QFont(font_families[0], size)

                    # Cache the font
                    if use_cache:
                        self._cached_fonts[cache_key] = font

                    return font

            logger.warning(f"Failed to register font: {font_name}")
            return None

        except Exception as e:
            logger.error(f"Error loading font {font_name}: {e}")
            return None

    def load_template(self, template_name: str) -> Optional[str]:
        """
        Load template content from file

        Args:
            template_name: Template file name

        Returns:
            str: Template content if successful, None otherwise
        """
        template_path = self.get_template_path(template_name)
        if not template_path:
            return None

        try:
            with open(template_path, 'r', encoding='utf-8') as file:
                return file.read()

        except Exception as e:
            logger.error(f"Failed to load template {template_name}: {e}")
            return None

    def get_available_themes(self) -> list:
        """
        Get list of available theme stylesheets

        Returns:
            list: List of theme names
        """
        themes = []
        styles_dir = self.resources_path / "styles"

        if styles_dir.exists():
            for file_path in styles_dir.glob("*.qss"):
                themes.append(file_path.stem)

        return themes

    def get_available_icons(self) -> list:
        """
        Get list of available icons

        Returns:
            list: List of icon names
        """
        icons = []
        icons_dir = self.resources_path / "icons"

        if icons_dir.exists():
            for file_path in icons_dir.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.svg', '.ico']:
                    icons.append(file_path.name)

        return icons

    def get_available_fonts(self) -> list:
        """
        Get list of available fonts

        Returns:
            list: List of font names
        """
        fonts = []
        fonts_dir = self.resources_path / "fonts"

        if fonts_dir.exists():
            for file_path in fonts_dir.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.ttf', '.otf', '.woff', '.woff2']:
                    fonts.append(file_path.name)

        return fonts

    def clear_cache(self):
        """Clear all cached resources"""
        self._cached_stylesheets.clear()
        self._cached_icons.clear()
        self._cached_fonts.clear()
        logger.info("Resource cache cleared")

    def preload_resources(self, resource_list: Dict[str, list]):
        """
        Preload specified resources into cache

        Args:
            resource_list: Dictionary with resource types and lists of names
        """
        try:
            # Preload stylesheets
            for style_name in resource_list.get('stylesheets', []):
                self.load_stylesheet(style_name, use_cache=True)

            # Preload icons
            for icon_name in resource_list.get('icons', []):
                self.load_icon(icon_name, use_cache=True)

            # Preload fonts
            for font_info in resource_list.get('fonts', []):
                if isinstance(font_info, dict):
                    font_name = font_info.get('name')
                    font_size = font_info.get('size', 12)
                    self.load_font(font_name, font_size, use_cache=True)
                else:
                    self.load_font(font_info, use_cache=True)

            logger.info("Resources preloaded successfully")

        except Exception as e:
            logger.error(f"Error preloading resources: {e}")

    def copy_default_resources(self):
        """
        Copy default resources from old application to new structure
        """
        try:
            # Define source paths (from original app)
            old_app_path = self.base_path.parent / "Pharmacy-Management-App"

            # Copy files if they exist
            resources_to_copy = [
                ("app_icon.ico", "icons/app_icon.ico"),
                ("light_styles.qss", "styles/light_theme.qss"),
                ("dark_styles.qss", "styles/dark_theme.qss"),
            ]

            for old_file, new_file in resources_to_copy:
                old_path = old_app_path / old_file
                new_path = self.resources_path / new_file

                if old_path.exists():
                    # Ensure target directory exists
                    new_path.parent.mkdir(parents=True, exist_ok=True)

                    # Copy file
                    import shutil
                    shutil.copy2(old_path, new_path)
                    logger.info(f"Copied resource: {old_file} -> {new_file}")

        except Exception as e:
            logger.error(f"Error copying default resources: {e}")

    def validate_resources(self) -> Dict[str, Any]:
        """
        Validate that required resources are available

        Returns:
            dict: Validation report
        """
        report = {
            'is_valid': True,
            'missing_resources': [],
            'available_resources': {}
        }

        # Required resources
        required_resources = [
            ('styles', 'light_theme.qss'),
            ('styles', 'dark_theme.qss'),
            ('icons', 'app_icon.ico'),
            ('fonts', 'NotoSansArabic-Regular.ttf'),
            ('fonts', 'NotoSansArabic-Bold.ttf'),
        ]

        for resource_type, resource_name in required_resources:
            path = self.get_resource_path(f"{resource_type}/{resource_name}")
            if not path:
                report['missing_resources'].append(f"{resource_type}/{resource_name}")
                report['is_valid'] = False

        # Get available resources
        report['available_resources'] = {
            'themes': self.get_available_themes(),
            'icons': self.get_available_icons(),
            'fonts': self.get_available_fonts()
        }

        return report

    def __str__(self) -> str:
        return f"ResourceManager(base_path='{self.base_path}', resources_path='{self.resources_path}')"


# Global resource manager instance
_resource_manager = None

def get_resource_manager() -> ResourceManager:
    """Get the global resource manager instance"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager
