class ParsingError(Exception):
    pass

# def validate_meta_data(data):
#     default_zone = {
#         "type": None,
#         "color": None,
#         "max_drones": None
#     }
#     for item in data.split(" "):
#         key, value = item.split("=")
#         if key.strip()
    # for item in [item1, item2, item3.strip()]:

def validate_order(line):
    use_default = False
    keys = ["hub", "start_hub", "end_hub", "connection", "nb_drones"]
    meta_keys = ["zone", "color", "max_drones"]
    meta_values = {
        "zone": ["restricted", "unrestricted"],
        "color": ["red", "darkred", "blue", "darkblue", "green", "darkgreen"],
        "max_drones": None
    }
    if ":" not in line:
        raise ParsingError("Line must contain a key and a value separated by ':'")
    if line.count(":") > 1:
        raise ParsingError("Line must contain only one ':' character to separate key and value")
    key, value = line.split(":", 1)
    key = key.strip()
    if key not in keys:
        raise ParsingError(f"Invalid key '{key}'. Expected one of: {', '.join(keys)}")
    # validate fields and meta data
    if key in ["hub", "start_hub", "end_hub"]:
        if len(value.split("]")) > 1 and value.split("]")[1].strip():
            raise ParsingError("After the metadata (enclosed in square brackets []), there should be no additional fields.")
        if ("[" not in value and "]" in value) or ("[" in value and "]" not in value):
            raise ParsingError("Hub definition (metadata) must contain metadata enclosed in square brackets []")
            # fields, meta = value.strip().split("[", 1)
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
        name, x, y = fields.strip().split(" ")
        try:
            int(x)
            int(y)
        except ValueError:
        if "[" not in value and "]" in value or "[" in value and "]" not in value:
            raise ParsingError("Hub definition (metadata) must contain metadata enclosed in square brackets []")
        else:
            if not use_default:
                meta = meta.replace("]", "", 1).strip()
                if not meta:
                    meta = None
                else:
                    for item in meta.split(" "):
                        if "=" not in item:
                            raise ParsingError(f"Invalid metadata format '{item}'. Expected key=value pairs.")
                        meta_key, meta_value = item.split("=", 1)
                        meta_key = meta_key.strip()
                        if meta_key not in meta_keys:
                            raise ParsingError(f"Invalid metadata key '{meta_key}'. Expected one of: {', '.join(meta_keys)}")
            else:
                meta = None
            


# def validate_hub(line, current):
#     line = line.strip()
#     key, value = line.split(":")
#     if current != 1 and key.strip() in ["hub", "start_hub", "end_hub"]:
#         # hub: conv_restricted6 14 0 [zone=restricted color=darkred max_drones=1]
#         meta_data = value.strip().split("[", 1)[1]
#         meta_data = meta_data.strip()[:len(meta_data)-1]
#         # validate_meta_data(meta_data)
#         value = value.strip().split(" ")
#         name , x, y = value[0], value[1], value[2]
#         # print(name, x , y)
#         try:
#             int(x)
#             int(y)
#         except ValueError:
#             raise ParsingError("x, y must be integers values")

    
    


def parser(input_file):
    line_number = 0
    valid_lines = 0
    config_space = {}
    config_space["hubs"] = []
    config_space["connections"] = []
    end_hub_count = 0
    start_hub_count = 0
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
            line = line.strip()
            try:
                validate_order(line)
            except ParsingError as e:
                print(f"Parsing Error: {e} in line {line_number}")
                exit()
            key, value = line.split(":", 1)
            key = key.strip()
            hub_cordinates = {}
            # get the hub data and set the zone informations in dict
            if "hub" in key:
                # try:
                #     validate_hub(line, valid_lines)
                # except ParsingError as e:
                #     print(f"Parsing Error: {e} in line {line_number}")
                #     exit()
                if key == "start_hub":
                    start_hub_count += 1
                if key == "end_hub":
                    end_hub_count += 1
                if start_hub_count > 1 or end_hub_count > 1:
                    raise ParsingError("There must be only one start_hub and one end_hub")
                tmp = value.strip().split(" ")
                hub_cordinates["name"] = tmp[0]
                hub_cordinates["cordinates"] = [tmp[1], tmp[2]]
                hub_cordinates["zone"] = {
                    "type": None,
                    "color": None,
                    "max_drones": None
                }
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
    parser("01_linear_path.txt")
except ParsingError as e:
    print(f"Parsing Error: {e}")