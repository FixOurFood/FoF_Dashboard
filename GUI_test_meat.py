import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import json

import fair
from fair.RCPs import rcp3pd, rcp45, rcp6, rcp85
from CreateToolTip import *


"""
FixOurFood intervention dashboard: A minimum viable product

This graphical user interface is built using tkinter, which manages the actions
and positions of widgets, grouped into frames.
Each time an action is performed, the "plot" routine is called, which updates the information
going into generated the plots on the right.

There parent frame "window" has three child sub-frames which manage all the
important widgets of the dashboard:

- frame_categories

    Contains horizontal buttons which switch between the diferent types of interventions:
        - Dietary interventions
        - Farming interventions
        - Policy and Governance interventions

- frame_controls

    Contains all the controls, including buttons, sliders and labels, to interact with
    the different types of interventions.
    Depending on the selected category of interventions, different groups of widgets
    are packed and unpacked into frame_controls

- frame_plots

    This frame displays the relevant plots, as well as a dropdown menu to select which
    plot to show. On the bottom, there is a label explaining the basic concepts associated
    to the plots

"""

# load the food item data files for these codes
fii = np.genfromtxt('food_item_info.txt', delimiter=":", dtype=None, names=('code', 'group', 'group_id', 'name', 'mean_emissions'), encoding=None)
len_items = len(fii)
len_groups = len(np.unique(fii['group']))

index_label = np.unique(fii['group'], return_index=True)[1]
group_names = [fii['group'][index] for index in sorted(index_label)]

index_id = np.unique(fii['group_id'], return_index=True)[1]
group_ids = [fii['group_id'][index] for index in sorted(index_id)]

print(group_ids, group_names)

FAOSTAT_years = np.arange(1961, 2019)

# Load food data
# 0 : element
# 1 : region
# 2 : item
# 3 : value
food_data = []
for item in fii['name']:
    print(f"Loading {item} data ...")
    food_data.append(np.load(f"data/food/FAOSTAT_{item}_data.npy"))

# Load population data
print("Loading population data...")
# UK_population = np.load("data/population/Total_population_UN_median_UK.npy")
population = np.load("data/population/Total_population_UN_median_world.npy")

emissions = np.zeros((len_items, len(FAOSTAT_years)))
emissions_groups = np.zeros((len_groups, len(FAOSTAT_years)))

for i in range(len(fii)):
    emissions[i] = food_data[i][(food_data[i][:, 0] == 10004)][:,3] * 365.25 * fii['mean_emissions'][i] * population / 1e12

for i, id in enumerate(group_ids):
    emissions_groups[i] = np.sum(emissions[fii['group_id'] == id], axis=0)

emissions_cumsum_group = np.cumsum(emissions_groups, axis=0)

weight      = np.array([food_data[i][(food_data[i][:, 0] == 10004)][:,3] for i in range(len(fii))])
calories    = np.array([food_data[i][(food_data[i][:, 0] == 664)][:,3] for i in range(len(fii))])
proteins    = np.array([food_data[i][(food_data[i][:, 0] == 674)][:,3] for i in range(len(fii))])

glossary_dict = {
    "CO2 concentration":"""Atmospheric CO2 concentration
    measured in parts per million (PPM)""",

    "CO2 emission per food item":"""Fossil CO2 emissions to the atmosphere
    measured in billion tons per year""",

    "CO2 emission per food group":"""Fossil CO2 emissions to the atmosphere
    measured in billion tons per year""",

    "Radiative forcing":"""Balance between total energy
    absorved by Earth's atmosphere and total
    radiated energy back to space
    measured in Watts per square meter""",

    "Temperature anomaly":"""Difference in Celcius degrees
    between projected atmospheric temperature
    and baseline expected from stable emissions""",

    "Nutrients":""" Daily protein and energy intake per capita,
    in grams and kCal, respectively""",

    "Omnivorous diet":""" Omnivorous diets include the consumption of both
    plant and animal origin food items.""",

    "Semi-vegetarian diet":""" While not uniquely defined, semi-vegetarian diets
    normally include the consumption of animal origin products, typically meat,
    but limited to only certain species, or certain ocassions.""",

    "Pescetarian diet":""" Pescetarian diet limits the consumption of animal
    meat to only that coming from seafood and fish meat.""",

    "Lacto-ovo-vegetarian diet":""" Lacto-ovo-vegetarian diets limits the
    consumption of animal products to only dairy products and eggs,
    supressing any kind of meat consumption.""",

    "Vegan diet":""" Full vegetarian or vegan diets do not include any
    product of animal origin, thus eliminating the consumption of meat, dairy
    products and eggs.""",
}

# Function to scale food item consumption to keep protein intake constant
def scale_food(fixed_quantity, beef_scale, vegetarian_scale):

    meat_fraction = (4-vegetarian_scale)/4
    ruminant_fraction = (4-beef_scale)/4

    total = np.sum(fixed_quantity, axis=0)

    total_no_bovine =  total - fixed_quantity[0] + fixed_quantity[0]*ruminant_fraction
    meat_scale = total / total_no_bovine

    return_meat = [ruminant_fraction, ruminant_fraction, meat_scale, meat_scale]
    return_meat.extend(np.ones(66))

    return return_meat, 1

