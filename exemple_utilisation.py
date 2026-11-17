# -*- coding: utf-8 -*-
from tilegen import suggest_names, print_suggestions

# Générer 5 suggestions
print("5 suggestions de noms :")
suggestions = suggest_names(5)
print_suggestions(suggestions)

# Générer 3 autres suggestions
print("3 autres suggestions :")
suggestions = suggest_names(3)
print_suggestions(suggestions)
