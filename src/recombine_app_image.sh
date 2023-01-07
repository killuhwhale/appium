#!/bin/bash


scho "Checkingigngingingin"
# Get the file path from the first argument
file_path="$1"

# Check if the file exists
if [ -f "$file_path" ]
then
    # The file exists
    echo "File exists."
else
    # The file does not exist
    echo "File does not exist. Recombining split files..."
    cat appium/app-part* > "$file_path"
    chmod +x "$file_path"
fi