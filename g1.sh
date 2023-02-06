#!/bin/sh
# Fast tests
cat ~/.gitconfig
cp /root/.gitconfig /etc/gitconfig
cat /root/.gitconfig
ls -la /__w/KiBot/KiBot
pytest-3 -v --durations=0 -m "not slow" -n 2 --test_dir=output -k test_sch_replace_1
