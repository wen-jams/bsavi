import holoviews as hv
from holoviews import dim, opts, streams
import pandas as pd
import numpy as np
import panel as pn
import spatialpandas
from bokeh.models import HoverTool
from scipy import signal
from typing import Callable

hv.extension('bokeh')
pn.extension()


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
        set of parameters if the "grouped" option is True
    myfunc_args: tuple
        arguments for user-provided function
    grouped: boolean
        specifies if user-provided function returns more than one set of parameters
    plot_type: string
        specifies how the data should be visualized. currently can pick either 'Curve'
        or 'Scatter'
    plot_opts: holoviews Options object
        customization options for the observable plot. see Holoviews documentation
    """
    
    def __init__(
        self, 
        name: str | list[str] = None, 
        parameters: dict | list[dict] = None, 
        myfunc: Callable = None,
        myfunc_args: tuple = None, 
        grouped: bool = False, 
        plot_type: str | list[str] = None,
        plot_opts: type[opts] | list[type[opts]] = None,
        latex_labels: dict = None
    ):
        self.name = [name]
        self.parameters = [parameters]
        self.myfunc = myfunc
        self.myfunc_args = myfunc_args
        self.latex_labels = [latex_labels]
        self.plot_type = [plot_type]
        self.plot_opts = [plot_opts]
        self.grouped = grouped
        if self.grouped:
            self.name = name
            self.parameters = parameters
            self.latex_labels = latex_labels
            self.plot_type = plot_type
            self.plot_opts = plot_opts
        self.number = len(self.name)
    
    def properties(self):
        if self.grouped:
            print("InViz Grouped Observable")
            for i in range(len(self.name)):
                print(f"\t- Observable {i+1}: {self.name[i]}")
        else:
            print("InViz Observable")
            print(f"Name: {self.name}")
        
    def generate_plot(self, index: int):
        self.plots_list = []
        if self.myfunc and self.myfunc_args is not None:
            computed_data = self.myfunc(index, *self.myfunc_args)
            self.number = len(computed_data)
        for i in range(0, self.number):
            hv_element = getattr(hv, self.plot_type[i])
            if self.parameters is not None:
                dataset = self.parameters[i]
                kdim = list(dataset.keys())[0]
                vdim = list(dataset.keys())[1]
                plot = hv_element(dataset[index], kdim, vdim, label=self.name[i])
            elif computed_data:
                dataset = computed_data[i]
                kdim = list(dataset.keys())[0]
                vdim = list(dataset.keys())[1]
                plot = hv_element(dataset, kdim, vdim, label=self.name[i])
            plot.opts(xlabel=lookup_latex_label(kdim, self.latex_labels), ylabel=lookup_latex_label(vdim, self.latex_labels))
            if self.plot_opts is not None:
                plot.opts(self.plot_opts[i])
            self.plots_list.append(plot)
        return self.plots_list
        
    def draw_plot(self, index, observable_name=None):
        if observable_name is not None:
            return 
        layout = hv.Layout(self.generate_plot(index))
        return layout.opts(shared_axes=False)


def lookup_latex_label(param, latex_dict):
    try:
        latex_param = latex_dict[param]
        label = r'$${}$$'.format(latex_param)
        return label
    except KeyError:
        label = param
        return label

# generate a scatter plot using the key dimensions from a holoviews.Dataset object, with the CLASS output displayed alongside it
def viz(
    data, 
    observables: list = None, 
    show_observables: bool = True, 
    latex_dict: dict = None
):
    # handle default case of no latex paramname dictionary
    if latex_dict is None:
        latex_dict = dict()
    # setting Panel widgets for user interaction
    variables = data.columns.values.tolist()
    var1 = pn.widgets.Select(value=variables[1], name='Horizontal Axis', options=variables)
    var2 = pn.widgets.Select(value=variables[2], name='Vertical Axis', options=variables)
    cmap_var = pn.widgets.Select(value=variables[0], name='Colormapped Parameter', options=variables)
    cmap_option = pn.widgets.Checkbox(value=True, name='Show Colormap', align='end')

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
        xlabel = lookup_latex_label(kdim1, latex_dict)
        ylabel = lookup_latex_label(kdim2, latex_dict)
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
    
    # handles the null selection case and multiple selections
    plots = {}
    # get total number of plots to draw from list of observables
    plotting_info = {}
    for each in observables:
        for i in range(len(each.name)):
            plotting_info[each.name[i]] = {'type': each.plot_type[i], 'opts': each.plot_opts[i]}
    def plot_observables(index):
        if not index:
            plots_list = []
            for name in plotting_info:
                hv_type = getattr(hv, plotting_info[name]['type'])
                empty_plot = hv_type(np.random.rand(0, 2)).opts(framewise=True)
                plots_list.append([empty_plot.relabel(f'{name} - No Selection').opts(plotting_info[name]['opts'])])
        else:
            new_index = [x for x in index if x not in list(plots.keys())]
            for element in new_index:
                new_plots = []
                for each in observables:
                    new_plots.extend(each.generate_plot(element))
                plots[element] = {plot.label: plot for plot in new_plots}
            
            plots_list = []
            for index_item in index:
                plot_types = list(plots[index_item].keys())

            for plot_item in plot_types:
                same_type = [plots[key][plot_item] for key in index]
                plots_list.append(same_type)
            
        layout = hv.Layout()
        for list_of_plots in plots_list:
            overlay = hv.Overlay(list_of_plots).opts(show_legend=False)
            layout = layout + overlay
        layout.opts(shared_axes=False)
        return layout
    
    
    # put it all together using Panel
    dashboard = pn.Column(pn.Row(var1, var2, cmap_var, cmap_option), pn.Row(points_dmap, selected_table))
    
    if show_observables == True:
        observables_dmap = hv.DynamicMap(plot_observables, streams=[selection]).opts(framewise=True)
        observables_pane = pn.panel(observables_dmap)
        dashboard = pn.Column(dashboard, observables_pane)
    
    return dashboard


# Set up the parameters of the problem.
ndim, nsamples = 3, 1000

# Generate some fake data.
np.random.seed(42)
data1 = np.random.randn(ndim * 4 * nsamples // 5).reshape(
    [4 * nsamples // 5, ndim]
)
data2 = 4 * np.random.rand(ndim)[None, :] + np.random.randn(
    ndim * nsamples // 5
).reshape([nsamples // 5, ndim])
data = np.vstack([data1, data2])

param_names = ['frequency', 'phase', 'amplitude']
latex = ['\omega / 2\pi', '\phi', '\mathrm{amplitude}']
df = pd.DataFrame(data, columns=param_names)
latex_dict = dict(zip(param_names, latex))

def compute_waveforms(index, input_data):
    selection = input_data.iloc[[index]]
    x = np.linspace(-4*np.pi, 4*np.pi, 1000)
    angular_freq = 2*np.pi*selection['frequency'].iloc[0]
    phase = selection['phase'].iloc[0]
    amp = selection['amplitude'].iloc[0]
    sin = amp * np.sin(angular_freq*x + phase)
    cos = amp * np.cos(angular_freq*x + phase)
    sinc = amp * np.sinc(angular_freq*x/np.pi + phase)
    sawtooth = amp * signal.sawtooth(angular_freq * x + phase)
    waves = [
        {'x': x, 'sin(x)': sin},
        {'x': x, 'sinc(x)': sinc},
        {'x': x, 'sawtooth': sawtooth},
    ]
    return waves


opts1 = opts.Curve(xlim=(-4*np.pi, 4*np.pi), height=400, width=500, fontscale=1.1, color=hv.Cycle('YlOrRd'), bgcolor='#151515', framewise=True)
opts2 = opts.Curve(xlim=(-4*np.pi, 4*np.pi), height=400, width=500, fontscale=1.1, color=hv.Cycle('PuBuGn'), bgcolor='#151515', framewise=True)
opts3 = opts.Curve(xlim=(-4*np.pi, 4*np.pi), height=400, width=500, fontscale=1.1, color=hv.Cycle('RdPu'), bgcolor='#f5f5f5', framewise=True)
waves_latex = {
    'x': 'x', 
    'sin(x)': '\sin{x}',
    'sinc(x)': '1/\sin{x}',
    'sawtooth': '\mathrm{Sawtooth~Wave}',
}

waveforms = Observable(
    name=[
        'Sine',
        'Sinc',
        'Sawtooth'
    ],
    myfunc=compute_waveforms,
    myfunc_args=(df,),
    grouped=True,
    plot_type=[
        'Curve',
        'Curve',
        'Curve',
    ],
    plot_opts=[
        opts1,
        opts2,
        opts3,
    ],
    latex_labels=waves_latex
)

viz(df, [waveforms], latex_dict=latex_dict).servable()