# Functions to pack and unpack intervention widgets
def pack_dietary_widgets():
    frame_farming.grid_forget()
    frame_policy.grid_forget()
    frame_diet.grid(row=0, column=0)
    button_diet.config(relief='sunken')
    button_farming.config(relief='raised')
    button_policy.config(relief='raised')

def pack_farming_widgets():
    frame_policy.grid_forget()
    frame_diet.grid_forget()
    frame_farming.grid(row=0, column=0)
    button_diet.config(relief='raised')
    button_farming.config(relief='sunken')
    button_policy.config(relief='raised')

def pack_policy_widgets():
    frame_farming.grid_forget()
    frame_diet.grid_forget()
    frame_policy.grid(row=0, column=0)
    button_diet.config(relief='raised')
    button_farming.config(relief='raised')
    button_policy.config(relief='sunken')

# function to generate the plots in tkinter canvas
def plot():

    # Read the selection and generate the arrays
    beef_value = beef_slider.get()
    vegetarian_value = vegetarian_slider.get()
    plot_key = plot_option.get()
    scale_key = scale.get()
    food_group_id_value = food_group.get()

    if plot_key == "CO2 emission per food item":
        for btn in food_group_rdbtn:
            btn.pack(side=tk.LEFT)
    else:
        for btn in food_group_rdbtn:
            btn.pack_forget()


    # Clear previous plots
    plot1.clear()
    plot2.clear()
    plot2.axis("off")

    # protein supply [g / capita / day] 674
    # kCal intake [kCal / capita / day] 664
    # consumed food weight [kg / capita / day] 10004

    if scale_key == "Weight":
        scaling_nutrient = weight
    elif scale_key == "Calories":
        scaling_nutrient = calories
    elif scale_key == "Proteins":
        scaling_nutrient = proteins

    # recompute bovine and meat scaling factors
    meat_scale, vegetarian_scale = scale_food(scaling_nutrient, beef_value, vegetarian_value)
    # print(meat_scale)

    scaled_emissions = np.zeros_like(emissions)
    scaled_calories = np.zeros_like(calories)
    scaled_proteins = np.zeros_like(proteins)

    for i in range(len_items):
        scaled_emissions[i] = emissions[i]*meat_scale[i]
        scaled_calories[i] = calories[i]*meat_scale[i]
        scaled_proteins[i] = proteins[i]*meat_scale[i]

    # per capita food supply emissions [kg CO2e / capita / year]
    # This is computed multiplying the food supply per item (kg/capita/day)
    # by the global mean specific GHGE per item [kg CO2e / kg], by the country population
    # and by the number of days on a year

    # category_emissions = np.zeros((len_categories, len(FAOSTAT_years)))
    C, F, T = fair.forward.fair_scm(emissions=np.sum(scaled_emissions, axis = 0), useMultigas=False)

    if plot_key == "CO2 concentration":
        plot1.plot(FAOSTAT_years, C, c = 'k')
        plot1.set_ylim((250,750))
        plot1.set_ylabel(r"$CO_2$ concentrations (PPM)")

    elif plot_key == "CO2 emission per food group":

        for i in reversed(range(len_groups)):
            plot1.fill_between(FAOSTAT_years, emissions_cumsum_group[i], label = group_names[i])

        plot1.legend(loc=2, fontsize=7)
        plot1.set_ylim((-1,40))
        plot1.set_ylabel(r"Fossil $CO_2$ Emissions (GtC)")

    elif plot_key == "CO2 emission per food item":

        print(food_group_id_value)
        for i in reversed(range(len_groups)):
            plot1.fill_between(FAOSTAT_years, emissions_cumsum_group[i], label = group_names[i])

        plot1.legend(loc=2, fontsize=7)
        plot1.set_ylim((-1,40))
        plot1.set_ylabel(r"Fossil $CO_2$ Emissions (GtC)")

    elif plot_key == "Nutrients":

        plot2.axis("on")
        plot1.plot(FAOSTAT_years, np.sum(scaled_calories, axis=0), label = "Energy intake", color = 'Blue')
        # plot1.set_ylim((150,700))
        plot2.plot(FAOSTAT_years, np.sum(scaled_proteins, axis=0), label = "Protein intake", color = 'Orange')
        # plot2.set_ylim((10,50))
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

    lbl_glossary.config(text=glossary_dict[plot_key], font=("Courier", 12))


# -----------------------------------------
#       MAIN WINDOW
# -----------------------------------------

window = tk.Tk()
window.geometry('960x1070')
window.title('FixOurFood FAIR carbon emission model')

frame_categories = tk.Frame(master=window)
frame_controls = tk.Frame(master=window)
frame_plots = tk.Frame(master=window)

frame_categories.pack(side = tk.TOP)
frame_controls.pack(side=tk.LEFT)
frame_plots.pack(side=tk.RIGHT)

# -----------------------------------------
#       INTERVENTION CATEGORIES
# -----------------------------------------

