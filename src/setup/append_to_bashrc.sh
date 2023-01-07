#!/bin/bash

# Set the text to be added to the file
text="$1"

# Set the path to the file
file_path="$2"

# Check if the text exists in the file
grep -q "$text" "$file_path"

# If the text does not exist in the file
if [ $? -ne 0 ]; then
  # Append the text to the file
  echo "$text" >> "$file_path"
fi

# Exit the script with a successful exit status
exit 0