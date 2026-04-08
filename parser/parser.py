def parser(input_file):
    config_space = {}
    config_space["hubs"] = []
    config_space["connections"] = []
    with open(input_file, "r") as file:
        for line in file:
            # overwrite comments and lines that does not have :
            if ":" not in line or line.startswith("#"):
                continue
            # split the line for two key and value from :
            line = line.strip()
            key, value = line.split(":")
            key = key.strip()
            hub_cordinates = {}
            # get the hub data and set the zone informations in dict
            if "hub" in key:
                tmp = value.strip().split(" ")
                hub_cordinates["name"] = tmp[0]
                hub_cordinates["cordinates"] = [tmp[1], tmp[2]]
                hub_cordinates["zone"] = {
                    "type": None,
                    "color": None,
                    "max_drones": None
                }
                for data in tmp[3:]:
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
    # print(config_space)
        




parser("03_ultimate_challenge.txt")


# 
# {'nb_drones': '5', 'start_hub': 
#  {'hub_name': 'hub','hub_cordinates': ['0', '0'], 'zone': {'color': '[color=green]'}},
#    'end_hub': {'hub_name': 'goal', 'hub_cordinates': ['10', '10'], 'zone': {'color': '[color=yellow]'}},
#      'hub': {'hub_name': 'obstacleX', 'hub_cordinates': ['5', '5'], 'zone_state': {'[zone': 'blocked', 'color': 'gray]'}},
#        'connection': 'tunnelB-goal'}