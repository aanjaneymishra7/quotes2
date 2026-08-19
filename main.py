"""Quote of the Day -- a small, warm, offline-first Android app.

Two screens: Home (today's quote) and Settings (colors, font, optional AI
key). All the actual logic -- which quote, how it's worded, how it's
persisted -- lives in quote_engine.py / ai_quotes.py / storage.py / theme.py,
kept deliberately free of any Kivy import so it's testable on its own. This
file is just the UI wiring on top of that.
"""
from __future__ import annotations

import os
from datetime import date

from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.utils import get_color_from_hex
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.label import MDLabel

import theme
from ai_quotes import generate_ai_message
from quote_engine import compose_daily_message, get_daily_quote, load_quotes
from storage import Storage

KV = """
#:import dp kivy.metrics.dp

<HomeScreen>:
    name: "home"
    MDFloatLayout:
        id: home_root
        md_bg_color: 1, 1, 1, 1

        MDIconButton:
            id: settings_button
            icon: "cog-outline"
            pos_hint: {"top": 0.98, "right": 0.97}
            theme_text_color: "Custom"
            text_color: 0.5, 0.5, 0.5, 1
            on_release: app.go_to_settings()

        MDCard:
            id: quote_card
            orientation: "vertical"
            size_hint: 0.88, 0.7
            pos_hint: {"center_x": 0.5, "center_y": 0.52}
            padding: dp(28)
            spacing: dp(14)
            radius: [24, 24, 24, 24]
            elevation: 2
            md_bg_color: 1, 1, 1, 1

            MDLabel:
                id: intro_label
                text: ""
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.5, 0.5, 0.5, 1
                font_size: "15sp"
                size_hint_y: None
                height: self.texture_size[1]

            Widget:
                size_hint_y: 0.06

            MDLabel:
                id: quote_label
                text: ""
                halign: "center"
                valign: "middle"
                theme_text_color: "Custom"
                text_color: 0.1, 0.1, 0.1, 1
                font_size: "26sp"

            MDLabel:
                id: author_label
                text: ""
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.5, 0.5, 0.5, 1
                font_size: "15sp"
                size_hint_y: None
                height: self.texture_size[1]

            Widget:
                size_hint_y: 0.06

            MDLabel:
                id: reflection_label
                text: ""
                halign: "center"
                theme_text_color: "Custom"
                text_color: 0.45, 0.45, 0.45, 1
                font_size: "14sp"
                size_hint_y: None
                height: self.texture_size[1]

        MDLabel:
            id: streak_label
            text: ""
            halign: "center"
            theme_text_color: "Custom"
            text_color: 0.6, 0.6, 0.6, 1
            font_size: "12sp"
            pos_hint: {"center_x": 0.5, "y": 0.02}
            size_hint_y: None
            height: dp(20)


<SettingsScreen>:
    name: "settings"
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.98, 0.98, 0.98, 1

        MDBoxLayout:
            orientation: "horizontal"
            size_hint_y: None
            height: dp(56)
            padding: [dp(8), dp(4)]
            MDIconButton:
                icon: "arrow-left"
                on_release: app.go_to_home()
            MDLabel:
                text: "Settings"
                font_style: "H6"
                halign: "left"

        ScrollView:
            size_hint_y: 1
            do_scroll_x: False

            MDBoxLayout:
                id: settings_column
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(10)
                padding: [dp(20), dp(8), dp(20), dp(32)]

                MDLabel:
                    text: "Color"
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: dp(24)

                ScrollView:
                    size_hint_y: None
                    height: dp(64)
                    do_scroll_y: False
                    MDBoxLayout:
                        id: palette_row
                        size_hint_x: None
                        width: self.minimum_width
                        spacing: dp(10)
                        padding: [dp(4), 0]

                MDLabel:
                    text: "Font"
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: dp(24)

                MDBoxLayout:
                    id: font_column
                    orientation: "vertical"
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(4)

                MDLabel:
                    text: "Text size"
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: dp(24)

                MDSlider:
                    id: font_size_slider
                    min: 18
                    max: 34
                    step: 1
                    size_hint_y: None
                    height: dp(36)

                MDLabel:
                    text: "AI upgrade (optional)"
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: dp(24)

                MDLabel:
                    text: "Add an Anthropic API key to get a freshly AI-written quote each day instead of one from the built-in collection. Leave blank to keep using the offline collection."
                    theme_text_color: "Secondary"
                    font_size: "12sp"
                    size_hint_y: None
                    height: self.texture_size[1]
                    text_size: self.width, None

                MDTextField:
                    id: api_key_field
                    hint_text: "Anthropic API key (optional)"
                    password: True
                    size_hint_y: None
                    height: dp(48)

                MDRaisedButton:
                    text: "Save"
                    pos_hint: {"center_x": 0.5}
                    on_release: app.save_settings_and_return()
"""


class HomeScreen(Screen):
    pass


class SettingsScreen(Screen):
    pass


