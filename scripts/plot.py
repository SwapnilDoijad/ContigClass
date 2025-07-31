import os
import sys
import argparse
import pandas as pd
from io import BytesIO
from PyPDF2 import PdfMerger
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Flowable
from reportlab.pdfbase.pdfmetrics import stringWidth
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# --- Parse Arguments ---
parser = argparse.ArgumentParser(description="Plot contig length vs GC content by class.")
parser.add_argument('-i', '--input', required=True, help='Input TSV file with contig annotations')
parser.add_argument('-o', '--output', default='output.pdf', help='Output PDF file')
args = parser.parse_args()

if not args.output.lower().endswith('.pdf'):
    raise ValueError("Output file must end with .pdf")

# --- Load Data ---
df = pd.read_csv(args.input, sep='\t')
if df.empty:
    print("Input TSV file is empty.")
    sys.exit(1)

df['length_capped'] = df['length'].clip(upper=5_500_000)
color_map = {
    'unknown': '#808080',
    'plasmid': '#FFD700',
    'megaplasmid': '#FFA500',
    'chromid': '#FF0000',
    'chromosome': '#00008B',
    'chromosomal_contig': '#87CEFA',
    'megaplasmid/chromid': '#C71585'
}

# --- Custom Flowable for Rotated Header Text ---
class RotatedAndWrappedText(Flowable):
    def __init__(self, text, font_size=8, padding=2):
        super().__init__()
        self.font_size = font_size
        self.leading = font_size + padding
        self.font_name = "Helvetica"
        self.text_lines = self.wrap_text(text, 40, self.font_name, font_size)
        self.width = self.leading * len(self.text_lines)
        self.height = font_size + 4

    def wrap_text(self, text, max_width, font, font_size):
        text = text.replace('_', ' ')
        words = text.split(' ')
        lines, current_line = [], ''
        for word in words:
            trial = f"{current_line} {word}".strip()
            if stringWidth(trial, font, font_size) <= max_width:
                current_line = trial
            else:
                if current_line: lines.append(current_line)
                current_line = word
                if len(lines) == 2: break
        if current_line: lines.append(current_line)
        return lines[:2] + ['...'] if len(lines) > 3 else lines

    def wrap(self, availWidth, availHeight): return self.height, self.width

    def draw(self):
        self.canv.saveState()
        self.canv.translate(self.height - 15, 3.5)
        self.canv.rotate(90)
        text = self.canv.beginText()
        text.setFont(self.font_name, self.font_size)
        text.setLeading(self.leading)
        for line in self.text_lines:
            text.textLine(line)
        self.canv.drawText(text)
        self.canv.restoreState()

# --- PDF Table ---
def calculate_column_widths(columns):
    fixed = {'file_id': 100, 'contig_id': 60, 'features': 60, 'length': 50, 'GC': 50, 'class': 100}
    return [fixed.get(col, 40) for col in columns]

def add_table_to_pdf(tsv_file, pdf):
    df = pd.read_csv(tsv_file, sep='\t')
    if df.empty:
        print("The input TSV file is empty.")
        sys.exit(1)

    non_rotated = {'file_id', 'contig_id', 'features', 'length', 'GC', 'class'}
    rotated = [col for col in df.columns if col not in non_rotated]
    header = [RotatedAndWrappedText(col) if col in rotated else col for col in df.columns]
    data = [header] + df.values.tolist()
    col_widths = calculate_column_widths(df.columns)

    table = Table(data, colWidths=col_widths)
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'BOTTOM'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 40),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 0),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])

    for i, col in enumerate(df.columns):
        if col in non_rotated:
            style.add('VALIGN', (i, 0), (i, 0), 'MIDDLE')

    table.setStyle(style)
    pdf.build([table])

# --- SVG Plot to Vector PDF ---
def save_plot_as_pdf(pdf_path):
    try:
        fig = Figure(figsize=(14, 10))
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)

        for cls in df['class'].unique():
            subset = df[df['class'] == cls]
            ax.scatter(subset['length_capped'], subset['GC'], label=cls, color=color_map.get(cls, '#bbbbbb'), s=300)

        ax.set_xlabel('Contig Length (bp)', fontsize=26)
        ax.set_ylabel('GC Content (%)', fontsize=26)
        ax.set_title('Contig Length vs GC Content by Class', fontsize=32, fontweight='bold')
        ax.tick_params(axis='both', labelsize=26)
        ax.set_xlim(0, 5_500_000)
        ax.legend(title='Class', loc='lower right', fontsize=20, title_fontsize=24)
        ax.ticklabel_format(style='sci', axis='x', scilimits=(6, 6))  # ensure scientific format
        ax.xaxis.offsetText.set_fontsize(22)  # set to your desired font size

        ax.grid(True)
        fig.tight_layout()

        svg_buffer = BytesIO()
        fig.savefig(svg_buffer, format='svg')
        svg_buffer.seek(0)

        drawing = svg2rlg(svg_buffer)

        c = pdf_canvas.Canvas(pdf_path, pagesize=landscape(A4))
        width, height = landscape(A4)

        desired_width = 400
        scale = desired_width / drawing.width
        drawing.width *= scale
        drawing.height *= scale
        drawing.scale(scale, scale)

        x = (width - drawing.width) / 2
        y = (height - drawing.height) / 2

        renderPDF.draw(drawing, c, x, y)
        c.showPage()
        c.save()

    except Exception as e:
        print(f"Error saving SVG plot to PDF: {e}")
        sys.exit(1)

# --- Combine Table and Plot PDFs ---
def generate_combined_pdf(tsv_file, output_pdf):
    table_pdf = "table_temp.pdf"
    plot_pdf = "plot_temp.pdf"

    try:
        add_table_to_pdf(tsv_file, SimpleDocTemplate(table_pdf, pagesize=landscape(A4)))
        save_plot_as_pdf(plot_pdf)

        merger = PdfMerger()
        merger.append(table_pdf)
        merger.append(plot_pdf)
        merger.write(output_pdf)
        merger.close()

        os.remove(table_pdf)
        os.remove(plot_pdf)

    except Exception as e:
        print(f"Error generating combined PDF: {e}")
        sys.exit(1)

# --- Execute ---
generate_combined_pdf(args.input, args.output)
