# Quarto Presentation Template

This project provides a reusable presentation template for Quarto Reveal.js, based on Beamer design.

The template supports:

- Custom colors, logo, and slide layout.
- Consistent slide dimensions and content margins.
- Title slide with author, institution, and date.
- Automatic footer with author, presentation title, and page numbers.
- Automatic Table of Contents.
- HTML presentations with interactive navigation.
- PDF export with clickable Table of Contents and PDF bookmarks.

## 1. Required files

Every presentation must have the following files:

```text
MyPresentation/
│
├── presentation.qmd
├── presentation.html
├── texsx.css
├── footer.html
├── images_used.svg
├── clickablePDFs.py
│
└── README.md
```

### File descriptions

| File | Purpose |
|---|---|
| `presentation.qmd` | Main Quarto presentation containing YAML metadata and slide content |
| `texsx-jgu.css` | JGU presentation design, including colors, slide layout, headers, and cover |
| `footer.html` | Automatically generates the author, presentation title, and slide numbers in the footer |
| `jgu_logo_kasten.svg` | Official JGU university logo |
| `clickablePDFs.py` | Converts the rendered HTML presentation to PDF and adds clickable ToC links and bookmarks |
| `README.md` | Setup and usage instructions |

**Important:** The `.qmd`, `.css`, `.html` footer, and `.svg` logo must be correctly linked. The Python script is only required when generating a PDF.

## 2. Configure the Quarto presentation

Create a `presentation.qmd` file with the following YAML header:

```yaml
---
title: "Introduction to Git, GitHub, and GitLab"
subtitle: "Creating, cloning, and updating repositories"

author: "David Bustamante"
date: today
date-format: "MMMM D, YYYY"

toc: true
toc-location: body
number-sections: false

format:
  revealjs:
    theme: simple
    css: texsx-jgu.css
    include-after-body: footer.html
    slide-number: false
    center: false
    transition: none
    incremental: false
    width: 1280
    height: 720
    pdf-export: true
---
```

### YAML settings

| Setting | Purpose |
|---|---|
| `title` | Presentation title displayed on the cover and footer |
| `subtitle` | Subtitle displayed on the cover |
| `author` | Author displayed on the cover and footer |
| `date` | Presentation date |
| `date-format` | Controls how the date appears |
| `css` | Loads the custom JGU theme |
| `include-after-body` | Loads the JavaScript footer |
| `slide-number: false` | Disables default Reveal.js numbering; the custom footer handles numbering |
| `center: false` | Uses the fixed top-aligned content layout |
| `width` / `height` | Presentation canvas dimensions |
| `toc: true` | Creates a Table of Contents |
| `toc-location: body` | Places the Table of Contents within the presentation |
| `number-sections: true` | Numbers the section headings |

To disable the Table of Contents, change:

```yaml
toc: false
```

The CSS and footer can be reused for different presentations. Only the metadata and content in the `.qmd` need to change.

## 3. Create presentation slides

Use level-two Markdown headings (`##`) to create new slides.

Example:

```markdown
## Introduction

This is the first content slide.

## Data and Methods

This is the second content slide.

## Results

This is the third content slide.
```

Each heading creates a separate slide.

Use regular Markdown for text, lists, tables, code blocks, and mathematical expressions.

The JGU CSS controls the visual presentation independently of the amount of content on a slide.

However, very long content may still exceed the available space. Split lengthy sections across multiple slides.

## 4. Render the presentation to HTML

Open `presentation.qmd` in Positron or RStudio.

Click **Render**.

Quarto creates:

```text
presentation.html
```

Depending on Quarto's configuration, additional supporting files may be generated:

```text
presentation_files/
```

Keep the supporting files together with the HTML presentation.

Open the resulting HTML file in a browser to display the presentation.

The JGU theme, logo, author, title, and slide numbers should appear automatically.

## 5. Transform the HTML presentation into a PDF

The Python script `clickablePDFs.py` converts the Reveal.js HTML presentation to PDF and adds internal navigation links and PDF bookmarks.

### 5.1 Install the required Python packages

Open the terminal in Positron or RStudio.

Run:

