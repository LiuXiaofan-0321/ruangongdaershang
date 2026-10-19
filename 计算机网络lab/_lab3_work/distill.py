from pathlib import Path
import hashlib,json
from docx import Document
W=Path(__file__).resolve().parent
ref=W/'template.docx'
d=Document(ref);s=d.sections[0]
sha=hashlib.sha256(ref.read_bytes()).hexdigest()
contract=f'''# Lab3 template contract

Reference: {ref}
SHA-256: {sha}
Reference render: template_word.pdf and template-1.png, one page inspected.
Evidence: template_style.json, template_parts.json, source section audit.
Original school .doc is retained unchanged. template.docx is a read-only conversion.

## Page system
One portrait A4 section, width {s.page_width.cm:.6f} cm, height {s.page_height.cm:.6f} cm.
Margins: top {s.top_margin.cm:.6f}, bottom {s.bottom_margin.cm:.6f}, left {s.left_margin.cm:.6f}, right {s.right_margin.cm:.6f} cm.
Header distance {s.header_distance.cm:.6f}, footer distance {s.footer_distance.cm:.6f} cm.
Same header/footer on all pages; no first/odd/even variation. Preserve sectPr and all source header/footer XML.

## Typography and components
Source title: centered 16 pt bold black, 1.3 line spacing, after 6 pt; use Title style with the source direct properties.
Source major headings: 12 pt bold black, before/after 3 pt, left aligned.
Body roles: source Chinese first-line-indent paragraph pattern, 12 pt regular black, 1.3 line spacing, 2-character indent.
Source placeholder red and instructional wording are editable; remove red from all completed slots.
Latin: Times New Roman. Body Chinese: SimSun. Bold Chinese roles: Microsoft YaHei with a real bold face, preserving source sizes and geometry; chosen under the user's permission to reference Lab2 and the requested cua-win font workflow.
Keep school title, metadata block, six sections in order, top metadata separator, header and PAGE/NUMPAGES fields.
Tables/figures may be added within body slots as required for Lab3; use black/gray rules, readable captions and no ornamental blocks.

## Slot map and stable locators
word/document.xml body p[0]: school title, preserve wording.
body tbl[0]: metadata, 3 rows x 3 columns. r0c0 course preserve; r0c1 2024 grade; r0c2 result blank.
r1c0 IPv4 experiment; r1c1 Liu Xiaofan; r1c2 actual experiment date 2026-10-13.
r2c0 Lab3; r2c1 student 10244602411; r2c2 duration preserve 2 periods.
body heading paragraphs with exact six school section labels: preserve labels and order.
Each subsequent red instruction paragraph: replace with the corresponding purpose/procedure/environment/analysis/conclusions/appendix.
Body slots have no fixed page capacity and may expand by cloning the body/heading component; add no sections.
Metadata floating positioning may be converted to inline only if it overlaps expanded content, preserving widths and placement on page 1; log and verify visually.

## Package preservation
Inventory baseline in template_parts.json. Preserve all styles, theme, numbering, fontTable, headers, footers, customXml and unrelated relationships.
Editable parts: word/document.xml; styles only for Title/source role adjustments; settings for updateFields; document relationships and media for figures; core properties for actual author/title.
All other source parts must remain byte-identical after final packaging. Preserve all existing drawing relationships.

## Fidelity gates
Same one section and exact geometry. School header/footer and metadata content order remain recognizable.
All six sections filled; no placeholder guidance remains. All figures numbered and captioned.
Native Word PDF export plus every page PNG inspection is the render gate. Packaged render_docx.py was attempted; its log reports missing soffice.exe, so no system LibreOffice is used.
Inspect all final pages for clipping, table splits, missing glyphs, stray blank pages, caption separation and excessive gaps.
Compare all preserve-only source ZIP parts byte for byte and preserve original reference SHA.
'''
(W/'artifact.md').write_text(contract,encoding='utf-8')
print(sha)
