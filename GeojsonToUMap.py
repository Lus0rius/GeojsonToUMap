import json
import os
import re
from datetime import date, datetime
from babel.dates import format_date
from collections import OrderedDict


def rep_ext(in_path: str, new_ext: str):
    return os.path.join(os.path.dirname(in_path), os.path.splitext(in_path)[0] + new_ext)


def replace_keyword_today(input_string: str):
    keyword_matches = re.findall(r"\$TODAY!?\w*\$", input_string)
    today = date.today()
    for keyword in keyword_matches:
        if "!" in keyword:
            localized_date = format_date(today, locale=keyword.split("!")[-1][:-1])
        else:
            localized_date = format_date(today, locale="en")
        input_string = input_string.replace(keyword, localized_date)
    return input_string


def replace_keyword_year(input_string: str):
    keyword_matches = re.findall(r"\$YEAR\$", input_string)
    year = datetime.now().year
    for keyword in keyword_matches:
        input_string = input_string.replace(keyword, str(year))
    return input_string


def convert_to_umap(layer_files: list[str], map_settings_file: str, out_file: str):
    """
    Converts multiple geojson files into an uMap file. Each input file is treated as a layer.

    :param layer_files: List containing all the files that will appear as layers in uMap.
    :param map_settings_file: Path of the .umap file containing all the map settings.
    :param out_file: Path of the output uMap file.
    """

    for i, in_file in enumerate(layer_files):
        if in_file[0] == "\"":
            layer_files[i] = in_file[1:]
        if in_file[-1] == "\"":
            layer_files[i] = in_file[:-1]

    tmp_settings_path = os.path.join(os.path.dirname(map_settings_file), "GeojsonToUMap_map_settings.tmp")

    # Replace keywords in the whole map settings file
    with open(map_settings_file, 'r', encoding='utf-8') as settings_string:
        data = settings_string.read()
        data = replace_keyword_today(data)
        data = replace_keyword_year(data)

    with open(tmp_settings_path, 'w', encoding='utf-8') as settings_string_out:
        settings_string_out.write(data)

    # Open map settings file as JSON
    with open(tmp_settings_path, 'r', encoding='utf-8') as settings_file:
        umap = json.load(settings_file)

    os.remove(tmp_settings_path)

    # Add each layer
    layers = []
    for file in reversed(layer_files):
        with open(file, 'r', encoding='utf-8') as layer_file:
            layer = json.load(layer_file)

        # Search for layer settings file and write it to the layer options
        layer_options_file = rep_ext(file, ".json")
        if os.path.exists(layer_options_file):
            with open(layer_options_file, 'r', encoding='utf-8') as options_file:
                layer_options = json.load(options_file)
                layer.update({'_umap_options': layer_options['_umap_options']})

        layers.append(layer)

    umap.update({'layers': layers})

    # Save uMap file
    with open(f"{out_file}", 'w', encoding='utf-8') as savefile:
        json.dump(umap, savefile, ensure_ascii=False, indent=2)

    return out_file


