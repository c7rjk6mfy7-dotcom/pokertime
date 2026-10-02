import json
import os
import random
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.properties import NumericProperty, BooleanProperty, StringProperty
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.utils import get_color_from_hex
from kivy.lang import Builder
from kivy.animation import Animation
from kivy.metrics import dp

# -------- Загрузка KV --------
KV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pokertimer.kv')
try:
    Builder.load_file(KV_PATH)
except Exception:
    print("ОШИБКА загрузки KV:")
    traceback.print_exc()

# -------- Пути к ресурсам --------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOASTY_PATH = os.path.join(BASE_DIR, 'toasty.mp3')

CARD_FILES_CANDIDATES = [
    'card.png',
    'card1.png', 'card2.png', 'card3.png', 'card4.png',
    'f1.png', 'f2.png', 'f3.png', 'f4.png',
]
FALLING_IMAGES = [
    os.path.join(BASE_DIR, name)
    for name in CARD_FILES_CANDIDATES
    if os.path.exists(os.path.join(BASE_DIR, name))
]

# -------- Цвета --------
BG_GREEN = get_color_from_hex('#005339')
ACCENT   = get_color_from_hex('#00d9a3')
YELLOW   = get_color_from_hex('#ffd93d')
RED      = get_color_from_hex('#ff5252')
TIMER_WHITE = get_color_from_hex('#ffffff')

# -------- Настройки по умолчанию --------
DEFAULT_SETTINGS = {
    'start_sb': 100,
    'start_bb': 200,
    'level_minutes': 15,
    'break_minutes': 10,
    'levels_per_break': 5,
    'max_levels': 30,
}


def load_settings():
    path = os.path.join(App.get_running_app().user_data_dir, 'settings.json')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            return merged
        except Exception:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    path = os.path.join(App.get_running_app().user_data_dir, 'settings.json')
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Не удалось сохранить настройки: {e}")


def build_structure(settings):
    structure = []
    sb = settings['start_sb']
    bb = settings['start_bb']
    level_num = 1
    max_levels = settings['max_levels']
    step_multipliers = [1.0, 1.5, 2.0, 3.0, 4.0]

    while level_num <= max_levels:
        for mult in step_multipliers:
            if level_num > max_levels:
                break
            sb_cur = int(round(sb * mult / 10.0) * 10)
            bb_cur = int(round(bb * mult / 10.0) * 10)
            structure.append({
                'type': 'level',
                'number': level_num,
                'sb': sb_cur,
                'bb': bb_cur,
                'duration': settings['level_minutes'] * 60,
            })
            level_num += 1

        sb *= 2
        bb *= 2

        if (level_num <= max_levels and
                (level_num - 1) % settings['levels_per_break'] == 0):
            structure.append({
                'type': 'break',
                'number': 0,
                'sb': 0,
                'bb': 0,
                'duration': settings['break_minutes'] * 60,
            })

    return structure


# ================== ПАДАЮЩАЯ КАРТА ==================
class FallingCard(Image):
    def __init__(self, source, start_x, duration, angle, **kwargs):
        super().__init__(**kwargs)
        self.source = source
        self.size_hint = (None, None)
        base = os.path.basename(source).lower()
        if base.startswith('f'):
            self.size = (dp(48), dp(48))
        else:
            self.size = (dp(60), dp(85))
        self.pos = (start_x, Window.height)
        self.opacity = 0.9
        self.angle = angle
        fall = Animation(y=-self.height - 20, angle=angle,
                         duration=duration, t='linear')
        fall.bind(on_complete=lambda *_: self._remove_self())
        fall.start(self)

    def _remove_self(self):
        if self.parent:
            self.parent.remove_widget(self)


