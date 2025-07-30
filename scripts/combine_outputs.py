import pandas as pd
import argparse
import os

def combine_outputs(directory, file_id, output_file):
    # Construct file paths
    keys_file = os.path.join(directory, f"{file_id}.keys.tsv")
    stats_file = os.path.join(directory, f"{file_id}.contig_stats.tsv")

    # Read the keys file
    keys_df = pd.read_csv(keys_file, sep='\t', header=None, names=['contig_id', 'count', 'marker_type', 'gene'])

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

    # Updated classification logic to prioritize chromosomal_contig
    def classify_contig(row):
        if row['length'] < 2000000 and row.get('ribosomal_RNA', 0) > 0:
            return 'chromosomal_contig'
        elif (2000000 < row['length'] < 10000000) or row.get('ribosomal_RNA', 0) > 0:
            return 'chromosome'
        elif row['length'] < 350000 and (row.get('plasmid_partitioning_protein', 0) > 0 or row.get('conjug', 0) > 0):
            return 'plasmid'
        elif 350000 < row['length'] < 2000000 and (row.get('plasmid_partitioning_protein', 0) > 0 or row.get('conjug', 0) > 0):
            return 'megaplasmid'
        elif 350000 < row['length'] < 2000000 and row.get('conjug', 0) == 0:
            return 'chromid'
        else:
            return 'unknown'

    combined_df['class'] = combined_df.apply(classify_contig, axis=1)

    # Reorder columns to place 'class' between 'GC' and 'conjug'
    columns = list(combined_df.columns)
    gc_index = columns.index('GC')
    columns.insert(gc_index + 1, columns.pop(columns.index('class')))
    combined_df = combined_df[columns]

    # Write the combined dataframe to the output file
    combined_df.to_csv(output_file, sep='\t', index=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine keys and stats files based on contig_id.")
    parser.add_argument("-d", "--directory", required=True, help="Directory containing input files.")
    parser.add_argument("-f", "--file_id", required=True, help="File ID to identify input files.")
    parser.add_argument("-o", "--output_file", required=True, help="Path to the output file.")
    args = parser.parse_args()

    combine_outputs(args.directory, args.file_id, args.output_file)
