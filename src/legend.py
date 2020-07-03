from matplotlib.pyplot import colorbar
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.cm import ScalarMappable
from matplotlib.figure import Figure
from matplotlib.colors import Normalize
import numpy as np
from settings import colormap


class LegendCanvas(FigureCanvas):
    def __init__(self, app):

        self.app = app

        self.fig = Figure(figsize=(7, 1))
        self.fig.subplots_adjust(bottom=0.5)

        self.fig.set_constrained_layout_pads(h_pad=100)
        FigureCanvas.__init__(self, self.fig)
        self.setFixedHeight(50)
        self.axes = self.fig.add_subplot(111)
        self.sm = ScalarMappable(cmap=colormap, norm=Normalize(vmin=0, vmax=1))
        self.sm.set_array(np.array([]))
        self.colorbar = colorbar(self.sm, cax=self.axes,
                                 pad=1,
                                 orientation='horizontal')
        self.fig.patch.set_visible(False)
        self.setStyleSheet("background-color:transparent;")

    def set_time(self, norm):
        self.sm.set_norm(norm)
        self.draw()
