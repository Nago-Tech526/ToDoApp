import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QTabWidget,
    QCheckBox, QDateEdit, QDialog, QFormLayout, QDialogButtonBox, QLabel
)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont

class TaskEditDialog(QDialog):
    def __init__(self, task_widget):
        super().__init__(task_widget)
        self.setWindowTitle("タスク編集")
        # 編集ウィンドウを常に前面に表示
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.task_widget = task_widget
        layout = QFormLayout(self)
        
        self.name_edit = QLineEdit(self.task_widget.name)
        layout.addRow("タスク名:", self.name_edit)
        
        self.details_edit = QLineEdit(self.task_widget.details)
        layout.addRow("詳細:", self.details_edit)
        
        self.date_edit = QDateEdit(self.task_widget.due_date)
        self.date_edit.setCalendarPopup(True)
        layout.addRow("期限:", self.date_edit)
        
        # ラベルは最大3個まで（各フィールドは空欄可）
        self.label_edits = []
        for i in range(3):
            text = self.task_widget.labels[i] if i < len(self.task_widget.labels) else ""
            le = QLineEdit(text)
            le.setPlaceholderText("ラベル")
            layout.addRow(f"ラベル{i+1}:", le)
            self.label_edits.append(le)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept(self):
        new_name = self.name_edit.text().strip()
        if not new_name:
            return  # タスク名は必須
        self.task_widget.name = new_name
        self.task_widget.details = self.details_edit.text().strip()
        self.task_widget.due_date = self.date_edit.date()
        new_labels = [le.text().strip() for le in self.label_edits if le.text().strip() != ""]
        self.task_widget.labels = new_labels
        super().accept()

class TaskWidget(QWidget):
    def __init__(self, name, due_date=None, details="", labels=None):
        if labels is None:
            labels = []
        super().__init__()
        self.name = name
        self.details = details
        self.labels = labels
        self.due_date = due_date if due_date else QDate.currentDate()
        
        # メインレイアウト：チェックボックス、中央のタスク表示、編集ボタン
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        self.checkbox = QCheckBox()
        self.checkbox.toggled.connect(self.updateStatus)
        main_layout.addWidget(self.checkbox)
        
        # 中央の表示エリア（2行構成）
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1行目：タスク名のみ表示
        self.name_label = QLabel(self.name)
        center_layout.addWidget(self.name_label)
        
        # 2行目：期限とラベルを横並びで表示
        second_row_widget = QWidget()
        second_row_layout = QHBoxLayout(second_row_widget)
        second_row_layout.setContentsMargins(0, 0, 0, 0)
        self.due_label = QLabel(self.due_date.toString("yyyy-MM-dd"))
        second_row_layout.addWidget(self.due_label)
        # ラベルは"#"付きで表示
        self.labels_label = QLabel(", ".join(["#" + label for label in self.labels]))
        second_row_layout.addWidget(self.labels_label)
        center_layout.addWidget(second_row_widget)
        
        main_layout.addWidget(center_widget)
        main_layout.addStretch()  # ストレッチを入れて、右端に寄せる
        
        # 編集用ボタン（右端に配置）
        self.edit_button = QPushButton("✏")
        self.edit_button.setFixedSize(30, 30)
        self.edit_button.clicked.connect(self.openEditDialog)
        main_layout.addWidget(self.edit_button)
        
        self.updateStatus(self.checkbox.isChecked())
    
    def updateStatus(self, checked):
        # 完了状態の場合、取り消し線とグレー表示
        font = self.name_label.font()
        font.setStrikeOut(checked)
        self.name_label.setFont(font)
        self.due_label.setFont(font)
        self.labels_label.setFont(font)
        if checked:
            self.name_label.setStyleSheet("color: gray;")
            self.due_label.setStyleSheet("color: gray;")
            self.labels_label.setStyleSheet("color: gray;")
        else:
            self.name_label.setStyleSheet("color: black;")
            self.due_label.setStyleSheet("color: black;")
            self.labels_label.setStyleSheet("color: black;")
    
    def openEditDialog(self):
        dialog = TaskEditDialog(self)
        dialog.exec_()
        self.refreshDisplay()
    
    def refreshDisplay(self):
        self.name_label.setText(self.name)
        self.due_label.setText(self.due_date.toString("yyyy-MM-dd"))
        # ラベルは"#"付きで表示
        self.labels_label.setText(", ".join(["#" + label for label in self.labels]))
    
    def get_data(self):
        return {
            "name": self.name,
            "details": self.details,
            "due_date": self.due_date.toString("yyyy-MM-dd"),
            "labels": self.labels,
            "completed": self.checkbox.isChecked()
        }
    
    def load_data(self, data):
        self.name = data.get("name", "")
        self.details = data.get("details", "")
        self.labels = data.get("labels", [])
        date_str = data.get("due_date", QDate.currentDate().toString("yyyy-MM-dd"))
        self.due_date = QDate.fromString(date_str, "yyyy-MM-dd")
        self.checkbox.setChecked(data.get("completed", False))
        self.refreshDisplay()

