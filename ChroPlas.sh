#!/bin/bash

# Display usage information
usage() {
  echo "Usage: $0 -i <input_folder> -o <output_folder>"
  echo "Options:"
  echo "  -i, --input-folder  <input_folder>   Specify the input folder containing gff files."
  echo "  -o, --output-folder <output_folder>  Specify the output folder where results will be stored."
  echo "  -h, --help          				   Display this help message and exit."
}

# Parse input arguments
while getopts "i:o:h-:" opt; do
  case $opt in
    i) input_folder="$OPTARG" ;;
    o) output_folder="$OPTARG" ;;
    h) usage; exit 0 ;;
    -) case "$OPTARG" in
         help) usage; exit 0 ;;
         *) echo "Invalid option: --$OPTARG"; usage; exit 1 ;;
       esac ;;
    *) usage; exit 1 ;;
  esac
done

# Check if input and output folders are provided
if [ -z "$input_folder" ] || [ -z "$output_folder" ]; then
  echo "Error: Both input and output folders are required."
  usage
  exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$output_folder"

source 	source chroPlas_env/bin/activate
# Process files in the input folder
for i in $(ls "$input_folder"); do 
  echo "Processing $i"
  for key in $(cat scripts/keys.txt); do
    echo "Processing key $key"
	python scripts/contig_stats.py -i "$input_folder/$i" -o "$output_folder/contig_stats_$i.tsv"
  done

done