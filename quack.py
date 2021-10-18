# Quack v1
# Copyright 2021, All Rights Reserved

from duckie import Game

if __name__ == "__main__":
    quack = Game('quack_data.json')
    quack.start()
    while quack.running:
        quack.update()
