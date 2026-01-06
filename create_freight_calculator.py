#!/usr/bin/env python3
"""
Create Die Co. Freight Calculator Excel Workbook
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, numbers
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule

def create_freight_calculator():
    """Create the complete freight calculator workbook"""

    wb = Workbook()

    # Create sheets
    ws1 = wb.active
    ws1.title = "Import Data Entry"
    ws2 = wb.create_sheet("Freight Calculator")
    ws3 = wb.create_sheet("ERP Upload")

    # Define styles
    header_font = Font(bold=True, size=14)
    bold_font = Font(bold=True)
    currency_format = '"$"#,##0.00'
    percentage_format = '0.00%'
    date_format = 'MM/DD/YYYY'
    number_format = '#,##0'

    # Colors
    light_blue = PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")
    yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    red_font = Font(bold=True, color="FF0000")

    # Alignment
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    # Border
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # ========== SHEET 1: Import Data Entry ==========
    print("Creating Sheet 1: Import Data Entry...")

    # Section A: Entry Summary
    ws1.merge_cells('A1:F1')
    ws1['A1'] = "DIE CO., INC. - IMPORT FREIGHT CALCULATOR"
    ws1['A1'].font = header_font
    ws1['A1'].alignment = center_align

    ws1['A2'] = "Entry Summary Data"
    ws1['A2'].font = bold_font

    # Entry information fields
    ws1['A3'] = "Entry #:"
    ws1['B3'].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

    ws1['A4'] = "Entry Date:"
    ws1['B4'].number_format = date_format
    ws1['B4'].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

    ws1['A5'] = "Vessel:"
    ws1['B5'].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

    ws1['A6'] = "Invoice #:"
    ws1['B6'].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

    # Cost fields
    ws1['A8'] = "Total Duty (Box 37):"
    ws1['B8'].number_format = currency_format
    ws1['B8'].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")
    ws1['C8'] = "From CBP Entry Summary"

    ws1['A9'] = "Customs Entry Fee:"
    ws1['B9'].number_format = currency_format
    ws1['B9'].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

    ws1['A10'] = "ISF - Security Filing:"
    ws1['B10'].number_format = currency_format
    ws1['B10'].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

    ws1['A11'] = "Ocean Freight:"
    ws1['B11'].number_format = currency_format
    ws1['B11'].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

    ws1['A12'] = "Terminal Handling/Services:"
    ws1['B12'].number_format = currency_format
    ws1['B12'].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

    ws1['A13'] = "Cartage & Services:"
    ws1['B13'].number_format = currency_format
    ws1['B13'].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

    ws1['A14'] = "Other Fees:"
    ws1['B14'].number_format = currency_format
    ws1['B14'].fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

    ws1['A16'] = "Total Freight Invoice:"
    ws1['B16'] = "=SUM(B9:B14)"
    ws1['B16'].number_format = currency_format
    ws1['B16'].font = bold_font
    ws1['C16'] = "From Freight Expediters Invoice"

    ws1['A18'] = "FREIGHT DIFFERENTIAL TO ALLOCATE:"
    ws1['B18'] = "=B16-B8"
    ws1['B18'].number_format = currency_format
    ws1['B18'].font = bold_font
    ws1['B18'].fill = yellow_fill
    ws1['C18'] = "Amount to distribute across parts"

    # Section B: Part Detail Table
    headers = ["Part #", "Description", "Quantity", "Net Weight (KG)", "# of Skids",
               "Weight per Skid", "Total Part Weight", "Weight %", "Allocated Freight"]

    for col_idx, header in enumerate(headers, start=1):
        cell = ws1.cell(row=20, column=col_idx)
        cell.value = header
        cell.font = bold_font
        cell.fill = light_blue
        cell.alignment = center_align
        cell.border = thin_border

    # Data rows (21-70)
    for row in range(21, 71):
        # Part # (A)
        ws1.cell(row=row, column=1).fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

        # Description (B)
        ws1.cell(row=row, column=2).fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

        # Quantity (C)
        ws1.cell(row=row, column=3).number_format = number_format
        ws1.cell(row=row, column=3).fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

        # Net Weight KG (D)
        ws1.cell(row=row, column=4).number_format = '0.00'
        ws1.cell(row=row, column=4).fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

        # # of Skids (E)
        ws1.cell(row=row, column=5).number_format = number_format
        ws1.cell(row=row, column=5).fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

        # Weight per Skid (F) - Formula
        ws1.cell(row=row, column=6).value = f"=IF(E{row}>0,D{row}*C{row}/E{row},0)"
        ws1.cell(row=row, column=6).number_format = '0.00'

        # Total Part Weight (G) - Formula
        ws1.cell(row=row, column=7).value = f"=C{row}*D{row}"
        ws1.cell(row=row, column=7).number_format = '#,##0.00'

        # Weight % (H) - Formula
        ws1.cell(row=row, column=8).value = f"=IF($G$71>0,G{row}/$G$71,0)"
        ws1.cell(row=row, column=8).number_format = percentage_format

        # Allocated Freight (I) - Formula
        ws1.cell(row=row, column=9).value = f"=H{row}*$B$18"
        ws1.cell(row=row, column=9).number_format = currency_format

    # Row 71: Totals
    ws1['A71'] = "TOTALS:"
    ws1['A71'].font = bold_font

    ws1['C71'] = "=SUM(C21:C70)"
    ws1['C71'].number_format = number_format
    ws1['C71'].font = bold_font

    ws1['E71'] = "=SUM(E21:E70)"
    ws1['E71'].number_format = number_format
    ws1['E71'].font = bold_font

    ws1['G71'] = "=SUM(G21:G70)"
    ws1['G71'].number_format = '#,##0.00'
    ws1['G71'].font = bold_font

    ws1['H71'] = "=SUM(H21:H70)"
    ws1['H71'].number_format = percentage_format
    ws1['H71'].font = bold_font

    ws1['I71'] = "=SUM(I21:I70)"
    ws1['I71'].number_format = currency_format
    ws1['I71'].font = bold_font

    # Row 73: Validation Check
    ws1['A73'] = "Validation Check:"
    ws1['A73'].font = bold_font
    ws1['B73'] = '=IF(ABS(I71-B18)<0.01,"✓ PASS","✗ FAIL - Allocation Error")'
    ws1['B73'].font = bold_font

    # Add conditional formatting to validation cell
    green_fill = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")
    red_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")

    ws1.conditional_formatting.add('B73',
        CellIsRule(operator='containsText', formula=['"PASS"'], fill=green_fill, font=Font(bold=True, color="FFFFFF")))
    ws1.conditional_formatting.add('B73',
        CellIsRule(operator='containsText', formula=['"FAIL"'], fill=red_fill, font=Font(bold=True, color="FFFFFF")))

    # Row 75: Instructions
    ws1['A75'] = "INSTRUCTIONS: Enter CBP Entry Summary data in Section A. Enter Freight Expediters invoice total. Enter part details starting row 21. Freight will auto-allocate by weight percentage."
    ws1.merge_cells('A75:I75')
    ws1['A75'].alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

    # Set column widths for Sheet 1
    ws1.column_dimensions['A'].width = 30
    ws1.column_dimensions['B'].width = 15
    ws1.column_dimensions['C'].width = 35
    ws1.column_dimensions['D'].width = 15
    ws1.column_dimensions['E'].width = 12
    ws1.column_dimensions['F'].width = 15
    ws1.column_dimensions['G'].width = 18
    ws1.column_dimensions['H'].width = 12
    ws1.column_dimensions['I'].width = 18

    # ========== SHEET 2: Freight Calculator ==========
    print("Creating Sheet 2: Freight Calculator...")

    ws2.merge_cells('A1:J1')
    ws2['A1'] = "FREIGHT COST ANALYSIS"
    ws2['A1'].font = header_font
    ws2['A1'].alignment = center_align

    # Row 2: Auto-populated import info
    ws2['A2'] = "Entry #:"
    ws2['B2'] = "='Import Data Entry'!B3"

    ws2['D2'] = "Vessel:"
    ws2['E2'] = "='Import Data Entry'!B5"

    ws2['G2'] = "Total Freight:"
    ws2['H2'] = "='Import Data Entry'!B18"
    ws2['H2'].number_format = currency_format

    # Row 4: Headers
    headers2 = ["Part #", "Description", "Quantity (M)", "Net Weight (KG)",
                "Allocated Freight", "Cost per M", "Cost per Unit", "Cost per KG", "DRM Code", "Notes"]

    for col_idx, header in enumerate(headers2, start=1):
        cell = ws2.cell(row=4, column=col_idx)
        cell.value = header
        cell.font = bold_font
        cell.fill = light_blue
        cell.alignment = center_align
        cell.border = thin_border

    # Rows 5-54: Auto-populated from Import Data Entry
    for row in range(5, 55):
        source_row = row + 16  # Maps to rows 21-70 on Sheet 1

        # Part # (A)
        ws2.cell(row=row, column=1).value = f"='Import Data Entry'!A{source_row}"

        # Description (B)
        ws2.cell(row=row, column=2).value = f"='Import Data Entry'!B{source_row}"

        # Quantity (M) (C) - Convert to thousands
        ws2.cell(row=row, column=3).value = f"='Import Data Entry'!C{source_row}/1000"
        ws2.cell(row=row, column=3).number_format = '0.000'

        # Net Weight (KG) (D)
        ws2.cell(row=row, column=4).value = f"='Import Data Entry'!D{source_row}"
        ws2.cell(row=row, column=4).number_format = '0.00'

        # Allocated Freight (E)
        ws2.cell(row=row, column=5).value = f"='Import Data Entry'!I{source_row}"
        ws2.cell(row=row, column=5).number_format = currency_format

        # Cost per M (F)
        ws2.cell(row=row, column=6).value = f"=IF(C{row}>0,E{row}/C{row},0)"
        ws2.cell(row=row, column=6).number_format = currency_format

        # Cost per Unit (G)
        ws2.cell(row=row, column=7).value = f"=IF(C{row}>0,E{row}/(C{row}*1000),0)"
        ws2.cell(row=row, column=7).number_format = '"$"0.000000'

        # Cost per KG (H)
        ws2.cell(row=row, column=8).value = f"=IF(D{row}>0,E{row}/(D{row}*C{row}*1000),0)"
        ws2.cell(row=row, column=8).number_format = '"$"0.000000'

        # DRM Code (I) - Manual input
        ws2.cell(row=row, column=9).fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

        # Notes (J) - Manual input
        ws2.cell(row=row, column=10).fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

    # Row 56: Totals
    ws2['A56'] = "TOTALS:"
    ws2['A56'].font = bold_font

    ws2['E56'] = "=SUM(E5:E54)"
    ws2['E56'].number_format = currency_format
    ws2['E56'].font = bold_font

    # Set column widths for Sheet 2
    ws2.column_dimensions['A'].width = 15
    ws2.column_dimensions['B'].width = 25
    ws2.column_dimensions['C'].width = 14
    ws2.column_dimensions['D'].width = 16
    ws2.column_dimensions['E'].width = 18
    ws2.column_dimensions['F'].width = 14
    ws2.column_dimensions['G'].width = 14
    ws2.column_dimensions['H'].width = 14
    ws2.column_dimensions['I'].width = 12
    ws2.column_dimensions['J'].width = 20

    # ========== SHEET 3: ERP Upload ==========
    print("Creating Sheet 3: ERP Upload...")

    ws3.merge_cells('A1:E1')
    ws3['A1'] = "ERP IMPORT TEMPLATE - DO NOT MODIFY HEADERS"
    ws3['A1'].font = red_font
    ws3['A1'].alignment = center_align

    # Row 2: Headers
    headers3 = ["Part_Number", "DRM_Code", "Freight_Cost_Per_M", "Freight_Cost_Per_Unit", "Entry_Number"]

    for col_idx, header in enumerate(headers3, start=1):
        cell = ws3.cell(row=2, column=col_idx)
        cell.value = header
        cell.font = bold_font
        cell.fill = light_blue
        cell.alignment = center_align
        cell.border = thin_border

    # Rows 3-52: Auto-populated from Freight Calculator
    for row in range(3, 53):
        source_row = row + 2  # Maps to rows 5-54 on Sheet 2

        # Part_Number (A)
        ws3.cell(row=row, column=1).value = f"='Freight Calculator'!A{source_row}"

        # DRM_Code (B)
        ws3.cell(row=row, column=2).value = f"='Freight Calculator'!I{source_row}"

        # Freight_Cost_Per_M (C)
        ws3.cell(row=row, column=3).value = f"=ROUND('Freight Calculator'!F{source_row},4)"
        ws3.cell(row=row, column=3).number_format = '0.0000'

        # Freight_Cost_Per_Unit (D)
        ws3.cell(row=row, column=4).value = f"=ROUND('Freight Calculator'!G{source_row},6)"
        ws3.cell(row=row, column=4).number_format = '0.000000'

        # Entry_Number (E)
        ws3.cell(row=row, column=5).value = "='Import Data Entry'!B3"

    # Set column widths for Sheet 3
    ws3.column_dimensions['A'].width = 18
    ws3.column_dimensions['B'].width = 15
    ws3.column_dimensions['C'].width = 22
    ws3.column_dimensions['D'].width = 24
    ws3.column_dimensions['E'].width = 18

    # ========== Named Ranges ==========
    print("Adding named ranges...")

    from openpyxl.workbook.defined_name import DefinedName

    # Create named ranges
    wb.defined_names['TotalFreight'] = DefinedName('TotalFreight', attr_text="'Import Data Entry'!$B$18")
    wb.defined_names['EntryNumber'] = DefinedName('EntryNumber', attr_text="'Import Data Entry'!$B$3")
    wb.defined_names['ValidationStatus'] = DefinedName('ValidationStatus', attr_text="'Import Data Entry'!$B$73")

    # ========== Add Example Data ==========
    print("Adding example data...")

    ws1['B3'] = "2024-001-ABC"
    ws1['B4'] = "01/15/2024"
    ws1['B5'] = "MSC DESTINY"
    ws1['B6'] = "FRT-2024-001"

    ws1['B8'] = 5000.00
    ws1['B9'] = 175.00
    ws1['B10'] = 85.00
    ws1['B11'] = 4500.00
    ws1['B12'] = 650.00
    ws1['B13'] = 425.00
    ws1['B14'] = 150.00

    # Example parts data
    example_parts = [
        ["PN-12345", "Widget Assembly A", 5000, 2.5, 10],
        ["PN-23456", "Bracket Mount B", 3000, 1.8, 6],
        ["PN-34567", "Cover Plate C", 8000, 0.9, 8],
        ["PN-45678", "Housing Unit D", 2500, 3.2, 5],
        ["PN-56789", "Connector E", 10000, 0.5, 12]
    ]

    for idx, part_data in enumerate(example_parts, start=21):
        ws1.cell(row=idx, column=1).value = part_data[0]  # Part #
        ws1.cell(row=idx, column=2).value = part_data[1]  # Description
        ws1.cell(row=idx, column=3).value = part_data[2]  # Quantity
        ws1.cell(row=idx, column=4).value = part_data[3]  # Net Weight
        ws1.cell(row=idx, column=5).value = part_data[4]  # # of Skids

    # Add example DRM codes in Sheet 2
    drm_codes = ["DRM-001", "DRM-002", "DRM-003", "DRM-004", "DRM-005"]
    for idx, drm in enumerate(drm_codes, start=5):
        ws2.cell(row=idx, column=9).value = drm

    # ========== Freeze Panes ==========
    print("Setting freeze panes...")
    ws1.freeze_panes = 'A21'
    ws2.freeze_panes = 'A5'
    ws3.freeze_panes = 'A3'

    # ========== Page Setup ==========
    print("Configuring print settings...")
    for ws in [ws1, ws2, ws3]:
        ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0

    # ========== Save Workbook ==========
    filename = "Die_Co_Freight_Calculator.xlsx"
    wb.save(filename)
    print(f"\n✓ Workbook '{filename}' created successfully!")
    print(f"  - Sheet 1: Import Data Entry (with example data)")
    print(f"  - Sheet 2: Freight Calculator")
    print(f"  - Sheet 3: ERP Upload")
    print(f"  - Named ranges: TotalFreight, EntryNumber, ValidationStatus")
    print(f"  - All formulas and formatting applied")

    return filename

if __name__ == "__main__":
    create_freight_calculator()
