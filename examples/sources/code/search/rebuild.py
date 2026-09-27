BATCH_SIZE = 500


def rebuild(index, products):
    index.clear()
    for start in range(0, len(products), BATCH_SIZE):
        index.add(products[start:start + BATCH_SIZE])
