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
    "CO2 concentration":"""Atmospheric CO2 concentration
    measured in parts per million (PPM)""",

    "CO2 emission":"""Fossil CO2 emissions to the atmosphere
    measured in billion tons per year""",

    "Radiative forcing":"""Balance between total energy
    absorved by Earth's atmosphere and total
    radiated energy back to space
    measured in Watts per square meter""",

    "Temperature anomaly":"""Difference in Celcius degrees
    between projected atmospheric temperature
    and baseline expected from stable emissions""",

    "Nutrients":""" Daily protein and energy intake per capita,
    in grams and kCal, respectively"""
}

FAOSTAT_years = np.arange(1961, 2019)

# Function to scale food item consumption to keep protein intake constant
def scale_food(fixed_quantity, beef_scale, vegetarian_scale):

    meat_fraction = (4-vegetarian_scale)/4
    bovine_fraction = (4-beef_scale)/4

    total = np.sum(fixed_quantity, axis=0)
    total_no_bovine =  total - fixed_quantity[0] + fixed_quantity[0]*bovine_fraction
    meat_scale = total / total_no_bovine
    return [bovine_fraction, meat_scale, meat_scale, meat_scale], 1

# Functions to pack and unpack intervention widgets
def pack_dietary_widgets():
    frame_breed.pack_forget()
    frame_manure.pack_forget()
    frame_feed.pack_forget()
    frame_afo.pack_forget()
    frame_calves.pack_forget()

    frame_beef.pack()
    frame_vegetarian.pack()
    frame_scale.pack()

def pack_farming_widgets():
    frame_beef.pack_forget()
    frame_vegetarian.pack_forget()
    frame_scale.pack_forget()

    frame_breed.pack()
    frame_manure.pack()
    frame_feed.pack()
    frame_afo.pack()
    frame_calves.pack()

# function to generate the plots in tkinter canvas
def plot():

    # Read the selection and generate the arrays
    beef_value = beef_slider.get()
    vegetarian_value = vegetarian_slider.get()
    country_key = country_codes[region.get()]
    plot_key = plot_option.get()
    scale_key = scale.get()

    # Clear previous plots
    plot1.clear()
    plot2.clear()
    plot2.axis("off")

    # protein supply [g / capita / day] 674
    # kCal intake [kCal / capita / day] 664
    # consumed food weight [kg / capita / day] 10004

    calories = []
    proteins = []
    weight = []

    for i in range(len_items):
        weight.append( food_data[i][(food_data[i][:, 0] == 10004) & (food_data[i][:, 1] == country_key)][:,3] )
        calories.append( food_data[i][(food_data[i][:, 0] == 664) & (food_data[i][:, 1] == country_key)][:,3] )
        proteins.append( food_data[i][(food_data[i][:, 0] == 674) & (food_data[i][:, 1] == country_key)][:,3] )

    if scale_key == "weight":
        scaling_nutrient = weight
    elif scale_key == "calories":
        scaling_nutrient = calories
    elif scale_key == "proteins":
        scaling_nutrient = proteins

    # recompute bovine and meat scaling factors
    meat_scale, vegetarian_scale = scale_food(scaling_nutrient, beef_value, vegetarian_value)

    # per capita food supply emissions [kg CO2e / capita / year]
    # This is computed multiplying the food supply per item (kg/capita/day)
    # by the global mean specific GHGE per item [kg CO2e / kg], by the country population
    # and by the number of days on a year
    emissions = []
    for i in range(4):
        emissions.append( food_data[i][(food_data[i][:, 0] == 10004) & (food_data[i][:, 1] == country_key)][:,3] * 365.25 * mean_emissions[i] * population / 1e12 * meat_scale[i] )
        calories[i] *= meat_scale[i]
        proteins[i] *= meat_scale[i]
    # vegetarian_emissions = beans_emissions + peas_emissions + pulses_emissions + soyabeans_emissions

    C, F, T = fair.forward.fair_scm(emissions=np.sum(emissions, axis = 0), useMultigas=False)

    if plot_key == "CO2 concentration":
        plot1.plot(FAOSTAT_years, C, c = 'k')
        plot1.set_ylim((250,750))
        plot1.set_ylabel(r"$CO_2$ concentrations (PPM)")


    elif plot_key == "CO2 emission":
        labels = ["Poultry", "Pig", "Mutton and Goat", "Bovine"]
        for i in range(4):
            plot1.fill_between(FAOSTAT_years, np.sum(emissions[:4-i], axis=0), label = labels[i])
        plot1.legend(loc=2, fontsize=7)
        plot1.set_ylim((-1,30))
        plot1.set_ylabel(r"Fossil $CO_2$ Emissions (GtC)")

    elif plot_key == "Nutrients":

        plot2.axis("on")
        plot1.plot(FAOSTAT_years, np.sum(calories, axis=0), label = "Energy intake", color = 'Blue')
        plot1.set_ylim((150,700))

        plot2.plot(FAOSTAT_years, np.sum(proteins, axis=0), label = "Protein intake", color = 'Orange')
        plot2.set_ylim((10,50))

        plot1.legend(loc=2, fontsize=7)
        plot2.legend(loc=1, fontsize=7)
        # plot1.set_ylim((-1,30))
        # plot1.set_ylabel(r"Fossil $CO_2$ Emissions (GtC)")


    elif plot_key == "Radiative forcing":
        plot1.plot(FAOSTAT_years, F, c = 'k')
        plot1.set_ylim((-5,5))
        plot1.set_ylabel(r"Total Radiative Forcing $(W/m^2)$")


    elif plot_key == "Temperature anomaly":
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

