#!/bin/bash
## 2025-07-30 10:06:48 create an env
	python3.9 -m venv ContigClass_env
	source ContigClass_env/bin/activate
	pip install --upgrade pip
	pip install biopython
	pip install pandas
	pip install matplotlib
	pip install fpdf
	pip install reportlab
	pip install PyPDF2
	pip install pdf2image pillow
	pip install svglib reportlab
