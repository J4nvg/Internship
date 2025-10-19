#!/bin/bash

DIR="full_sim_per_tactic"

for file in "$DIR"/*.py; do
    [ -e "$file" ] || continue
    echo "Launching $file in new terminal window..."
    powershell.exe wt.exe new-window --title "$(basename "$file")" wsl bash -c "cd $(pwd); uv run '$file'; echo; echo '--- $file finished ---'; exec bash" &
done

echo "All scripts launched in separate terminal windows."
