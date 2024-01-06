**Temperature Plotting**

The National Weather Service archives weather observations at numerous locations around the United States every day.  The data is accessible using the Python Requests libary and and API key.
In this example, maximum temperature data is retrieved for specific dates for the state of Maine, and plotted on a map.

API queries are made to determine the weather stations that are active on the date range of interest.  Then, the maximum temperature is requested for those dates.  The station latitude/longitude and temperature reading are fed to a Radial Basis Function Interpolator in the SciPy library.  This allows interpolation from an unstructured dataset (arbitrary locations) to a grid for the final plot.  The state outline is obtained by reading a Shape file.  The grid temperature data and the state of Maine outlines are overlaid using Matplotlib, so that data is only plotted over land, and not over the ocean.

![Temperatuer Plot](temps_small.png)
