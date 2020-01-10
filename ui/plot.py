from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import QSizePolicy
from settings import colormap


class PlotCanvas(FigureCanvas):

    def __init__(self, app):

        self.app = app
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        self.fig.subplots_adjust(bottom=0.2, top=0.9)
        self.sm = ScalarMappable(cmap=colormap, norm=Normalize(vmin=0, vmax=1))
        self.sm.set_array(np.array([]))
        self.fig.patch.set_visible(False)
        self.legend = None

        FigureCanvas.__init__(self, self.fig)
        self.setStyleSheet("background-color:transparent;")
        self.setParent(app)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)

        self.lines = []
        self.model_values = []
        self.observed = None
        self.time = None
        self.zoom_level = 0
        self.setAcceptDrops(True)

    def clear_plot(self):
        for line in self.lines:
            self.axes.lines.remove(line)
        self.lines = []
        if self.observed is not None:
            self.axes.lines.remove(self.observed)
            self.observed = None

    def plot_observed(self):

        self.observed = None

        if self.app.series is None:
            return

        if self.app.resampleCheckBox.isChecked() and (self.app.series.index[1] -
                                                      self.app.series.index[0]) < pd.Timedelta(days=28):
            series = self.app.series.resample('1M').mean()
        else:
            series = self.app.series

        series.plot(ax=self.axes, label='Series', color='C{}'.format(len(self.app.variables)))
        self.observed = self.axes.lines[-1]

    def plot_difference(self):
        var1 = self.app.variables[self.app.modelDropDown.currentIndex()]
        var2 = self.app.variables[self.app.differenceDropDown.currentIndex()]

        difference = pd.Series(var1.get_element(self.app.element.number) - var2.get_element(self.app.element.number),
                               index=var1.times)
        if self.app.resampleCheckBox.isChecked() and (difference.index[1] - difference.index[0]) < pd.Timedelta(days=28):
            difference = difference.resample('1M').mean()
        difference.plot(ax=self.axes, color='C0', label='{} - {}'.format(var1.hdf.model.name, var2.hdf.model.name))
        self.lines.append(self.axes.lines[-1])

    def plot_models(self):
        self.model_values = []
        for i, var in enumerate(self.app.variables):

            s = pd.Series(var.get_element(self.app.element.number), index=var.times, name='modelled')
            if self.app.variable.name == 'table_elev':
                s = self.app.element.elevation - s

            if self.app.resampleCheckBox.isChecked() and (s.index[1] - s.index[0]) < pd.Timedelta(days=28):
                s = s.resample('1M').mean()

            s.plot(color='C{}'.format(i), ax=self.axes,
                   label=var.hdf.model.name)

            self.lines.append(self.axes.lines[-1])
            self.model_values.append(s)

        if self.app.variable.name == 'table_elev':
            self.axes.axhline(self.app.element.elevation, color='brown')

            self.lines.append(self.axes.lines[-1])

    def plot_discharge(self):
        self.model_values = []

        for i, var in enumerate(self.app.variables):
            s = pd.read_csv(var.hdf.model.path('output_{}_discharge_sim_regulartimestep.txt'.format(
                var.hdf.model.catchment_name)), squeeze=True)

            s.name = 'modelled'

            s.index = pd.date_range(start=var.hdf.model.start_date, periods=len(s), freq='1D')

            if self.app.resampleCheckBox.isChecked():
                s = s.resample('1M').mean()

            s.plot(color='C{}'.format(i), ax=self.axes, label=var.hdf.model.name)

            self.lines.append(self.axes.lines[-1])
            self.model_values.append(s)

    def calculate_nse(self):
        if self.observed is None:
            return

        for model_values, line in zip(self.model_values, self.lines):

            join = pd.merge_asof(model_values, self.app.series.resample('1M').mean() if self.app.resampleCheckBox.isChecked() else self.app.series, left_index=True, right_index=True, )[self.xmin:self.xmax]

            join = join[join.modelled.notnull() & join.observed.notnull()]

            ns = 1 - (((join.modelled - join.observed) ** 2).sum() / ((join.observed - join.observed.mean()) ** 2).sum())

            line.set_label('{} ({:.2f})'.format(line.get_label().split(' ')[0], ns))

        self.legend = self.axes.legend()



    def update_data(self):

        self.clear_plot()
        self.plot_observed()
        if self.app.outletCheckBox.isChecked():
            self.plot_discharge()
            self.axes.set_title('Discharge at the Outlet')
            self.axes.set_ylabel('Discharge $(m^3/s)$')
            if self.axes.yaxis_inverted():
                self.axes.invert_yaxis()
        else:
            if not self.app.differenceCheckBox.isChecked():
                self.plot_models()

            else:
                self.plot_difference()

            if self.app.variable.name == 'ph_depth' and not self.axes.yaxis_inverted():
                self.axes.invert_yaxis()
            elif self.app.variable.name != 'ph_depth' and self.axes.yaxis_inverted():
                self.axes.invert_yaxis()

            self.axes.set_title('Element {} - {:.2f} m {}'.format(self.app.element.number,
                                                                  self.app.element.elevation,
                                                                  self.app.element.location))

            self.axes.set_ylabel(self.app.variables[0].long_name)

        self.set_backgroud()

        self.axes.relim()
        self.axes.autoscale_view()

        self.axes.set_xlabel('Time')
        if len(self.lines) > 1 or self.app.differenceCheckBox.isChecked():
            self.legend = self.axes.legend()
        elif self.legend:
            self.legend.remove()
        self.set_x_limits()

    def set_backgroud(self):
        self.axes.patch.set_visible(False)

    def set_time(self, time, norm):
        if self.time in self.axes.lines:
            self.axes.lines.remove(self.time)
        self.time = self.axes.axvline(time, color='black', linewidth=0.8)
        self.set_backgroud()
        self.sm.set_norm(norm)
        self.set_x_limits()

    def set_zoom(self, value):
        self.zoom_level = value
        self.set_x_limits()

    def set_x_limits(self):
        if not self.time:
            return
        x_values = self.lines[0].get_xdata()
        minx = min(x_values).to_timestamp()
        maxx = max(x_values).to_timestamp()
        duration = maxx - minx
        interval = duration / 100
        duration = (duration - interval * self.zoom_level) / 2
        time = self.time.get_xdata()[0]
        xmin = time - duration
        xmax = time + duration

        if xmin < minx:
            diff = minx - xmin
            xmin += diff
            xmax += diff

        if xmax > maxx:
            diff = xmax - maxx
            xmax -= diff
            xmin -= diff

        self.axes.set_xlim(xmin, xmax)

        self.xmin = xmin
        self.xmax = xmax

        self.calculate_nse()
        self.draw()
