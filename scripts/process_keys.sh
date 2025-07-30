#!/bin/bash

# This script processes keys.txt to extract contig IDs and counts for plasmid_marker_gene and chromosomal_marker_gene.

# Input arguments
input_file=$1
output_file=$2

# Check if input file and output file are provided
if [ -z "$input_file" ] || [ -z "$output_file" ]; then
  echo "Usage: $0 <input_file> <output_file>"
  exit 1
fi

> "$output_file"
while IFS= read -r line; do
  # Skip lines containing '##'
  if [[ "$line" == *"##"* ]]; then
    marker=$(echo "$line" | sed 's/## //')
    continue
  fi
  echo "Processing marker: $marker : gene: $line"
  gene=$(echo "$line" | sed 's/ /_/'g )
  grep "$line" "$input_file" | awk '{print $1}' | sort | uniq -c | awk -v marker="$marker" -v gene="$gene" '{print $2, $1, marker, gene}' | tr ' ' '\t' >> "$output_file"
done < scripts/keys.txt

sort -k1,1 -k2,2nr "$output_file" -o "$output_file"

