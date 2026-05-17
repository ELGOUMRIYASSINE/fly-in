import matplotlib.pyplot as plt
import matplotlib.colors as colors
from colorir import Palette
from matplotlib.widgets import Button

class Learn():
    def draw(self):
        self.fig, self.ax = plt.subplots(figsize=(10, 6), facecolor="#f7f9fc")
        plt.subplots_adjust(bottom=0.18)
    
jj = Learn()
jj.draw()