# GeojsonToUMap
This small python library allows to manipulate Geojson files in order to import them into an uMap (https://umap.openstreetmap.fr). It contains 2 features:
 - Merging one or more Geojson files into one, using the capabilities of *MultiLineString*.
 - Converting several Geojson files into an uMap file, directly defining the style of individual layers and features, rather than doing it manually in Umap.

The original Geojson files may for example have been created by importing data from OpenStreetMap (via https://overpass-turbo.eu) or in JOSM.

Here is an example of what using this software can produce:
<img alt="Example of resulting uMap layers" src="https://github.com/lus0rius/GeojsonToUMap/blob/main/Examples/Comparison.png?raw=true" width="500">

## Convert or merge Geojson files to MultiLineStrings
It is possible ton convert a single Geojson file to new file containing a single MultiLineString using the function merge_geojson(). Here are its arguments:
 - **in_file**: *string of text*. Path of the input Geojson file, absolute or relative to the location of the python file.
 - **out_file**: *string of text*. Path of the output Geojson file containing the MultiLineString.
 - Optional arguments:
	 - **overwrite**: *boolean* (default False). If set to False, if the out_file already exists, the function will append the new MultiLineString to the existing file (useful to merge multiple files together). If True, it will overwrite the file.
	 - **is_umap_layer**: *boolean* (default False). If True, the function will search for a .json file with the same name of the Geojson input file containing settings useful if the output feature / layer is going to be exported into a uMap file. WARNING: if this argument is set to True, the resulting Geojson file will not be readable by applications such as JOSM.
	 - **indent**: *integer number* (default 0). If the value is superior to 0 (we recommend 2 or 4), the output file will be readable by humans. If the value is equal to 0 or less, the output file will be concatenated in one single line, saving a lot of disk space.
	 - **rounding**: *integer number* (default 6). If the value is superior to 0, all the coordinates of LineString geometries (only LineString) will be rounded to the value of this argument after the decimal point.
	 - **keys_order_file**: *string of text* Path of a file containing all possible property keys in order. This makes the order of the keys uniform if you use the "Table" layout when clicking on a layer in uMap.

By calling this function multiple times, it is possible to merge multiple Geojson files in one single file containing multiple MultiLineStrings. If you want to merge an entire directory, you can use the directory_to_geojson() function.

## Convert Geojson to uMap
The convert_to_umap() function allows you to export a list of Geojson files into a uMap file, containing all the data of a uMap and importable on this site. Its arguments are all mandatory:
 - **layer_files**: *list of strings of text*. List containing all the files that you want to appear as layers in uMap.
 - **map_settings_file**: *string of text*. Path of the .umap file containing all the map settings. To obtain this file, you must have created the uMap (preferably empty) to which we will add the layers. Then, edit the file with a Notepad application and keep only the first 54 lines with map settings and map geometry (closing the file with a curly bracket at the end). It supports some keywords that you can write in the settings file:
	 - <span>$TODAY$</span> is replaced by the current date in English.
	 - <span>$TODAY!fr$</span> is replaced by the current date in French. It works for any language code.
	 - <span>$YEAR\\$</span> is replaced by the current year (ex. 2022).
 - **out_file**: *string of text*. Path of the output uMap file, absolute or relative to the location of the python file.
 
## Troubleshooting
As this library was mainly created for my own use, it is not free of bugs. Please feel free to report them. Common error messages:
 - **FileNotFoundError**: The file input does not exist.
 - **SyntaxError: (unicode error) 'unicodeescape'**: Make sure you use / and not \ in file paths.
 - **JSONDecodeError**: The Geojson file input does not conform to the Json syntax.
