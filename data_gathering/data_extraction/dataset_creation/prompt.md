- autoanything - rozbite i źle czyta ratingi

- dodać `other_features` do `specifications`.
- if price is a range, set from and to???
- add related search?
- if not sure about the quantity (or anything, never guess) return null,
- mean rating (don't round) and for each separately (dunhamssports check) (test on marksandspencer)
- for the price provide number and currency
- perhaps rethink variants <---------- maybe just remove that!
- for similar products just add their titles
- breadcrumbs - return only the name (single string)
- sizes - just return size (don't return quantity)
- in prompt add exact names of the json file fields
- colors should be a list of strings (see prettylittlething)
- available size instead of sizes
- specs -> material - list of strings
- specs -> dimensions - list of strings????
- provide just general and specific categories before the recommended prods and opinions and ratings
- similar products - just titles
- return only proper json

test later on polish ebutik


temp 0.6 vs 0.7

new remarks:
- instead of colors name it color variants - done
- size variants - done
- remove variants - done
- remove breadcrumbs?? I already have categories - done
- make AI provide only one of the: similar products, products I may also like, related products, recommended for me?? - done
- ratings not correctly extracted - dunhamssports and monoprice!!!!
- opinions should show reviews - monoprice
- opinions not extracted - pinkcherry
- number_of_available_items should work better - or just remove it - done
- customer reviews shows similar products (barnsandnoble) - done
- similar products includes "See Details" (barnsandnoble) - done

- work on specifications - less of them but more meaningful ones (prettylittlething has good ones - it provides style, occasion, etc.)
- specifications - return only specifications relevant to the product itself
- specifications shouldn't include description
- maybe instead of specifications call it product features
- make specifications just a dictionary or dict of dicts
- bytom and eobuwie lack categories for 0.7 - done
- tigerdirect lacks similar products - done

- categories are not always filled
- for categories add "try to be as general as possible"
- work on similar products (ebay 2, fashionnova)
- size variants shouldn't include dimensions
- in sizes or specs it sometimes provide size tables - this is bad
- lidl similar products are wrong
- rename color variants to available colors??? Same for sizes

Skupić się jedynie na fashion and beauty i suplach oraz rzeczach typu target, allegro, lidl?

To remove from the dataset:
- car parts websites
- vibemushrooms
- deguns, guns
- apteki - doz
- obi
- zooart
- computer equipment (microcenter, morele)

Simplification alg remarks:
- on the head and thw body find all meta tags and put on top of the text (as it's now for the head meta tags)
