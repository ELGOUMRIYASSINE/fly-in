def parser(input_file):
    config_space = {}
    with open(input_file, "r") as file:
        for line in file:
            if ":" not in line or line.startswith("#"):
                continue
            line = line.strip()
            # print(line)
            key, value = line.split(":")
            key = key.strip()
            if "hub" in key:
                hub_cordinates = {}
                tmp = value.strip().split(" ")
                # print(tmp)
                hub_cordinates["hub_name"] = tmp[0]
                hub_cordinates["hub_cordinates"] = [tmp[1], tmp[2]]
                if len(tmp) == 5:
                    hub_cordinates["zone_state"] = {}
                    zone_key , zone_state = tmp[3].split("=")[0], tmp[3].split("=")[1]
                    color_key, color_value = tmp[4].split("=")[0], tmp[4].split("=")[1]
                    hub_cordinates["zone_state"][zone_key] = zone_state
                    hub_cordinates["zone_state"][color_key] = color_value

                else:
                    hub_cordinates["zone"] = {"color": tmp[3]}
                # print(tmp)
                value = hub_cordinates
            if not isinstance(value, dict):
                value = value.strip()
            config_space[key] = value
    print(config_space)



parser("01_linear_path.txt")
