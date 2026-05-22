---
name: play-tic-tac-toe
description: Play an interactive game of tic-tac-toe with the user. Use when the user asks to play tic-tac-toe, noughts and crosses, or a simple X/O board game.
---

# play-tic-tac-toe

**Trigger**: User asks to play tic-tac-toe, noughts and crosses, or a simple X/O board game.

## Board

Use a 3x3 board numbered left-to-right, top-to-bottom:

```text
1 | 2 | 3
--+---+--
4 | 5 | 6
--+---+--
7 | 8 | 9
```

## Process

- Ask who should play first if the user has not specified.
- Assign `X` to the first player and `O` to the second player.
- After each move, render the board and ask for the next move unless the game is over.
- Reject moves outside `1`-`9` or moves into occupied cells; ask for a legal move instead.
- Detect wins across rows, columns, and diagonals; detect draws when all cells are filled.

## Move Format

Accept either a bare cell number, such as `5`, or short natural language like "put X in 5".

## Strategy

When choosing a move:

1. Take a winning cell if one is available this turn.
2. Block the opponent's winning cell if they can win next turn.
3. Prefer center, then corners, then edges.
4. Avoid moves that allow the opponent an immediate fork when a safer legal move exists.

## Output

Keep turns concise: board, result if any, and the next prompt.
