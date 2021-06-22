from shetranio.hdf import Geometries
import numpy as np
from matplotlib.cm import get_cmap
from settings import colormap
from matplotlib.colors import Normalize, to_hex
from pyqtlet import MapWidget
from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from pyqtlet import L
import json
from PyQt5.QtCore import pyqtSlot, QJsonValue


class Group(L.featureGroup):
    def __init__(self):
        super().__init__()

    def update_style(self, style):
        self.runJavaScript("{}.setStyle({})".format(self.jsName, json.dumps(style)))


class MapCanvas(QFrame):
    clickedElement = pyqtSignal(object)
    loaded = pyqtSignal()
    progress = pyqtSignal(float)

    def __init__(self, app):

        self.app = app
        self.mapWidget = MapWidget()

        profile = self.mapWidget._page.profile()
        user_agent = 'ShetranResultsViewer'
        profile.setHttpUserAgent(user_agent)
        self.mapWidget._page.setWebChannel(self.mapWidget._channel)
        self.mapWidget._loadPage()

        QWidget.__init__(self, self.mapWidget)
        self.setParent(app)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.mapWidget)
        self.setLayout(self.layout)

        self.map = L.map(self.mapWidget)
        self.map.setZoom(10)

        self.group = Group()
        self.group.addTo(self.map)
        self.setLineWidth(10)
        self.setFrameShape(QFrame.StyledPanel)

        self.clickedElement.connect(self.select_element)
        self.element = None
        self.elements = []
        self.river_elements = []
        self.land_elements = []
        self.visible_elements = None
        self.norm = None
        self.mapWidget.setAcceptDrops(False)

    def pan_to(self):

        def _pan_to(bounds):
            self.map.fitBounds([list(b.values()) for b in bounds.values()])

        self.group.getJsResponse('{}.getBounds()'.format(self.group.jsName), _pan_to)

    def add_data(self, model):

        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png').addTo(self.map)

        geoms = Geometries(model.hdf, model.dem, srs=model.srid)

        banks = np.concatenate((
            model.hdf.number.north_bank,
            model.hdf.number.west_bank,
            model.hdf.number.east_bank,
            model.hdf.number.south_bank))

        prog = 0
        for geom, number in zip(geoms, model.hdf.element_numbers):
            if number in banks:
                continue
            coords = [[y, x] for (x, y) in geom['coordinates'][0]]
            lat = np.mean([coord[0] for coord in coords[:-1]]).round(3)
            lon = np.mean([coord[1] for coord in coords[:-1]]).round(3)
            elevation = model.hdf.elevations[number-1]
            element = Element(coords, number, elevation, (lat, lon), self.clickedElement)
            self.elements.append(element)
            if number in model.hdf.land_elements:
                self.land_elements.append(element)
            else:
                self.river_elements.append(element)
            self.group.addLayer(element)
            prog += 100/len(geoms)
            self.progress.emit(prog)

        self.pan_to()

        self.loaded.emit()

    def set_onclick(self):
        for element in self.elements:
            element.onclick()

    def set_onhover(self):
        for element in self.elements:
            element.onhover()

    def select_element(self, element):
        if self.element is not None:
            self.element.update_style({'weight': self.element.default_weight})

        if self.app.disable_clicking:
            return

        self.element = element
        element.update_style({'weight': 3})

    def show_land(self):
        for element in self.river_elements:
            self.group.removeLayer(element)
        for element in self.land_elements:
            self.group.addLayer(element)
        self.visible_elements = self.land_elements
        self.select_element(self.land_elements[0])

    def show_rivers(self):
        for element in self.land_elements:
            self.group.removeLayer(element)
        for element in self.river_elements:
            self.group.addLayer(element)
        self.visible_elements = self.river_elements
        self.select_element(self.river_elements[0])

    def set_elements_enabled(self):
        for element in self.elements:
            element.runJavaScript("{}.interactive = false".format(element.jsName))


    def set_time(self, time, variable, difference=None):
        values = variable.get_time(time)
        if difference is not None:
            values -= difference.get_time(time)
        if variable.name == 'table_elev':
            values = variable.hdf.elevations[variable.hdf.land_elements-1] - values

        cm = get_cmap(colormap)
        if np.all(values == 0):
            self.norm = Normalize(vmin=0, vmax=1)
        else:
            self.norm = Normalize(vmin=min(values), vmax=max(values))
        values = cm(self.norm(values))
        for element, value in zip(self.visible_elements, values):
            element.update_style({'fillColor': to_hex(value)})


class Element(L.polygon):
    default_weight = 0.1

    @pyqtSlot(QJsonValue)
    def _signal(self):
        self.signal.emit(self)

    def __init__(self, shape, element_number, elevation, location, signal):
        super().__init__(shape, {'weight': self.default_weight, 'fillOpacity': 0.8})
        self.signal = signal
        self.number = element_number
        self.elevation = elevation
        self.location = location
        self.setProperty('element_number', element_number)
        self._connectEventToSignal('click', '_signal')

    def onclick(self):
        self.runJavaScript("{}.off()".format(self.jsName))
        self._connectEventToSignal('click', '_signal')

    def onhover(self):
        self.runJavaScript("{}.off()".format(self.jsName))
        self._connectEventToSignal('mouseover', '_signal')

    def update_style(self, style):
        self.runJavaScript("{}.setStyle({})".format(self.jsName, json.dumps(style)))
