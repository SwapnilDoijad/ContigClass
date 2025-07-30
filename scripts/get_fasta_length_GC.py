import argparse
import os
from Bio import SeqIO
from Bio.SeqUtils import gc_fraction

FASTA_EXTENSIONS = ('.fasta', '.fa', '.fna', '.fasta.gz', '.fa.gz', '.fna.gz')

def is_fasta_file(filename):
    return filename.lower().endswith(FASTA_EXTENSIONS)

def compute_contig_stats(filepath):
    contig_lengths = []
    gc_contents = []

    try:
        for record in SeqIO.parse(filepath, "fasta"):
            seq = record.seq
            contig_lengths.append(len(seq))
            gc_contents.append(gc_fraction(seq) * 100)
    except Exception as e:
        print(f"⚠️ Could not parse {filepath}: {e}")
        return None

    if not contig_lengths:
        return None

    num_contigs = len(contig_lengths)
    total_length = sum(contig_lengths)
    avg_gc = sum(gc_contents) / num_contigs if num_contigs > 0 else 0
    file_id = os.path.basename(filepath)

    return file_id, num_contigs, total_length, avg_gc

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute contig stats from all FASTA files in a folder.")
    parser.add_argument("-i", "--input", required=True, help="Input folder containing FASTA files")
    parser.add_argument("-o", "--output", required=True, help="Output TSV file")

    args = parser.parse_args()
    input_folder = args.input
    output_file = args.output

    results = []

    for filename in os.listdir(input_folder):
        filepath = os.path.join(input_folder, filename)
        if os.path.isfile(filepath) and is_fasta_file(filename):
            stat = compute_contig_stats(filepath)
            if stat:
                results.append(stat)

    # Write TSV
    with open(output_file, "w") as out:
        out.write("file_id\tcontigs\tlength\tGC\n")
        for file_id, contigs, length, gc in results:
            out.write(f"{file_id}\t{contigs}\t{length}\t{gc:.2f}\n")

    print(f"✅ Processed {len(results)} FASTA files. Results written to {output_file}")