frame_interventions = tk.Frame(master=frame_controls)
frame_data = tk.Frame(master=frame_controls)
frame_scale = tk.Frame(master=frame_controls)

frame_controls.pack(side=tk.LEFT)
frame_plots.pack(side=tk.RIGHT)
frame_interventions.pack(side = tk.TOP)
frame_data.pack()

lbl_data = tk.Label(frame_controls, text = """
Bovine, Mutton & Goat, Pig and Poultry
meat related GHGE (Green House Gas Emissions)
for the 1961 - 2018 period from the FAOSTAT
data, measured in GtC.
""")

lbl_data.pack()

# Plot option dropdown menu
option_list = ["CO2 emission", "CO2 concentration", "Radiative forcing", "Temperature anomaly", "Nutrients"]
plot_option = tk.StringVar()
plot_option.set("CO2 emission")
opt_plot = tk.OptionMenu(frame_plots, plot_option, *option_list, command = lambda _: plot())
opt_plot.pack()


# Intervention cathegory button widget
button_diet = tk.Button(master = frame_interventions, text = "Dietary interventions", command=pack_dietary_widgets)
button_farming = tk.Button(master = frame_interventions, text = "Farming interventions", command=pack_farming_widgets)
button_diet.pack(side = tk.LEFT)
button_farming.pack(side = tk.LEFT)

# region set widget
region = tk.StringVar()
region.set("uk")
rbtn_world =  tk.Radiobutton(master = frame_data, text = "Chile", variable = region, value = "chile", command=plot)
rbtn_uk =   tk.Radiobutton(master = frame_data, text = "UK", variable = region, value = "uk", command=plot)
rbtn_yorkshire =  tk.Radiobutton(master = frame_data, text = "USA", variable = region, value = "usa", command=plot)

rbtn_world.pack(side = tk.LEFT)
rbtn_uk.pack(side = tk.LEFT)
rbtn_yorkshire.pack(side = tk.LEFT)


# Dietary intervention widget
frame_beef = tk.Frame(master=frame_controls)
frame_vegetarian = tk.Frame(master=frame_controls)


beef_slider = tk.Scale(master = frame_beef, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot())
vegetarian_slider = tk.Scale(master = frame_vegetarian, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot())

lbl_beef = tk.Label(master=frame_beef, text="Reduce bovine meat consumption")
lbl_vegetarian = tk.Label(master=frame_vegetarian, text="Reduce meat consumption")

lbl_beef.pack(side = tk.LEFT)
beef_slider.pack(side = tk.RIGHT)

lbl_vegetarian.pack(side = tk.LEFT)
vegetarian_slider.pack(side = tk.RIGHT)

lbl_scale = tk.Label(master=frame_scale, text = "Replace by")
scale = tk.StringVar()
scale.set("weight")
rbtn_weight =  tk.Radiobutton(master = frame_scale, text = "Weight", variable = scale, value = "weight", command=plot)
rbtn_proteins =   tk.Radiobutton(master = frame_scale, text = "Proteins", variable = scale, value = "proteins", command=plot)
rbtn_calories =  tk.Radiobutton(master = frame_scale, text = "Calories", variable = scale, value = "calories", command=plot)

lbl_scale.pack(side = tk.LEFT)
rbtn_weight.pack(side = tk.LEFT)
rbtn_proteins.pack(side = tk.LEFT)
rbtn_calories.pack(side = tk.LEFT)


# Farming intervention widget
frame_manure = tk.Frame(master=frame_controls)
frame_breed = tk.Frame(master=frame_controls)
frame_feed = tk.Frame(master=frame_controls)
frame_afo = tk.Frame(master=frame_controls)
frame_calves = tk.Frame(master=frame_controls)

manure_slider = tk.Scale(master = frame_manure, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot())
breed_slider = tk.Scale(master = frame_breed, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot())
feed_slider = tk.Scale(master = frame_feed, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot())
afo_slider = tk.Scale(master = frame_afo, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot())
calves_slider = tk.Scale(master = frame_calves, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot())

lbl_manure = tk.Label(master=frame_manure, text="Improve manure treatment")
lbl_breed = tk.Label(master=frame_breed, text="Improve breeding")
lbl_feed = tk.Label(master=frame_feed, text="Improve stock feed composition")
lbl_afo = tk.Label(master=frame_afo, text="Grazing versus feedlot")
lbl_calves = tk.Label(master=frame_calves, text="Use calves from dairy herd")

lbl_manure.pack(side = tk.LEFT)
lbl_breed.pack(side = tk.LEFT)
lbl_feed.pack(side = tk.LEFT)
lbl_afo.pack(side = tk.LEFT)
lbl_calves.pack(side = tk.LEFT)

manure_slider.pack(side = tk.RIGHT)
breed_slider.pack(side = tk.RIGHT)
feed_slider.pack(side = tk.RIGHT)
afo_slider.pack(side = tk.RIGHT)
calves_slider.pack(side = tk.RIGHT)


# Figure widget
fig, plot1 = plt.subplots(figsize = (5,5))
plot2 = plot1.twinx()

canvas = FigureCanvasTkAgg(fig, master = frame_plots)
canvas.get_tk_widget().pack()

# Glossary widget
lbl_glossary = tk.Label(frame_plots, text = glossary_dict[plot_option.get()])
lbl_glossary.pack()

################# Setup #################
pack_dietary_widgets()
plot()

################ Loop ###################
window.mainloop()
