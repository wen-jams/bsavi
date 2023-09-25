import holoviews as hv
from holoviews import dim, opts, streams
import pandas as pd
import numpy as np
import panel as pn
import spatialpandas
from bokeh.models import HoverTool
from typing import List, Callable, Union

hv.extension('bokeh', enable_mathjax=True)
pn.extension()


# unpacks the nested data. handles the two supported datatypes
def _unpacker(dataset, index):
    if isinstance(dataset, dict):
        unpacked_data = {key: dataset[key][index] for key in dataset.keys()}
    if isinstance(dataset, pd.core.frame.DataFrame):
        columns = dataset.columns
        dataseries = dataset.iloc[index]
        unpacked_data = pd.DataFrame({columns[item]: dataseries[columns[item]] for item in range(len(columns))})
    return unpacked_data


#  given a param name, find corresponding latex-formatted param name
def _lookup_latex_label(param, latex_dict):
    # handle default case of no latex paramname dictionary
    if latex_dict is None:
        latex_dict = dict()
    try:
        latex_param = latex_dict[param]
        label = r'$${}$$'.format(latex_param)
        return label
    except KeyError:
        label = param
        return label
    

class Observable:
    """
    Observable class for InViz.
    
    Parameters
    ----------
    name: string or list of strings
        specifies the display name of the observable for things like plot titles

    parameters: dict-like or list of dict-likes
        the data to associated with that observable. can be python dict (or pandas DataFrame)
        whose keys (or column names) will be used for things like plot axis labels. 

    latex_labels: dict or list of dicts
        key: value -> parameter label: latex version. parameter label must match the
        corresponding one in the parameters dict

    myfunc: callable
        a user-provided function that returns parameters. can return more than one
        set of parameters.

    myfunc_args: tuple
        arguments for user-provided function

    plot_type: string
        specifies how the data should be visualized. currently can pick either 'Curve'
        or 'Scatter'

    plot_opts: holoviews Options object
        customization options for the observable plot. see Holoviews documentation
    """
    
    def __init__(
        self, 
        name: Union[str, List[str]], 
        parameters: Union[dict, List[dict]] = None, 
        myfunc: Callable = None,
        myfunc_args: tuple = None, 
        plot_type: Union[str, List[str]] = None,
        plot_opts: Union[opts, List[opts]] = None,
        latex_labels: dict = None
    ):
        if isinstance(name, str):
            self.name = [name]
        else:
            self.name = name
        if isinstance(parameters, dict):
            self.parameters = [parameters]
        elif isinstance(parameters, pd.core.frame.DataFrame):
            prms = []
            for column in parameters.columns:
                dset = pd.DataFrame(list(parameters.loc[:, column]))
                prms.append(dset)
            self.parameters = prms
        else:
            self.parameters = parameters
        self.myfunc = myfunc
        self.myfunc_args = myfunc_args
        if isinstance(plot_type, str):
            self.plot_type = [plot_type]
        else:
            self.plot_type = plot_type
        if isinstance(plot_opts, hv.core.options.Options):
            self.plot_opts = [plot_opts]
        else:
            self.plot_opts = plot_opts
        self.latex_labels = latex_labels
        self.number = len(self.name)
    
    def properties(self):
        if len(self.name) > 1:
            print("InViz Grouped Observables")
            for i in range(len(self.name)):
                print(f"\t- Observable {i+1}: {self.name[i]}")
        else:
            print("InViz Observable")
            print(f"Name: {self.name[0]}")
        
    def generate_plot(self, index: int):
        self.plots_list = []
        if self.myfunc and self.myfunc_args is not None:
            computed_data = self.myfunc(index, *self.myfunc_args)
            self.number = len(computed_data)
        for i in range(0, self.number):
            if len(self.plot_type) == 1:
                hv_element = getattr(hv, self.plot_type[0])
            else:
                hv_element = getattr(hv, self.plot_type[i])
            if self.parameters is not None:
                dataset = self.parameters[i]
                unpacked_data = _unpacker(dataset, index)
                kdim, vdim = unpacked_data.keys()
                plot = hv_element(unpacked_data, kdim, vdim, group=self.name[i], label=str(index)) #FIXME
                # plot = hv_element(unpacked_data, kdim, vdim, label=self.name[i])
            elif computed_data:
                dataset = computed_data[i]
                kdim, vdim = dataset.keys()
                plot = hv_element(dataset, kdim, vdim, group=self.name[i], label=str(index)) #FIXME
                # plot = hv_element(dataset, kdim, vdim, label=self.name[i])
            # set defaults
            plot.opts(
                title=f'{self.name[i]}',
                height=400,
                width=500,
                padding=0.1,
                fontscale=1.1,
                xlabel=_lookup_latex_label(kdim, self.latex_labels), 
                ylabel=_lookup_latex_label(vdim, self.latex_labels),
                framewise=True
            )
            # add user defined customizations
            if self.plot_opts is not None:
                if len(self.plot_opts) == 1:
                    plot.opts(self.plot_opts)
                else:
                    plot.opts(self.plot_opts[i])
            
            self.plots_list.append(plot)
        return self.plots_list
        
    def draw_plot(self, index):
        layout = hv.Layout(self.generate_plot(index))
        return layout.opts(shared_axes=False)
        

