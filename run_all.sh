#!/bin/bash
set -e
python src/calib.py
python src/build_all.py
python src/figures.py
python src/build_dash.py
python src/paper.py