```powershell
python -m pip install playwright pymupdf beautifulsoup4
```

Install the Chromium browser used by Playwright:

```powershell
python -m playwright install chromium
```

These installation steps are only required once per Python environment, unless an update requires reinstalling the browser.

### 5.2 Prepare the files

Ensure the rendered HTML file, its supporting assets, and the Python script are accessible.

Example:

```text
MyPresentation/
│
├── presentation.qmd
├── presentation.html
├── presentation_files/
│
├── texsx-jgu.css
├── footer.html
├── jgu_logo_kasten.svg
├── clickablePDFs.py
```

The HTML must already have been generated by Quarto.

### 5.3 Open the correct folder in the terminal

In Positron, open a PowerShell terminal.

Navigate to the presentation folder using:

```powershell
cd "PATH\TO\MyPresentation"
```

Alternatively, open the terminal directly in the folder containing the presentation.

### 5.4 Generate the PDF

Run:

```powershell
python clickablePDFs.py "NAME.html" -o "NAME.pdf"
```

Replace `NAME.html` with the actual filename of the rendered presentation and `NAME.pdf` with the desired output filename.

Example:

```powershell
python clickablePDFs.py "presentation.html" -o "presentation.pdf"
```

The script will:

1. Load the Reveal.js presentation using Chromium.
2. Activate the presentation's PDF print mode.
3. Export the slides while preserving the JGU design.
4. Check the generated PDF page count.
5. Add internal hyperlinks from the Table of Contents to the corresponding slides.
6. Add PDF bookmarks for section navigation.
7. Save the resulting PDF.

The script performs checks to avoid linking to incorrect pages if the PDF layout differs from the HTML presentation.

### 5.5 Verify the PDF

Open the generated PDF and check:

- The JGU logo and slide formatting are preserved.
- Every slide occupies a separate PDF page.
- The footer contains the correct author, title, and page number.
- The Table of Contents links navigate to their corresponding sections.
- PDF bookmarks appear in the PDF reader's navigation panel.

Some PDF readers require a click or Ctrl + Click to follow internal links.

## 6. Troubleshooting

### Python cannot find the HTML file

Verify that the rendered HTML file exists in the current directory:

```powershell
dir *.html
```

Run the script using its correct filename.

### PowerShell cannot find the Python script

Verify that `clickablePDFs.py` is in the current directory:

```powershell
dir *.py
```

Navigate to the correct folder or provide the full script path.

### Playwright cannot find Chromium

Run:

```powershell
python -m playwright install chromium
```

### PDF page count does not match the number of slides

Reveal.js may generate additional pages during printing.

The conversion script checks for this situation and may remove a verified blank trailing page.

If an extra page contains visible content, inspect the presentation's print layout rather than removing it blindly.

### JGU logo or styling is missing

Verify that:

- `texsx-jgu.css` is in the expected location.
- `jgu_logo_kasten.svg` is accessible relative to the CSS.
- The YAML references the correct stylesheet.
- The generated HTML can access all supporting assets.

### Footer is missing

Verify that the YAML contains:

```yaml
include-after-body: footer.html
```

Also verify that `footer.html` is available when Quarto renders the document.

### Table of Contents links are not clickable

Use the generated PDF from `clickablePDFs.py`, not a PDF exported manually through the browser.

Ensure the HTML presentation contains a Table of Contents and the script completes successfully.

## 7. Reusing the template for new presentations

To create another presentation:

1. Copy the template files into a new folder.
2. Create or edit the `.qmd` file.
3. Update the title, subtitle, author, and date.
4. Write the slide content using Markdown.
5. Click Render to generate the HTML.
6. Run `clickablePDFs.py` to generate the PDF.

The JGU theme and footer do not need to be rewritten for each presentation.

## 8. Recommended workflow

```text
Write presentation.qmd
         |
         v
Render with Quarto
         |
         v
presentation.html
         |
         v
python clickablePDFs.py
         |
         v
presentation.pdf
         |
         v
Clickable ToC + PDF bookmarks
```

**Result:** One Quarto source document can be used to produce both an interactive HTML presentation and a PDF version with internal navigation.
