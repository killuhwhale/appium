#!/bin/bash

# Check if nvm is installed
length=${#NVM_DIR}
echo $out
echo $length
num_files=$(ls -1a $NVM_DIR | wc -l)
echo $num_files
if [ $num_files -gt 0 ]; then
  # If nvm is installed, print "Installed"
  echo "Installed"
else
  # If nvm is not installed, print "Not installed"
  echo "Not installed"
fi

# Exit the script with a successful exit status
exit 0