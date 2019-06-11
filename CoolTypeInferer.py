from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtPrintSupport import *

from uis import Ui_MainWindow, Ui_HowToUse, Ui_AboutAuthors, Ui_AboutCoolTypeInferer

import os
import sys

from cool import tokenizer
from cool import CoolParser
from cool.cmp import evaluate_reverse_parse
from cool import FormatVisitor, TypeCollector, TypeBuilder, TypeChecker, TypeInferer

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.actionNewFile.triggered.connect(self.new_file)
        self.ui.actionLoadFile.triggered.connect(self.load_file)
        self.ui.actionSaveFile.triggered.connect(self.save_file)
        self.ui.actionSaveFileAs.triggered.connect(self.save_file_as)
        self.ui.actionExit.triggered.connect(self._exit)
        self.ui.actionAnalyse.triggered.connect(self.analyse)
        self.ui.actionHowToUse.triggered.connect(self.how_to_use)
        self.ui.actionAboutAuthors.triggered.connect(self.about_authors)
        self.ui.actionAboutCoolTypeInferer.triggered.connect(self.about_cool_type_inferer)
        
        self.new_file()


    def clear_results(self):
        self.ui.textResults.setPlainText("")
    
    def update_status(self):
        self.ui.groupCode.setStatusTip(self.path if self.path else "*New File")
        # self.ui.statusbar.showMessage(self.path if self.path else "")

    def new_file(self):
        self.path = None
        self.ui.textCode.setPlainText("")
        self.update_status()
        self.clear_results()

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load File", "", "Cool files (*.cl)")

        if not path:
            # If dialog is cancelled, will return ''
            return

        try:
            with open(path, 'r') as f:
                text = f.read()

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.ui.textCode.setPlainText(text)
            self.update_status()
            self.clear_results()

    def save_file(self):
        if self.path is None:
            # If we do not have a path, we need to use Save As.
            return self.save_file_as()

        text = self.ui.textCode.toPlainText()
        try:
            with open(self.path, 'w') as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Cool files (*.cl)")
        text = self.ui.textCode.toPlainText()

        if not path:
            # If dialog is cancelled, will return ''
            return

        try:
            with open(path, 'w') as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.update_status()

    def _exit(self):
        self.close()

    
    def analyse(self):
        text = self.ui.textCode.toPlainText()
        self.ui.textResults.setPlainText('')
        tokens = tokenizer(text)
        self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}================== PARSING ====================\n')
        parse, operations = CoolParser(tokens)
        if not operations:
            self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}Unexpected token: {parse.lex} at Ln: {parse.line}, Col {parse.column}\n')
            return
        self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}Successful parsing!\n')
        # print('\n'.join(repr(x) for x in parse))
        # self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}==================== AST ======================\n')
        ast = evaluate_reverse_parse(parse, operations, tokens)
        formatter = FormatVisitor()
        tree = formatter.visit(ast)
        # self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}{tree}\n')
        # self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}============== COLLECTING TYPES ===============\n')
        errors = []
        collector = TypeCollector(errors)
        collector.visit(ast)
        context = collector.context
        # self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}Errors: [\n')
        # for error in errors:
        #     self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}{error}\n')
        # self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}]\n')
        # self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}Context:\n')
        # self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}{context}\n')
        # self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}=============== BUILDING TYPES ================\n')
        builder = TypeBuilder(context, errors)
        builder.visit(ast)
        # self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}Errors: [\n')
        # for error in errors:
        #     self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}{error}\n')
        # self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}]\n')
        # self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}Context:\n')
        # self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}{context}\n')
        self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}=============== CHECKING TYPES ================\n')
        checker = TypeChecker(context, errors)
        scope = checker.visit(ast)
        self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}Errors: [\n')
        for error in errors:
            self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}{error}\n')
        self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}]\n')
        self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}============== INFERINING TYPES ===============\n')
        inferences = []
        inferer = TypeInferer(context, errors, inferences)
        while inferer.visit(ast, scope): pass
        self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}Inferences: [\n')
        for inference in inferences:
            self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}{inference}\n')
        self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}]\n')
        self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}Context:\n')
        self.ui.textResults.setPlainText(f'{self.ui.textResults.toPlainText()}{context}\n')

    def how_to_use(self):
        dialog = QDialog()
        ui_dialog = Ui_HowToUse()
        ui_dialog.setupUi(dialog)

        dialog.exec()

    def about_authors(self):
        dialog = QDialog()
        ui_dialog = Ui_AboutAuthors()
        ui_dialog.setupUi(dialog)

        dialog.exec()

    def about_cool_type_inferer(self):
        dialog = QDialog()
        ui_dialog = Ui_AboutCoolTypeInferer()
        ui_dialog.setupUi(dialog)

        dialog.exec()
        


if __name__ == '__main__':

    # sys.argv.append("--disable-web-security")
    # app = QApplication(sys.argv)
    app = QApplication([])

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
