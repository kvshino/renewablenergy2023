import customtkinter
import tkinter
from functions.fetchdata import *
from functions.functions import *
import asyncio
from mercati_energetici import MercatiElettrici
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def plot_graph(data, x, y, xlabel, ylabel, title, color):
    """
    Plots a graph.

    Args:
        data: a dataframe containing x and y
        x: dataframe column for the x-coordinates
        y: dataframe column for the y-coordinates
        xlabel: label for the x-coordinates
        ylabel: label for the y-coordinates
        title: used for the window
        color: color of the line plot

    """
   

    x = np.linspace(0, 2 * np.pi, 100)
    y = np.sin(x)

    fig = Figure(figsize=(5, 4), dpi=100)
    plot = fig.add_subplot(111)
    plot.plot(x, y)
    plot.set_xlabel('X-axis')
    plot.set_ylabel('Y-axis')
    plot.set_title('Sine Wave Plot')

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack()



data = setup()
customtkinter.set_default_color_theme("dark-blue")
root = customtkinter.CTk()
root.geometry("500x350")
frame = customtkinter.CTkFrame(master=root)
frame.pack(pady=20,padx=60,fill="both",expand=True)

label = customtkinter.CTkLabel(master=frame, text="Plot")
label.pack(pady=12,padx=10)

button = customtkinter.CTkButton(master = frame,text="Plot",command= plot_graph(data, "hours", "load_profile", "kW", "Load profile","Load profile", "#B55E60"))
button.pack(pady=12,padx=10)
root.mainloop()