# generate the visualization
def viz(
    data, 
    observables: list = None, 
    show_observables: bool = False, 
    latex_dict: dict = None
):
    # setting Panel widgets for user interaction
    variables = data.columns.values.tolist()
    var1 = pn.widgets.Select(
        value=variables[0], 
        name='Horizontal Axis', 
        options=variables,
        width=150
    )
    var2 = pn.widgets.Select(
        value=variables[1], 
        name='Vertical Axis', 
        options=variables,
        width=150
    )
    cmap_var = pn.widgets.Select(
        value=variables[2], 
        name='Colormap', 
        options=variables,
        width=150
    )
    cmap_option = pn.widgets.Checkbox(
        value=True, 
        name='Show Colormap', 
        align='end',
        width=150
    )

    # function for generating the scatter plot, given 2 dimensions as x and y axes, and an additional dimension to colormap
    # to the points on the plot. Also has an option to show or hide the colormap
    def plot_data(kdim1, kdim2, colordim, showcmap):
        if showcmap == True:
            cmapping = opts.Points(
                color=dim(colordim),
                colorbar=True,
                cmap='GnBu_r')
        else:
            cmapping = opts.Points(color='grey', colorbar=True)
        hover = HoverTool(tooltips=None)
        xlabel = _lookup_latex_label(kdim1, latex_dict)
        ylabel = _lookup_latex_label(kdim2, latex_dict)
        popts = opts.Points(
            title='Input Data',
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
        table_options = opts.Table(
            height=300, 
            width=600, 
            hooks=[hook], 
            bgcolor='#f5f5f5'
        )
        data_with_index = data.reset_index()
        table = hv.DynamicMap(
            lambda index: hv.Table(data_with_index.iloc[index], kdims=['index', kdim1, kdim2, colordim]), 
            streams=[selection]
        )
        return table.opts(table_options).relabel('Selected Points')
    
    
    # generate the table
    selected_table = pn.bind(
        make_table, 
        kdim1=var1, 
        kdim2=var2, 
        colordim=cmap_var)
    
    #table_stream = streams.Selection1D(source=selected_table)
    
    # handles the null selection case and multiple selections
    plots = {}
    # get total number of plots to draw from list of observables
    plotting_info = {}
    if observables is None:
        observables = []
    else:
        show_observables = True
    for each in observables:
        for i in range(len(each.name)):
            if each.plot_opts is None:
                specific_opts = None
            elif len(each.plot_opts) == 1:
                specific_opts = each.plot_opts[0]
            elif each.plot_opts[i] is not None:
                specific_opts = each.plot_opts[i]
            
            if len(each.plot_type) == 1:
                plotting_info[each.name[i]] = {'type': each.plot_type[0], 'opts': specific_opts}
            else:
                plotting_info[each.name[i]] = {'type': each.plot_type[i], 'opts': specific_opts}

    def plot_observables(index):
        if not index:
            plots_list = []
            for name in plotting_info:
                hv_type = getattr(hv, plotting_info[name]['type'])
                empty_plot = hv_type(np.random.rand(0, 2), group=f'{name}', label='None').opts(
                    title=f'{name} - No Selection', 
                    height=400, 
                    width=500, 
                    fontscale=1.1, 
                    framewise=True)
                if plotting_info[name]['opts'] is not None:
                    empty_plot.opts(plotting_info[name]['opts'])
                plots_list.append([empty_plot])
        else:
            new_index = [x for x in index if x not in list(plots.keys())]
            for element in new_index:
                new_plots = []
                for each in observables:
                    new_plots.extend(each.generate_plot(element))
                plots[element] = {plot.group: plot for plot in new_plots} #FIXME
                # plots[element] = {plot.label: plot for plot in new_plots}
            
            plots_list = []
            for index_item in index:
                plot_types = list(plots[index_item].keys())

            for plot_item in plot_types:
                same_type = [plots[key][plot_item] for key in index]
                plots_list.append(same_type)
            
        layout = hv.Layout()
        for list_of_plots in plots_list:
            overlay = hv.Overlay(list_of_plots).opts(show_legend=True, legend_position='right')
            layout = layout + overlay
        layout.opts(shared_axes=False, toolbar='left').cols(2)
        return layout
    
    # put it all together using Panel
    input_panel = pn.Row(
        pn.Column(var1, var2, cmap_var, cmap_option), 
        points_dmap
    )
    dashboard = pn.Column(input_panel, selected_table)
    
    if show_observables == True:
        observables_dmap = hv.DynamicMap(plot_observables, streams=[selection]).opts(framewise=True)
        observables_pane = pn.panel(observables_dmap)
        dashboard = pn.Row(dashboard, observables_pane)
    
    return dashboard
