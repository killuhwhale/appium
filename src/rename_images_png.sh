#!/bin/bash

# To use this script, save it to a file and make it executable (e.g. chmod +x rename_png_files.sh).
# Then, run it with the directory containing the .png files as an argument (e.g. ./rename_png_files.sh /path/to/directory).

# This script will loop through all .png files in the specified directory, generate a new filename using a
#  counter that starts at 0 and increases by 1 for each file, and then rename the file.

# chmod +x rename_images_png.sh 
# ./rename_images_png.sh ~/Pictures/


# Make sure a directory is provided as an argument
if [ $# -eq 0 ]
then
    echo "Error: No directory provided"
    exit 1
fi

# Navigate to the directory
cd "$1"

# Initialize a counter
counter=0

# Loop through all .png files in the directory
for file in *.png
do
    # Get the current extension
    extension="${file##*.}"

    # Generate a new filename
    new_filename="${counter}.${extension}"

    # Rename the file
    mv "$file" "$new_filename"

    # Increment the counter
    counter=$((counter+1))
done

# Navigate back to the original directory
cd -