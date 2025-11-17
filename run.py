from PyQt6.QtWidgets import QApplication
import datetime
from main import mainWindow
import sys
    
if __name__ == '__main__':
    # try:
    #     app = QApplication(sys.argv)
    #     ex = mainWindow()
    #     ex.show()
    #     sys.exit(app.exec())
    # except Exception as e:
    #     logs = open(f'logs.txt', 'w+')
    #     logs.write(f'{datetime.now}: {e}')

    app = QApplication(sys.argv)
    ex = mainWindow()
    ex.show()
    sys.exit(app.exec())