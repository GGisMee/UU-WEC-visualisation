def gen_float(i, m=0):
    # i = ditt heltal
    # m = metod-id (0 för färg, 1 för storlek, 2 för hastighet osv)
    return (hash((i, m)) % 10**10) / 10**10

# Samma i, olika metoder (m)
print("Färg för id 5:   ", gen_float(5, m=0)) # Ex: 0.7412...
print("Storlek för id 5:", gen_float(5, m=1)) # Ex: 0.1294...

# Samma i och m ger alltid samma svar
print("Färg för id 5 igen:", gen_float(5, m=0)) # Ex: 0.7412...