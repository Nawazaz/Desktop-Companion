"""
SettingsDialog — lets the user edit the companion's name/personality and
manage the list of apps it can open, without touching any code. Saves back
to settings.json on "Save".
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QHeaderView, QMessageBox,
    QListWidget, QAbstractItemView
)
from PySide6.QtCore import Qt

from settings import load_settings, save_settings
from app_discovery import discover_installed_apps


class AppPickerDialog(QDialog):
    """Shows every app found in the Start Menu, lets you multi-select which
    ones to add to the launcher list."""

    def __init__(self, discovered_apps, existing_names):
        super().__init__()
        self.setWindowTitle("Pick Installed Apps")
        self.resize(420, 480)
        self.selected = []  # filled in on Add Selected

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Found {len(discovered_apps)} apps. Select one or more to add:"))

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._apps_by_row = []
        for name, path in discovered_apps:
            if name.lower() in existing_names:
                continue  # skip ones already in the table
            self.list_widget.addItem(f"{name}   —   {path}")
            self._apps_by_row.append((name, path))
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("Add Selected")
        add_btn.clicked.connect(self._add_selected)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(add_btn)
        layout.addLayout(btn_row)

    def _add_selected(self):
        for index in self.list_widget.selectedIndexes():
            self.selected.append(self._apps_by_row[index.row()])
        self.accept()


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Companion Settings")
        self.resize(480, 420)

        self.settings = load_settings()

        layout = QVBoxLayout(self)

        # --- name / personality ---
        form = QFormLayout()
        self.name_edit = QLineEdit(self.settings.get("companion_name", "Companion"))
        form.addRow("Companion name:", self.name_edit)

        self.personality_edit = QTextEdit(self.settings.get("personality", ""))
        self.personality_edit.setPlaceholderText(
            "Optional: e.g. 'speaks a bit sarcastically', 'loves puns', "
            "'is very encouraging about studying'..."
        )
        self.personality_edit.setMaximumHeight(70)
        form.addRow("Personality notes:", self.personality_edit)
        layout.addLayout(form)

        layout.addWidget(QLabel("Note: name/personality changes take effect the next time you start the app."))

        # --- app list table ---
        layout.addWidget(QLabel("Apps it can open (type 'open <name>' in chat):"))
        self.app_table = QTableWidget(0, 2)
        self.app_table.setHorizontalHeaderLabels(["Name", "Path (or command)"])
        self.app_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.app_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._populate_app_table()
        layout.addWidget(self.app_table)

        # add/remove row buttons
        row_btns = QHBoxLayout()
        add_btn = QPushButton("Add App")
        add_btn.clicked.connect(self._add_row)
        discover_btn = QPushButton("Discover Installed Apps...")
        discover_btn.clicked.connect(self._discover_apps)
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected_row)
        row_btns.addWidget(add_btn)
        row_btns.addWidget(discover_btn)
        row_btns.addWidget(remove_btn)
        layout.addLayout(row_btns)

        # save/cancel
        action_btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.close)
        action_btns.addStretch()
        action_btns.addWidget(cancel_btn)
        action_btns.addWidget(save_btn)
        layout.addLayout(action_btns)

    def _populate_app_table(self):
        apps = self.settings.get("apps", {})
        self.app_table.setRowCount(0)
        for name, paths in apps.items():
            self._add_row(name=name, path=paths[0] if paths else "")

    def _add_row(self, checked=False, name="", path=""):
        row = self.app_table.rowCount()
        self.app_table.insertRow(row)
        self.app_table.setItem(row, 0, QTableWidgetItem(name))
        self.app_table.setItem(row, 1, QTableWidgetItem(path))

    def _remove_selected_row(self):
        row = self.app_table.currentRow()
        if row >= 0:
            self.app_table.removeRow(row)

    def _discover_apps(self):
        discovered = discover_installed_apps()

        if not discovered:
            QMessageBox.information(
                self, "No apps found",
                "Couldn't find any apps automatically. This needs the 'pywin32' "
                "package - install it with:\n\npip install pywin32\n\nthen try again. "
                "You can still add apps manually below in the meantime."
            )
            return

        existing_names = set()
        for row in range(self.app_table.rowCount()):
            item = self.app_table.item(row, 0)
            if item:
                existing_names.add(item.text().strip().lower())

        picker = AppPickerDialog(discovered, existing_names)
        if picker.exec() == QDialog.Accepted:
            for name, path in picker.selected:
                self._add_row(name=name, path=path)

    def _save(self):
        apps = {}
        for row in range(self.app_table.rowCount()):
            name_item = self.app_table.item(row, 0)
            path_item = self.app_table.item(row, 1)
            name = name_item.text().strip().lower() if name_item else ""
            path = path_item.text().strip() if path_item else ""
            if name and path:
                apps[name] = [path]

        self.settings["companion_name"] = self.name_edit.text().strip() or "Companion"
        self.settings["personality"] = self.personality_edit.toPlainText().strip()
        self.settings["apps"] = apps

        save_settings(self.settings)
        QMessageBox.information(self, "Saved", "Settings saved! App list changes apply immediately.\nName/personality changes apply next time you start the app.")
        self.close()