value = "hub1   10   20   [zone data]"

before_bracket = value.split("[", 1)[1]
meta_data = before_bracket.strip().split()

print(meta_data)