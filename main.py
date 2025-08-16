import sys
import os
import json
import re
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import importlib
import traceback
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QMessageBox, QFileDialog, QLabel
)

plugins_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Plugins")
if plugins_dir not in sys.path:
    sys.path.append(plugins_dir)

# Color variables
COLOR_WINDOW_BG = "#FFFFFF"                 # Main window background
COLOR_BTN_NEW = "#4CAF50"                   # "New" button background
COLOR_BTN_SAVE = "#2196F3"                  # "Save" button background
COLOR_BTN_DELETE = "#f44336"                # "Delete" button background
COLOR_BTN_TEXT = "white"                     # Text color for all main buttons

COLOR_MENUBAR_BG = "#FFFFFF"                # Menu bar background
COLOR_MENUBAR_TEXT = "#111111"              # Menu bar text

COLOR_TREE_BG = "#E8F0FE"                   # Model tree background
COLOR_TREE_TEXT = "#111111"                 # Model tree text
COLOR_TREE_SELECTED_BG = "#D0E4FF"          # Selected tree item background
COLOR_TREE_SELECTED_TEXT = "#111111"        # Selected tree item text

COLOR_FILTER_BG = "#FFFFFF"                  # Filter input background
COLOR_FILTER_TEXT = "#111111"                # Filter input text

COLOR_SESSION_BG = "#FFFFFF"                 # Session list background
COLOR_SESSION_ALT_BG = "#F7F7F7"            # Alternate row background in session list
COLOR_SESSION_TEXT = "#111111"              # Session list text
COLOR_SESSION_SELECTED_BG = "#CCE5FF"       # Selected session background
COLOR_SESSION_SELECTED_TEXT = "#111111"     # Selected session text

COLOR_TEXTEDIT_BG = "#FFFFFF"                # QTextEdit background
COLOR_TEXTEDIT_TEXT = "#111111"             # QTextEdit text

COLOR_FIELD_BG = "#FFFFFF"                   # QLineEdit background (tags, seed, size, sampler)
COLOR_FIELD_TEXT = "#111111"                 # QLineEdit text

COLOR_CONTROL_BG = "#FFFFFF"                 # QSpinBox / QDoubleSpinBox background
COLOR_CONTROL_TEXT = "#111111"               # QSpinBox / QDoubleSpinBox text

COLOR_SCROLLAREA_BG = "#FFFFFF"              # Scroll area background

COLOR_PLUGINWINDOW_BG = "#FFFFFF"           # Plugin manager window background
COLOR_PLUGINWINDOW_LABEL_TEXT = "#111111"   # Plugin manager labels text
COLOR_PLUGINLIST_BG = "#FFFFFF"             # Plugin list background
COLOR_PLUGINLIST_TEXT = "#111111"           # Plugin list text
COLOR_PLUGINBTN_BG = "#2196F3"              # Plugin manager buttons background
COLOR_PLUGINBTN_TEXT = "white"               # Plugin manager buttons text

COLOR_SUGGESTION_BG = "#FFFFFF"             # Autocomplete suggestion background
COLOR_SUGGESTION_TEXT = "#111111"           # Autocomplete suggestion text
COLOR_SUGGESTION_HOVER_BG = "#EFEFEF"       # Autocomplete suggestion hover background
COLOR_SUGGESTION_SELECTED_BG = "#DDEEFF"    # Autocomplete suggestion selected background


MODEL_EXTS = (".ckpt", ".safetensors", ".dduf", ".pt")
SESSION_BASE_DIR = "model_sessions"
CONFIG_FILE = "config.json"

# Load config
with open("config.json", "r") as f:
    config = json.load(f)
plugins = config.get("plugins", [])

# Import plugins and apply colors
for plugin_name in plugins:
    if plugin_name.lower().endswith(".py"):
        plugin_name = plugin_name[:-3]
    try:
        plugin_module = importlib.import_module(plugin_name)
        plugin_colors = {}
        if hasattr(plugin_module, "get_colors"):
            plugin_colors = plugin_module.get_colors()

        print(f"Plugin loaded: {plugin_name}")

        if isinstance(plugin_colors, dict):
            for var_name, var_value in plugin_colors.items():
                if not isinstance(var_name, str):
                    continue
                if var_name in globals():
                    globals()[var_name] = var_value 
                else:
                    print(f"Variable '{var_name}' does not exist and cannot be overwritten.")

    except ImportError:
        print(f"Plugin '{plugin_name}' konnte nicht geladen werden.")
    except Exception as e:
        print(f"Fehler beim Ausführen des Plugins '{plugin_name}': {e}")


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"plugins": [], "model_path": "", "lora_path": ""}
def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

