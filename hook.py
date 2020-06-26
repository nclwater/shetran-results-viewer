import os
import sys

base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
proj_lib = os.path.join(base_path, 'proj')

os.environ['PROJ_LIB'] = proj_lib
