#!/user/bin/bash

sudo apt install libsecret-common
sudo apt install libsecret-1-0
sudo apt install libnss3 libnspr4

echo "Downloading VS Code"
curl -o code.deb -L "http://go.microsoft.com/fwlink/?LinkID=760868"

echo "Installing VS Code."
sudo dpkg -i  code.deb