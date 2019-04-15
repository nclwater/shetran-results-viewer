import sys
from shetran.hdf import Hdf, Geometries
from shetran.dem import Dem
import argparse
from pyqtlet import L, MapWidget
import numpy as np

from PyQt5.QtWidgets import QComboBox, QProgressBar, QApplication, QMainWindow, QSizePolicy, QLineEdit, QPushButton, QFileDialog, QVBoxLayout, QWidget
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QJsonValue


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


parser = argparse.ArgumentParser()
parser.add_argument('-h5')
parser.add_argument('-dem')
args = parser.parse_args()

variables = dict(
        potential_evapotranspiration=dict(name='Potential Evapotranspiration'),
        transpiration=dict(name='Transpiration'),
        surface_evaporation=dict(name='Surface Evaporation'),
        evaporation_from_interception=dict(name='Evaporation from Interception'),
        drainage_from_interception=dict(name='Drainage from Interception'),
        canopy_storage=dict(name='Canopy Storage'),
        vertical_flows=dict(name='Vertical Flows'),
        snow_depth=dict(name='Snow Depth'),
        ph_depth=dict(name='Phreatic Depth'),
        overland_flow=dict(name='Overland Flow'),
        surface_depth=dict(name='Surface Depth'),
        surface_water_potential=dict(name='Surface Water Potential'),
        theta=dict(name='Theta'),
        total_sediment_depth=dict(name='Total Sediment Depth'),
        surface_erosion_rate=dict(name='Surface Erosion Rate'),
        sediment_discharge_rate=dict(name='Sediment Discharge Rate'),
        mass_balance_error=dict(name='Mass Balance Error'))


class App(QMainWindow):

    def __init__(self):
        super().__init__()

        for attribute, fileClass in [['h5', Hdf], ['dem', Dem]]:

            if getattr(args, attribute) is None:
                options = QFileDialog.Options()

                fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                          "All Files (*);;Python Files (*.py)", options=options)
                if fileName:
                    self.__setattr__(attribute, fileClass(fileName))

            else:
                print(args)
                self.__setattr__(attribute, fileClass(args.__getattribute__(attribute)))

        self.variables = [{'variable': key, **val} for key, val in variables.items() if self.h5.__getattribute__(key) is not None]

        self.variable = self.variables[0]

        self.variableDropDown = QComboBox(self)
        for variable in self.variables:
            self.variableDropDown.addItem(variable['name'])
        self.variableDropDown.activated.connect(self.set_variable)
        self.variableDropDown.setGeometry(10,10,500, 50)
        self.left = 0
        self.top = 0
        self.title = 'SHETran Results Viewer'
        self.width = 1000
        self.height = 600
        self.element = 1
        self.show()
        self.progress = QProgressBar(self)
        self.progress.setGeometry(100,100, 200, 500)
        self.progress.show()

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.plotCanvas = PlotCanvas(self, width=5, height=4)

        self.mapCanvas = MapCanvas(self)

        self.mapCanvas.clickedElement.connect(self.update_data)

        self.switch_elements()

        # self.show()

    def set_variable(self, variable_index):
        self.variable = self.variables[variable_index]
        self.switch_elements()

    def update_data(self, element):
        self.element = element

        new_data, times = self.get_values()

        self.plotCanvas.line[0].set_data(times, new_data)
        self.plotCanvas.axes.relim()
        self.plotCanvas.axes.autoscale_view()
        self.plotCanvas.axes.set_title('{} {}'.format(self.element, self.variable['name']))
        self.plotCanvas.draw()

    def get_values(self):
        var = self.variable['variable']
        idx = self.h5.element_numbers.tolist().index(self.element)
        values = self.h5.__getattribute__(var).values
        times = self.h5.__getattribute__(var).times
        print(values.shape)
        if var in ['overland_flow', 'surface_depth']:
            if idx < self.h5.overland_flow.values.shape[0]:
                if var == 'overland_flow':
                    return values[idx, :, :].max(axis=0), times
                else:
                    return values[idx, :], times
            else:
                return []
        elif var == 'surface_depth':
            if idx < self.h5.overland_flow.values.shape[0]:
                return values[idx, 0, :], times
            else:
                return [], []
        else:
            if self.element in self.h5.number.square:
                return values[self.h5.number.square == self.element].flatten(), times
            else:
                return [], []

    def switch_elements(self):
        if self.variable['variable'] in ['overland_flow','surface_depth']:
            self.mapCanvas.show_land()
        else:
            self.mapCanvas.show_rivers()


class PlotCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        self.setGeometry(10,110,480,480)
        fig.tight_layout()

        data, times = self.parent().get_values()
        ax = self.figure.add_subplot(111)
        self.line = ax.plot(times, data, 'r-')
        ax.set_title('{} {}'.format(self.parent().element, self.parent().variable['variable']))
        self.draw()


class MapCanvas(QWidget):
    clickedElement = pyqtSignal(int)

    def __init__(self, parent=None):
        self.mapWidget = MapWidget()
        QWidget.__init__(self, self.mapWidget)
        self.setParent(parent)
        self.setGeometry(500,100,500,500)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.mapWidget)
        self.setLayout(self.layout)

        self.map = L.map(self.mapWidget)
        self.map.setView([12.97, 77.59], 10)

        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.map)

        geoms = Geometries(self.parent().h5, self.parent().dem)

        class Element(L.polygon):

            @pyqtSlot(QJsonValue)
            def _signal(self, event):
                self.mapWidget.parent().clickedElement.emit(self.property('name'))

            def __init__(self, latLngs, element_number):
                super().__init__(latLngs)
                self.setProperty('name', element_number)
                self._connectEventToSignal('mouseover', '_signal')

        self.group = L.featureGroup()
        self.group.addTo(self.map)
        self.elements = []
        self.show()

        prog = 0
        for geom, number in zip(geoms, np.unique(self.parent().h5.sv4_numbering)):
            if number == 0:
                continue
            coords = [list(reversed(coord)) for coord in geom['coordinates'][0]]
            self.elements.append(Element(coords, number))
            self.group.addLayer(self.elements[-1])
            prog += 100/len(geoms)
            self.parent().progress.setValue(prog)
        self.parent().progress.hide()
        self.parent().plotCanvas.show()

        def pan_to(bounds):
            ne = bounds['_northEast']

            sw = bounds['_southWest']
            latlng = [sw['lat']+(ne['lat']-sw['lat'])/2, sw['lng']+(ne['lng']-sw['lng'])/2]
            self.map.panTo(latlng)

        self.group.getJsResponse('{}.getBounds()'.format(self.group.jsName), pan_to)

    def show_land(self):
        for element in self.elements:
            if element.property('name') >= self.parent().h5.overland_flow.values.shape[0]:
                self.group.removeLayer(element)
            else:
                self.group.addLayer(element)

    def show_rivers(self):
        for element in self.elements:
            if element.property('name') < self.parent().h5.overland_flow.values.shape[0]:
                self.group.removeLayer(element)
            else:
                self.group.addLayer(element)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
