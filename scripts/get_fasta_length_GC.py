import argparse
import os
from Bio import SeqIO

GFF_EXTENSIONS = ('.gff', '.gff3')

def is_gff_file(filename):
    return filename.lower().endswith(GFF_EXTENSIONS)

def calculate_gc(sequence):
    gc_count = sequence.count("G") + sequence.count("C")
    total_count = len(sequence)
    return (gc_count / total_count) * 100 if total_count > 0 else 0

def extract_sequences_from_gff(filepath):
    sequences = {}
    reading_sequences = False
    current_contig = None
    current_sequence = []

    try:
        with open(filepath, "r") as file:
            for line in file:
                if line.startswith("##FASTA"):
                    reading_sequences = True
                    continue

                if reading_sequences:
                    if line.startswith(">"):
                        if current_contig and current_sequence:
                            sequences[current_contig] = "".join(current_sequence)
                        current_contig = line[1:].strip()
                        current_sequence = []
                    else:
                        current_sequence.append(line.strip())

            # Add the last contig
            if current_contig and current_sequence:
                sequences[current_contig] = "".join(current_sequence)
    except Exception as e:
        print(f"⚠️ Could not extract sequences from GFF file {filepath}: {e}")

    return sequences

def process_gff(filepath):
    contig_data = {}
    sequences = extract_sequences_from_gff(filepath)

    try:
        with open(filepath, "r") as file:
            for line in file:
                if line.startswith("#") or line.startswith("##FASTA"):
                    continue

                parts = line.strip().split("\t")
                if len(parts) < 9:
                    continue

                contig_id = parts[0]
                feature_type = parts[2]  # The third column in GFF is the feature type

                if contig_id not in contig_data:
                    contig_data[contig_id] = {
                        "feature_count": 0,
                        "total_length": 0,
                        "gc_count": 0,
                        "base_count": 0
                    }

                # Increment feature count for the contig
                contig_data[contig_id]["feature_count"] += 1

    except Exception as e:
        print(f"⚠️ Error processing GFF file {filepath}: {e}")

    for contig_id, sequence in sequences.items():
        if contig_id not in contig_data:
            contig_data[contig_id] = {
                "feature_count": 0,
                "total_length": 0,
                "gc_count": 0,
                "base_count": 0
            }

        # Calculate total length directly from the sequence
        total_bases = len(sequence)
        gc_count = sequence.upper().count("G") + sequence.upper().count("C")

        contig_data[contig_id]["total_length"] = total_bases
        contig_data[contig_id]["gc_count"] = gc_count
        contig_data[contig_id]["base_count"] = total_bases

    results = []
    for contig_id, data in contig_data.items():
        avg_gc = (data["gc_count"] / data["base_count"]) * 100 if data["base_count"] > 0 else 0
        results.append((contig_id, data["feature_count"], data["total_length"], f"{avg_gc:.2f}"))

    return results

def process_file(filepath, fasta_sequences):
    filename = os.path.basename(filepath)
    if is_gff_file(filename):
        result = process_gff(filepath, fasta_sequences)
        if result:
            count, length, gc = result
            return [(filename, count, length, gc)]
    return None  # unsupported file type

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a single GFF file.")
    parser.add_argument("-i", "--input", required=True, help="Input GFF file")
    parser.add_argument("-o", "--output", required=True, help="Output TSV file")

    args = parser.parse_args()
    input_file = args.input
    output_file = args.output

    results = []

    if os.path.isfile(input_file):
        file_id = os.path.splitext(os.path.basename(input_file))[0]  # Remove the file extension
        res = process_gff(input_file)
        if res:
            for contig_result in res:
                results.append((file_id, *contig_result))

    # Write TSV
    with open(output_file, "w") as out:
        out.write("file_id\tcontig_id\tfeatures\tlength\tGC\n")
        for file_id, contig_id, features, length, gc in results:
            out.write(f"{file_id}\t{contig_id}\t{features}\t{length}\t{gc}\n")
