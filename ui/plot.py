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
        self.series_path = None
        self.difference = None

        FigureCanvas.__init__(self, self.fig)
        self.setStyleSheet("background-color:transparent;")
        self.setParent(app)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)

        self.lines = []
        self.time = None
        self.zoom_level = 0
        self.setAcceptDrops(True)

    def update_data(self, series_path=None, difference=None, resample=False):

        self.series_path = series_path
        self.difference = difference

        for line in self.lines:
            self.axes.lines.remove(line)
        self.lines = []

        variables = self.app.variables
        variable_name = variables[0].name
        element = self.app.element

        if series_path is not None:
            try:
                series = pd.read_csv(series_path, usecols=[0, 1], index_col=0, squeeze=True)
                series.index = pd.DatetimeIndex(pd.to_datetime(series.index))

                start = max(min(variables[0].times), min(series.index))
                end = min(max(variables[0].times), max(series.index))
                series = series.sort_index().loc[start:end].rename('observed')
                if resample and (series.index[1] - series.index[0]) < pd.Timedelta(days=28):
                    series = series.resample('1M')
                series.plot(ax=self.axes, label='Observed', color='C{}'.format(len(variables)))
                self.lines.append(self.axes.lines[-1])
            except:
                print('could not plot')
                pass

        if difference is None:
            for i, var in enumerate(variables):

                s = pd.Series(var.get_element(element.number), index=var.times, name='modelled')
                if variable_name == 'table_elev':
                    s = element.elevation - s

                if series_path is not None:
                    xmin, xmax = self.set_x_limits()
                    join = pd.merge(s[xmin:xmax], series, how='left', left_index=True, right_index=True)
                    ns = 1 - (((join.modelled-join.observed)**2).sum()/((join.observed-join.observed.mean())**2).sum())

                if resample and (s.index[1] - s.index[0]) < pd.Timedelta(days=28):
                    s = s.resample('1M').mean()

                s.plot(color='C{}'.format(i), ax=self.axes,
                       label='{} ({:.2f})'.format(var.hdf.model.name, ns)
                       if series_path is not None else var.hdf.model.name)



                self.lines.append(self.axes.lines[-1])

            if variable_name == 'table_elev':
                self.axes.axhline(element.elevation, color='brown')
                self.lines.append(self.axes.lines[-1])

        else:
            var1 = variables[difference[0]]
            var2 = variables[difference[1]]
            difference = pd.Series(var1.get_element(element.number) - var2.get_element(element.number),
                                   index=var1.times)
            if resample and (difference.index[1] - difference.index[0]) < pd.Timedelta(days=28):
                difference = difference.resample('1M')
            difference.plot(ax=self.axes, color='C0', label='{} - {}'.format(var1.hdf.model.name, var2.hdf.model.name))
            self.lines.append(self.axes.lines[-1])

        if variable_name == 'ph_depth' and not self.axes.yaxis_inverted():
            self.axes.invert_yaxis()
        elif variable_name != 'ph_depth' and self.axes.yaxis_inverted():
            self.axes.invert_yaxis()

        self.set_backgroud()

        self.axes.relim()
        self.axes.autoscale_view()

        self.axes.set_title('Element {} - {:.2f} m {}'.format(element.number, element.elevation, element.location))
        self.axes.set_ylabel(variables[0].long_name)
        self.axes.set_xlabel('Time')
        if len(self.lines) > 1 or difference is not None:
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
        if self.series_path:
            self.update_data(series_path=self.series_path)

    def set_zoom(self, value):
        self.zoom_level = value
        self.set_x_limits()

        if self.series_path:
            self.update_data(series_path=self.series_path)

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
        self.draw()

        return xmin, xmax
