import pandas as pd
import argparse
import os

def combine_outputs(directory, file_id, output_file):
    # Construct file paths
    keys_file = os.path.join(directory, f"{file_id}.keys.tsv")
    stats_file = os.path.join(directory, f"{file_id}.contig_stats.tsv")

    # Read the keys file
    keys_df = pd.read_csv(keys_file, sep='\t', header=None, names=['contig_id', 'count', 'marker_type', 'gene'])

    # Replace underscores with spaces in the 'gene' column
    keys_df['gene'] = keys_df['gene'].str.replace('_', ' ')

    # Pivot the keys file to count occurrences of each gene type
    gene_counts = keys_df.pivot_table(index='contig_id', columns='gene', values='count', aggfunc='sum', fill_value=0)

    # Ensure all counts are integers
    gene_counts = gene_counts.astype(int)

    # Read the stats file
    stats_df = pd.read_csv(stats_file, sep='\t')

    # Merge the dataframes on contig_id, ensuring all contigs from stats_df are included
    combined_df = pd.merge(stats_df, gene_counts, on='contig_id', how='left')

    # Fill missing values with 0 for gene counts
    combined_df.fillna(0, inplace=True)

    # Ensure all counts are integers
    combined_df = combined_df.astype({col: 'int' for col in gene_counts.columns})

    # Read the keys.tsv file to dynamically define classification rules
    keys_path = os.path.join(os.path.dirname(__file__), 'keys.tsv')
    keys_df = pd.read_csv(keys_path, sep='\t')

    def classify_contig(row):
        # Define priority order for classification
        priority_order = ['chromosome', 'chromosomal_contig', 'plasmid', 'megaplasmid', 'chromid']

        classifications = []

        for _, key_row in keys_df.iterrows():
            min_size = key_row['min_size(Mb)'] * 1e6
            max_size = key_row['max_size(Mb)'] * 1e6

            # Check size range first
            if not (min_size <= row['length'] <= max_size):
                continue

            must_present = key_row['key_genes_must_present'].split(',') if pd.notna(key_row['key_genes_must_present']) and key_row['key_genes_must_present'].strip() else []
            must_absent = key_row['key_genes_must_absent'].split(',') if pd.notna(key_row['key_genes_must_absent']) and key_row['key_genes_must_absent'].strip() else []

            # Check presence and absence of genes
            if (not must_present or any(row.get(gene.strip(), 0) > 0 for gene in must_present)) and \
               (not must_absent or all(row.get(gene.strip(), 0) == 0 for gene in must_absent)):
                classifications.append(key_row['class'])

        # Handle overlapping classifications
        if 'megaplasmid' in classifications and 'chromid' in classifications:
            # print(f"Contig {row['contig_id']} classified as megaplasmid/chromid based on shared genes")
            return 'megaplasmid/chromid'

        if classifications:
            classification = classifications[0]  # Take the first matching classification based on priority
            # print(f"Contig {row['contig_id']} classified as {classification} based on rules")
            return classification

        # print(f"Contig {row['contig_id']} classified as unknown: Did not meet any classification rules")
        return 'unknown'

    combined_df['class'] = combined_df.apply(classify_contig, axis=1)

    # Reorder columns to place 'class' between 'GC' and 'conjug'
    columns = list(combined_df.columns)
    gc_index = columns.index('GC')
    columns.insert(gc_index + 1, columns.pop(columns.index('class')))
    combined_df = combined_df[columns]

    # Dynamically determine gene order from key_genes_must_present and key_genes_must_absent in keys.tsv
    gene_order = []
    for _, row in keys_df.iterrows():
        if pd.notna(row['key_genes_must_present']):
            gene_order.extend([gene.strip() for gene in row['key_genes_must_present'].split(',')])
        if pd.notna(row['key_genes_must_absent']):
            gene_order.extend([gene.strip() for gene in row['key_genes_must_absent'].split(',')])

    # Remove duplicates while preserving order
    gene_order = list(dict.fromkeys(gene_order))

    gene_columns = [col for col in gene_order if col in combined_df.columns]
    other_columns = [col for col in combined_df.columns if col not in gene_columns]
    combined_df = combined_df[other_columns + gene_columns]

    # Debugging: Print the dynamically determined gene order and columns in the dataframe
    # print("Gene order from keys.tsv:", gene_order)
    # print("Columns in combined_df before reordering:", combined_df.columns.tolist())

    # Write the combined dataframe to the output file
    combined_df.to_csv(output_file, sep='\t', index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine keys and stats files based on contig_id.")
    parser.add_argument("-d", "--directory", required=True, help="Directory containing input files.")
    parser.add_argument("-f", "--file_id", required=True, help="File ID to identify input files.")
    parser.add_argument("-o", "--output_file", required=True, help="Path to the output file.")
    args = parser.parse_args()

    combine_outputs(args.directory, args.file_id, args.output_file)
