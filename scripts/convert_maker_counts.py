import argparse
import pandas as pd

def main(input_file, output_file):
    # Read the tab-separated input file
    df = pd.read_csv(input_file, sep="\t", header=None,
                     names=["contig", "count", "marker_type", "function"])

    # Group by contig and marker_type, and sum the counts
    grouped = df.groupby(["contig", "marker_type"])["count"].sum().unstack(fill_value=0)

    # Ensure both marker types are present
    for col in ["plasmid", "chromosome"]:
        if col not in grouped.columns:
            grouped[col] = 0

    # Reorder columns
    grouped = grouped[["plasmid", "chromosome"]]

    # Write to output file
    grouped.to_csv(output_file, sep="\t")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert marker table to summarized format.")
    parser.add_argument("-i", "--input", required=True, help="Input file path")
    parser.add_argument("-o", "--output", required=True, help="Output file path")

    args = parser.parse_args()
    main(args.input, args.output)
