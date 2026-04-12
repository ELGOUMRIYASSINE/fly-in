import re

class ParsingError(Exception):
    pass


def validate_meta_value(meta_key, meta_value):
    zone_values = ["restricted", "unrestricted", "normal", "blocked", "priority"]
    meta_key = meta_key.strip()
    if meta_key == "color":
        if not re.match(r'^[a-zA-Z]+$', meta_value):
            raise ParsingError(f"Invalid color value '{meta_value}'. Color must be a string of letters.")
    elif meta_key == "max_drones":
        if not re.match(r'^\d+$', meta_value):
            raise ParsingError(f"Invalid max_drones value '{meta_value}'. max_drones must be an integer.")
    elif meta_key == "zone":
        if meta_value not in zone_values:
            raise ParsingError(f"Invalid zone value '{meta_value}'. Zone must be one of: {', '.join(zone_values)}")


def validate_order(line):
    use_default = False
    keys = ["hub", "start_hub", "end_hub", "connection", "nb_drones"]
    if ":" not in line:
        raise ParsingError("Line must contain a key and a value separated by ':'")
    if line.count(":") > 1:
        raise ParsingError("Line must contain only one ':' character to separate key and value")
    key, value = line.split(":", 1)
    if "[" in value:
        bracket_pos = value.index("[")
        if bracket_pos > 0 and value[bracket_pos - 1] != " ":
            raise ParsingError(
                f"Missing space before '[' in metadata. "
                f"Got '{value.strip()}'. Expected a space before '[metadata]'."
            )
    if value.count("[") == 1 and value.count("]") == 1 and value.index("[") > value.index("]"):
        raise ParsingError("Hub definition (metadata) must have the format: name x y [key=value ...]")
    key = key.strip()
    if key not in keys:
        raise ParsingError(f"Invalid key '{key}'. Expected one of: {', '.join(keys)}")

    # validate fields and meta data
    if key in ["hub", "start_hub", "end_hub"]:
        if ("[" not in value and "]" in value) or ("[" in value and "]" not in value):
            raise ParsingError("Hub definition (metadata) must contain metadata enclosed in square brackets []")
        elif value.count("[") > 1 or value.count("]") > 1:
            raise ParsingError("Hub definition (metadata) must contain only one pair of square brackets []")
        elif value.count("[") == 0 and value.count("]") == 0:
            use_default = True
            fields = value.strip()
        else:
            fields, meta = value.strip().split("[", 1)
        count = len(fields.strip().split(" "))
        if count != 3:
            raise ParsingError("Hub definition must have exactly three fields: name, x, y before the metadata")
        x, y = fields.strip().split(" ")[1:]
        try:
            int(x)
            int(y)
        except ValueError:
            raise ParsingError("x and y must be integer values")
        if not use_default:
            meta = meta.replace("]", "", 1).strip()
            if not meta:
                use_default = True
            else:
                for item in meta.split(" "):
                    if "=" not in item:
                        raise ParsingError(f"Invalid metadata format '{item}'. Expected key=value pairs.")
                    meta_key, meta_value = item.split("=", 1)
                    validate_meta_value(meta_key, meta_value)
        else:
            meta = None
    return use_default
            

def parser(input_file):
    line_number = 0
    valid_lines = 0
    config_space = {}
    config_space["hubs"] = []
    config_space["connections"] = []
    no_repeat_keys = {
        "nb_drones": 0,
        "start_hub": 0,
        "end_hub": 0
    } 
    default_meta = {
        "color": "white",
        "type": "normal",
        "max_drones": 0
    }
    with open(input_file, "r") as file:
        for line in file:
            line_number += 1
            line = line.strip()
            if line.startswith("#"):
                continue
            if not line:
                continue
            # split the line for two key and value from 
            valid_lines += 1
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            else:
                line = line.strip()
            try:
                meta_state = validate_order(line)
            except ParsingError as e:
                print(f"Parsing Error: {e} in line {line_number}")
                exit()
            key, value = line.split(":", 1)
            key = key.strip()
            no_repeat_keys[key] = no_repeat_keys.get(key, 0) + 1
            if no_repeat_keys[key] > 1 and key in ["nb_drones", "start_hub", "end_hub"]:
                raise ParsingError(f"Duplicate key '{key}' found. The key '{key}' must be defined only once.")
            hub_cordinates = {}
            # get the hub data and set the zone informations in dict
            if "hub" in key:
                if no_repeat_keys["start_hub"] > 1 or no_repeat_keys["end_hub"] > 1:
                    raise ParsingError("There must be only one start_hub and one end_hub")
                tmp = value.strip().split(" ")
                hub_cordinates["name"] = tmp[0]
                hub_cordinates["cordinates"] = [tmp[1], tmp[2]]
                hub_cordinates["zone"] = {
                    "type": None,
                    "color": None,
                    "max_drones": None
                }
                if not meta_state:
                    for data in tmp[3:]:
                        if data.replace("[]", "").strip() == "":
                            continue
                        sub_key, sub_value = data.split("=", 1)
                        sub_key = sub_key.replace("[", "")
                        sub_value = sub_value.replace("]", "")
                        if sub_key == "zone":
                            hub_cordinates["zone"]["type"] = sub_value
                        else:   
                            hub_cordinates["zone"][sub_key] = sub_value
                value = hub_cordinates
            # get the connectio data into and dict with from , to keys
            elif key == "connection":
                tmp_key, tmp_value = value.split("-", 1)
                connection_data = {"from":tmp_key.strip(), "to":tmp_value.strip()}
                value = connection_data
            if isinstance(value, dict):
                if key == "hub":
                    config_space["hubs"].append(value)
                if key == "connection":
                    config_space["connections"].append(value)
            else:
                config_space[key] = value

    for key, line in config_space.items():
        if key == "hubs":
            for dic in line:
                print(dic)
        elif key == "connections":
            for con in line:
                print(con)
        else:
            print(key, line)
        print()
        



try:
    parser("03_ultimate_challenge.txt")
except ParsingError as e:
    print(f"Parsing Error: {e}")