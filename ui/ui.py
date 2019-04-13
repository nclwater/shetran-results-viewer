import sys
from shetran.hdf import Hdf
from shetran.dem import Dem
import argparse
from pyqtlet import L, MapWidget

from PyQt5.QtWidgets import QApplication, QMainWindow, QSizePolicy, QPushButton, QFileDialog, QVBoxLayout, QWidget

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


parser = argparse.ArgumentParser()
parser.add_argument('-h5')
parser.add_argument('-dem')
args = parser.parse_args()


class App(QMainWindow):

    def __init__(self):
        super().__init__()

        if not hasattr(args, 'h5'):
            options = QFileDialog.Options()

            fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                      "All Files (*);;Python Files (*.py)", options=options)
            if fileName:
                print(fileName)
                self.h5 = Hdf(fileName)

        else:
            self.h5 = Hdf(args.h5)

        if not hasattr(args, 'dem'):
            options = QFileDialog.Options()

            fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                      "All Files (*);;Python Files (*.py)", options=options)
            if fileName:
                print(fileName)
                self.dem = Dem(fileName)

        else:
            self.dem = Dem(args.dem)

        self.left = 10
        self.top = 10
        self.title = 'SHETran Results Viewer'
        self.width = 1200
        self.height = 700
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        m = PlotCanvas(self, width=5, height=4)
        m.move(0, 0)

        map = MapCanvas(self)

        button = QPushButton('Next Element', self)
        button.setToolTip('show data from the next element')
        button.move(500, 0)
        button.resize(140, 100)

        def update_data():

            m.element += 1

            new_data = self.h5.overland_flow.values[m.element, 0, :]

            m.line[0].set_data(range(len(new_data)), new_data)

            m.draw()

        button.clicked.connect(update_data)

        self.show()


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.element = 0

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.plot()

    def plot(self):
        data = self.parent().h5.overland_flow.values[self.element, 0, :]
        ax = self.figure.add_subplot(111)
        self.line = ax.plot(data, 'r-')
        ax.set_title('Overland Flow')
        self.draw()

class MapCanvas(QWidget):
    def __init__(self, parent=None):
        self.mapWidget = MapWidget()
        QWidget.__init__(self, self.mapWidget)
        self.setParent(parent)
        self.setGeometry(500,100,500,500)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.mapWidget)
        self.setLayout(self.layout)

        # Working with the maps with pyqtlet
        self.map = L.map(self.mapWidget)
        self.map.setView([12.97, 77.59], 10)
        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.map)
        self.marker = L.marker([12.934056, 77.610029])
        self.marker.bindPopup('Hello World')
        self.map.addLayer(self.marker)
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())