from tile_name_generator import suggest_names

# Générer 5 suggestions
print("5 suggestions de noms :")
noms = suggest_names(5)
for i, nom in enumerate(noms, 1):
    print(f"{i}. {nom}")

# Générer 3 autres suggestions
print("\n3 autres suggestions :")
noms = suggest_names(3)
for i, nom in enumerate(noms, 1):
    print(f"{i}. {nom}")
