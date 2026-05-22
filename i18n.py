import json
import os

from version import APP_NAME, APP_TAGLINE

DEFAULT_LANG = "id"
SUPPORTED = ("id", "en")


def locales_dir(bundle_dir):
    return os.path.join(bundle_dir, "locales")


def load_locale_file(bundle_dir, lang):
    path = os.path.join(locales_dir(bundle_dir), f"{lang}.json")
    if not os.path.isfile(path):
        path = os.path.join(locales_dir(bundle_dir), f"{DEFAULT_LANG}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_language(data_dir, bundle_dir):
    config_path = os.path.join(data_dir, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                lang = json.load(f).get("language", DEFAULT_LANG)
            if lang in SUPPORTED:
                return lang
        except (OSError, json.JSONDecodeError):
            pass
    return DEFAULT_LANG


def save_language(data_dir, lang):
    if lang not in SUPPORTED:
        lang = DEFAULT_LANG
    config_path = os.path.join(data_dir, "config.json")
    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    config["language"] = lang
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return lang


class I18n:
    def __init__(self, bundle_dir, data_dir):
        self.bundle_dir = bundle_dir
        self.data_dir = data_dir
        self.lang = get_language(data_dir, bundle_dir)
        self._strings = load_locale_file(bundle_dir, self.lang)

    def t(self, key, **kwargs):
        text = self._strings.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text

    def set_language(self, lang):
        self.lang = save_language(self.data_dir, lang)
        self._strings = load_locale_file(self.bundle_dir, self.lang)
        return self.lang

    def web_strings(self):
        keys = [k for k in self._strings if k.startswith("web_")]
        return {k: self._strings[k] for k in keys}

    def app_title(self):
        name = self._strings.get("app_name", APP_NAME)
        tag = self._strings.get("app_tagline", APP_TAGLINE)
        return f"{name} ({tag})"
