# -*- coding: utf-8 -*-
"""Simple i18n translations for the app. Keys are used in templates via _('key')."""

TRANSLATIONS = {
    "en": {
        "nav.demo": "Demo",
        "nav.all_trails": "All Trails",
        "nav.my_trails": "My Trails",
        "nav.profile": "Profile",
        "nav.settings": "Settings",
        "footer.text": "Adaptive Trail Recommender System",
        "settings.theme": "Appearance",
        "settings.theme_legend": "Theme",
        "settings.preferences": "Preferences",
        "settings.language": "Language",
        "settings.theme_light": "Light",
        "settings.theme_dark": "Dark",
        "settings.theme_system": "System",
        "settings.reduce_animations": "Reduce animations",
        "settings.reduce_animations_hint": "Minimizes motion for accessibility and comfort.",
        "settings.readability_accessibility": "Accessibility",
        "settings.text_size": "Text size",
        "settings.text_size_small": "Small",
        "settings.text_size_normal": "Normal",
        "settings.text_size_large": "Large",
        "settings.language_en": "English",
        "settings.language_fr": "Français",
        "settings.title": "Settings",
        "settings.language_hint": "The page will reload when you change the language.",
        "site.title": "Adaptive Trails",
    },
    "fr": {
        "nav.demo": "Démo",
        "nav.all_trails": "Tous les sentiers",
        "nav.my_trails": "Mes sentiers",
        "nav.profile": "Profil",
        "nav.settings": "Paramètres",
        "footer.text": "Système de recommandation de sentiers adaptatif",
        "settings.theme": "Apparence",
        "settings.theme_legend": "Thème",
        "settings.preferences": "Préférences",
        "settings.language": "Langue",
        "settings.theme_light": "Clair",
        "settings.theme_dark": "Sombre",
        "settings.theme_system": "Système",
        "settings.reduce_animations": "Réduire les animations",
        "settings.reduce_animations_hint": "Réduit les mouvements pour l'accessibilité et le confort.",
        "settings.readability_accessibility": "Accessibilité",
        "settings.text_size": "Taille du texte",
        "settings.text_size_small": "Petite",
        "settings.text_size_normal": "Normale",
        "settings.text_size_large": "Grande",
        "settings.language_en": "English",
        "settings.language_fr": "Français",
        "settings.title": "Paramètres",
        "settings.language_hint": "La page se rechargera lorsque vous changez la langue.",
        "site.title": "Adaptive Trails",
    },
}

SUPPORTED_LOCALES = ["en", "fr"]
DEFAULT_LOCALE = "en"


def get_translation(locale: str, key: str) -> str:
    """Return translation for key in locale, or key if missing."""
    if locale not in TRANSLATIONS:
        locale = DEFAULT_LOCALE
    return TRANSLATIONS.get(locale, {}).get(key) or TRANSLATIONS.get(DEFAULT_LOCALE, {}).get(key) or key
