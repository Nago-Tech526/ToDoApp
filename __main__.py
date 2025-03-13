import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QTabWidget,
    QCheckBox, QLabel, QDateEdit
)
from PyQt5.QtCore import Qt, QDate, QTimer, QSize
from PyQt5.QtGui import QFont

class EditableLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)  # テキストが長い場合、折り返す
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        # 編集用の QLineEdit を作成（初期は非表示）
        self.edit = QLineEdit(self)
        self.edit.setText(text)
        self.edit.hide()
        self.edit.returnPressed.connect(self.finishEditing)
        self.edit.editingFinished.connect(self.finishEditing)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 編集用ウィジェットがラベルと同じ領域を覆うようにする
        self.edit.setGeometry(self.rect())
    
    def mouseDoubleClickEvent(self, event):
        # ダブルクリックで編集モードへ
        self.edit.setText(self.text())
        self.edit.setGeometry(self.rect())
        self.edit.show()
        self.edit.setFocus()
        super().mouseDoubleClickEvent(event)
    
    def finishEditing(self):
        # 編集完了時、テキストを更新して編集用ウィジェットを隠す
        new_text = self.edit.text()
        self.setText(new_text)
        self.edit.hide()

class TaskWidget(QWidget):
    def __init__(self, text, due_date=None):
        super().__init__()
        # チェックボックスとタスク内容を水平に配置
        main_layout = QHBoxLayout(self)
        self.checkbox = QCheckBox()
        main_layout.addWidget(self.checkbox)
        
        # タスク名と期日を含むコンテナを作成（縦方向に配置）
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(2)
        
        self.label = EditableLabel(text)
        container_layout.addWidget(self.label)
        
        self.dateEdit = QDateEdit()
        self.dateEdit.setCalendarPopup(True)
        if due_date:
            self.dateEdit.setDate(due_date)
        else:
            self.dateEdit.setDate(QDate.currentDate())
        container_layout.addWidget(self.dateEdit)
        
        main_layout.addWidget(container)
        main_layout.addStretch()
        
        # チェックボックスの状態に応じてタスクの表示を更新
        self.checkbox.toggled.connect(self.updateStatus)
        self.updateStatus(self.checkbox.isChecked())
    
    def updateStatus(self, checked):
        font = self.label.font()
        font.setStrikeOut(checked)
        self.label.setFont(font)
        # 完了時は文字色をグレー、未完了は黒
        if checked:
            self.label.setStyleSheet("color: gray;")
        else:
            self.label.setStyleSheet("color: black;")
    
    def sizeHint(self):
        # 通常のサイズヒントの高さを70%にして返す
        original = super().sizeHint()
        return QSize(original.width(), int(original.height() * 0.7))

# QLineEdit を継承して ctrl+enter でタスク追加を実行するクラス
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
        
        # タスク追加用の入力フィールドとボタン
        self.input_layout = QHBoxLayout()
        self.task_input = TaskLineEdit(self.addTask)
        self.task_input.setPlaceholderText("新しいタスクを入力 (ctrl+enterで追加)")
        self.add_button = QPushButton("追加")
        self.add_button.clicked.connect(self.addTask)
        self.input_layout.addWidget(self.task_input)
        self.input_layout.addWidget(self.add_button)
        self.layout.addLayout(self.input_layout)
        
        # タスクを表示するリスト（ドラッグ＆ドロップで順番変更可能）
        self.task_list = QListWidget()
        self.task_list.setDragDropMode(QListWidget.InternalMove)
        self.layout.addWidget(self.task_list)
        
        self.tab_name = tab_name

    def addTask(self):
        task_text = self.task_input.text().strip()
        if task_text:
            task_widget = TaskWidget(task_text)
            list_item = QListWidgetItem(self.task_list)
            list_item.setSizeHint(task_widget.sizeHint())
            self.task_list.addItem(list_item)
            self.task_list.setItemWidget(list_item, task_widget)
            self.task_input.clear()

    def removeCompletedTasks(self):
        # リストの最後から順にチェックし、完了済みタスクを削除
        for index in reversed(range(self.task_list.count())):
            item = self.task_list.item(index)
            widget = self.task_list.itemWidget(item)
            if widget and widget.checkbox.isChecked():
                self.task_list.takeItem(index)
    
    def get_tasks(self):
        # 各タスクの情報をリストとして返す
        tasks = []
        for index in range(self.task_list.count()):
            item = self.task_list.item(index)
            widget = self.task_list.itemWidget(item)
            if widget:
                tasks.append({
                    "text": widget.label.text(),
                    "due_date": widget.dateEdit.date().toString("yyyy-MM-dd"),
                    "completed": widget.checkbox.isChecked()
                })
        return tasks
    
    def load_tasks(self, tasks):
        # タスク情報リストからタスクウィジェットを生成
        for task in tasks:
            task_widget = TaskWidget(task["text"])
            task_widget.dateEdit.setDate(QDate.fromString(task["due_date"], "yyyy-MM-dd"))
            task_widget.checkbox.setChecked(task["completed"])
            list_item = QListWidgetItem(self.task_list)
            list_item.setSizeHint(task_widget.sizeHint())
            self.task_list.addItem(list_item)
            self.task_list.setItemWidget(list_item, task_widget)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ToDo管理ツール")
        # 常に最前面に表示する
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        # タブウィジェットにより2つの画面（ToDo, Backlog）を切り替え
        self.tabs = QTabWidget()
        self.todo_tab = TaskListTab("ToDo")
        self.backlog_tab = TaskListTab("Backlog")
        self.tabs.addTab(self.todo_tab, "ToDo")
        self.tabs.addTab(self.backlog_tab, "Backlog")
        
        self.setCentralWidget(self.tabs)

        # 日付変更を監視（1分ごとにチェック）
        self.last_date = QDate.currentDate()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.checkDateChange)
        self.timer.start(60000)

        # アプリ起動時にタスクの読み込み
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