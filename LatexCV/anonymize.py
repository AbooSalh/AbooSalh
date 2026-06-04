#!/usr/bin/env python3
"""Generate an anonymized copy of the resume for public review."""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from build import render_resume, compile_pdf, load_data, OUTPUT_DIR

data, _ = load_data()

original_name = data["personal"]["name"]
original_phone = data["personal"]["phone"]
original_email = data["personal"]["email"]
original_linkedin = data["personal"]["links"]["linkedin"]
original_github = data["personal"]["links"]["github"]
original_website = data["personal"]["links"]["website"]

profile_name = sys.argv[1] if len(sys.argv) > 1 else "fullstack"

tex_path = render_resume(profile_name, data, OUTPUT_DIR)
tex_content = open(tex_path).read()

# Find the profile label to use in heading and metadata
profile = None
for p in data.get("profiles", []):
    if p["name"] == profile_name:
        profile = p
        break
profile_label = profile["label"] if profile else "Developer"

# Replace PDF metadata
tex_content = tex_content.replace(
    f"pdftitle={{{profile['pdf_title']}}}",
    "pdftitle={Anonymized Resume}"
)

# Replace the heading block with anonymized version
heading_pattern = re.compile(
    r'\\begin\{center\}\s*\\textbf\{\\Huge \\scshape [^}]+\}.*?\\end\{center\}',
    re.DOTALL
)
anon_heading = (
    "\\begin{center}\n"
    f"    \\textbf{{\\Huge \\scshape {profile_label}}} \\\\ \\vspace{{1pt}}\n"
    "\\end{center}"
)
tex_content = heading_pattern.sub(lambda m: anon_heading, tex_content)

# Also replace any stray occurrences of identifying info in the body
tex_content = tex_content.replace(original_name, "[NAME REMOVED]")
tex_content = tex_content.replace(original_phone, "[PHONE REMOVED]")
tex_content = tex_content.replace(original_email, "[EMAIL REMOVED]")
tex_content = tex_content.replace(original_linkedin, "[LINKEDIN REMOVED]")
tex_content = tex_content.replace(original_github, "[GITHUB REMOVED]")
tex_content = tex_content.replace(original_website, "[WEBSITE REMOVED]")
tex_content = tex_content.replace("abosaleh.site", "[WEBSITE REMOVED]")
tex_content = tex_content.replace("AbooSalh", "[USERNAME REMOVED]")

# Write anonymized .tex
anon_tex_path = tex_path.replace(".tex", "-anon.tex")
with open(anon_tex_path, "w") as f:
    f.write(tex_content)

pdf_path = compile_pdf(anon_tex_path, output_dir=OUTPUT_DIR)
if pdf_path:
    print(f"Anonymized resume: {pdf_path}")
else:
    print("Compilation failed")
    sys.exit(1)
