# fantasy-optimizer
[![Build Status](https://travis-ci.org/lynshi/fantasy-assistant.svg?branch=master)](https://travis-ci.org/lynshi/fantasy-assistant)
[![Coverage Status](https://coveralls.io/repos/github/lynshi/fantasy-assistant/badge.svg?branch=master)](https://coveralls.io/github/lynshi/fantasy-assistant?branch=master)

Given a list of players, average fantasy points per game, and salaries for daily fantasy sports, this project produces the optimal lineup, within budget and positional constraints, maximizing the average points per game total. This is accomplished with a integer linear program solved using [PuLP](https://pythonhosted.org/PuLP/). Please note the only acceptable roster input format currently is the CSV produced by [Yahoo Daily Fantasy](https://sports.yahoo.com/dailyfantasy).
