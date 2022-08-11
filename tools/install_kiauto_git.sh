#!/bin/sh
# Install KiAuto from GitHub repo, for CI/CD (needs root)

# Remove KiAuto
dpkg --remove kiauto
# Install KiAuto@master
curl https://codeload.github.com/INTI-CMNB/KiAuto/zip/refs/heads/master --output pp.zip
unzip pp.zip
pip3 install KiAuto-master/
# Clean the downloaded stuff
rm -rf KiAuto-master/ pp.zip
# Check what we got
echo $PATH
ls -la /usr/bin/*_do || true
ls -la /usr/local/bin/*_do || true
which pcbnew_do
pcbnew_do --version