class TaskLineEdit(QLineEdit):
    def __init__(self, add_callback, parent=None):
        super().__init__(parent)
        self.add_callback = add_callback
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and (event.modifiers() & Qt.ControlModifier):
            self.add_callback()
            return
        super().keyPressEvent(event)

class TaskListTab(QWidget):
    def __init__(self, tab_name):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # タスク追加用入力エリア（タスク名のみ必須）
        self.input_layout = QHBoxLayout()
        self.task_input = TaskLineEdit(self.addTask)
        self.task_input.setPlaceholderText("新しいタスク名を入力 (ctrl+enterで追加)")
        self.add_button = QPushButton("追加")
        self.add_button.clicked.connect(self.addTask)
        self.input_layout.addWidget(self.task_input)
        self.input_layout.addWidget(self.add_button)
        self.layout.addLayout(self.input_layout)
        
        # タスクリスト（ドラッグ＆ドロップで順番変更可能）
        self.task_list = QListWidget()
        self.task_list.setDragDropMode(QListWidget.InternalMove)
        self.layout.addWidget(self.task_list)
        
        self.tab_name = tab_name

    def addTask(self):
        task_text = self.task_input.text().strip()
        if task_text:
            # 追加時はタスク名のみ必須。詳細・期限・ラベルは空欄／初期値
            task_widget = TaskWidget(task_text)
            list_item = QListWidgetItem(self.task_list)
            list_item.setSizeHint(task_widget.sizeHint())
            self.task_list.addItem(list_item)
            self.task_list.setItemWidget(list_item, task_widget)
            self.task_input.clear()
    
    def removeCompletedTasks(self):
        for index in reversed(range(self.task_list.count())):
            item = self.task_list.item(index)
            widget = self.task_list.itemWidget(item)
            if widget and widget.checkbox.isChecked():
                self.task_list.takeItem(index)
    
    def get_tasks(self):
        tasks = []
        for index in range(self.task_list.count()):
            item = self.task_list.item(index)
            widget = self.task_list.itemWidget(item)
            if widget:
                tasks.append(widget.get_data())
        return tasks
    
    def load_tasks(self, tasks):
        for task in tasks:
            task_widget = TaskWidget("")
            task_widget.load_data(task)
            list_item = QListWidgetItem(self.task_list)
            list_item.setSizeHint(task_widget.sizeHint())
            self.task_list.addItem(list_item)
            self.task_list.setItemWidget(list_item, task_widget)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ToDo管理ツール")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        # 画面はToDoとBacklogの2画面
        self.tabs = QTabWidget()
        self.todo_tab = TaskListTab("ToDo")
        self.backlog_tab = TaskListTab("Backlog")
        self.tabs.addTab(self.todo_tab, "ToDo")
        self.tabs.addTab(self.backlog_tab, "Backlog")
        self.setCentralWidget(self.tabs)
        
        self.last_date = QDate.currentDate()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.checkDateChange)
        self.timer.start(60000)
        
        self.load_tasks_from_file()
    
    def checkDateChange(self):
        current_date = QDate.currentDate()
        if current_date > self.last_date:
            self.todo_tab.removeCompletedTasks()
            self.backlog_tab.removeCompletedTasks()
            self.last_date = current_date
    
    def load_tasks_from_file(self):
        if os.path.exists("tasks.json"):
            with open("tasks.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            if "ToDo" in data:
                self.todo_tab.load_tasks(data["ToDo"])
            if "Backlog" in data:
                self.backlog_tab.load_tasks(data["Backlog"])
    
    def save_tasks_to_file(self):
        data = {
            "ToDo": self.todo_tab.get_tasks(),
            "Backlog": self.backlog_tab.get_tasks()
        }
        with open("tasks.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    def closeEvent(self, event):
        self.save_tasks_to_file()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(600, 400)
    window.show()
    sys.exit(app.exec_())