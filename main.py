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
COLOR_BG_TREE = "#E8F0FE"
COLOR_BTN_NEW = "#4CAF50"
COLOR_BTN_SAVE = "#2196F3"
COLOR_BTN_DELETE = "#f44336"
COLOR_BTN_TEXT = "white"

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

plugins = config.get("plugins", [])

# Import plugins and apply colors
for plugin_name in plugins:
     # Remove .py extension
    if plugin_name.lower().endswith(".py"):
        plugin_name = plugin_name[:-3]

    try:
        plugin_module = importlib.import_module(plugin_name)
        if hasattr(plugin_module, "get_colors"):
            plugin_colors = plugin_module.get_colors()
            for var_name in ["COLOR_BG_TREE", "COLOR_BTN_NEW", "COLOR_BTN_SAVE", "COLOR_BTN_DELETE", "COLOR_BTN_TEXT"]:
                if var_name in plugin_colors:
                    globals()[var_name] = plugin_colors[var_name]
        print(f"Plugin loaded: {plugin_name}")
    except ImportError:
        print(f"Plugin '{plugin_name}' could not be loaded.")
    except Exception as e:
        print(f"Error while executing plugin '{plugin_name}': {e}")

MODEL_EXTS = (".ckpt", ".safetensors", ".dduf", ".pt")
SESSION_BASE_DIR = "model_sessions"
CONFIG_FILE = "config.json"


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

        # Make sure the key exists
        if "plugins" not in self.config:
            self.config["plugins"] = []

        layout = QVBoxLayout()
        self.label = QLabel("Imported plugins:")
        layout.addWidget(self.label)

        self.plugin_list = QListWidget()
        self.plugin_list.addItems(self.config["plugins"])
        layout.addWidget(self.plugin_list)

        btn_layout = QHBoxLayout()
        self.add_button = QPushButton("add")
        self.add_button.clicked.connect(self.add_plugin)
        btn_layout.addWidget(self.add_button)

        self.delete_button = QPushButton("delete")
        self.delete_button.clicked.connect(self.delete_plugin)
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
                self, "Confirm deletion",
                f"Do you really want to delete {item.text()}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
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

        # Linke Sidebar: Modelle
        self.model_tree = QtWidgets.QTreeWidget()
        self.model_tree.setHeaderHidden(True)
        self.model_tree.itemClicked.connect(self.load_sessions)
        self.model_tree.setStyleSheet(f"QTreeWidget {{background-color: {COLOR_BG_TREE};}}")
        self.splitter.addWidget(self.model_tree)

        # Rechte Seite: Editor & Session-Liste
        right_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter.addWidget(right_splitter)

        self.session_list = QtWidgets.QListWidget()
        self.session_list.itemClicked.connect(self.load_file)
        self.session_list.setAlternatingRowColors(True)
        self.session_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.session_list.customContextMenuRequested.connect(self.open_context_menu)
        right_splitter.addWidget(self.session_list)

        # Editor
        editor_container = QtWidgets.QWidget()
        editor_layout = QtWidgets.QVBoxLayout()
        form_layout = QtWidgets.QFormLayout()
        self.pos_input = QtWidgets.QTextEdit()
        self.neg_input = QtWidgets.QTextEdit()
        self.notes_input = QtWidgets.QTextEdit()
        form_layout.addRow("Positive Prompt:", self.pos_input)
        form_layout.addRow("Negative Prompt:", self.neg_input)
        form_layout.addRow("Notes:", self.notes_input)

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

        button_layout = QHBoxLayout()
        self.new_btn = QtWidgets.QPushButton("New")
        self.save_btn = QtWidgets.QPushButton("Save")
        self.delete_btn = QtWidgets.QPushButton("delete")
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
        right_splitter.addWidget(scroll)

        # Menü
        menubar = self.menuBar()
        settings_menu = menubar.addMenu("Settings")
        model_path_action = QtWidgets.QAction("Change model path", self)
        model_path_action.triggered.connect(self.select_model_path)
        settings_menu.addAction(model_path_action)
        lora_path_action = QtWidgets.QAction("Change LoRA path", self)
        lora_path_action.triggered.connect(self.select_lora_path)
        settings_menu.addAction(lora_path_action)
        # Menü: Plugin-Verwaltung hinzufügen
        plugin_action = QtWidgets.QAction("Manage plugins", self)
        plugin_action.triggered.connect(self.open_plugin_window)
        settings_menu.addAction(plugin_action)


        # Start
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
        


    def load_sessions(self, item):
        if item.parent() is None:
            return  # Category clicked

        model_name = item.text(0)
        parent_text = item.parent().text(0)
        self.current_model_type = "LoRA" if parent_text == "LoRAs" else "Base"

        model_folder = os.path.join(SESSION_BASE_DIR, model_name)
        self.session_list.clear()
        if os.path.exists(model_folder):
            for f in sorted(os.listdir(model_folder)):
                if f.endswith(".txt"):
                    self.session_list.addItem(f)

        self.clear_editor()
        self.load_editor_fields(self.current_model_type)

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
                    self.parse_file_content(content)
                except json.JSONDecodeError:
                    QtWidgets.QMessageBox.warning(
                        self, "Error", "The file does not contain valid JSON. Editor is being cleared."
                    )
                    self.clear_editor()
            else:
                self.clear_editor()

    def parse_file_content(self, content):
        data = json.loads(content)
        self.pos_input.setPlainText(data.get("positive_prompt", ""))
        self.neg_input.setPlainText(data.get("negative_prompt", ""))
        self.notes_input.setPlainText(data.get("notes", ""))

        # All optional fields: check if available
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
        now = datetime.now().strftime("%Y.%m.%d")
        self.session_list.addItem(f"{now}.txt")
        self.session_list.setCurrentRow(self.session_list.count() - 1)

    def save_file(self):
        current_item = self.session_list.currentItem()
        if not current_item:
            self.new_file()
            current_item = self.session_list.currentItem()

        model_item = self.model_tree.currentItem()
        if not model_item or not model_item.parent():
            return
        model_name = model_item.text(0)
        file_path = os.path.join(SESSION_BASE_DIR, model_name, current_item.text())
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.gather_file_content())
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
