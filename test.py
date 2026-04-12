import re

# # test = "azzzl"

# # check = re.match(r'^[a-zA-Z]+$', test)
# # check_two = re.search(r'[a-c]$', test)

# print(bool(re.match("^[\d+]$", "12")))
# print(bool(re.match(r"\d+", "123")))

print(bool(re.match(r"abc", "abc")))

print(r"yassine \d hello world")

test = {
    "color": "red",
    "type": "no_fly_zone",
    "max_drones": 5
}

if "color" in test:
    print("true yassine")