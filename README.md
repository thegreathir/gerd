# gerd
## Gerd is an online word party game based on [Taboo](https://boardgamegeek.com/boardgame/1111/taboo)

Players take turns describing a word or phrase to their partner without using the word itself, similar and opposite words.
In a limited time, each team that described and guessed more words correctly will win.
This repo contains the backend of the game's online implementation.
The game implementation is room-based, which means each player can create a room and share it with other players who he/she wants to play with.


## Implementation
This repo contains back-end part of the project using [django-rest-framework](https://www.django-rest-framework.org/) and [django-channels](https://channels.readthedocs.io/en/stable/).

## Test
Project test coverage is 93%.
To run tests:
```bash
./manage.py test
```

## Web client
The web client is available at [this repo](https://github.com/amsen20/gerd-front).
