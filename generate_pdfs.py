import os
import re
import subprocess
from markdown_it import MarkdownIt

def get_page_count(pdf_path: str) -> int:
    with open(pdf_path, 'rb') as f:
        data = f.read()
    pages = re.findall(rb'/Type\s*/Page(?![a-zA-Z])', data)
    return len(pages)

def run_headless_print(html_path: str, pdf_path: str):
    chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    browser = chrome_path if os.path.exists(chrome_path) else edge_path

    abs_html = os.path.abspath(html_path).replace('\\', '/')
    abs_pdf = os.path.abspath(pdf_path)

    cmd = [
        browser,
        '--headless',
        '--disable-gpu',
        '--no-pdf-header-footer',
        f'--print-to-pdf={abs_pdf}',
        f'file:///{abs_html}'
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def generate_evaluation_writeup():
    print("Generating evaluation_writeup.pdf (Target: 1 page)...")
    md = MarkdownIt('commonmark').enable('table')
    with open('evaluation_writeup.md', encoding='utf-8') as f:
        text = f.read()
    
    body_html = md.render(text)

    css = """
    @page {
        size: A4 portrait;
        margin: 8mm 14mm 8mm 14mm;
    }
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-size: 8.8pt;
        line-height: 1.30;
        color: #1a202c;
    }
    h1 {
        font-size: 13.5pt;
        font-weight: 700;
        color: #0f172a;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 3px;
        margin-bottom: 5px;
    }
    h2 {
        font-size: 9.8pt;
        font-weight: 700;
        color: #1e3a8a;
        border-bottom: 1px solid #cbd5e1;
        padding-bottom: 1px;
        margin-top: 6px;
        margin-bottom: 3px;
    }
    p {
        margin: 2px 0 3px 0;
    }
    ul, ol {
        margin: 2px 0 3px 0;
        padding-left: 17px;
    }
    li {
        margin-bottom: 2px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 4px 0 5px 0;
        font-size: 8.2pt;
    }
    th, td {
        border: 1px solid #cbd5e1;
        padding: 3px 6px;
        text-align: left;
    }
    th {
        background-color: #f1f5f9;
        font-weight: 600;
        color: #0f172a;
    }
    code {
        font-family: Consolas, 'Courier New', monospace;
        font-size: 8pt;
        background: #f1f5f9;
        padding: 1px 3px;
        border-radius: 2px;
        color: #0f172a;
    }
    strong {
        color: #0f172a;
    }
    """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Evaluation Writeup</title>
<style>{css}</style>
</head>
<body>
{body_html}
</body>
</html>"""

    html_file = 'temp_evaluation_writeup.html'
    pdf_file = 'evaluation_writeup.pdf'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    run_headless_print(html_file, pdf_file)
    count = get_page_count(pdf_file)
    if os.path.exists(html_file):
        os.remove(html_file)
    print(f"evaluation_writeup.pdf: {count} page(s)")
    return count

def generate_design_note():
    print("Generating design_note.pdf (Target: 2 pages)...")
    md = MarkdownIt('commonmark').enable('table')
    with open('design_note.md', encoding='utf-8') as f:
        text = f.read()
    
    parts = text.split('\n---\n')
    
    html_parts = []
    for part in parts:
        rendered = md.render(part)
        html_parts.append(rendered)

    body_html = f"""
    <div class="page-1">
        {html_parts[0]}
    </div>
    <div class="page-break"></div>
    <div class="page-2">
        {html_parts[1]}
        <hr class="section-divider">
        {html_parts[2]}
    </div>
    """

    css = """
    @page {
        size: A4 portrait;
        margin: 14mm 16mm 14mm 16mm;
    }
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-size: 9.6pt;
        line-height: 1.38;
        color: #1a202c;
    }
    .page-break {
        page-break-before: always;
        break-before: page;
    }
    h1 {
        font-size: 15.5pt;
        font-weight: 700;
        color: #0f172a;
        border-bottom: 2.5px solid #2563eb;
        padding-bottom: 4px;
        margin-bottom: 8px;
    }
    h2 {
        font-size: 11.5pt;
        font-weight: 700;
        color: #1e3a8a;
        border-bottom: 1px solid #cbd5e1;
        padding-bottom: 2px;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    h3 {
        font-size: 10pt;
        font-weight: 600;
        color: #0284c7;
        margin-top: 8px;
        margin-bottom: 4px;
    }
    p {
        margin: 4px 0 5px 0;
    }
    ul, ol {
        margin: 4px 0 6px 0;
        padding-left: 20px;
    }
    li {
        margin-bottom: 3.5px;
    }
    .section-divider {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 10px 0;
    }
    code {
        font-family: Consolas, 'Courier New', monospace;
        font-size: 8.6pt;
        background: #f1f5f9;
        padding: 1.5px 3.5px;
        border-radius: 3px;
        color: #0f172a;
        border: 1px solid #e2e8f0;
    }
    blockquote {
        margin: 6px 0;
        padding: 4px 10px;
        background: #f8fafc;
        border-left: 3px solid #3b82f6;
        color: #334155;
        font-style: italic;
    }
    strong {
        color: #0f172a;
    }
    """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Design Note — HTB Cheatsheet Assistant</title>
<style>{css}</style>
</head>
<body>
{body_html}
</body>
</html>"""

    html_file = 'temp_design_note.html'
    pdf_file = 'design_note.pdf'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    run_headless_print(html_file, pdf_file)
    count = get_page_count(pdf_file)
    if os.path.exists(html_file):
        os.remove(html_file)
    print(f"design_note.pdf: {count} page(s)")
    return count

def generate_test_set_answer_key():
    print("Generating test_set_answer_key.pdf (Target: 14-15 pages)...")
    md = MarkdownIt('commonmark').enable('table')
    with open('test_set_answer_key.md', encoding='utf-8') as f:
        text = f.read()

    # Split into sections
    parts = re.split(r'\n(?=### Q\d+:)', text)
    preamble = parts[0]
    questions = parts[1:]

    # Let's inspect pages
    # We want 14-15 pages total.
    # Page 1: Preamble (Overview, Protocol, Table)
    # Then we have 15 questions.
    # If we put:
    # Page 1: Preamble
    # Page 2: Q1
    # Page 3: Q2
    # Page 4: Q3
    # Page 5: Q4
    # Page 6: Q5
    # Page 7: Q6
    # Page 8: Q7
    # Page 9: Q8
    # Page 10: Q9
    # Page 11: Q10
    # Page 12: Q11
    # Page 13: Q12
    # Page 14: Q13
    # Page 15: Q14 & Q15
    # That gives exactly 15 pages.
    # Or if Q7 & Q8 are combined and Q14 & Q15 are combined, that gives exactly 14 pages!
    
    pages_content = []
    pages_content.append(preamble)
    for q in questions[:13]:
        pages_content.append(q)
    # Combine Q14 & Q15
    pages_content.append(questions[13] + "\n\n---\n\n" + questions[14])

    rendered_pages = []
    for i, p_text in enumerate(pages_content):
        # In ground-truth machine lists, wrap them nicely
        p_html = md.render(p_text)
        rendered_pages.append(f'<div class="doc-page">{p_html}</div>')

    css = """
    @page {
        size: A4 portrait;
        margin: 10mm 14mm 10mm 14mm;
    }
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-size: 8.5pt;
        line-height: 1.30;
        color: #1e293b;
    }
    .doc-page {
        page-break-after: always;
        break-after: page;
    }
    .doc-page:last-child {
        page-break-after: auto;
        break-after: auto;
    }
    h1 {
        font-size: 13.5pt;
        font-weight: 700;
        color: #0f172a;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 3px;
        margin-bottom: 5px;
    }
    h2 {
        font-size: 10.5pt;
        font-weight: 700;
        color: #1e3a8a;
        border-bottom: 1px solid #cbd5e1;
        padding-bottom: 2px;
        margin-top: 6px;
        margin-bottom: 3px;
    }
    h3 {
        font-size: 10pt;
        font-weight: 700;
        color: #0369a1;
        margin-top: 5px;
        margin-bottom: 3px;
        border-bottom: 1px solid #e0f2fe;
        padding-bottom: 2px;
    }
    p {
        margin: 2.5px 0 3px 0;
    }
    ul, ol {
        margin: 2.5px 0 3px 0;
        padding-left: 17px;
    }
    li {
        margin-bottom: 2px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 5px 0;
        font-size: 8pt;
    }
    th, td {
        border: 1px solid #cbd5e1;
        padding: 3px 5px;
        text-align: left;
    }
    th {
        background-color: #f1f5f9;
        font-weight: 600;
    }
    code {
        font-family: Consolas, 'Courier New', monospace;
        font-size: 7.8pt;
        background: #f8fafc;
        padding: 0.5px 2.5px;
        border-radius: 2px;
        color: #0f172a;
        border: 1px solid #e2e8f0;
        word-break: break-all;
    }
    blockquote {
        margin: 3px 0;
        padding: 3px 7px;
        background: #f8fafc;
        border-left: 3px solid #3b82f6;
        color: #475569;
        font-size: 8.2pt;
    }
    pre {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 3px 5px;
        border-radius: 2px;
        margin: 3px 0;
        font-size: 7.8pt;
        white-space: pre-wrap;
        word-break: break-all;
    }
    hr {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 6px 0;
    }
    """

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Test Set & Hand-Derived Answer Key</title>
<style>{css}</style>
</head>
<body>
{''.join(rendered_pages)}
</body>
</html>"""

    html_file = 'temp_test_set_answer_key.html'
    pdf_file = 'test_set_answer_key.pdf'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    run_headless_print(html_file, pdf_file)
    count = get_page_count(pdf_file)
    if os.path.exists(html_file):
        os.remove(html_file)
    print(f"test_set_answer_key.pdf: {count} page(s)")
    return count

if __name__ == '__main__':
    c1 = generate_evaluation_writeup()
    c2 = generate_design_note()
    c3 = generate_test_set_answer_key()
    print("\n--- Summary ---")
    print(f"evaluation_writeup.pdf: {c1} page(s)")
    print(f"design_note.pdf: {c2} page(s)")
    print(f"test_set_answer_key.pdf: {c3} page(s)")
