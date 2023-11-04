import holoviews as hv
from holoviews import dim, opts, streams
import pandas as pd
import numpy as np
import panel as pn
# import spatialpandas
from bokeh.models import HoverTool
from typing import List, Callable, Union

hv.extension('bokeh', enable_mathjax=True)
pn.extension('mathjax')


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
    
class _observable_utils:
    def __init__(
        self,
        name: Union[str, List[str]], 
        plot_type: Union[str, List[str]] = None,
        plot_opts: Union[opts, List[opts]] = None,
        latex_labels: dict = None
    ):
        if isinstance(name, str):
            self.name = [name]
        else:
            self.name = name
        if isinstance(plot_type, str):
            self.plot_type = [plot_type]
        elif isinstance(plot_type, list):
            self.plot_type = plot_type
        else:
            self.plot_type = ['Curve']
        if isinstance(plot_opts, hv.core.options.Options):
            self.plot_opts = [plot_opts]
        else:
            self.plot_opts = plot_opts
        self.latex_labels = latex_labels
        self.number = len(self.name)

    def properties(self):
        if len(self.name) > 1:
            print("BSAVI Grouped Observables")
            for i in range(len(self.name)):
                print(f"\t- Observable {i+1}: {self.name[i]}")
        else:
            print("BSAVI Observable")
            print(f"Name: {self.name[0]}")


class Observable(_observable_utils):
    """
    Observable class for tabulated data.
    
    Parameters
    ----------
    name: string or list of strings
        specifies the display name of the observable for things like plot titles

    data: dict-like or list of dict-likes
        the data to associated with that observable. can be python dict (or pandas DataFrame)
        whose keys (or column names) will be used for things like plot axis labels. 

    plot_type: string
        specifies how the data should be visualized. currently can pick either 'Curve'
        or 'Scatter'

    plot_opts: holoviews Options object
        customization options for the observable plot. see Holoviews documentation

    latex_labels: dict
        dictionary of plain text parameter names as keys and 
        latex versions as values for the data table
    """    
    def __init__(
        self, 
        name: Union[str, List[str]], 
        data: Union[dict, List[dict]], 
        plot_type: Union[str, List[str]] = None,
        plot_opts: Union[opts, List[opts]] = None,
        latex_labels: dict = None
    ):
        super().__init__(name, plot_type, plot_opts, latex_labels)
        
        if isinstance(data, dict):
            self.data = [data]
        elif isinstance(data, pd.core.frame.DataFrame):
            prms = []
            for column in data.columns:
                dset = pd.DataFrame(list(data.loc[:, column]))
                prms.append(dset)
            self.data = prms
        else:
            self.data = data
        
    def generate_plot(self, index: list):
        plots_dict = {}
        
        for i in range(0, self.number):
            indexed_plots = []
            for n in index:
                if len(self.plot_type) == 1:
                    hv_element = getattr(hv, self.plot_type[0])
                else:
                    hv_element = getattr(hv, self.plot_type[i])
                dataset = self.data[i]
                unpacked_data = _unpacker(dataset, n)
                kdim, vdim = unpacked_data.keys()
                plot = hv_element(unpacked_data, kdim, vdim) #TODO
                # plot = hv_element(unpacked_data, kdim, vdim, label=self.name[i])
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
                indexed_plots.append(plot)
                plots_dict[self.name[i]] = dict(zip(index, indexed_plots))
        return plots_dict
        
    def draw_plot(self, index: list):
        layout = hv.Layout()
        plots = self.generate_plot(index)
        for name in plots:
            overlay = hv.NdOverlay(plots[name], kdims='index').opts(legend_position='right')
            layout = layout + overlay
        return layout.opts(shared_axes=False)
        

