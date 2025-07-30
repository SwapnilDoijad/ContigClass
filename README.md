# ChroPlas

## Introduction
ChroPlas is a tool to identify contigs as chromosome, plasmid, chromids, and other elements, based on the key genes. This repository contains scripts and data for this classification process.

## Installation
To install and set up ChroPlas, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/ChroPlas.git
   ```
2. Navigate to the project directory:
   ```bash
   cd ChroPlas
   ```
3. Run the installation script:
   ```bash
   ./installation.sh
   ```

## Usage
To use ChroPlas, run the main script `ChroPlas.sh` with the following options:

```bash
Usage: ./ChroPlas.sh -i <input_folder> -o <output_folder>
```

### Options:
- `-i`, `--input-folder` `<input_folder>`: Specify the input folder containing GFF files.
- `-o`, `--output-folder` `<output_folder>`: Specify the output folder where results will be stored.
- `-h`, `--help`: Display the help message and exit.

### Example:
```bash
./ChroPlas.sh -i test_data/ -o results/
```

## Test Data
Test data is available in the `test_data/` directory. Example files include:
- `14C2.gff3`
- `BRA5.gff3`
- `GCF_000379605.1.gff3`

## License
This project is licensed under the [License Name]. See the LICENSE file for details.