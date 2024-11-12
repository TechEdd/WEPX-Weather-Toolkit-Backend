import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature


extent = [-125,-66, 24, 50]

# Create a figure with a specific size and equirectangular projection
fig, ax = plt.subplots(figsize=(12, 8), 
                       subplot_kw={'projection': ccrs.PlateCarree()})



# Add full-resolution coastlines
ax.coastlines(resolution='10m')

# Add county boundaries at full resolution
counties = cfeature.NaturalEarthFeature(
    category='cultural',
    name='admin_2_counties',
    scale='10m',  # Full resolution
    facecolor='none')


# country boundaries
country_bodr = cfeature.NaturalEarthFeature(category='cultural', 
    name='admin_0_boundary_lines_land', scale='10m', facecolor='none')

# province boundaries
provinc_bodr = cfeature.NaturalEarthFeature(category='cultural', 
    name='admin_1_states_provinces_lines', scale='10m', facecolor='none')


ax.add_feature(counties, edgecolor='gray', linewidth=0.1)
ax.add_feature(country_bodr, linewidth=0.6, edgecolor="k")  #USA/Canada
ax.add_feature(provinc_bodr, linewidth=0.6, edgecolor="k")
ax.add_feature(cfeature.BORDERS, linewidth=0.3)


# Optionally, add land and ocean features for better visualization
#ax.add_feature(cfeature.LAND, edgecolor='none', facecolor='lightgray', alpha=0.8)
#ax.add_feature(cfeature.OCEAN, edgecolor='none', facecolor='lightblue', alpha=0.8)

# Remove borders, ticks, and axis labels to get a borderless map
ax.set_frame_on(False)
ax.get_xaxis().set_visible(False)
ax.get_yaxis().set_visible(False)

# Adjust the figure layout to remove margins and whitespace
plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

# Set the map extent to the desired bounding box
ax.set_extent(extent, crs=ccrs.PlateCarree())

# Save the figure as an SVG without any borders
plt.savefig("map_with_counties_fullscreen.svg", format='svg', bbox_inches='tight', pad_inches=0, transparent=True)

# Show the plot (optional)
plt.show()