button_diet = tk.Button(master = frame_categories, text = "Dietary interventions", command=pack_dietary_widgets, font=("Courier", 12))
button_farming = tk.Button(master = frame_categories, text = "Farming interventions", command=pack_farming_widgets, font=("Courier", 12))
button_policy = tk.Button(master = frame_categories, text = "Policy and Governance interventions", command=pack_policy_widgets, font=("Courier", 12))

button_diet_ttp = CreateToolTip(button_diet, \
'Interventions to diet and alimentary practices. '
'Typically involve a modification on consumed food items '
'and individual-level food consuming practices.')

button_farming_ttp = CreateToolTip(button_farming, \
'Interventions to farming practices. '
'Mainly focused on food production, storage and distributions, '
'and waste management.')

button_policy_ttp = CreateToolTip(button_policy, \
'Interventions to policy and governance regulations. '
'Evaluate the effect of regulations and legislation practices '
'on food environmental impact')

button_diet.pack(side = tk.LEFT)
button_farming.pack(side = tk.LEFT)
button_policy.pack(side = tk.LEFT)

# -----------------------------------------
#         INTERVENTION CONTROLS
# -----------------------------------------

frame_diet = tk.Frame(master = frame_controls)

tk.Label(master = frame_diet, text="Reduce bovine meat consumption", font=("Courier", 12)).grid(row = 0, column = 0, columnspan=3)
tk.Label(master = frame_diet, text="Reduce meat consumption",        font=("Courier", 12)).grid(row = 1, column = 0, columnspan=3)
beef_slider =       tk.Scale(master = frame_diet, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot())
beef_slider_ttp = CreateToolTip(beef_slider, \
'0: 0% ruminant meat reduction \n'
'1: 25% ruminant meat reduction \n'
'2: 50% ruminant meat reduction \n'
'3: 75% ruminant meat reduction \n'
'4: 100% ruminant meat reduction')


vegetarian_slider = tk.Scale(master = frame_diet, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot())
beef_slider.grid(row = 0, column = 3)
vegetarian_slider.grid(row = 1, column = 3)

scale = tk.StringVar()
scale.set("Weight")
tk.Label(master=frame_diet, text = "Replace by", font=("Courier", 12)).grid(row = 2, column = 0)
for ic, label in enumerate(['Weight', 'Proteins', 'Calories']):
    tk.Radiobutton(master = frame_diet, text = label,   variable = scale, value = label,   command=plot, font=("Courier", 12)).grid(row = 2, column = ic+1)

# Farming intervention widget

frame_farming = tk.Frame(master = frame_controls)

tk.Scale(master = frame_farming, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot()).grid(row = 0, column = 3)
tk.Scale(master = frame_farming, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot()).grid(row = 1, column = 3)
tk.Scale(master = frame_farming, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot()).grid(row = 2, column = 3)
tk.Scale(master = frame_farming, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot()).grid(row = 3, column = 3)
tk.Scale(master = frame_farming, from_=0, to=4, orient=tk.HORIZONTAL, command= lambda _: plot()).grid(row = 4, column = 3)

tk.Label(master = frame_farming, text="Improve manure treatment",       font=("Courier", 12)).grid(row = 0, column  = 0, columnspan=3)
tk.Label(master = frame_farming, text="Improve breeding",               font=("Courier", 12)).grid(row = 1, column  = 0, columnspan=3)
tk.Label(master = frame_farming, text="Improve stock feed composition", font=("Courier", 12)).grid(row = 2, column  = 0, columnspan=3)
tk.Label(master = frame_farming, text="Grazing versus feedlot",         font=("Courier", 12)).grid(row = 3, column  = 0, columnspan=3)
tk.Label(master = frame_farming, text="Use calves from dairy herd",     font=("Courier", 12)).grid(row = 4, column  = 0, columnspan=3)

# Policy intervention widgets

frame_policy = tk.Frame(master = frame_controls)


# -----------------------------------------
#           PLOT CANVAS
# -----------------------------------------

# Plot option dropdown menu
option_list = ["CO2 emission per food group", "CO2 emission per food item", "CO2 concentration", "Radiative forcing", "Temperature anomaly", "Nutrients"]
plot_option = tk.StringVar()
plot_option.set("CO2 emission per food group")
opt_plot = tk.OptionMenu(frame_plots, plot_option, *option_list, command = lambda _: plot())
opt_plot.config(font=("Courier", 12))
opt_plot.pack()

# Figure widget
fig, plot1 = plt.subplots(figsize = (5,8))
plot2 = plot1.twinx()

canvas = FigureCanvasTkAgg(fig, master = frame_plots)
canvas.get_tk_widget().pack()

food_group = tk.IntVar()
food_group.set(group_ids[0])
food_group_rdbtn = [tk.Radiobutton(master = frame_plots, text = group_names[i], variable = food_group, value = group_ids[i], command=plot, font=("Courier", 12)) for i in range(len_groups)]

# Glossary widget
lbl_glossary = tk.Label(master = frame_plots, text = glossary_dict[plot_option.get()])
lbl_glossary.pack()

################# Setup #################

pack_dietary_widgets()
plot()

################ Loop ###################
window.mainloop()
