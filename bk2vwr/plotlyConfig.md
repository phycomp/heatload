When working with Plotly, the term "config" refers to a dictionary of configuration options that control various aspects of a Plotly figure's behavior and appearance. This config dictionary is typically passed as an argument when displaying or rendering a Plotly figure, allowing for customization of elements like the modebar, interactivity features, and more.
Why use config?
Older methods of configuring Plotly figures might have involved setting individual properties directly or using deprecated arguments. The config parameter provides a centralized and organized way to manage all these options within a single dictionary, making your code cleaner and more maintainable.
How to use config:
Create a config dictionary: Define a Python dictionary where keys are Plotly configuration options (e.g., 'scrollZoom', 'displayModeBar', 'modeBarButtonsToRemove') and values are their desired settings (e.g., True, False, a list of button names).
Pass config to the display function: When you display your Plotly figure (e.g., using fig.show() in Python, or Plotly.newPlot() in JavaScript), you pass this config dictionary as an argument.
Example (Python):
Python

import plotly.graph_objects as go

# Create a sample figure
fig = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[4, 1, 2])])

# Define the configuration options
my_config = {
    'scrollZoom': True,  # Enable scroll zooming
    'displayModeBar': False,  # Hide the modebar
    'displaylogo': False, # Hide the Plotly logo
    'modeBarButtonsToRemove': ['lasso2d', 'select2d'] # Remove specific buttons
}

# Display the figure with the custom configuration
fig.show(config=my_config)
Common config options:
scrollZoom: Enables or disables zooming with the mouse scroll wheel.
displayModeBar: Controls the visibility of the Plotly modebar.
modeBarButtonsToRemove: A list of modebar buttons to hide.
displaylogo: Hides the Plotly logo.
responsive: Makes the figure responsive to container size changes.
