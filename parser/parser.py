def parser(input_file):
    config_space = {}
    config_space["hubs"] = []
    with open(input_file, "r") as file:
        connections_count = 1
        hub_counter = 1
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
                hub_cordinates["name"] = tmp[0]
                hub_cordinates["cordinates"] = [tmp[1], tmp[2]]
                if len(tmp) > 2:
                    hub_cordinates["zone"] = {}
                    for data in tmp[3:]:
                        sub_key, sub_value = data.split("=")
                        sub_key = sub_key.replace("[", "")
                        sub_value = sub_value.replace("]", "")
                        hub_cordinates["zone"][sub_key] = sub_value
                else:
                    hub_cordinates["zone"] = {"color": tmp[3].split("=")[0][1:len(tmp[3]) - 1]}
            if isinstance(value, dict):
                if key in "hub":
                    config_space["hubs"].append(value)
                if key in "connections":
                    config_space["connections"].append(value)
            else:
                config_space[key] = value
            # print(config_space)
                
    print(config_space)



parser("03_ultimate_challenge.txt")


# 
# {'nb_drones': '5', 'start_hub': 
#  {'hub_name': 'hub','hub_cordinates': ['0', '0'], 'zone': {'color': '[color=green]'}},
#    'end_hub': {'hub_name': 'goal', 'hub_cordinates': ['10', '10'], 'zone': {'color': '[color=yellow]'}},
#      'hub': {'hub_name': 'obstacleX', 'hub_cordinates': ['5', '5'], 'zone_state': {'[zone': 'blocked', 'color': 'gray]'}},
#        'connection': 'tunnelB-goal'}