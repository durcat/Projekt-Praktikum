#!/bin/zsh
# Startet imu_3d_viewer.py mit der science-Umgebung.
# Doppelklick im Finder oder im Terminal: ./viewer_starten.command [messung.csv]
cd "${0:A:h}"
exec /Users/kiko/venvs/science/bin/python imu_3d_viewer.py "$@"