class PluginWindow(QWidget):
    def __init__(self, config):
        super().__init__()
        self.setWindowTitle("Plugin-Verwaltung")
        self.config = config
        if "plugins" not in self.config:
            self.config["plugins"] = []
        self.setStyleSheet(f"QWidget {{ background-color: {COLOR_PLUGINWINDOW_BG}; color: {COLOR_PLUGINWINDOW_LABEL_TEXT}; }}")
        layout = QVBoxLayout()
        self.label = QLabel("Imported plugins:")
        self.label.setStyleSheet(f"QLabel {{ color: {COLOR_PLUGINWINDOW_LABEL_TEXT}; }}")
        layout.addWidget(self.label)
        self.plugin_list = QListWidget()
        self.plugin_list.addItems(self.config["plugins"])
        self.plugin_list.setStyleSheet(f"QListWidget {{ background-color: {COLOR_PLUGINLIST_BG}; color: {COLOR_PLUGINLIST_TEXT}; }}")
        layout.addWidget(self.plugin_list)
        btn_layout = QHBoxLayout()
        self.add_button = QPushButton("add")
        self.add_button.clicked.connect(self.add_plugin)
        self.add_button.setStyleSheet(f"background-color: {COLOR_PLUGINBTN_BG}; color: {COLOR_PLUGINBTN_TEXT};")
        btn_layout.addWidget(self.add_button)
        self.delete_button = QPushButton("delete")
        self.delete_button.clicked.connect(self.delete_plugin)
        self.delete_button.setStyleSheet(f"background-color: {COLOR_PLUGINBTN_BG}; color: {COLOR_PLUGINBTN_TEXT};")
        btn_layout.addWidget(self.delete_button)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def add_plugin(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select plugin file", filter="Python files (*.py)")
        if path:
            plugin_name = os.path.basename(path)
            if plugin_name not in self.config["plugins"]:
                self.config["plugins"].append(plugin_name)
                self.plugin_list.addItem(plugin_name)
                save_config(self.config)

    def delete_plugin(self):
        selected_items = self.plugin_list.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            reply = QMessageBox.question(
                self,
                "Confirm deletion",
                f"Do you really want to delete {item.text()}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                if item.text() in self.config["plugins"]:
                    self.config["plugins"].remove(item.text())
                self.plugin_list.takeItem(self.plugin_list.row(item))
                save_config(self.config)


class PromptManager(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Prompt Explorer")
        self.resize(900, 500)
        self.config = load_config()
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_plugins(self.config.get("plugins", []))
        self.model_path = self.config.get("model_path", "")
        self.lora_path = self.config.get("lora_path", "")
        self.splitter = QtWidgets.QSplitter()
        self.setCentralWidget(self.splitter)
        self.model_tree = QtWidgets.QTreeWidget()
        self.model_tree.setHeaderHidden(True)
        self.model_tree.itemClicked.connect(self.load_sessions)
        self.model_tree.setStyleSheet(
            f"QTreeWidget {{ background-color: {COLOR_TREE_BG}; color: {COLOR_TREE_TEXT}; }}"
            f"QTreeWidget::item:selected {{ background-color: {COLOR_TREE_SELECTED_BG}; color: {COLOR_TREE_SELECTED_TEXT}; }}"
        )
        self.splitter.addWidget(self.model_tree)
        right_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter.addWidget(right_splitter)
        self.filter_input = QtWidgets.QLineEdit()
        self.filter_input.setPlaceholderText("Filter by name or tag...")
        self.filter_input.textChanged.connect(self.apply_filter)
        self.filter_input.setStyleSheet(f"QLineEdit {{ background-color: {COLOR_FILTER_BG}; color: {COLOR_FILTER_TEXT}; }}")
        right_splitter.addWidget(self.filter_input)
        self.session_list = QtWidgets.QListWidget()
        self.session_list.itemClicked.connect(self.load_file)
        self.session_list.setAlternatingRowColors(True)
        self.session_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.session_list.customContextMenuRequested.connect(self.open_context_menu)
        self.session_list.setStyleSheet(
            "QListWidget {{ background-color: %s; color: %s; alternate-background-color: %s; }}"
            "QListWidget::item:selected {{ background-color: %s; color: %s; }}"
            % (COLOR_SESSION_BG, COLOR_SESSION_TEXT, COLOR_SESSION_ALT_BG, COLOR_SESSION_SELECTED_BG, COLOR_SESSION_SELECTED_TEXT)
        )
        right_splitter.addWidget(self.session_list)
        editor_container = QtWidgets.QWidget()
        editor_layout = QtWidgets.QVBoxLayout()
        form_layout = QtWidgets.QFormLayout()
        self.pos_input = QtWidgets.QTextEdit()
        self.neg_input = QtWidgets.QTextEdit()
        self.notes_input = QtWidgets.QTextEdit()
        self.tag_input = QtWidgets.QLineEdit()
        form_layout.addRow("Positive Prompt:", self.pos_input)
        form_layout.addRow("Negative Prompt:", self.neg_input)
        form_layout.addRow("Notes:", self.notes_input)
        form_layout.addRow("Tags:", self.tag_input)
        self.steps_input = QtWidgets.QSpinBox()
        self.steps_input.setRange(1, 1000)
        self.sampler_input = QtWidgets.QLineEdit()
        self.cfg_input = QtWidgets.QDoubleSpinBox()
        self.cfg_input.setRange(0.0, 1000.0)
        self.cfg_input.setSingleStep(0.1)
        self.seed_input = QtWidgets.QLineEdit("0")
        self.size_input = QtWidgets.QLineEdit("512x512")
        form_layout.addRow("Steps:", self.steps_input)
        form_layout.addRow("Sampler:", self.sampler_input)
        form_layout.addRow("CFG:", self.cfg_input)
        form_layout.addRow("Seed:", self.seed_input)
        form_layout.addRow("Size:", self.size_input)
        editor_layout.addLayout(form_layout)
        button_layout = QtWidgets.QHBoxLayout()
        self.new_btn = QtWidgets.QPushButton("New")
        self.save_btn = QtWidgets.QPushButton("Save")
        self.delete_btn = QtWidgets.QPushButton("Delete")
        self.new_btn.setStyleSheet(f"background-color: {COLOR_BTN_NEW}; color: {COLOR_BTN_TEXT};")
        self.save_btn.setStyleSheet(f"background-color: {COLOR_BTN_SAVE}; color: {COLOR_BTN_TEXT};")
        self.delete_btn.setStyleSheet(f"background-color: {COLOR_BTN_DELETE}; color: {COLOR_BTN_TEXT};")
        self.new_btn.clicked.connect(self.new_file)
        self.save_btn.clicked.connect(self.save_file)
        self.delete_btn.clicked.connect(self.delete_file)
        button_layout.addWidget(self.new_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.delete_btn)
        editor_layout.addLayout(button_layout)
        editor_container.setLayout(editor_layout)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(editor_container)
        scroll.setStyleSheet(f"QScrollArea {{ background-color: {COLOR_SCROLLAREA_BG}; }}")
        right_splitter.addWidget(scroll)
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        model_path_action = QtWidgets.QAction("Change model path", self)
        model_path_action.triggered.connect(self.select_model_path)
        settings_menu.addAction(model_path_action)
        lora_path_action = QtWidgets.QAction("Change LoRA path", self)
        lora_path_action.triggered.connect(self.select_lora_path)
        settings_menu.addAction(lora_path_action)
        plugin_action = QtWidgets.QAction("Manage plugins", self)
        plugin_action.triggered.connect(self.open_plugin_window)
        settings_menu.addAction(plugin_action)
        menubar.setStyleSheet(f"QMenuBar {{ background-color: {COLOR_MENUBAR_BG}; color: {COLOR_MENUBAR_TEXT}; }}")
        self.pos_input.setStyleSheet(f"QTextEdit {{ background-color: {COLOR_TEXTEDIT_BG}; color: {COLOR_TEXTEDIT_TEXT}; }}")
        self.neg_input.setStyleSheet(f"QTextEdit {{ background-color: {COLOR_TEXTEDIT_BG}; color: {COLOR_TEXTEDIT_TEXT}; }}")
        self.notes_input.setStyleSheet(f"QTextEdit {{ background-color: {COLOR_TEXTEDIT_BG}; color: {COLOR_TEXTEDIT_TEXT}; }}")
        self.tag_input.setStyleSheet(f"QLineEdit {{ background-color: {COLOR_FIELD_BG}; color: {COLOR_FIELD_TEXT}; }}")
        self.sampler_input.setStyleSheet(f"QLineEdit {{ background-color: {COLOR_FIELD_BG}; color: {COLOR_FIELD_TEXT}; }}")
        self.seed_input.setStyleSheet(f"QLineEdit {{ background-color: {COLOR_FIELD_BG}; color: {COLOR_FIELD_TEXT}; }}")
        self.size_input.setStyleSheet(f"QLineEdit {{ background-color: {COLOR_FIELD_BG}; color: {COLOR_FIELD_TEXT}; }}")
        self.steps_input.setStyleSheet(f"QSpinBox {{ background-color: {COLOR_CONTROL_BG}; color: {COLOR_CONTROL_TEXT}; }}")
        self.cfg_input.setStyleSheet(f"QDoubleSpinBox {{ background-color: {COLOR_CONTROL_BG}; color: {COLOR_CONTROL_TEXT}; }}")
        self.init_autocomplete()
        if not self.model_path or not os.path.isdir(self.model_path):
            self.select_model_path()
        else:
            self.scan_models()


    def open_plugin_window(self):
        self.plugin_window = PluginWindow(self.config)
        self.plugin_window.show()

    def select_model_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select model folder"
        )
        if path:
            self.model_path = path
            self.config["model_path"] = path
            save_config(self.config)
            self.scan_models()

    def select_lora_path(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select LoRA folder")
        if path:
            self.lora_path = path
            self.config["lora_path"] = path
            save_config(self.config)
            self.scan_models()

    def scan_models(self):
        if not os.path.exists(SESSION_BASE_DIR):
            os.makedirs(SESSION_BASE_DIR)

        self.model_tree.clear()

        # Base-models
        base_item = QtWidgets.QTreeWidgetItem(["Base-models"])
        self.model_tree.addTopLevelItem(base_item)
        if self.model_path and os.path.isdir(self.model_path):
            for file in os.listdir(self.model_path):
                if file.lower().endswith(MODEL_EXTS):
                    model_name = os.path.splitext(file)[0]
                    target_dir = os.path.join(SESSION_BASE_DIR, model_name)
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    QtWidgets.QTreeWidgetItem(base_item, [model_name])

        # LoRAs
        lora_item = QtWidgets.QTreeWidgetItem(["LoRAs"])
        self.model_tree.addTopLevelItem(lora_item)
        if self.lora_path and os.path.isdir(self.lora_path):
            for file in os.listdir(self.lora_path):
                if file.lower().endswith(MODEL_EXTS):
                    lora_name = os.path.splitext(file)[0]
                    target_dir = os.path.join(SESSION_BASE_DIR, lora_name)  # Create folder
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    QtWidgets.QTreeWidgetItem(lora_item, [lora_name])

        self.model_tree.expandAll()


    def open_context_menu(self, position):
        item = self.session_list.itemAt(position)
        if not item:
            return

        menu = QtWidgets.QMenu()
        rename_action = menu.addAction("Rename")
        export_action = menu.addAction("Export")
        action = menu.exec_(self.session_list.viewport().mapToGlobal(position))

        if action == rename_action:
            self.rename_file(item)
        elif action == export_action:
            self.export_file(item)

    def sanitize_filename(self, name):
        # Replace everything that is not alphanumeric or _ or -
        name = re.sub(r'[^\w\-]', '_', name)
        return name

    def rename_file(self, item):
        old_name = item.text()
        new_name, ok = QtWidgets.QInputDialog.getText(self, "Rename file", "New name:", text=old_name)
        if not ok or not new_name:
            return

        # Only file name, keep extension
        base, ext = os.path.splitext(old_name)
        new_name_safe = self.sanitize_filename(new_name) + ext

        model_item = self.model_tree.currentItem()
        if not model_item:
            return

        old_path = os.path.join(SESSION_BASE_DIR, model_item.text(0), old_name)
        new_path = os.path.join(SESSION_BASE_DIR, model_item.text(0), new_name_safe)

        try:
            os.rename(old_path, new_path)
            item.setText(new_name_safe)
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(self, "Error", f"File not found:\n{old_path}")
                
    def export_file(self, item):
        model_item = self.model_tree.currentItem()
        if not model_item or not model_item.parent():
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select a model first.")
            return

        model_name = model_item.text(0)
        file_path = os.path.join(SESSION_BASE_DIR, model_name, item.text())

        if not os.path.exists(file_path):
            QtWidgets.QMessageBox.warning(self, "Error", "File does not exist.")
            return

        # Read content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Export file path (Downloads folder)
        downloads_path = os.path.join(os.path.expanduser("~"), "downloads")
        export_name = f"{os.path.splitext(item.text())[0]}_export.txt"
        export_path = os.path.join(downloads_path, export_name)

        with open(export_path, "w", encoding="utf-8") as f:
            f.write(content)

        QtWidgets.QMessageBox.information(
            self, "Export completed", f"File exported to:\n{export_path}"
        )
        
    def load_sessions(self, item, column):
        if not item:
            return
        model_name = item.text(0)
        if not model_name:
            return

        self.session_list.clear()
        model_dir = os.path.join(SESSION_BASE_DIR, model_name)
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        for filename in os.listdir(model_dir):
            if filename.endswith(".json"):  # statt .txt
                file_path = os.path.join(model_dir, filename)
                tags = []
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        tags = data.get("tags", [])
                except Exception as e:
                    print(f"Fehler beim Laden von {filename}: {e}")

                item_widget = QtWidgets.QListWidgetItem(filename)
                item_widget.setData(QtCore.Qt.UserRole, tags)
                self.session_list.addItem(item_widget)

    def load_editor_fields(self, session_type):
        form_layout = self.steps_input.parent().layout()
        if not isinstance(form_layout, QtWidgets.QFormLayout):
            return

        if session_type == "LoRA":
            # Show relevant fields + labels
            for i in range(form_layout.rowCount()):
                label_item = form_layout.itemAt(i, QtWidgets.QFormLayout.LabelRole)
                field_item = form_layout.itemAt(i, QtWidgets.QFormLayout.FieldRole)

                # If label/field None -> skip
                label_widget = label_item.widget() if label_item else None
                field_widget = field_item.widget() if field_item else None

                if field_widget in [self.pos_input, self.neg_input, self.notes_input]:
                    if label_widget:
                        label_widget.show()
                    field_widget.show()
                else:
                    if label_widget:
                        label_widget.hide()
                    if field_widget:
                        field_widget.hide()

        else:
            # View all
            for i in range(form_layout.rowCount()):
                label_item = form_layout.itemAt(i, QtWidgets.QFormLayout.LabelRole)
                field_item = form_layout.itemAt(i, QtWidgets.QFormLayout.FieldRole)
                if label_item and label_item.widget():
                    label_item.widget().show()
                if field_item and field_item.widget():
                    field_item.widget().show()

    def load_file(self, item):
        model_item = self.model_tree.currentItem()
        if not model_item or not model_item.parent():
            return

        model_name = model_item.text(0)
        file_path = os.path.join(SESSION_BASE_DIR, model_name, item.text())

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                try:
                    # Versuch JSON zu laden
                    self.parse_file_content(content)
                except json.JSONDecodeError:
                    # Fallback für Plain TXT
                    for line in content.splitlines():
                        if line.startswith("Positive Prompt:"):
                            self.pos_input.setPlainText(line.replace("Positive Prompt:", "").strip())
                        elif line.startswith("Negative Prompt:"):
                            self.neg_input.setPlainText(line.replace("Negative Prompt:", "").strip())
                        elif line.startswith("Notes:"):
                            self.notes_input.setPlainText(line.replace("Notes:", "").strip())
                        elif line.startswith("Tags:"):
                            self.tag_input.setText(line.replace("Tags:", "").strip())
            else:
                self.clear_editor()


    def parse_file_content(self, content):
        data = json.loads(content)
        self.pos_input.setPlainText(data.get("positive_prompt", ""))
        self.neg_input.setPlainText(data.get("negative_prompt", ""))
        self.notes_input.setPlainText(data.get("notes", ""))
        tags = data.get("tags", [])

        if isinstance(tags, list):
            tags = ", ".join(tags)
            
        self.tag_input.setText(tags)
        self.steps_input.setValue(data.get("steps", 1))
        self.sampler_input.setText(data.get("sampler", ""))
        self.cfg_input.setValue(data.get("cfg", 7.0))

        seed_val = data.get("seed", 0)
        try:
            seed_val = int(seed_val)
        except (ValueError, TypeError):
            seed_val = 0
        self.seed_input.setText(str(seed_val))

        self.size_input.setText(data.get("size", "512x512"))



    def gather_file_content(self):
        content = {
            "positive_prompt": self.pos_input.toPlainText(),
            "negative_prompt": self.neg_input.toPlainText(),
            "notes": self.notes_input.toPlainText(),
            "tags": self.tag_input.text()
        }

        if getattr(self, "current_model_type", "Base") != "LoRA":
            try:
                seed_val = int(self.seed_input.text())
            except ValueError:
                seed_val = 0
            content.update({
                "steps": self.steps_input.value(),
                "sampler": self.sampler_input.text(),
                "cfg": self.cfg_input.value(),
                "seed": seed_val,
                "size": self.size_input.text()
            })

        return json.dumps(content, indent=4)


    def clear_editor(self):
        self.pos_input.clear()
        self.neg_input.clear()
        self.notes_input.clear()
        self.steps_input.setValue(1)
        self.sampler_input.clear()
        self.cfg_input.setValue(7.0)
        self.seed_input.setText("0")
        self.size_input.setText("512x512")

    def new_file(self):
        self.clear_editor()

        now = datetime.now().strftime("%Y.%m.%d_%H-%M-%S")
        file_name = f"{now}.json" 
        folder_path = os.path.join("sessions", "default_model")  
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, file_name)

        data = {
            "positive": "",
            "negative": "",
            "notes": "",
            "tags": []
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        item = QtWidgets.QListWidgetItem(file_name)
        item.setData(QtCore.Qt.UserRole, [])
        self.session_list.addItem(item)
        self.session_list.setCurrentItem(item)

        self.pos_input.clear()
        self.neg_input.clear()
        self.notes_input.clear()
        self.tag_input.clear()

    def save_file(self):
        current_item = self.session_list.currentItem()
        if not current_item:
            self.new_file()
            current_item = self.session_list.currentItem()

        model_item = self.model_tree.currentItem()
        if not model_item or not model_item.parent():
            return
        model_name = model_item.text(0)

        folder_path = os.path.join(SESSION_BASE_DIR, model_name)
        os.makedirs(folder_path, exist_ok=True)

        file_name = current_item.text()
        if not file_name.endswith(".json"):
            file_name += ".json"
        file_path = os.path.join(folder_path, file_name)

        tags = [tag.strip() for tag in self.tag_input.text().split(",") if tag.strip()]
        data = {
            "positive": self.pos_input.toPlainText(),
            "negative": self.neg_input.toPlainText(),
            "notes": self.notes_input.toPlainText(),
            "tags": tags
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        current_item.setData(QtCore.Qt.UserRole, tags)

        try:
            with open("tags.json", "r", encoding="utf-8") as f:
                all_tags = json.load(f)
        except FileNotFoundError:
            all_tags = []

        updated = False
        for tag in tags:
            if tag not in all_tags:
                all_tags.append(tag)
                updated = True

        if updated:
            with open("tags.json", "w", encoding="utf-8") as f:
                json.dump(all_tags, f, ensure_ascii=False, indent=4)
            self.all_tags = all_tags

        QtWidgets.QMessageBox.information(self, "Saved", "File saved!")

    def delete_file(self):
        current_item = self.session_list.currentItem()
        if current_item:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Confirm deletion",
                f"Do you really want to delete '{current_item.text()}'?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )
            if reply == QtWidgets.QMessageBox.Yes:
                model_item = self.model_tree.currentItem()
                model_name = model_item.text(0)
                file_path = os.path.join(SESSION_BASE_DIR, model_name, current_item.text())
                if os.path.exists(file_path):
                    os.remove(file_path)
                self.session_list.takeItem(self.session_list.row(current_item))
                self.clear_editor()

    def apply_filter(self):
        filter_text = self.filter_input.text().lower()

        for i in range(self.session_list.count()):
            item = self.session_list.item(i)
            name = item.text().lower()
            tags = item.data(QtCore.Qt.UserRole)

            if tags:  
                tags_str = ",".join(tags).lower() if isinstance(tags, list) else str(tags).lower()
            else:
                tags_str = ""
            item.setHidden(filter_text not in name and filter_text not in tags_str)

    def init_autocomplete(self):
        self.suggestion_list = QtWidgets.QListWidget(self)
        self.suggestion_list.setWindowFlags(
            QtCore.Qt.ToolTip | QtCore.Qt.FramelessWindowHint
        )
        self.suggestion_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.suggestion_list.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.suggestion_list.setStyleSheet(
            f"QListWidget {{ background-color: {COLOR_SUGGESTION_BG}; color: {COLOR_SUGGESTION_TEXT}; }}"
            f"QListWidget::item:hover {{ background-color: {COLOR_SUGGESTION_HOVER_BG}; }}"
            f"QListWidget::item:selected {{ background-color: {COLOR_SUGGESTION_SELECTED_BG}; }}"
        )
        self.suggestion_list.hide()
        self.suggestion_list.itemClicked.connect(self.insert_suggestion)
        self.tag_input.textEdited.connect(self.update_suggestions)
        self.tag_input.installEventFilter(self)
        try:
            with open("tags.json", "r", encoding="utf-8") as f:
                self.all_tags = json.load(f)
        except FileNotFoundError:
            self.all_tags = []


    def update_suggestions(self, text):
        cursor_pos = self.tag_input.cursorPosition()
        current_text = text[:cursor_pos]

        if "," in current_text:
            last_part = current_text.split(",")[-1].strip()
        else:
            last_part = current_text.strip()

        if not last_part:
            self.suggestion_list.hide()
            return

        matches = [t for t in self.all_tags if t.lower().startswith(last_part.lower())]
        matches = matches[:3]

        if not matches:
            self.suggestion_list.hide()
            return

        self.suggestion_list.clear()
        for m in matches:
            self.suggestion_list.addItem(m)

        pos = self.tag_input.mapToGlobal(QtCore.QPoint(0, -self.suggestion_list.sizeHintForRow(0) * len(matches)))
        self.suggestion_list.move(pos)
        self.suggestion_list.resize(self.tag_input.width(), self.suggestion_list.sizeHintForRow(0) * len(matches))
        self.suggestion_list.show()

    def insert_suggestion(self, item):
        cursor_pos = self.tag_input.cursorPosition()
        text = self.tag_input.text()

        parts = [p.strip() for p in text.split(",")]
        if len(parts) > 1:
            parts[-1] = item.text()
        else:
            parts[0] = item.text()

        new_text = ", ".join(p for p in parts if p)  
        self.tag_input.setText(new_text)
        self.suggestion_list.hide()

    def eventFilter(self, source, event):
        if source is self.tag_input:
            if event.type() == QtCore.QEvent.FocusOut:
                self.suggestion_list.hide()
        return super().eventFilter(source, event)

class PluginManager:
    def __init__(self):
        self.plugins = {}

    def load_plugins(self, plugin_files):
        """Loads all specified plugins and saves the modules in the dict self.plugins"""
        for file_name in plugin_files:
            path = os.path.join("plugins", file_name)  #if you use a plugins folder
            if not os.path.exists(path):
                print(f"Plugin not found: {path}")
                continue
            module_name = os.path.splitext(file_name)[0]
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None:
                print(f"Spec could not be created: {file_name}")
                continue
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                self.plugins[module_name] = module
                print(f"Plugin loaded: {module_name}")
            except Exception as e:
                print(f"Error loading {module_name}: {e}")
                traceback.print_exc()

    def run_modify_color(self, data):
        for plugin in self.plugins:
            if hasattr(plugin, "ModifyColor"):
                try:
                    plugin.ModifyColor(data)
                    print(f"[PluginManager] ModifyColor executed for {plugin.__name__}")
                except Exception as e:
                    print(f"[PluginManager] ❌ Error in ModifyColor of {plugin.__name__}: {e}")
                    traceback.print_exc()

    def run_add_settings(self, core_data):
        for plugin in self.plugins:
            if hasattr(plugin, "AddSettings"):
                try:
                    plugin.AddSettings(core_data)
                    print(f"[PluginManager] AddSettings ausgeführt für {plugin.__name__}")
                except Exception as e:
                    print(f"[PluginManager] ❌ Error in AddSettings of {plugin.__name__}: {e}")
                    traceback.print_exc()

    def run_run(self, core_data):
        for plugin in self.plugins:
            if hasattr(plugin, "Run"):
                try:
                    plugin.Run(core_data)
                    print(f"[PluginManager] Run executed for {plugin.__name__}")
                except Exception as e:
                    print(f"[PluginManager] ❌ Error running {plugin.__name__}: {e}")
                    traceback.print_exc()

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = PromptManager()
    window.show()
    sys.exit(app.exec_())
