import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
NavigationToolbar2Tk)

import fair
from fair.RCPs import rcp3pd, rcp45, rcp6, rcp85

# Define food items
food_items = ["Bovine", "Goat", "Pig", "Poultry", "Beans", "Peas", "Pulses", "Soyabeans"]
len_items = len(food_items)
# mean emissions per kg of item in 2018 [kg CO2e / kg]
mean_emissions = [70.5, 39.7, 12.3, 9.9, 1.8, 1.0, 1.8, 1.8]

# Load food data
food_data = []
for item in food_items:
    print(f"Loading {item} data ...")
    food_data.append(np.load(f"data/food/FAOSTAT_{item}_data.npy"))

# Load population data
print("Loading population data...")
# USA_population = np.load("data/population/Total_population_UN_median_USA.npy")
# Chile_population = np.load("data/population/Total_population_UN_median_Chile.npy")
# UK_population = np.load("data/population/Total_population_UN_median_UK.npy")
population = np.load("data/population/Total_population_UN_median_world.npy")

country_codes = {
    "chile" : 152,
    "uk" : 826,
    "usa" : 840
}


glossary_dict = {
    "concentration":"""Atmospheric CO2 concentration
    measured in parts per million (PPM)""",

    "emission":"""Fossil CO2 emissions to the atmosphere
    measured in billion tons per year""",

    "forcing":"""Radiative forcing: Balance between total energy
    absorved by Earth's atmosphere and total
    radiated energy back to space
    measured in Watts per square meter""",

    "temperature":"""Temperature anomaly, expressed as the difference
    in degrees between projected atmospheric temperature
    and baseline expected from stable emissions, measured
    in Kelvin degrees"""
}

FAOSTAT_years = np.arange(1961, 2019)

def scale_protein(protein, beef_scale, vegetarian_scale):

    meat_fraction = (4-vegetarian_scale)/4
    bovine_fraction = (4-beef_scale)/4

    total = np.sum(protein, axis=0)
    total_no_bovine =  total - protein[0] + protein[0]*bovine_fraction
    meat_scale = total / total_no_bovine
    return [bovine_fraction, meat_scale, meat_scale, meat_scale], 1

# function to generate the plots in tkinter canvas
def plot():

    # Read the selection and generate the arrays
    beef_value = beef_slider.get()
    vegetarian_value = vegetarian_slider.get()
    country_key = country_codes[region.get()]
    plot_key = plot_option.get()

    # Clear previous plots
    plot1.clear()

    # protein supply [gr / capita / day]
    protein = []
    for i in range(len_items):
        protein.append( food_data[i][(food_data[i][:, 0] == 674) & (food_data[i][:, 1] == country_key)][:,3] )

    # recompute bovine and meat scaling factors
    meat_scale, vegetarian_scale = scale_protein(protein, beef_value, vegetarian_value)

    # per capita food supply emissions [kg CO2e / capita / year]
    # This is computed multiplying the food supply per item (kg/capita/day)
    # by the global mean specific GHGE per item [kg CO2e / kg], by the country population
    # and by the number of days on a year
    emissions = []
    for i in range(4):
        emissions.append( food_data[i][(food_data[i][:, 0] == 10004) & (food_data[i][:, 1] == country_key)][:,3] * 365.25 * mean_emissions[i] * population / 1e12 * meat_scale[i] )

    # vegetarian_emissions = beans_emissions + peas_emissions + pulses_emissions + soyabeans_emissions

    C, F, T = fair.forward.fair_scm(emissions=np.sum(emissions, axis = 0), useMultigas=False)

    if plot_key == "concentration":
        plot1.plot(FAOSTAT_years, C, c = 'k')
        plot1.set_ylim((250,750))
        plot1.set_ylabel(r"$CO_2$ concentrations (PPM)")

    elif plot_key == "emission":
        labels = ["Poultry", "Pig", "Mutton and Goat", "Bovine"]
        for i in range(4):
            plot1.fill_between(FAOSTAT_years, np.sum(emissions[:4-i], axis=0), label = labels[i])
        plot1.legend(loc=2, fontsize=7)
        plot1.set_ylim((-1,22))
        plot1.set_ylabel(r"Fossil $CO_2$ Emissions (GtC)")


    elif plot_key == "forcing":
        plot1.plot(FAOSTAT_years, F, c = 'k')
        plot1.set_ylim((-5,5))
        plot1.set_ylabel(r"Total Radiative Forcing $(W/m^2)$")


    elif plot_key == "temperature":
        plot1.plot(FAOSTAT_years, T, c = 'k')
        plot1.set_ylim((-1,2))
        plot1.set_ylabel(r"Temperature anomaly (K)")

    plot1.set_xlabel("Year")
    canvas.draw()

    lbl_glossary.config(text=glossary_dict[plot_key])


# The main Tkinter window
window = tk.Tk()
window.geometry("800x600")
window.title('FAIR carbon emission model')

# Subframes to contain controls and plots
frame_controls = tk.Frame(master=window)
frame_plots = tk.Frame(master=window)
frame_data = tk.Frame(master=frame_controls)

frame_beef = tk.Frame(master=frame_controls)
frame_vegetarian = tk.Frame(master=frame_controls)

frame_controls.pack(side=tk.LEFT)
frame_plots.pack(side=tk.RIGHT)
frame_data.pack()

lbl_data = tk.Label(frame_controls, text = """
Bovine, Mutton & Goat, Pig and Poultry
meat related GHGE (Green House Gas Emissions)
for the 1961 - 2018 period from the FAOSTAT
data, measured in GtC.
"""
)
lbl_data.pack()

frame_beef.pack()
frame_vegetarian.pack()

# Plot option dropdown menu
option_list = ["emission", "concentration", "forcing", "temperature"]
plot_option = tk.StringVar()
plot_option.set("emission")
opt_plot = tk.OptionMenu(frame_plots, plot_option, *option_list, command = lambda _: plot())
opt_plot.pack()

# region set widget
region = tk.StringVar()
region.set("uk")
rbtn_world =  tk.Radiobutton(master = frame_data, text = "Chile", variable = region, value = "chile", command=plot)
rbtn_uk =   tk.Radiobutton(master = frame_data, text = "UK", variable = region, value = "uk", command=plot)
rbtn_yorkshire =  tk.Radiobutton(master = frame_data, text = "USA", variable = region, value = "usa", command=plot)

rbtn_world.pack(side = tk.LEFT)
rbtn_uk.pack(side = tk.LEFT)
rbtn_yorkshire.pack(side = tk.LEFT)


# Transformation widget
beef_slider = tk.Scale(master = frame_beef, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot())
vegetarian_slider = tk.Scale(master = frame_vegetarian, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot())

lbl_beef = tk.Label(master=frame_beef, text="Remove bovine meat from diet")
lbl_vegetarian = tk.Label(master=frame_vegetarian, text="Remove meat from diet")

lbl_beef.pack(side = tk.LEFT)
lbl_vegetarian.pack(side = tk.LEFT)

vegetarian_slider.pack(side = tk.RIGHT)
beef_slider.pack(side = tk.RIGHT)

# Figure widget
fig = Figure(figsize = (5, 5), dpi = 100)
plot1 = fig.add_subplot(111)
canvas = FigureCanvasTkAgg(fig, master = frame_plots)
canvas.get_tk_widget().pack()

# Glossary widget
lbl_glossary = tk.Label(frame_plots, text = glossary_dict[plot_option.get()])
lbl_glossary.pack()

################# Setup #################
plot()

################ Loop ###################
window.mainloop()