class CardsLayer(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._spawn_event = None

    def start_spawning(self):
        if self._spawn_event or not FALLING_IMAGES:
            return
        self._spawn_event = Clock.schedule_interval(self._spawn_card, 1.2)

    def stop_spawning(self):
        if self._spawn_event:
            self._spawn_event.cancel()
            self._spawn_event = None

    def _spawn_card(self, dt):
        source = random.choice(FALLING_IMAGES)
        base = os.path.basename(source).lower()
        card_w = dp(48) if base.startswith('f') else dp(60)
        side = random.choice(['left', 'right'])
        if side == 'left':
            x = random.uniform(0, max(1, Window.width * 0.12))
        else:
            x = random.uniform(
                Window.width * 0.88,
                max(Window.width * 0.88, Window.width - card_w)
            )
        duration = random.uniform(4.5, 7.5)
        angle = random.choice([-15, 10, 15, -10, 0])
        self.add_widget(FallingCard(source=source, start_x=x,
                                    duration=duration, angle=angle))


# ================== ГЛАВНЫЙ ЭКРАН ==================
class MainScreen(Screen):
    current_index = NumericProperty(0)
    time_left     = NumericProperty(0)
    running       = BooleanProperty(False)
    timer_text    = StringProperty("15:00")
    level_text    = StringProperty("level 1")
    blinds_text   = StringProperty("100/200")
    next_text     = StringProperty("next: 200/400")
    play_icon     = StringProperty("▶")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings = DEFAULT_SETTINGS.copy()
        self.structure = []
        self._clock_event = None
        self._toasty = None
        self._loaded = False

    def on_enter(self):
        Clock.schedule_once(self._enter_deferred, 0)

    def _enter_deferred(self, dt):
        if not self._loaded:
            self._load_sound()
            self._loaded = True
            self.reload_tournament()
            self.ids.cards_layer.start_spawning()
            Clock.schedule_once(lambda dt2: self._auto_start(), 0.5)
        else:
            self.reload_tournament()
            self.ids.cards_layer.start_spawning()

    def on_leave(self):
        if 'cards_layer' in self.ids:
            self.ids.cards_layer.stop_spawning()

    def _load_sound(self):
        try:
            if os.path.exists(TOASTY_PATH):
                self._toasty = SoundLoader.load(TOASTY_PATH)
                if self._toasty:
                    self._toasty.volume = 1.0
        except Exception:
            self._toasty = None

    def _play_toasty(self):
        if self._toasty:
            self._toasty.stop()
            self._toasty.play()

    def _auto_start(self):
        self._start()

    def reload_tournament(self):
        self._pause()
        self.settings = load_settings()
        self.structure = build_structure(self.settings)
        self.current_index = 0
        self._refresh_ui()

    def _refresh_ui(self):
        if not self.structure:
            return
        item = self.structure[self.current_index]
        if item['type'] == 'break':
            self.level_text  = "ПЕРЕРЫВ"
            self.blinds_text = "Отдых"
        else:
            self.level_text  = f"level {item['number']}"
            self.blinds_text = f"{item['sb']}/{item['bb']}"
        self.time_left = item['duration']
        self._update_timer_text()
        self._update_next_text()

    def _update_timer_text(self):
        m = self.time_left // 60
        s = self.time_left % 60
        self.timer_text = f"{m:02d}:{s:02d}"

    def _update_next_text(self):
        nxt = self.current_index + 1
        if nxt < len(self.structure):
            ni = self.structure[nxt]
            if ni['type'] == 'break':
                self.next_text = f"next: ПЕРЕРЫВ {ni['duration'] // 60} мин"
            else:
                self.next_text = f"next: {ni['sb']}/{ni['bb']}"
        else:
            self.next_text = "next: —"

    def toggle_timer(self):
        if self.running:
            self._pause()
        else:
            self._start()

    def _start(self):
        if self.time_left <= 0:
            self.time_left = self.structure[self.current_index]['duration']
        self.running = True
        self.play_icon = "⏸"
        if self._clock_event:
            self._clock_event.cancel()
        self._clock_event = Clock.schedule_interval(self._tick, 1.0)

    def _pause(self):
        self.running = False
        self.play_icon = "▶"
        if self._clock_event:
            self._clock_event.cancel()
            self._clock_event = None

    def _tick(self, dt):
        self.time_left -= 1
        if self.time_left < 0:
            self.time_left = 0
        self._update_timer_text()
        if self.time_left <= 60:
            self.ids.lbl_timer.color = RED
        else:
            self.ids.lbl_timer.color = TIMER_WHITE
        if self.time_left <= 0:
            self.next_level()

    def next_level(self):
        if self.current_index < len(self.structure) - 1:
            self.current_index += 1
            self._play_toasty()
            self._refresh_ui()
        else:
            self._pause()
            self.ids.lbl_timer.text = "ФИНАЛ"
            self.ids.lbl_timer.color = RED

    def prev_level(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._refresh_ui()

    def reset_tournament(self):
        self._pause()
        self.current_index = 0
        self._refresh_ui()
        self._start()

    def open_settings(self):
        self.manager.current = 'settings'


# ================== ЭКРАН НАСТРОЕК ==================
class SettingsScreen(Screen):
    def on_enter(self):
        Clock.schedule_once(self._enter_deferred, 0)

    def _enter_deferred(self, dt):
        s = load_settings()
        self.ids.inp_sb.text = str(s['start_sb'])
        self.ids.inp_bb.text = str(s['start_bb'])
        self.ids.inp_level_min.text = str(s['level_minutes'])
        self.ids.inp_break_min.text = str(s['break_minutes'])
        self.ids.inp_per_break.text = str(s['levels_per_break'])
        self.ids.inp_max_levels.text = str(s['max_levels'])
        self.ids.lbl_status.text = ""

    def _collect(self):
        return {
            'start_sb': max(1, int(self.ids.inp_sb.text or 100)),
            'start_bb': max(1, int(self.ids.inp_bb.text or 200)),
            'level_minutes': max(1, int(self.ids.inp_level_min.text or 15)),
            'break_minutes': max(1, int(self.ids.inp_break_min.text or 10)),
            'levels_per_break': max(1, int(self.ids.inp_per_break.text or 5)),
            'max_levels': max(1, int(self.ids.inp_max_levels.text or 30)),
        }

    def apply_and_back(self):
        try:
            s = self._collect()
            if s['start_bb'] < s['start_sb']:
                self.ids.lbl_status.text = "BB не может быть меньше SB"
                self.ids.lbl_status.color = RED
                return
            save_settings(s)
            self.manager.current = 'main'
        except ValueError:
            self.ids.lbl_status.text = "Проверь числа"
            self.ids.lbl_status.color = RED

    def back_to_main(self):
        self.manager.current = 'main'

    def reset_defaults(self):
        self.ids.inp_sb.text = str(DEFAULT_SETTINGS['start_sb'])
        self.ids.inp_bb.text = str(DEFAULT_SETTINGS['start_bb'])
        self.ids.inp_level_min.text = str(DEFAULT_SETTINGS['level_minutes'])
        self.ids.inp_break_min.text = str(DEFAULT_SETTINGS['break_minutes'])
        self.ids.inp_per_break.text = str(DEFAULT_SETTINGS['levels_per_break'])
        self.ids.inp_max_levels.text = str(DEFAULT_SETTINGS['max_levels'])
        self.ids.lbl_status.text = "Значения по умолчанию"


# ================== ПРИЛОЖЕНИЕ ==================
class PokerTimerApp(App):
    def build(self):
        self.title = "Poker House Timer"
        Window.clearcolor = BG_GREEN

        # Fullscreen — только для десктопа, на Android мешает
        from kivy.utils import platform
        if platform in ('win', 'linux', 'macosx'):
            Window.fullscreen = 'auto'
            Window.borderless = True
            Window.show_cursor = True

        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(SettingsScreen(name='settings'))

        Window.bind(on_key_down=self._on_key_down)
        self.sm = sm
        return sm

    def _on_key_down(self, window, key, scancode=None, codepoint=None,
                     modifier=None, **kwargs):
        """Клавиатура/пульт на десктопе и частично на Android."""
        current = self.sm.current
        if current == 'main':
            main = self.sm.get_screen('main')
            if key in (13, 32):     # Enter / Пробел
                main.toggle_timer()
                return True
            if key == 275:          # →
                main.next_level()
                return True
            if key == 276:          # ←
                main.prev_level()
                return True
            if key == 27:           # ESC — выход
                App.get_running_app().stop()
                return True
        elif current == 'settings':
            if key == 27:
                self.sm.current = 'main'
                return True
        return False


if __name__ == '__main__':
    PokerTimerApp().run()
