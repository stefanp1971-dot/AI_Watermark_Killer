import os, json
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty
from kivy.lang import Builder
from PIL import Image, ImageEnhance
from kivy.utils import platform
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button

# 1. SYSTEMSRACHE ERMITTELN & TEXTE LADEN
lang = "en"
if platform == 'android':
    try:
        from jnius import autoclass
        lang = autoclass('java.util.Locale').getDefault().getLanguage().lower()
    except: pass

with open('strings.json', 'r', encoding='utf-8') as f:
    TXT = json.load(f).get(lang, json.load(f)["en"])

# 2. OBERFLAECHE LADEN
Builder.load_string(f'''
<MainScreen>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: 0.04, 0.04, 0.05, 1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: "90dp"
        padding: "20dp"
        Label:
            text: "{TXT['title']}"
            font_size: "20sp"
            bold: True
        Label:
            text: root.status_text
            font_size: "13sp"
    BoxLayout:
        orientation: 'vertical'
        padding: "20dp"
        spacing: "15dp"
        Button:
            text: "{TXT['btn_scan']}"
            size_hint_y: None
            height: "55dp"
            on_press: root.trigger_scan()
        ScrollView:
            Label:
                id: file_list
                text: "-"
        Button:
            text: "{TXT['btn_clean']}"
            size_hint_y: None
            height: "58dp"
            on_press: root.trigger_cleaning()
''')

class MainScreen(BoxLayout):
    status_text = StringProperty("ℹ️ Ready")
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.found_files = []
        self.show_legal()

    def show_legal(self):
        content = BoxLayout(orientation='vertical', padding=15, spacing=10)
        lbl = Label(text=TXT["popup_text"], font_size="12sp", halign='center')
        btn = Button(text=TXT["popup_btn"] if "popup_btn" in TXT else "OK", size_hint_y=None, height="50dp")
        content.add_widget(lbl); content.add_widget(btn)
        popup = Popup(title=TXT["popup_title"], content=content, size_hint=(0.95, 0.75), auto_dismiss=False)
        btn.bind(on_press=popup.dismiss); popup.open()

    def trigger_scan(self):
        base_dir = os.path.join(os.path.expanduser("~"), "Pictures")
        if platform == 'android':
            from android.storage import primary_external_storage_path
            base_dir = os.path.join(primary_external_storage_path(), "Pictures")
        self.found_files = []
        if os.path.exists(base_dir):
            for r, _, fs in os.walk(base_dir):
                for f in fs:
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        p = os.path.join(r, f)
                        try:
                            with open(p, 'rb') as file: h = file.read(4096)
                            if b'c2pa' in h or b'SynthID' in h: self.found_files.append(p)
                        except: pass
        self.ids.file_list.text = "\\n".join([os.path.basename(x) for x in self.found_files]) if self.found_files else "Clean"

    def trigger_cleaning(self):
        for p in self.found_files:
            try:
                img = Image.open(p)
                w, h = img.size
                cropped = img.crop((1, 1, w - 1, h - 1))
                temp = ImageEnhance.Brightness(cropped).enhance(0.999)
                final = ImageEnhance.Brightness(temp).enhance(1.001)
                final.save(p, format=img.format, quality=96)
                img.close()
            except: pass
        self.ids.file_list.text = ""
        self.found_files = []

class AIKillerApp(App):
    def build(self): return MainScreen()

if __name__ == '__main__': AIKillerApp().run()
