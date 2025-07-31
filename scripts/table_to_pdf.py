import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Flowable
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
import argparse
import sys

class RotatedAndWrappedText(Flowable):
    def __init__(self, text, font_size=8, padding=2):
        super().__init__()
        self.font_size = font_size
        self.leading = font_size + padding
        self.font_name = "Helvetica"
        self.text_lines = self.wrap_text(text, max_width=40, font=self.font_name, font_size=self.font_size)

        # Height when drawn vertically becomes width in table
        self.width = self.leading * len(self.text_lines)
        self.height = font_size + 4  # vertical height of the text line block

    def wrap_text(self, text, max_width, font="Helvetica", font_size=8):
        full_width = stringWidth(text, font, font_size)

        # If it fits in one line, keep it
        if full_width <= max_width:
            return [text]

        # Optionally force a split to fill vertical space for short entries
        if full_width <= max_width * 0.6:
            mid = len(text) // 2
            return [text[:mid], text[mid:]]

        # Replace underscores with spaces
        text = text.replace('_', ' ')
        words = text.split(' ')
        lines = []
        current_line = ''

        for word in words:
            trial_line = f"{current_line} {word}".strip()
            trial_width = stringWidth(trial_line, font, font_size)

            if trial_width <= max_width:
                current_line = trial_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

                # ✅ Check line count
                if len(lines) == 2:
                    break  # Stop adding more lines (only 2 so we can add 1 more below)

        if current_line:
            lines.append(current_line)

        # ✅ If still too long, truncate or join rest into last line
        if len(lines) > 3:
            lines = lines[:2] + ['...']  # or use text[:N] if you want a cutoff
        elif len(lines) > 3:
            lines = lines[:3]

        return lines


    def insert_soft_breaks(self, text, break_char='_'):
        # Replace underscores or long runs with spaces for breaking
        return text.replace(break_char, ' ')



    def wrap(self, availWidth, availHeight):
        # This defines the table cell size (before rotation)
        return self.height, self.width

    def draw(self):
        self.canv.saveState()

        # Shift origin slightly left and upward before rotation
        x_offset = -15   # controls horizontal/left alignment
        y_offset = 3.5    # controls bottom spacing

        # Move origin: first shift into place, then rotate
        self.canv.translate(self.height + x_offset, y_offset)
        self.canv.rotate(90)

        text_object = self.canv.beginText()
        text_object.setFont("Helvetica", self.font_size)
        text_object.setTextOrigin(0, 0)
        text_object.setLeading(self.leading)

        for line in self.text_lines:
            text_object.textLine(line)

        self.canv.drawText(text_object)
        self.canv.restoreState()


def calculate_column_widths(columns):
    manual_widths = {
        'file_id': 100,
        'contig_id': 60,
        'features': 60,
        'length': 50,
        'GC': 50,
        'class': 100
    }

    default_width = 40
    col_widths = []

    for col_name in columns:
        col_widths.append(manual_widths.get(col_name, default_width))

    return col_widths


def convert_tsv_to_pdf(tsv_file, pdf_file):
    try:
        df = pd.read_csv(tsv_file, sep='\t')
    except Exception as e:
        print(f"Error reading TSV file: {e}")
        sys.exit(1)

    if df.empty:
        print("The input TSV file is empty.")
        sys.exit(1)

    # Columns to exclude from rotation
    non_rotated_columns = {'file_id', 'contig_id', 'features', 'length', 'GC', 'class'}

    # Determine which columns to rotate
    rotated_columns = [col for col in df.columns if col not in non_rotated_columns]

    # Create PDF document
    pdf = SimpleDocTemplate(pdf_file, pagesize=landscape(A4))

    # Prepare table data
    data = [df.columns.tolist()] + df.values.tolist()

    # Apply rotated Flowables to selected headers
    rotated_and_wrapped_columns = {
        header: RotatedAndWrappedText(header) for header in rotated_columns
    }
    data[0] = [rotated_and_wrapped_columns.get(col, col) for col in data[0]]

    # Calculate column widths
    col_widths = calculate_column_widths(df.columns.tolist())

    # Adjust padding based on maximum lines in rotated headers
    max_lines = max((len(col.split('_')) for col in rotated_columns), default=1)
    dynamic_padding = max(40, max_lines * 10)

    # Create and style the table
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

    for idx, col_name in enumerate(df.columns):
        if col_name in {'file_id', 'contig_id', 'features', 'length', 'GC', 'class'}:
            style.add('VALIGN', (idx, 0), (idx, 0), 'MIDDLE')
    
    table.setStyle(style)

    pdf.build([table])
    print(f"PDF successfully saved to: {pdf_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a TSV file to a formatted PDF table.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input TSV file.")
    parser.add_argument("-o", "--output", required=True, help="Path to the output PDF file.")

    args = parser.parse_args()
    convert_tsv_to_pdf(args.input, args.output)
