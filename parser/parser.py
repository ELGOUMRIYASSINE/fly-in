# def check_structur(line, valid_lines):
#     if not ":" in line:
#         print(line)
#         raise ValueError("Line must be key and value separated with ':' ")
#     if valid_lines == 1:
#         if not "nb_drones" in line:
#             raise ValueError("The first Line must be nb_drones")
#     key, value = line.split(":")
#     value = value.strip()
#     value = value.split(" ")
#     if key == "hub":
#         if valid_lines != 1 and not  4 <= len(value) <= 6:
#             print(value)
#             raise ValueError("Error: there is more then 3 zone state!")
# def hub_checker():

    
    


def parser(input_file):
    line_number = 0
    valid_lines = 0
    config_space = {}
    config_space["hubs"] = []
    config_space["connections"] = []
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
            # try:
            #     # check_structur(line, valid_lines)
            # except Exception as e:
            #     print(f"Error: {e} in line {line_number}")
            #     exit()
            line = line.strip()
            key, value = line.split(":", 1)
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
        




parser("03_ultimate_challenge.txt")


# 
# {'nb_drones': '5', 'start_hub': 
#  {'hub_name': 'hub','hub_cordinates': ['0', '0'], 'zone': {'color': '[color=green]'}},
#    'end_hub': {'hub_name': 'goal', 'hub_cordinates': ['10', '10'], 'zone': {'color': '[color=yellow]'}},
#      'hub': {'hub_name': 'obstacleX', 'hub_cordinates': ['5', '5'], 'zone_state': {'[zone': 'blocked', 'color': 'gray]'}},
#        'connection': 'tunnelB-goal'}