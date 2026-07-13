---
name: play-tic-tac-toe
description: Pick the next move in a Tic-Tac-Toe game. Triggered when the caller provides a board state and the player's symbol (X or O) and asks for the next move.
---

# Play Tic-Tac-Toe

Tic-Tac-Toe is a two-player game played on a 3x3 grid. Players
alternate placing their symbol (X or O) on empty cells. The first
player to place three of their symbols in a horizontal, vertical,
or diagonal line wins. If the grid fills with no winner, the game
is a draw.

## Move format

Cells are numbered 1-9 using the numeric-keypad layout:

    1 | 2 | 3
   -----------
    4 | 5 | 6
   -----------
    7 | 8 | 9

## What to output

When asked for a move, output ONLY the cell number of a legal
(empty) cell. No explanation, no punctuation, no whitespace — just
a single digit from 1 to 9.
