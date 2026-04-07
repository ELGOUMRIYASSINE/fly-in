def parser(input_file):
    config_space = {}
    config_space["hubs"] = []
    config_space["connections"] = []
    with open(input_file, "r") as file:
        for line in file:
            if ":" not in line or line.startswith("#"):
                continue
            line = line.strip()
            key, value = line.split(":")
            key = key.strip()
            hub_cordinates = {}
            connection_data = {}
            if "hub" in key:
                tmp = value.strip().split(" ")
                hub_cordinates["name"] = tmp[0]
                hub_cordinates["cordinates"] = [tmp[1], tmp[2]]
                if len(tmp) > 2:
                    hub_cordinates["zone"] = {}
                    for data in tmp[3:]:
                        sub_key, sub_value = data.split("=", 1)
                        sub_key = sub_key.replace("[", "")
                        sub_value = sub_value.replace("]", "")
                        hub_cordinates["zone"][sub_key] = sub_value
                else:
                    hub_cordinates["zone"] = {"color": tmp[3].split("=", 1)[0][1:len(tmp[3]) - 1]}
                value = hub_cordinates
            elif key == "connections":
                tmp_key, tmp_value = value.split("-", 1)
                connection_data[tmp_key] = {"from":tmp_key, "to":tmp_value}
                value = connection_data
            if isinstance(value, dict):
                if key == "hub":
                    config_space["hubs"].append(value)
                if key == "connections":
                    config_space["connections"].append(value)
            else:
                
    print(config_space)



parser("03_ultimate_challenge.txt")


# 
# {'nb_drones': '5', 'start_hub': 
#  {'hub_name': 'hub','hub_cordinates': ['0', '0'], 'zone': {'color': '[color=green]'}},
#    'end_hub': {'hub_name': 'goal', 'hub_cordinates': ['10', '10'], 'zone': {'color': '[color=yellow]'}},
#      'hub': {'hub_name': 'obstacleX', 'hub_cordinates': ['5', '5'], 'zone_state': {'[zone': 'blocked', 'color': 'gray]'}},
#        'connection': 'tunnelB-goal'}