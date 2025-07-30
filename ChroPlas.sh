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

## chroPlas directory
chroPlas_dir=$(dirname "$(realpath "$0")")

# Check if input and output folders are provided
if [ -z "$input_folder" ] || [ -z "$output_folder" ]; then
  echo "Error: Both input and output folders are required."
  usage
  exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$output_folder/tmp"

source $chroPlas_dir/chroPlas_env/bin/activate
# Process gffs in the input folder
for gff in $(ls $input_folder/); do
	gff_id=$(basename "$gff" | sed -E 's/\.(gff3?|GFF3?)$//')
	echo "Processing gff: $gff_id"

	python $chroPlas_dir/scripts/get_fasta_length_GC.py \
	-i "$input_folder/$gff" \
	-o "$output_folder/tmp/$gff_id.contig_stats.tsv"

	bash $chroPlas_dir/scripts/process_keys.sh \
	"$input_folder"/"$gff" \
	"$output_folder"/tmp/"$gff_id".keys.tsv

	python $chroPlas_dir/scripts/convert_maker_counts.py \
	-i "$output_folder"/tmp/"$gff_id".keys.tsv \
	-o "$output_folder"/tmp/"$gff_id".maker_counts.tsv

	python $chroPlas_dir/scripts/combine_outputs.py \
	-d "$output_folder/tmp" \
	-f "$gff_id" \
	-o "$output_folder/$gff_id.combined_stats.tsv"

done
deactivate

