"""Disposable fixture module: order discount calculation."""


def discount(total, member):
    rate = 0.10 if member else 0.0
    return round(total * (1 - rate), 2)
