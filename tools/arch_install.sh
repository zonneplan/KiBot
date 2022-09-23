#!/bin/sh
# Update the system
sudo pacman -Syyu --noconfirm
# Install the yay installer (needed for AUR) (Also installs git)
sudo pacman -S yay binutils --noconfirm
# Python installer
sudo pacman -S python-pip --noconfirm
###############################################################################
# Big dependencies
###############################################################################
# KiCad install, no 3D models (Down: 308.75 MiB, size: 1617.84 MiB)
# python-wxpython is installed here
sudo pacman -S kicad kicad-library --noconfirm
# KiBot graphic deps
# Note: librsvg is already installed for KiCad
# Note: gsfonts provides Helvetica, the default imagemagick font
sudo pacman -S ghostscript gsfonts imagemagick librsvg --noconfirm
# Install rar (from AUR KiBot optional)
yay -S --noconfirm rar
# Install pandoc (KiBot optional)
sudo pacman -S pandoc texlive-core --noconfirm
# Not needed at all, already installed and very optional
# sudo pacman -S poppler --noconfirm
###############################################################################
# KiAuto
###############################################################################
# Dependencies
sudo pacman -S recordmydesktop xdotool xclip libxslt python-psutil python-xvfbwrapper --noconfirm
# KiAuto, clean install, no extra packages
sudo pip install KiAuto
###############################################################################
# KiBoM
###############################################################################
# KiBoM & KiBot dependency
sudo pacman -S python-xlsxwriter --noconfirm
# Install KiBoM, clean install, no extra packages (from repo)
git clone https://github.com/INTI-CMNB/KiBoM.git
cd KiBoM/
sudo pip install .
cd ..
sudo rm -r KiBoM/
###############################################################################
# iBoM
###############################################################################
# Install iBoM, clean install, no extra packages
git clone https://github.com/INTI-CMNB/InteractiveHtmlBom.git
cd InteractiveHtmlBom/
sudo pip install .
cd ..
sudo rm -r InteractiveHtmlBom/
###############################################################################
# KiDiff
###############################################################################
# Install KiDiff, clean install, no extra packages
sudo pip install KiDiff
###############################################################################
# PcbDraw 0.9.0
###############################################################################
# Dependencies
sudo pacman -S python-numpy python-lxml python-mistune1 python-pybars3 python-wand python-yaml python-pcbnewtransition python-scipy --noconfirm
yay -S python-svgpathtools-git --noconfirm
# Install PcbDraw, clean install, no extra packages
git clone https://github.com/INTI-CMNB/PcbDraw.git
cd PcbDraw/
git submodule update --init --recursive
git checkout v0.9.0_maintain
sudo pip install .
cd ..
sudo rm -r PcbDraw/
###############################################################################
# KiCost Digi-key plug-in
###############################################################################
# kicost_digikey_api_v3 dependencies
# Repeated: sudo pacman -S python-requests python-urllib3 python-six python-certifi python-setuptools --noconfirm
sudo pacman -S python-inflection python-pyopenssl python-tldextract python-dateutil --noconfirm
# Install Digi-Key KiCost plug-in, clean install, no extra packages
sudo pip install kicost_digikey_api_v3 dependencies
###############################################################################
# KiCost
###############################################################################
# KiCost dependencies
# Repeated: sudo pacman -S python-lxml python-xlsxwriter python-requests python-yaml --noconfirm
sudo pacman -S python-beautifulsoup4 python-tqdm python-validators python-colorama python-pillow --noconfirm
# Install KiCost plug-in, clean install, no extra packages
sudo pip install kicost
###############################################################################
# KiBot
###############################################################################
# KiBot install, pulls qrcodegen dependency
sudo pip install kibot
