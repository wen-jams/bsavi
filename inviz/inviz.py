import holoviews as hv
from holoviews import dim, opts, streams
import pandas as pd
import numpy as np
import panel as pn
import spatialpandas
from bokeh.models import HoverTool
import matplotlib.pyplot as plt

hv.extension('bokeh')
pn.extension()


# generate a scatter plot using the key dimensions from a holoviews.Dataset object, with the CLASS output displayed alongside it
def viz(data, data_observable=None, myfunction=None, myfunction_args=None, show_observables=True, latex_dict=None, curve_opts=None):
    # handle default case of no latex paramname dictionary
    if latex_dict is None:
        latex_dict = dict()
    # setting Panel widgets for user interaction
    variables = data.columns.values.tolist()
    var1 = pn.widgets.Select(value=variables[1], name='Horizontal Axis', options=variables)
    var2 = pn.widgets.Select(value=variables[2], name='Vertical Axis', options=variables)
    cmap_var = pn.widgets.Select(value=variables[0], name='Colormapped Parameter', options=variables)
    cmap_option = pn.widgets.Checkbox(value=True, name='Show Colormap', align='end')
    
    #  given a param name, find corresponding latex-formatted param name
    def lookup_latex_label(param):
        try:
            latex_param = latex_dict[param]
            label = r'$${}$$'.format(latex_param)
            return label
        except KeyError:
            label = param
            return label
    
    # function for generating the scatter plot, given 2 dimensions as x and y axes, and an additional dimension to colormap
    # to the points on the plot. Also has an option to show or hide the colormap
    def plot_data(kdim1, kdim2, colordim, showcmap):
        if showcmap == True:
            cmapping = opts.Points(color=dim(colordim),
                colorbar=True,
                cmap='GnBu_r')
        else:
            cmapping = opts.Points(color='grey', colorbar=True)
        hover = HoverTool(tooltips=None)
        xlabel = lookup_latex_label(kdim1)
        ylabel = lookup_latex_label(kdim2)
        popts = opts.Points(
            bgcolor='#E5E9F0',
            fontscale=1.1,
            xlabel=xlabel,
            ylabel=ylabel,
            toolbar='above',
            line_color='black',
            #alpha=0.75, selection_alpha=1, nonselection_alpha=0.1,
            tools=[hover, 'box_select','lasso_select','tap'],
            size=7)
        points = hv.Points(data, kdims=[kdim1, kdim2]).opts(popts, cmapping)
        return points
    
    # bind the widget values to the plotting function so it gets called every time the user interacts with the widget
    # call the bound plotting function inside a holoview DynamicMap object for interaction
    interactive_points = pn.bind(plot_data, kdim1=var1, kdim2=var2, colordim=cmap_var, showcmap=cmap_option)
    points_dmap = hv.DynamicMap(interactive_points, kdims=[]).opts(width=500, height=400, framewise=True)
    
    # define a stream to get a list of all the points the user has selected on the plot
    selection = streams.Selection1D(source=points_dmap)
    
    # formatting the table using plot hooks
    def hook(plot, element):
        plot.handles['table'].autosize_mode = "none"
        for column in plot.handles['table'].columns:
            column.width = 100
    
    # function to generate a table of all the selected points
    def make_table(kdim1, kdim2, colordim):
        table_options = opts.Table(height=300, width=1000, hooks=[hook], bgcolor='#f5f5f5')
        table = hv.DynamicMap(lambda index: hv.Table(data.iloc[index], kdims=[kdim1, kdim2, colordim]), streams=[selection])
        return table.opts(table_options).relabel('Selected Points')
    
    
    # generate the table
    selected_table = pn.bind(make_table, kdim1=var1, kdim2=var2, colordim=cmap_var)
    
    #table_stream = streams.Selection1D(source=selected_table)
    
    # function to run CLASS on data from the selection. 
    # handles the null selection case and multiple selections
    curves = {}
    empty_plot = hv.Curve(np.random.rand(0, 2)).opts(framewise=True)
    if data_observable is not None:
        data_observable = data_observable.to_dict('index')
    def plot_observables(index):
        if not index:
            curves_list = [[empty_plot.relabel('Plot 1 - No Selection')], 
                           [empty_plot.relabel('Plot 2 - No Selection')], 
                           [empty_plot.relabel('Plot 3 - No Selection')]]
        else:
            new_index = [x for x in index if x not in list(curves.keys())]
            for element in new_index:
                if data_observable is not None:
                    observables = data_observable[element]
                elif myfunction is not None:
                    observables = myfunction(element, *myfunction_args)
                observables_keys = list(observables.keys())

                new_plots = []
                for key in observables_keys:
                    dataset = observables[key]
                    kdim = list(dataset.keys())[0]
                    vdim = list(dataset.keys())[1]
                    plot_observable = hv.Curve(dataset, kdim, vdim, label=key).opts(framewise=True)
                    new_plots.append(plot_observable)
                curves[element] = {plot.label: plot for plot in new_plots}

            curves_list = []
            for index_item in index:
                curve_types = list(curves[index_item].keys())

            for curve_item in curve_types:
                same_type = [curves[key][curve_item] for key in index]
                curves_list.append(same_type)
            
        layout = hv.Layout()
        for list_of_curves in curves_list:
            overlay = hv.Overlay(list_of_curves)
            layout = layout + overlay    
        return layout
    
    
    # put it all together using Panel
    dashboard = pn.Column(pn.Row(var1, var2, cmap_var, cmap_option), pn.Row(points_dmap, selected_table))
    
    if show_observables == True:
        observables_dmap = hv.DynamicMap(plot_observables, streams=[selection]).opts(
            curve_opts, 
            opts.Layout(shared_axes=False),
            opts.Overlay(show_legend=False)
        )
        observables_pane = pn.panel(observables_dmap)
        dashboard = pn.Column(dashboard, observables_pane)
    
    return dashboard
