#!/bin/bash

# This script processes keys.txt to extract contig IDs and counts for plasmid_marker_gene and chromosomal_marker_gene.

# Input arguments
input_file=$1
output_file=$2

keys_dir=$(dirname "$(realpath "$0")")

# Check if input file and output file are provided
if [ -z "$input_file" ] || [ -z "$output_file" ]; then
  echo "Usage: $0 <input_file> <output_file>"
  exit 1
fi

> "$output_file"
while IFS= read -r line; do
  class=$(awk -F'\t' '{print $1}' <<< "$line")
  genes=$(awk -F'\t' '{print $4}' <<< "$line")
  gene_list=$(echo "$genes" | tr ',' '\n' | sed '/^$/d')
  while IFS= read -r gene; do
    if [[ -n "$gene" ]]; then
      gene_id=$(echo $gene | sed 's/ /_/g')
      grep "$gene" "$input_file" | awk '{print $1}' | sort | uniq -c | awk -v class="$class" -v gene="$gene_id" '{print $2, $1, class, gene}' | tr ' ' '\t' >> "$output_file"
    fi
  done <<< "$gene_list"

done < <(tail -n +2 "$keys_dir/keys.tsv")

sort -k1,1 -k2,2nr "$output_file" -o "$output_file"

