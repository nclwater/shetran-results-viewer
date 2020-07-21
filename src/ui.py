import sys
from shetranio.model import Model
from shetranio.hdf import LandVariable
import argparse
import os
from PyQt5.QtWidgets import QSplitter, QRadioButton, QHBoxLayout, QComboBox, QProgressBar, QCheckBox, QMessageBox, \
    QApplication, QMainWindow, QSizePolicy, QPushButton, QFileDialog, QVBoxLayout, QWidget, QSlider, QInputDialog
from PyQt5.QtCore import QThread, Qt
import pandas as pd
from plot import PlotCanvas
from legend import LegendCanvas
from map import MapCanvas


parser = argparse.ArgumentParser()
parser.add_argument('-l')
args = parser.parse_args()


class App(QMainWindow):

    def __init__(self):
        super().__init__()

        self.models = []
        self.args = args
        self.variables = None
        self.variable = None

        self.disable_clicking = False

        self.modelDropDown = QComboBox()
        self.modelDropDown.activated.connect(self.set_model)

        self.slider = QSlider(parent=self, orientation=Qt.Horizontal, )
        self.slider.valueChanged.connect(self.set_time)

        self.droppedPath = None

        self.differenceCheckBox = QCheckBox("Difference:")

        self.differenceCheckBox.clicked.connect(self.show_or_hide_difference_dropdown)

        self.differenceDropDown = QComboBox()
        self.differenceDropDown.setEnabled(False)

        self.differenceDropDown.activated.connect(self.set_model)

        self.series = None

        self.add_model()
        self.model = self.models[0]

        row1 = QHBoxLayout()
        row2 = QHBoxLayout()
        row3 = QHBoxLayout()
        row4 = QSplitter()

        self.mainWidget = QWidget(self)
        self.mainWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        row1.addWidget(self.modelDropDown)

        self.plot_on_click = QRadioButton(text='Click')
        self.plot_on_hover = QRadioButton(text='Hover')

        self.plot_on_click.toggle()

        self.plot_on_click.toggled.connect(self.set_hover)
        self.plot_on_hover.toggled.connect(self.set_hover)

        self.plot_on_click.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.plot_on_hover.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.plot_on_click.setGeometry(510, 10, 100, 50)
        self.plot_on_hover.setGeometry(600, 10, 100, 50)

        self.variableDropDown = QComboBox()
        for variable in self.model.hdf.spatial_variables:
            self.variableDropDown.addItem(variable.long_name)
        self.variableDropDown.activated.connect(self.set_variables)

        self.download_button = QPushButton(text='Download')
        self.download_button.clicked.connect(self.download_values)

        self.add_model_button = QPushButton(text='Add Model')
        self.add_model_button.clicked.connect(self.add_model)

        self.remove_model_button = QPushButton(text='Remove Model')
        self.remove_model_button.clicked.connect(self.remove_model)

        self.add_series_button = QPushButton(text='Add Series')
        self.add_series_button.clicked.connect(lambda: self.add_series())

        self.clear_series_button = QPushButton(text='Clear Series')
        self.clear_series_button.clicked.connect(self.clear_series)

        row2.addWidget(self.variableDropDown)
        row2.addWidget(self.differenceCheckBox)
        row2.addWidget(self.differenceDropDown)
        row2.addWidget(self.add_model_button)
        row2.addWidget(self.remove_model_button)
        row2.addWidget(self.add_series_button)
        row2.addWidget(self.clear_series_button)
        row2.addWidget(self.download_button)
        row2.addWidget(self.plot_on_click)
        row2.addWidget(self.plot_on_hover)

        self.title = 'SHETran Results Viewer'

        self.element = None
        self.time = 0

        self.progress = QProgressBar(self)

        self.resampleCheckBox = QCheckBox('Plot Monthly Means')
        self.resampleCheckBox.stateChanged.connect(self.update_resample)

        self.outletCheckBox = QCheckBox('Outlet Discharge')
        self.outletCheckBox.stateChanged.connect(self.update_outlet)
        try:
            assert self.model.get('SimulatedDischargeTimestep') is not None
            assert os.path.exists(self.model.path('output_{}_discharge_sim_regulartimestep.txt'.format(
                self.model.catchment_name)))
        except AssertionError:
            self.outletCheckBox.setDisabled(True)

        row2.addWidget(self.progress)
        row3.addWidget(self.resampleCheckBox)
        row3.addWidget(self.outletCheckBox)
        row3.addWidget(self.slider)

        self.setWindowTitle(self.title)

        plot_layout = QVBoxLayout()
        self.plotCanvas = PlotCanvas(self)
        self.plotZoom = QSlider(orientation=Qt.Horizontal)
        self.plotZoom.valueChanged.connect(self.plotCanvas.set_zoom)
        plot_layout.addWidget(self.plotCanvas)
        plot_layout.addWidget(self.plotZoom)

        plot = QWidget()
        plot.setLayout(plot_layout)
        row4.addWidget(plot)

        map_and_legend_layout = QVBoxLayout()

        self.mapCanvas = MapCanvas(self)
        self.legendCanvas = LegendCanvas(self)
        map_and_legend_layout.addWidget(self.mapCanvas)
        map_and_legend_layout.addWidget(self.legendCanvas)

        map_and_legend = QWidget()
        map_and_legend.setLayout(map_and_legend_layout)

        width = 500
        height = 400
        plot.setMinimumWidth(width)
        plot.setMinimumHeight(height)
        map_and_legend.setMinimumWidth(width)
        map_and_legend.setMinimumHeight(height)
        self.mainWidget.setMinimumHeight(600)
        self.mainWidget.setMinimumWidth(width*2)

        row4.addWidget(map_and_legend)
        row4.setCollapsible(0, False)
        row4.setCollapsible(1, False)

        self.mapCanvas.progress.connect(self.set_progress)
        self.mapCanvas.clickedElement.connect(self.update_element)
        self.mapCanvas.loaded.connect(self.on_load)

        self.mapCanvas.add_data(self.model)

        self.rename = QPushButton(parent=self, text='Rename Model')
        row1.addWidget(self.rename)
        self.rename.clicked.connect(self.rename_model)

        self.pan = QPushButton(parent=self, text='Reset View')
        row1.addWidget(self.pan)
        self.pan.clicked.connect(self.mapCanvas.pan_to)

        rows = QVBoxLayout()
        for row in [row1, row2, row3]:
            w = QWidget()
            w.setLayout(row)
            w.setMaximumHeight(50)
            rows.addWidget(w)

        rows.addWidget(row4)
        self.setAcceptDrops(True)

        self.model.hdf.get_elevations()

        self.mainWidget.setLayout(rows)
        self.setCentralWidget(self.mainWidget)
        self.set_variables(0)
        self.show()
        self.activateWindow()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            if event.mimeData().text().endswith(('.csv', '.xml')):
                event.accept()
                return

        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            self.droppedPath = url.toLocalFile()
            break

        if self.droppedPath.endswith('.csv'):
            self.add_series()

        elif self.droppedPath.endswith('.xml'):
            self.add_model()

    def add_model(self):
        if self.args.l is None and self.droppedPath is None:
            library_path = QFileDialog.getOpenFileName(
                self,
                'Choose a library file',
                "",
                "XML files (*.xml);;All Files (*)",
                options=QFileDialog.Options())[0]
        elif self.droppedPath:
            library_path = self.droppedPath
            self.droppedPath = None
        else:
            library_path = self.args.l
            self.args.l = None
        if os.path.exists(library_path):

            text, ok = QInputDialog.getText(self, "Model Name", "Enter a model name", text=str(len(self.models)+1))

            if ok and text:

                try:

                    model = Model(library_path, name=text)
                    self.models.append(model)
                    self.modelDropDown.addItem('{} - {}'.format(model.name, model.library))
                    self.differenceDropDown.addItem(model.name)
                    self.differenceCheckBox.setEnabled(len(self.models) > 1)

                    table_elev = LandVariable(model.hdf, 'ph_depth')
                    table_elev.long_name = 'Water Table Elevation (m)'
                    table_elev.name = 'table_elev'
                    model.hdf.variables.append(table_elev)
                    model.hdf.spatial_variables.append(table_elev)

                    if len(self.models) > 1:
                        self.set_variables(self.variableDropDown.currentIndex())

                except:
                    import traceback
                    msg = QMessageBox()
                    msg.setText(traceback.format_exc())
                    msg.exec_()
                    self.add_model()


    def rename_model(self):
        text, ok = QInputDialog.getText(self, "Model Name", "Enter a model name", text=self.model.name)

        if ok and text:
            self.model.name = text
            idx = self.modelDropDown.currentIndex()
            self.modelDropDown.setItemText(idx, '{} - {}'.format(self.model.name, self.model.library))
            self.differenceDropDown.setItemText(idx, self.model.name)
            self.plotCanvas.update_data()


    def remove_model(self):
        if len(self.models) == 1:
            return
        self.modelDropDown.removeItem(self.models.index(self.model))
        self.differenceDropDown.removeItem(self.models.index(self.model))
        self.modelDropDown.setCurrentIndex(0)
        self.models.remove(self.model)
        self.differenceCheckBox.setEnabled(len(self.models) > 1)
        self.set_model()
        self.set_variables(self.variableDropDown.currentIndex())

    def show_or_hide_difference_dropdown(self):
        self.differenceDropDown.setEnabled(self.differenceCheckBox.isChecked())
        self.mapCanvas.set_time(self.time, self.variable,
                                self.variables[self.differenceDropDown.currentIndex()]
                                if self.differenceCheckBox.isChecked() else None)
        self.series = None
        self.plotCanvas.update_data()

    def add_series(self):
        if self.droppedPath is None:
            series_path = QFileDialog.getOpenFileName(
                self,
                'Choose a CSV file',
                "",
                "CSV files (*.csv);;All Files (*)",
                options=QFileDialog.Options())[0]

        else:
            series_path = self.droppedPath
            self.droppedPath = None

        if os.path.exists(series_path):

            try:
                self.series = pd.read_csv(series_path, usecols=[0, 1], index_col=0, squeeze=True)
                self.series.index = pd.DatetimeIndex(pd.to_datetime(self.series.index, dayfirst=True))

                start = max(min(self.variables[0].times), min(self.series.index))
                end = min(max(self.variables[0].times), max(self.series.index))
                self.series = self.series.sort_index().loc[start:end].rename('observed')
                self.differenceCheckBox.setChecked(False)
                self.differenceDropDown.setEnabled(False)
                self.plotCanvas.update_data()
            except:
                self.series = None
                print('Could not read series')
                import traceback
                msg = QMessageBox()
                msg.setText(traceback.format_exc())
                msg.exec_()



    def clear_series(self):
        self.series = None
        self.plotCanvas.update_data()

    def set_variables(self, variable_index):
        self.variables = [model.hdf.spatial_variables[variable_index] for model in self.models]
        self.variable = self.variables[self.models.index(self.model)]
        self.slider.setMaximum(len(self.variables[0].times) - 1)
        self.switch_elements()
        self.set_time(self.time)

    def update_resample(self):
        self.plotCanvas.update_data()

    def update_outlet(self):
        if self.outletCheckBox.isChecked():
            self.download_button.setEnabled(False)
            self.plotCanvas.update_data()
            self.disable_clicking = True

        else:
            self.download_button.setEnabled(True)
            self.disable_clicking = False

        self.switch_elements()

    def update_element(self, element):
        if not self.disable_clicking:
            try:
                self.variables[0].get_element(element.number)
            except ValueError:
                return
            self.element = element
            self.plotCanvas.update_data()

    def set_hover(self):
        class Thread(QThread):
            def __init__(self, parent=None):
                QThread.__init__(self)
                self.setParent(parent)

            def __del__(self):
                self.wait()

            def run(self):
                if self.parent().plot_on_click.isChecked():
                    self.parent().mapCanvas.set_onclick()
                else:
                    self.parent().mapCanvas.set_onhover()

        Thread(self).start()

    def switch_elements(self):
        if self.variables[0].is_river:
            self.mapCanvas.show_rivers()
            self.element = self.mapCanvas.river_elements[0]
        else:
            self.mapCanvas.show_land()
            self.element = self.mapCanvas.land_elements[0]

        self.plotCanvas.update_data()

    def on_load(self):
        self.progress.hide()
        self.plotCanvas.show()
        self.mapCanvas.show()

    def set_progress(self, progress):
        self.progress.setValue(progress)

    def download_values(self):
        if not self.element:
            return
        array = pd.DataFrame({'time': self.variables[0].times[:],
                              **{'{}'.format(var.hdf.model.name): var.get_element(self.element.number).round(3)
                                 for var in self.variables}})

        directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '{} at {}.csv'.format(
            self.variables[0].long_name, self.element.number).replace('/', ' per '))

        dialog = QFileDialog.getSaveFileName(directory=directory, filter="CSV Files (*.csv)")
        if dialog[0] != '':
            with open(dialog[0], 'w') as f:
                f.write('{} at {} ({},{})\n'.format(self.variables[0].long_name, self.element.number,
                                                    self.element.location[0], self.element.location[1]))
            array.to_csv(dialog[0], index=False, mode='a')

    def set_time(self, time):
        self.time = time
        if self.differenceDropDown.isEnabled():
            difference = self.variables[self.differenceDropDown.currentIndex()]
        else:
            difference = None
        self.mapCanvas.set_time(self.time, self.variable, difference=difference)
        self.plotCanvas.set_time(self.variable.times[self.time], self.mapCanvas.norm)
        self.legendCanvas.set_time(self.mapCanvas.norm)

    def set_model(self):
        self.model = self.models[self.modelDropDown.currentIndex()]
        self.variable = self.variables[self.modelDropDown.currentIndex()]
        if self.differenceDropDown.isEnabled():
            self.plotCanvas.update_data()
        self.set_time(self.time)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
