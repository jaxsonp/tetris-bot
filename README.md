# Tetris

A (probably sorta) Tetris Guideline compliant tetris game.

My highscore: `129546`
Bot highscore: `102712`

## TODO

- Game fires callback multiple times per frame. Fix this
- Probably race conditions in inter-thread interaction via bot state
- Detect T-spins
- Advanced scoring (T-spins, perfect clears, etc)
	- Does b2b difficult clears apply before or after combo?
	- Leveling: caps? 20 lines cleared -> lvl 2 or 3?