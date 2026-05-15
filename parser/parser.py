import re


class ParsingError(Exception):
    pass


def validate_meta_value(meta_key, meta_value, type):
    zone_values = ["restricted", "normal", "blocked", "priority"]
    meta_key = meta_key.strip()
    if meta_key == "color" and type == "hub":
        if not re.match(r'^[a-zA-Z]+$', meta_value):
            raise ParsingError(f"Invalid color value '{meta_value}'. Color must be a string of letters.")
    elif meta_key == "max_drones" and type == "hub":
        if not re.match(r'^\d+$', meta_value) or int(meta_value) <= 0:
            raise ParsingError(f"Invalid max_drones value '{meta_value}'. max_drones must be a positive integer.")
    elif meta_key == "zone" and type == "hub":
        if meta_value not in zone_values:
            raise ParsingError(f"Invalid zone value '{meta_value}'. Zone must be one of: {', '.join(zone_values)}")
    elif meta_key == "max_link_capacity" and type == "connection":
        if not re.match(r'^\d+$', meta_value) or int(meta_value) <= 0:
            raise ParsingError(f"Invalid max_link_capacity value '{meta_value}'. max_link_capacity must be a positive integer.")
    else:
        raise ParsingError(f"Unknown metadata key '{meta_key}' for '{type}'.")


def validate_connection(value, use_default):
    # strip metadata to get just the hub part
    if use_default:
        hub_part = value.strip()
    else:
        hub_part = value.strip().split("[", 1)[0].strip()

    if "-" not in hub_part:
        raise ParsingError("Connection definition must contain a '-' character to separate 'from' and 'to' hubs")
    if hub_part.count("-") > 1:
        raise ParsingError("Connection definition must contain only one '-' character to separate 'from' and 'to' hubs")

    from_hub, to_hub = hub_part.split("-", 1)
    if not from_hub.strip() or not to_hub.strip():
        raise ParsingError("Connection definition must specify both hubs ==> [hub_1-hub_2]")


def validate_order(line):
    use_default = False
    keys = ["hub", "start_hub", "end_hub", "connection", "nb_drones"]

    if ":" not in line:
        raise ParsingError("Line must contain a key and a value separated by ':'")
    if line.count(":") > 1:
        raise ParsingError("Line must contain only one ':' character to separate key and value")

    key, value = line.split(":", 1)

    if value.count("[") == 0 and value.count("]") == 0:
        use_default = True
    if ("[" not in value and "]" in value) or ("[" in value and "]" not in value):
        raise ParsingError(f"{key.capitalize()} definition (metadata) must contain metadata enclosed in square brackets []")
    if value.count("[") > 1 or value.count("]") > 1:
        raise ParsingError(f"{key.capitalize()} definition (metadata) must contain only one pair of square brackets []")
    if value.count("[") == 1 and value.count("]") == 1 and value.index("[") > value.index("]"):
        raise ParsingError(f"{key.capitalize()} definition (metadata) must have the format: name x y [key=value ...]")
    if "[" in value:
        bracket_pos = value.index("[")
        if bracket_pos > 0 and value[bracket_pos - 1] != " ":
            raise ParsingError(
                f"Missing space before '[' in metadata. "
                f"Got '{value.strip()}'. Expected a space before '[metadata]'."
            )

    key = key.strip()
    if key not in keys:
        raise ParsingError(f"Invalid key '{key}'. Expected one of: {', '.join(keys)}")

    # validate fields and metadata per key type
    if key in ["hub", "start_hub", "end_hub"]:
        if not use_default:
            fields, meta = value.strip().split("[", 1)
        else:
            fields = value.strip()
        parts = fields.strip().split()
        if len(parts) != 3:
            raise ParsingError("Hub definition must have exactly three fields: name, x, y before the metadata")
        _, raw_x, raw_y = parts
        try:
            int(raw_x)
            int(raw_y)
        except ValueError:
            raise ParsingError("x and y must be integer values")
        if not use_default:
            meta = meta.replace("]", "", 1).strip()
            if meta:
                for item in meta.split():
                    if "=" not in item:
                        raise ParsingError(f"Invalid metadata format '{item}'. Expected key=value pairs.")
                    meta_key, meta_value = item.split("=", 1)
                    validate_meta_value(meta_key, meta_value, "hub")

    elif key == "connection":
        validate_connection(value, use_default)
        if not use_default:
            _, meta = value.strip().split("[", 1)
            meta = meta.replace("]", "", 1).strip()
            if meta:
                for item in meta.split():
                    if "=" not in item:
                        raise ParsingError(f"Invalid metadata format '{item}'. Expected key=value pairs.")
                    meta_key, meta_value = item.split("=", 1)
                    validate_meta_value(meta_key, meta_value, "connection")

    elif key == "nb_drones":
        v = value.strip()
        if not re.match(r'^\d+$', v) or int(v) <= 0:
            raise ParsingError(f"nb_drones must be a positive integer, got '{v}'.")

    return use_default