class QuotesApp(MDApp):
    def build(self):
        self.title = "Quote of the Day"
        self.theme_cls.primary_palette = "Orange"
        Builder.load_string(KV)

        self._register_fonts()

        data_path = os.path.join(self.user_data_dir, "data.json")
        self.storage = Storage(path=data_path)
        self.quotes = load_quotes()

        self.sm = ScreenManager(transition=SlideTransition())
        self.home_screen = HomeScreen()
        self.settings_screen = SettingsScreen()
        self.sm.add_widget(self.home_screen)
        self.sm.add_widget(self.settings_screen)

        self._build_settings_widgets()
        self.refresh_today()
        self.apply_theme()

        return self.sm

    def on_resume(self):
        # Covers the "fresh quote is ready when I open the app" behavior
        # even when the app was only backgrounded (not fully closed) --
        # Android calls this when the app returns to the foreground.
        self.refresh_today()
        self.apply_theme()
        return True

    # -- fonts -------------------------------------------------------------

    def _register_fonts(self):
        for font in theme.FONTS:
            LabelBase.register(name=font["label"], fn_regular=font["file"])

    # -- daily quote logic --------------------------------------------------

    def refresh_today(self):
        settings = self.storage.load_settings()
        state = self.storage.load_state()

        quote, new_state = get_daily_quote(self.quotes, state, today=date.today())
        if new_state != state:
            self.storage.save_state(new_state)

        message = None
        api_key = settings.get("anthropic_api_key", "").strip()
        if api_key:
            message = generate_ai_message(api_key)
        if message is None:
            message = compose_daily_message(quote, today=date.today())

        self.current_message = message
        self.current_streak = new_state.streak
        self._update_home_widgets()

    def _update_home_widgets(self):
        ids = self.home_screen.ids
        msg = self.current_message
        ids.intro_label.text = msg["intro"]
        ids.quote_label.text = f'"{msg["text"]}"'
        ids.author_label.text = f'— {msg["author"]}'
        ids.reflection_label.text = msg["reflection"]

        streak = self.current_streak
        if streak >= 2:
            ids.streak_label.text = f"{streak} days in a row"
        else:
            ids.streak_label.text = ""

    # -- theming -------------------------------------------------------------

    def apply_theme(self):
        settings = self.storage.load_settings()
        palette = theme.get_palette(settings["palette_name"])
        font = theme.get_font(settings["font_label"])
        font_size = settings.get("font_size_sp", 26)

        bg = get_color_from_hex(palette["background"])
        card_color = get_color_from_hex(palette["card"])
        accent = get_color_from_hex(palette["accent"])
        text_color = get_color_from_hex(palette["text"])
        subtext_color = get_color_from_hex(palette["subtext"])

        Window.clearcolor = bg

        ids = self.home_screen.ids
        ids.home_root.md_bg_color = bg
        ids.quote_card.md_bg_color = card_color

        ids.intro_label.text_color = subtext_color
        ids.author_label.text_color = subtext_color
        ids.reflection_label.text_color = subtext_color
        ids.streak_label.text_color = accent

        ids.quote_label.text_color = text_color
        ids.quote_label.font_name = font["label"]
        ids.quote_label.font_size = f"{font_size}sp"

        ids.settings_button.text_color = accent

    # -- settings screen widgets ---------------------------------------------

    def _build_settings_widgets(self):
        ids = self.settings_screen.ids

        for palette in theme.PALETTES:
            swatch = MDRaisedButton(
                text="",
                md_bg_color=get_color_from_hex(palette["accent"]),
                size_hint=(None, None),
                size=(dp(48), dp(48)),
                rounded_button=True,
                on_release=lambda inst, name=palette["name"]: self._select_palette(name),
            )
            ids.palette_row.add_widget(swatch)

        self._font_buttons = {}
        for font in theme.FONTS:
            btn = MDFlatButton(
                text=f'{font["label"]} \u2014 {font["feel"]}',
                font_name=font["label"],
                on_release=lambda inst, label=font["label"]: self._select_font(label),
            )
            self._font_buttons[font["label"]] = btn
            ids.font_column.add_widget(btn)

        self._pending_palette = None
        self._pending_font = None

    def _select_palette(self, name):
        self._pending_palette = name

    def _select_font(self, label):
        self._pending_font = label

    def go_to_settings(self):
        settings = self.storage.load_settings()
        ids = self.settings_screen.ids
        ids.font_size_slider.value = settings.get("font_size_sp", 26)
        ids.api_key_field.text = settings.get("anthropic_api_key", "")
        self._pending_palette = settings.get("palette_name")
        self._pending_font = settings.get("font_label")
        self.sm.current = "settings"

    def go_to_home(self):
        self.sm.current = "home"

    def save_settings_and_return(self):
        settings = self.storage.load_settings()
        ids = self.settings_screen.ids

        if self._pending_palette:
            settings["palette_name"] = self._pending_palette
        if self._pending_font:
            settings["font_label"] = self._pending_font
        settings["font_size_sp"] = int(ids.font_size_slider.value)
        settings["anthropic_api_key"] = ids.api_key_field.text.strip()

        self.storage.save_settings(settings)
        self.apply_theme()
        self.refresh_today()
        self.sm.current = "home"


if __name__ == "__main__":
    QuotesApp().run()