class LiveObservable(_observable_utils):
    """
    LiveObservable class for dynamically calculated data.
    
    Parameters
    ----------
    name: string or list of strings
        specifies the display name of the observable for things like plot titles

    myfunc: callable
        a user-provided function that returns data. can return more than one
        set of data.

    myfunc_args: tuple
        arguments for user-provided function

    plot_type: string
        specifies how the data should be visualized. currently can pick either 'Curve'
        or 'Scatter'

    plot_opts: holoviews Options object
        customization options for the observable plot. see Holoviews documentation

    latex_labels: dict
        dictionary of plain text parameter names as keys and 
        latex versions as values for the data table
    """    
    def __init__(
        self, 
        name: Union[str, List[str]], 
        myfunc: Callable,
        myfunc_args: tuple,
        plot_type: Union[str, List[str]] = None,
        plot_opts: Union[opts, List[opts]] = None,
        latex_labels: dict = None
    ):
        super().__init__(name, plot_type, plot_opts, latex_labels)
        self.myfunc = myfunc
        self.myfunc_args = myfunc_args

    def properties(self):
        super().properties()
        print(f'Calculated by {self.myfunc.__name__}')
    def generate_plot(self, index: list):
        plots_dict = {k: {} for k in self.name}

        for n in index:
            computed_data = self.myfunc(n, *self.myfunc_args)
            
            for i in range(0, self.number):
                if len(self.plot_type) == 1:
                    hv_element = getattr(hv, self.plot_type[0])
                else:
                    hv_element = getattr(hv, self.plot_type[i])  
                dataset = computed_data[i]
                kdim, vdim = dataset.keys()
                plot = hv_element(dataset, kdim, vdim) #TODO
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
                plots_dict[self.name[i]].update({n: plot})
        return plots_dict

    def draw_plot(self, index: list):
        layout = hv.Layout()
        plots = self.generate_plot(index)
        for name in plots:
            overlay = hv.NdOverlay(plots[name], kdims='index').opts(legend_position='right')
            layout = layout + overlay
        return layout.opts(shared_axes=False)
        

# generate the visualization
def viz(
    data, 
    observables: list[Union[Observable, LiveObservable]] = None, 
    show_observables: bool = False, 
    latex_dict: dict = None
    ):
    """
    Interactive dashboard linking data and observables

    Parameters
    ----------
    data: Pandas DataFrame
        a table containing samples of parameter values
    
    observables: list[Observable | LiveObservable]
        a list of Observables corresponding to the samples
    
    show_observables: bool
        whether display observables

    latex_labels: dict
        dictionary of plain text parameter names as keys and 
        latex versions as values for the data table
    """
    # setting Panel widgets for user interaction
    variables = data.columns.values.tolist()
    var1 = pn.widgets.Select(value=variables[0], name='Horizontal Axis', 
                             options=variables, width=150)
    var2 = pn.widgets.Select(value=variables[1], name='Vertical Axis', 
                             options=variables, width=150)
    cmap_var = pn.widgets.Select(value=variables[2], name='Colormap', 
                                 options=variables,width=150)
    cmap_option = pn.widgets.Checkbox(value=True, name='Show Colormap', 
                                      align='end',width=150)

    # function for generating the scatter plot, given 2 dimensions as x and y axes, and an additional dimension to colormap
    # to the points on the plot. Also has an option to show or hide the colormap
    def plot_data(kdim1, kdim2, colordim, showcmap):
        if showcmap == True:
            cmapping = opts.Points(
                color=dim(colordim),
                colorbar=True,
                cmap='Spectral_r')
        else:
            cmapping = opts.Points(color='grey', colorbar=True)
        hover = HoverTool(tooltips=None)
        xlabel = _lookup_latex_label(kdim1, latex_dict)
        ylabel = _lookup_latex_label(kdim2, latex_dict)
        popts = opts.Points(
            title='Sample Data',
            bgcolor='#FEFEFE',
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
    
    # handles the null selection case and multiple selections
    plot_dict = {k: {} for k in list(plotting_info.keys())}
    
    def plot_observables(index):
        if not index:
            layout = hv.Layout()
            for name in plotting_info:
                # get name of plot element (type)
                hv_type = getattr(hv, plotting_info[name]['type'])
                # generate empty plot with default options
                empty_plot = hv_type(np.random.rand(0, 2), group=f'{name}', label='None').opts(
                    title=f'{name} - No Selection', height=400, width=500, fontscale=1.1, framewise=True)
                # apply custom options if specified
                if plotting_info[name]['opts'] is not None:
                    empty_plot.opts(plotting_info[name]['opts'])
                # make an empty NdOverlay and append to layout
                empty_overlay = hv.NdOverlay({'none': empty_plot}, kdims='index').opts(legend_position='right')
                layout = layout + empty_overlay
        else:
            # get the indices that haven't been seen before
            new_index = [x for x in index if x not in list(plot_dict[list(plot_dict.keys())[0]].keys())]
            # go through each observable and generate its plots, adding them
            # to the shared plot_dict
            for each in observables:
                new_plots = each.generate_plot(new_index)
                # observable names should match plot_dict keys
                for key in each.name:
                    if new_index:
                        plot_dict[key].update(new_plots[key])
            # recursively build a layout of NdOverlays
            layout = hv.Layout()
            for key in plot_dict:
                filtered_indexed_plots = {idx_num: plot_dict[key][idx_num] for idx_num in index}
                overlay = hv.NdOverlay(filtered_indexed_plots, kdims='index').opts(legend_position='right')
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