def parser(input_file):
    line_number = 0
    config_space = {}
    config_space["hubs"] = []
    config_space["connections"] = []
    no_repeat_keys = {
        "nb_drones": 0,
        "start_hub": 0,
        "end_hub": 0
    }
    seen_connections = set()
    known_hub_names = set() 

    with open(f"maps/{input_file}", "r") as file:
        for line in file:
            line_number += 1
            line = line.strip()

            if line.startswith("#") or not line:
                continue
            # strip inline comments
            if "#" in line:
                line = line.split("#", 1)[0].strip()
            try:
                use_default = validate_order(line)
            except ParsingError as e:
                print(f"Parsing Error: {e} in line {line_number}")
                exit(1)
            key, value = line.split(":", 1)
            key = key.strip()

            # keys that must not repeat
            no_repeat_keys[key] = no_repeat_keys.get(key, 0) + 1
            if no_repeat_keys.get(key, 0) > 1 and key in ["nb_drones", "start_hub", "end_hub"]:
                print(f"Parsing Error: Duplicate key '{key}' found. '{key}' must be defined only once. in line {line_number}")
                exit(1)

            
            if "hub" in key:
                if not use_default:
                    fields, meta_raw = value.strip().split("[", 1)
                    meta_raw = meta_raw.replace("]", "", 1).strip()
                else:
                    fields = value.strip()
                    meta_raw = ""

                tmp = fields.strip().split()
                hub_name = tmp[0]

                # hub names must not contain dashes
                if "-" in hub_name:
                    print(f"Parsing Error: Hub name '{hub_name}' must not contain dashes. in line {line_number}")
                    exit(1)

                # duplicate hub name check
                if hub_name in known_hub_names:
                    print(f"Parsing Error: Duplicate hub name '{hub_name}'. in line {line_number}")
                    exit(1)
                known_hub_names.add(hub_name)

                hub_data = {
                    "name": hub_name,
                    "type": key, 
                    "coordinates": [int(tmp[1]), int(tmp[2])],
                    "zone": {
                        "type": "normal",    
                        "color": None,        
                        "max_drones": 1       
                    }
                }

                # apply metadata key=value pairs
                if meta_raw:
                    for item in meta_raw.split():
                        sub_key, sub_value = item.split("=", 1)
                        sub_key = sub_key.strip()
                        sub_value = sub_value.strip()
                        if sub_key == "zone":
                            hub_data["zone"]["type"] = sub_value
                        elif sub_key == "color":
                            hub_data["zone"]["color"] = sub_value
                        elif sub_key == "max_drones":
                            hub_data["zone"]["max_drones"] = int(sub_value)

                config_space["hubs"].append(hub_data)

                # keep a direct name reference to start/end for easy access later
                if key == "start_hub":
                    config_space["start_hub"] = hub_name
                elif key == "end_hub":
                    config_space["end_hub"] = hub_name

            # connection
            elif key == "connection":
                if not use_default:
                    hub_part, meta_raw = value.strip().split("[", 1)
                    meta_raw = meta_raw.replace("]", "", 1).strip()
                else:
                    hub_part = value.strip()
                    meta_raw = ""

                from_hub, to_hub = hub_part.strip().split("-", 1)
                from_hub = from_hub.strip()
                to_hub   = to_hub.strip()

                # both hubs must already be defined
                if from_hub not in known_hub_names:
                    print(f"Parsing Error: Connection references undefined hub '{from_hub}'. in line {line_number}")
                    exit(1)
                if to_hub not in known_hub_names:
                    print(f"Parsing Error: Connection references undefined hub '{to_hub}'. in line {line_number}")
                    exit(1)

                # duplicate connection check (a-b == b-a)
                conn_key = (min(from_hub, to_hub), max(from_hub, to_hub))
                if conn_key in seen_connections:
                    print(f"Parsing Error: Duplicate connection '{from_hub}-{to_hub}'. in line {line_number}")
                    exit(1)
                seen_connections.add(conn_key)

                connection_data = {
                    "from": from_hub,
                    "to": to_hub,
                    "max_link_capacity": 1    # default
                }

                if meta_raw:
                    for item in meta_raw.split():
                        sub_key, sub_value = item.split("=", 1)
                        if sub_key.strip() == "max_link_capacity":
                            connection_data["max_link_capacity"] = int(sub_value.strip())

                config_space["connections"].append(connection_data)

            else:
                config_space[key] = value.strip()

    if "nb_drones" not in config_space:
        print("Parsing Error: Missing required 'nb_drones' definition.")
        exit(1)
    if "start_hub" not in config_space:
        print("Parsing Error: Missing required 'start_hub' definition.")
        exit(1)
    if "end_hub" not in config_space:
        print("Parsing Error: Missing required 'end_hub' definition.")
        exit(1)
    return config_space