def merge_geojson(in_file: str, out_file: str,
                  overwrite: bool = False, is_umap_layer: bool = False, indent: int = 0, rounding: int = 6,
                  keys_order_file: str = None,):
    """
    Merges all LineStrings of a geojson file into a single MultiLineString and appends it to another Geojson file.

    :param in_file: Path of the input Geojson file.
    :param out_file: Path of the output Geojson file containing the MultiLineString.
    :param overwrite: If False, appends the new MultiLineString to the existing out_file.
    :param is_umap_layer: If True, searches for a .json file of the same name containing uMap features.
    :param indent: If > 0, the output file will be readable by humans.
    :param rounding: If > 0, LineString coordinates are rounded to the value of this parameter after the decimal point.
    :param keys_order_file: Path of a file containing all possible properties in order.
    """

    if in_file[0] == "\"":
        in_file = in_file[1:]
    if in_file[-1] == "\"":
        in_file = in_file[:-1]

    # Read input Geojson
    with open(in_file, 'r', encoding='utf-8') as input_file:
        in_json = json.load(input_file)

    geometries = []
    properties_list = []
    properties = OrderedDict()
    non_line_features = []  # Non-line features are not changed from the original file

    # Read geometry for each feature the in input file
    for feature in in_json['features']:
        if feature['geometry']['type'] != "LineString":
            non_line_features.append(feature)
        else:
            properties_list.append(feature['properties'])
            geometry = feature['geometry']['coordinates']

            if rounding > 0:
                # Round each coordinate to save space
                for i, coord_xy in enumerate(geometry):
                    for j, coord in enumerate(coord_xy):
                        geometry[i][j] = round(coord, rounding)

            geometries.append(feature['geometry']['coordinates'])

    # Keep only the properties of the feature that has the most properties
    for item in properties_list:
        if item is not None and len(item) > len(properties):
            properties = item

    if keys_order_file is not None:
        # Sorts the keys in order of appearance in the keys order file
        with open(keys_order_file, 'r', encoding='utf-8') as order_file:
            ordered_properties = OrderedDict()
            for line in order_file.readlines():
                line_wo_lf = line[:-1]
                if line[:-1] in properties.keys():
                    ordered_properties.update({line_wo_lf: properties[line_wo_lf]})
            for prop in properties:
                if prop not in ordered_properties.keys():
                    ordered_properties.update({prop: properties[prop]})
            properties = ordered_properties

    if is_umap_layer:
        # Search for feature uMap settings file and write it to the properties
        umap_options_file = rep_ext(in_file, ".json")
        if os.path.exists(umap_options_file):
            with open(umap_options_file, 'r', encoding='utf-8') as options_file:
                umap_options = json.load(options_file)
                properties.update({"_umap_options": umap_options["_umap_options"]})

    out_features = [{
        "type": "Feature",
        "properties": properties,
        "geometry": {
            "type": "MultiLineString",
            "coordinates": geometries
        }
    }]
    out_features.extend(non_line_features)

    if not overwrite and os.path.exists(out_file):
        # Reading existing out_file in order to append the processed MultiLineString to it
        with open(out_file, 'r', encoding='utf-8') as openfile:
            imported_json = json.load(openfile)

        imported_features = imported_json['features']
        for imp_feature in imported_features:
            out_features.append(imp_feature)

    out_json = {
        "type": "FeatureCollection",
        "features": out_features
    }

    with open(f"{out_file}", 'w', encoding='utf-8') as savefile:
        if indent < 1:
            json.dump(out_json, savefile, ensure_ascii=False)
        else:
            json.dump(out_json, savefile, ensure_ascii=False, indent=indent)

    return out_file


def directory_to_geojson(directory: str, output_file: str,
                         overwrite: bool = True, is_umap_layer: bool = False, indent: int = 0, rounding: int = 6,
                         keys_order_file: str = None):
    """
    Merges all geojson files in a directory containing multiple LineStrings to a single geojson file containing
    one MultiLineString per input file.

    :param directory: Path of the directory containing all files to merge.
    :param output_file: Path of the output Geojson file containing all MultiLineStrings.
    :param overwrite: If False, appends the new MultiLineString to the existing out_file.
    :param is_umap_layer: If True, searches for a .json file of the same name containing uMap features.
    :param indent: If > 0, the output file will be readable by humans.
    :param rounding: If > 0, LineString coordinates are rounded to the value of this parameter after the decimal point.
    :param keys_order_file: Path of a file containing all possible properties in order.
    """

    if overwrite and os.path.exists(output_file):
        os.remove(output_file)

    filelist = [os.path.join(directory, file) for file in os.listdir(directory)
                if os.path.splitext(file)[1] == ".geojson"]
    c = 0
    tot = len(filelist)

    for file in filelist:
        merge_geojson(file, output_file, False, is_umap_layer, indent, rounding, keys_order_file)
        c += 1
        print(f"{c}/{tot}")
