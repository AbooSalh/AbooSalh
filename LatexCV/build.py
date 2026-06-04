#!/usr/bin/env python3
"""
build.py — LaTeX CV & Cover Letter Generator

Usage:
  python3 build.py all                  Build all profile CVs
  python3 build.py <profile>            Build one profile (e.g. siemens)
  python3 build.py list                 List available profiles + companies
  python3 build.py cover <company> <role> <profile>
                                         Generate cover letter for a company
  python3 build.py tailor --jd <text>   AI-tailor CV from job description
  python3 build.py tailor --jd-file <path>
                                         AI-tailor CV from job description file

Environment:
  GEMINI_API_KEY    Required for 'tailor' command (get from aistudio.google.com)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
TEMPLATES_DIR = os.path.join(HERE, "templates")
OUTPUT_DIR = os.path.join(HERE, "output")
CUSTOM_COMMANDS_PATH = "../custom-commands"

# ---------- helpers ----------

def info(msg):
    print(f"[INFO] {msg}")

def warn(msg):
    print(f"[WARN] {msg}")

def error(msg):
    print(f"[ERROR] {msg}")
    sys.exit(1)

def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_file(path):
    with open(path, "r") as f:
        return f.read()

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

def load_yaml(path):
    try:
        import yaml
    except ImportError:
        error("PyYAML is required. Install: pip install pyyaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)

def load_data():
    profile_path = os.path.join(DATA_DIR, "profile.yaml")
    companies_path = os.path.join(DATA_DIR, "companies.yaml")
    if not os.path.exists(profile_path):
        error(f"Profile data not found at {profile_path}")
    data = load_yaml(profile_path)

    companies = []
    if os.path.exists(companies_path):
        companies = load_yaml(companies_path)
    return data, companies

def profile_names(data):
    return [p["name"] for p in data.get("profiles", [])]

# ---------- LaTeX section generators ----------

def escape_tex(text):
    """Escape special LaTeX characters.
    Must escape # and & before any other processing since they're most common.
    """
    text = text.replace('#', r'\#')
    text = text.replace('&', r'\&')
    text = text.replace('%', r'\%')
    text = text.replace('_', r'\_')
    text = text.replace('<', r'\textless{}')
    text = text.replace('>', r'\textgreater{}')
    return text

def make_heading(data):
    p = data["personal"]
    links = []
    links.append(f"{p['phone']} \\quad | \\quad")
    links.append(f"\\href{{mailto:{p['email']}}}{{\\underline{{{p['email']}}}}} \\quad | \\quad")
    links.append(f"\\href{{{p['links']['linkedin']}}}{{\\underline{{{p['links']['linkedin'].replace('https://', '')}}}}} \\\\ \\vspace{{1pt}}")
    links.append(f"\\href{{{p['links']['github']}}}{{\\underline{{{p['links']['github'].replace('https://', '')}}}}} \\quad | \\quad")
    links.append(f"\\href{{{p['links']['website']}}}{{\\underline{{{p['links']['website'].replace('https://', '')}}}}}")

    return (
        "\\begin{center}\n"
        f"    \\textbf{{\\Huge \\scshape {p['name']}}} \\\\ \\vspace{{1pt}}\n"
        f"    {' '.join(links)}\n"
        "\\end{center}"
    )

def make_education(data, profile_name):
    edu = data["education"]
    coursework = edu.get("coursework", [])
    course_str = ", ".join(coursework)

    tex = "\\section{Education}\n"
    tex += "    \\resumeSubHeadingListStart\n\n"
    tex += "    \\resumeSubheading\n"
    tex += f"    {{{edu['institution']} | {edu['location']}}}{{Expected {edu['grad_year']}}}\n"

    show_gpa = profile_name in edu.get("show_gpa_profiles", [])
    if show_gpa:
        tex += f"    {{{edu['degree']}}}{{GPA: {edu['gpa']}}}\n"
    else:
        tex += f"    {{{edu['degree']}}}{{}}\n"

    tex += "    \\resumeItemListStart\n"
    tex += f"        \\resumeItem{{\\textbf{{Coursework:}} {escape_tex(course_str)}}}\n"

    # Per-profile activities in education section
    activities = edu.get("activities", {})
    if profile_name in activities:
        for act in activities[profile_name]:
            tex += f"        \\resumeItem{{\\textbf{{{escape_tex(act['org'])}}}: {escape_tex(act['description'])}}}\n"

    tex += "    \\resumeItemListEnd\n\n"
    tex += "    \\resumeSubHeadingListEnd"
    return tex

def make_experience(data, profile_name):
    """Generate LaTeX for work experience section."""
    entries = data.get("experience", [])
    tex = "\\resumeSubHeadingListStart\n\n"

    for entry in entries:
        # Find the variant for this profile
        variant = None
        for v in entry.get("variants", []):
            if profile_name in v.get("profiles", []):
                variant = v
                break
        if not variant:
            continue

        company = entry["company"]
        role = variant["role"]
        start = entry["start"]
        end = entry["end"]
        url = entry.get("url", "")

        url_part = f"\\href{{{url}}}{{\\underline{{{escape_tex(entry.get('display_url', company))}}}}}" if url else company

        tex += "\\resumeSubheading\n"
        tex += f"  {{{role}}}{{{start} -- {end}}}\n"
        tex += f"  {{{company}}}{{{url_part}}}\n"
        tex += "  \\resumeItemListStart\n"
        for bullet in variant.get("bullets", []):
            tex += f"    \\resumeItem{{{escape_tex(bullet)}}}\n"
        tex += "  \\resumeItemListEnd\n\n"

    tex += "\\resumeSubHeadingListEnd"
    return tex

def make_projects(data, profile_name):
    """Generate LaTeX for projects section."""
    entries = data.get("projects", [])

    # Filter to this profile
    profile_projects = [p for p in entries if profile_name in p.get("profiles", [])]
    if not profile_projects:
        return ""

    tex = "\\resumeSubHeadingListStart\n\n"
    for proj in profile_projects:
        display_url = proj.get("display_url", proj.get("url", ""))
        url_part = f"\\href{{{proj['url']}}}{{\\underline{{{display_url}}}}}" if proj.get("url") else ""
        heading = f"\\textbf{{{escape_tex(proj['name'])}}} $|$ \\emph{{{escape_tex(proj['tech'])}}}"
        separator = "}{\n" if url_part else "}{\n"
        tex += "\\resumeProjectHeading\n"
        tex += f"  {{{heading}}}{{{url_part}}}\n"
        tex += "  \\resumeItemListStart\n"
        for bullet in proj.get("bullets", []):
            tex += f"    \\resumeItem{{{escape_tex(bullet)}}}\n"
        tex += "  \\resumeItemListEnd\n\n"
    tex += "\\resumeSubHeadingListEnd"
    return tex

def make_skills_section(data, profile_name):
    """Generate LaTeX for skills. Returns just the skill lines (no wrapping)."""
    profile = None
    for p in data.get("profiles", []):
        if p["name"] == profile_name:
            profile = p
            break
    if not profile:
        return ""

    skills = profile.get("skills", {})
    lines = []
    for category, items in skills.items():
        lines.append(f"\\textbf{{{category}}}{{: {escape_tex(items)}}}")

    return " \\\\\n".join(lines)

def make_certifications(data):
    certs = data.get("certifications", [])
    if not certs:
        return ""
    lines = []
    for c in certs:
        lines.append(f"\\textbf{{{escape_tex(c['name'])}}}{{ — {escape_tex(c['issuer'])}}}")
    return " \\\\\n".join(lines)

def make_leadership(data, profile_name):
    entries = data.get("leadership", [])
    profile_entries = [e for e in entries if profile_name in e.get("profiles", [])]
    if not profile_entries:
        return ""

    tex = "\\section{Leadership}\n"
    tex += "\\resumeSubHeadingListStart\n\n"
    for entry in profile_entries:
        tex += "\\resumeSubheading\n"
        tex += f"  {{{entry['role']}}}{{{entry['start']} -- {entry['end']}}}\n"
        tex += f"  {{{entry['organization']}}}{{}}\n"
        tex += "  \\resumeItemListStart\n"
        for bullet in entry.get("bullets", []):
            tex += f"    \\resumeItem{{{escape_tex(bullet)}}}\n"
        tex += "  \\resumeItemListEnd\n\n"
    tex += "\\resumeSubHeadingListEnd"
    return tex

def make_achievements(data, profile_name):
    entries = data.get("achievements", [])
    profile_entries = [e for e in entries if profile_name in e.get("profiles", [])]
    if not profile_entries:
        return ""

    tex = "\\begin{itemize}[leftmargin=0.15in, label={}]\n"
    tex += "\\small{\\item{\n"
    parts = []
    for entry in profile_entries:
        if entry.get("url"):
            parts.append(f"\\textbf{{{escape_tex(entry['text'])}}}{{ — \\href{{{entry['url']}}}{{\\underline{{{entry['url']}}}}}}}")
        else:
            parts.append(f"\\textbf{{{escape_tex(entry['text'])}}}")
    tex += " \\\\\n".join(parts)
    tex += "\n}}\n"
    tex += "\\end{itemize}"
    return tex

def make_experience_section(data, profile_name):
    """Full work experience section with wrapping."""
    exp_content = make_experience(data, profile_name)
    if not exp_content.strip():
        return ""
    tex = "\\section{Work Experience}\n"
    tex += exp_content
    return tex

def make_projects_section(data, profile_name):
    """Full projects section with wrapping."""
    proj_content = make_projects(data, profile_name)
    if not proj_content.strip():
        return ""
    tex = "\\section{Projects}\n"
    tex += proj_content
    return tex

def make_leadership_section(data, profile_name):
    lead_content = make_leadership(data, profile_name)
    if not lead_content.strip():
        return ""
    return lead_content

def make_achievements_section(data, profile_name):
    ach_content = make_achievements(data, profile_name)
    if not ach_content.strip():
        return ""
    tex = "\\section{Achievements}\n"
    tex += ach_content
    return tex

# ---------- Resume generation ----------

def render_resume(profile_name, data, output_dir):
    """Generate a .tex file for a given profile and return the path."""
    ensure_output_dir()

    # Find profile config
    profile = None
    for p in data.get("profiles", []):
        if p["name"] == profile_name:
            profile = p
            break
    if not profile:
        error(f"Profile '{profile_name}' not found. Available: {', '.join(profile_names(data))}")

    # Read template
    template_path = os.path.join(TEMPLATES_DIR, "resume.tex.j2")
    if not os.path.exists(template_path):
        error(f"Template not found at {template_path}")
    template = read_file(template_path)

    # Generate each section
    heading = make_heading(data)
    summary = ""
    education = make_education(data, profile_name)
    experience = make_experience_section(data, profile_name)
    projects = make_projects_section(data, profile_name)
    skills = make_skills_section(data, profile_name)
    certifications = make_certifications(data)
    leadership = make_leadership_section(data, profile_name)
    achievements = make_achievements_section(data, profile_name)

    # Fill template
    replacements = {
        "<<LABEL>>": profile["label"],
        "<<PDF_TITLE>>": profile["pdf_title"],
        "<<PDF_SUBJECT>>": profile["pdf_subject"],
        "<<CUSTOM_COMMANDS_PATH>>": CUSTOM_COMMANDS_PATH,
        "<<HEADING>>": heading,
        "<<SUMMARY>>": summary,
        "<<EDUCATION>>": education,
        "<<EXPERIENCE>>": experience,
        "<<PROJECTS>>": projects,
        "<<SKILLS>>": skills,
        "<<CERTIFICATIONS>>": certifications,
        "<<LEADERSHIP>>": leadership,
        "<<ACHIEVEMENTS>>": achievements,
    }

    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)

    # Write .tex file
    tex_filename = f"resume-{profile_name}.tex"
    tex_path = os.path.join(output_dir, tex_filename)
    write_file(tex_path, template)
    info(f"Generated: {tex_path}")
    return tex_path

def compile_pdf(tex_path, output_dir=None):
    """Compile a .tex file to PDF using latexmk."""
    ensure_output_dir()
    tex_dir = os.path.dirname(tex_path)
    tex_basename = os.path.basename(tex_path)
    tex_name = os.path.splitext(tex_basename)[0]

    cmd = [
        "latexmk", "-pdf",
        "-output-directory=" + output_dir,
        tex_basename,
    ]

    result = subprocess.run(
        cmd,
        cwd=tex_dir,
        capture_output=True,
        text=True,
        timeout=60,
    )

    pdf_path = os.path.join(output_dir, tex_name + ".pdf")
    if os.path.exists(pdf_path):
        info(f"Compiled: {pdf_path}")
        return pdf_path
    else:
        warn(f"Compilation may have failed for {tex_path}")
        warn(result.stderr[-500:] if result.stderr else "No stderr output")
        return None

# ---------- Cover letter generation ----------

def render_cover_letter(company, role, profile_name, data, companies, body_paragraphs=None, output_dir=None):
    """Generate a cover letter .tex file and compile it."""
    ensure_output_dir()
    output_dir = output_dir or OUTPUT_DIR

    # Look up company in companies.yaml
    company_data = None
    for c in companies:
        if c["company"].lower() == company.lower() and c.get("profile") == profile_name:
            company_data = c
            break
    if not company_data:
        company_data = {"location": "", "hiring_manager": "Hiring Manager", "profile": profile_name}

    p = data["personal"]
    location = company_data.get("location", "")
    hiring_manager = company_data.get("hiring_manager", "Hiring Manager")
    github_display = p["links"]["github"].replace("https://", "")
    website_display = p["links"]["website"].replace("https://", "")

    safe_name = re.sub(r'[^a-zA-Z0-9-]', '-', f"{company}-{role}".lower())
    safe_name = re.sub(r'-+', '-', safe_name).strip('-')

    # Read template
    template_path = os.path.join(TEMPLATES_DIR, "cover.tex.j2")
    template = read_file(template_path)

    if body_paragraphs and len(body_paragraphs) >= 3:
        p1, p2, p3 = escape_tex(body_paragraphs[0]), escape_tex(body_paragraphs[1]), escape_tex(body_paragraphs[2])
    else:
        # Default body
        p1 = f"I am writing to apply for the \\textbf{{{escape_tex(role)}}} position at {company}. As a developer with experience building and deploying production systems, I am confident that my technical skills and problem-solving approach align well with the needs of your team."
        profile = None
        for prof in data.get("profiles", []):
            if prof["name"] == profile_name:
                profile = prof
                break

        summary_context = ""
        if profile:
            summary_context = f" My background as a {escape_tex(profile.get('label', 'developer'))} includes {escape_tex(profile.get('summary', ''))}"

        p2 = f"Most recently, I architected and deployed a multi-language tour booking platform serving 115 monthly active users across 6+ countries. I built the full observability stack with Prometheus and Grafana, implemented RBAC with JWT authentication, and automated CI/CD deployments.{summary_context}"
        p3 = f"I am excited about the opportunity to contribute to {company} and would welcome the chance to discuss how my background aligns with your needs."

    replacements = {
        "<<COMPANY>>": company,
        "<<ROLE>>": role,
        "<<NAME>>": p["name"],
        "<<PHONE>>": p["phone"],
        "<<EMAIL>>": p["email"],
        "<<GITHUB_URL>>": p["links"]["github"],
        "<<GITHUB_DISPLAY>>": github_display,
        "<<WEBSITE_URL>>": p["links"]["website"],
        "<<WEBSITE_DISPLAY>>": website_display,
        "<<HIRING_MANAGER>>": hiring_manager,
        "<<LOCATION>>": location,
        "<<BODY_PARAGRAPH_1>>": p1,
        "<<BODY_PARAGRAPH_2>>": p2,
        "<<BODY_PARAGRAPH_3>>": p3,
    }

    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)

    tex_filename = f"cover-{safe_name}.tex"
    tex_path = os.path.join(output_dir, tex_filename)
    write_file(tex_path, template)
    info(f"Generated: {tex_path}")

    # Compile
    pdf_path = compile_pdf(tex_path, output_dir=output_dir)
    return pdf_path

# ---------- AI Tailor ----------

def call_gemini(prompt, system_instruction=None):
    """Call Gemini API and return the response text."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        error(
            "GEMINI_API_KEY environment variable not set.\n"
            "Get a free API key at https://aistudio.google.com/\n"
            "Then: export GEMINI_API_KEY='your-key-here'"
        )

    try:
        import requests
    except ImportError:
        error("requests library required. Install: pip install requests")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    contents = [{"parts": [{"text": prompt}]}]

    payload = {
        "contents": contents,
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.3,
            "maxOutputTokens": 8192,
        }
    }

    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        return text
    except Exception as e:
        error(f"Gemini API call failed: {e}")

def build_tailor_prompt(data, jd_text, profile_name=None):
    """Build the prompt for AI tailoring."""
    profile_list = profile_names(data)

    # Serialize relevant data
    personal = data["personal"]
    education = data["education"]
    certs = data.get("certifications", [])
    projects = data.get("projects", [])
    leadership = data.get("leadership", [])
    achievements = data.get("achievements", [])
    experience = data.get("experience", [])

    # Build a concise representation of the candidate
    candidate_info = f"""
CANDIDATE NAME: {personal['name']}
EDUCATION: {education['degree']} at {education['institution']}, graduating {education['grad_year']}
COURSEWORK: {', '.join(education.get('coursework', []))}

PROFILES AVAILABLE: {', '.join(profile_list)}

EXPERIENCE:
"""
    for exp in experience:
        for v in exp.get("variants", []):
            candidate_info += f"\n  Role: {v['role']} at {exp['company']} ({exp['start']} - {exp['end']})"
            candidate_info += f"\n  Profiles: {', '.join(v['profiles'])}"
            for b in v.get("bullets", []):
                candidate_info += f"\n    - {b}"
            candidate_info += "\n"

    candidate_info += "\nPROJECTS:\n"
    for proj in projects:
        candidate_info += f"\n  {proj['name']} ({proj['tech']})"
        candidate_info += f"\n  Profiles: {', '.join(proj.get('profiles', []))}"
        for b in proj.get("bullets", []):
            candidate_info += f"\n    - {b}"

    candidate_info += "\n\nCERTIFICATIONS:\n"
    for c in certs:
        candidate_info += f"  - {c['name']} ({c['issuer']})\n"

    candidate_info += "\nSKILLS PER PROFILE:\n"
    for prof in data.get("profiles", []):
        candidate_info += f"\n  {prof['name']}:\n"
        candidate_info += f"    Summary: {prof.get('summary', '')}\n"
        for cat, skills in prof.get("skills", {}).items():
            candidate_info += f"    {cat}: {skills}\n"

    candidate_info += "\nLEADERSHIP:\n"
    for lead in leadership:
        candidate_info += f"  {lead['role']} at {lead['organization']} ({lead['start']} - {lead['end']})\n"
        for b in lead.get("bullets", []):
            candidate_info += f"    - {b}\n"

    profile_instruction = ""
    if profile_name:
        profile_instruction = f"\nUse the profile '{profile_name}' as the base and tailor from there."

    prompt = f"""
You are an expert resume tailor and cover letter writer. Your task is to customize a candidate's resume and generate a cover letter based on a job description.

RULES:
- Select only the MOST RELEVANT experience, projects, and skills for this specific job
- Rewrite bullet points to use active voice, past tense, and MATCH THE JOB DESCRIPTION's terminology and keywords
- Quantify achievements when possible (metrics, numbers)
- NEVER fabricate experience, skills, or qualifications
- Keep the education section unchanged
- Keep certifications unchanged
- Choose the best profile from the available profiles that matches the job
- Return ONLY valid JSON matching the schema below - no other text

JSON SCHEMA:
{{
  "profile_name": "the name of the best-matching profile from the available profiles",
  "summary": "2-3 sentence tailored summary rewritten for this specific job",
  "experience": [
    {{
      "company": "Company Name",
      "role": "Role Title",
      "bullets": ["rewritten bullet 1", "rewritten bullet 2", ...]
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "tech": "Technologies",
      "bullets": ["rewritten bullet 1", ...]
    }}
  ],
  "skills": {{
    "category1": "skill text reordered to highlight job-relevant skills first",
    "category2": "skill text ..."
  }},
  "cover_letter": {{
    "body_paragraphs": [
      "Paragraph 1: Introduction — who you are, what role you're applying for, why you're a great fit (2-3 sentences)",
      "Paragraph 2: Relevant experience and achievements aligned with the job requirements (3-4 sentences)",
      "Paragraph 3: Why this company/team interests you and a closing statement (2-3 sentences)"
    ]
  }}
}}
{profile_instruction}

CANDIDATE DATA:
{candidate_info}

JOB DESCRIPTION:
{jd_text}
"""
    return prompt

def parse_tailor_response(response_text):
    """Parse the JSON response from Gemini."""
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        import re
        match = re.search(r'```(?:json)?\s*\n(.*?)\n```', response_text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        error(f"Failed to parse Gemini response as JSON. Response:\n{response_text[:500]}")

def build_tailored_resume(result, data, output_dir):
    """Build a tailored resume from AI result, then compile."""
    profile_name = result.get("profile_name")
    if not profile_name:
        profile_name = profile_names(data)[0]

    # Find the original profile (to preserve pdf_title etc)
    original_profile = None
    for p in data.get("profiles", []):
        if p["name"] == profile_name:
            original_profile = p
            break

    if original_profile:
        # Merge AI results into the profile
        original_profile["summary"] = result.get("summary", original_profile["summary"])
        if "skills" in result:
            original_profile["skills"] = result["skills"]

    # Build modified data with AI-selected experience/projects
    modified_data = dict(data)

    # Replace experience with AI-tailored version
    if "experience" in result:
        modified_experience = []
        for exp_entry in result["experience"]:
            # Find matching original entry to preserve URLs etc
            matched = False
            for orig_exp in data.get("experience", []):
                for v in orig_exp.get("variants", []):
                    if v["role"] == exp_entry["role"] or exp_entry.get("company") == orig_exp["company"]:
                        modified_experience.append({
                            "company": orig_exp["company"],
                            "url": orig_exp.get("url", ""),
                            "start": orig_exp["start"],
                            "end": orig_exp["end"],
                            "variants": [{
                                "role": exp_entry["role"],
                                "profiles": [profile_name],
                                "bullets": exp_entry["bullets"],
                            }]
                        })
                        matched = True
                        break
                if matched:
                    break
            if not matched:
                # Add as new entry
                modified_experience.append({
                    "company": exp_entry.get("company", ""),
                    "role": exp_entry.get("role", ""),
                    "start": "",
                    "end": "",
                    "variants": [{
                        "role": exp_entry.get("role", ""),
                        "profiles": [profile_name],
                        "bullets": exp_entry.get("bullets", []),
                    }]
                })
        modified_data["experience"] = modified_experience

    # Replace projects with AI-tailored version
    if "projects" in result:
        modified_projects = []
        for proj_entry in result["projects"]:
            for orig_proj in data.get("projects", []):
                if orig_proj["name"] == proj_entry["name"]:
                    modified_projects.append({
                        "name": proj_entry["name"],
                        "url": orig_proj["url"],
                        "display_url": orig_proj.get("display_url", ""),
                        "tech": proj_entry.get("tech", orig_proj["tech"]),
                        "profiles": [profile_name],
                        "bullets": proj_entry["bullets"],
                    })
        modified_data["projects"] = modified_projects

    # Rename output to include -tailored suffix
    tex_path = render_resume(profile_name, modified_data, output_dir)
    tailored_tex_path = tex_path.replace(".tex", "-tailored.tex")
    os.rename(tex_path, tailored_tex_path)

    pdf_path = compile_pdf(tailored_tex_path, output_dir=OUTPUT_DIR)
    return pdf_path, result.get("cover_letter", {}).get("body_paragraphs", [])

# ---------- CLI ----------

def cmd_list(data, companies):
    profiles = profile_names(data)
    print("Available profiles:")
    for p in profiles:
        print(f"  - {p}")
    print()
    print("Target companies (for cover letters):")
    for c in companies:
        print(f"  - {c['company']} ({c.get('role', '')}) -> profile: {c.get('profile', '?')}")
    print()

def cmd_build(args, data, companies):
    ensure_output_dir()
    profile_name = args.profile

    if profile_name not in profile_names(data):
        error(f"Unknown profile '{profile_name}'. Use 'list' to see available profiles.")

    tex_path = render_resume(profile_name, data, OUTPUT_DIR)
    compile_pdf(tex_path, output_dir=OUTPUT_DIR)

def cmd_all(data, companies):
    ensure_output_dir()
    for profile_name in profile_names(data):
        info(f"Building profile: {profile_name}")
        tex_path = render_resume(profile_name, data, OUTPUT_DIR)
        compile_pdf(tex_path, output_dir=OUTPUT_DIR)
    info("All profiles built.")

def cmd_cover(args, data, companies):
    ensure_output_dir()
    company = args.company
    role = args.role
    profile_name = args.profile

    render_cover_letter(company, role, profile_name, data, companies, output_dir=OUTPUT_DIR)

def cmd_tailor(args, data, companies):
    ensure_output_dir()
    jd_text = args.jd or ""
    if args.jd_file:
        with open(args.jd_file, "r") as f:
            jd_text = f.read()

    if not jd_text.strip():
        error("No job description provided. Use --jd or --jd-file.")

    system_prompt = (
        "You are an expert resume tailor and cover letter writer. "
        "You return ONLY valid JSON that matches the requested schema. "
        "You never fabricate information."
    )

    prompt = build_tailor_prompt(data, jd_text, profile_name=args.profile)
    info("Calling Gemini API (may take 10-20 seconds)...")
    response = call_gemini(prompt, system_instruction=system_prompt)
    result = parse_tailor_response(response)

    if not result.get("profile_name"):
        # If AI didn't pick one, use user's hint or first profile
        result["profile_name"] = args.profile or profile_names(data)[0]

    info(f"AI selected profile: {result.get('profile_name')}")
    info(f"AI summary: {result.get('summary', '')[:100]}...")
    info("Building tailored CV...")

    pdf_path, cover_body = build_tailored_resume(result, data, OUTPUT_DIR)

    # Also generate a cover letter if body paragraphs provided
    company = args.company or result.get("profile_name", "").capitalize()
    role = args.role or "Position"
    profile_name = result.get("profile_name", args.profile or profile_names(data)[0])

    if cover_body:
        render_cover_letter(company, role, profile_name, data, companies,
                           body_paragraphs=cover_body, output_dir=OUTPUT_DIR)

    # Save the tailored data JSON
    result_path = os.path.join(OUTPUT_DIR, f"tailored-{profile_name}.json")
    write_file(result_path, json.dumps(result, indent=2))
    info(f"Tailored data saved: {result_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Build LaTeX CVs and cover letters with optional AI tailoring",
        usage="%(prog)s [command|profile] [options]\n\n"
              "Commands:\n"
              "  all                          Build all profile CVs\n"
              "  list                         List profiles and companies\n"
              "  <profile>                    Build one profile (e.g. siemens)\n"
              "  cover COMPANY ROLE PROFILE   Generate cover letter\n"
              "  tailor --jd-file <file>      AI-tailor CV from job description"
    )

    parser.add_argument("command", nargs="?", help="Command or profile name")
    parser.add_argument("args", nargs="*", help="Additional arguments")

    parser.add_argument("--jd", help="Job description text (for tailor)")
    parser.add_argument("--jd-file", help="File containing job description (for tailor)")
    parser.add_argument("--profile", help="Profile hint (for tailor)")
    parser.add_argument("--company", help="Company name (for tailor cover letter)")
    parser.add_argument("--role", help="Role title (for tailor cover letter)")

    parsed, unknown = parser.parse_known_args()
    # Collect any extra positional args that weren't consumed
    extra_args = parsed.args[:]
    if unknown:
        extra_args.extend(unknown)

    # Load data
    data, companies = load_data()
    profiles = profile_names(data)

    cmd = parsed.command

    if cmd == "list":
        cmd_list(data, companies)
    elif cmd == "all":
        cmd_all(data, companies)
    elif cmd == "cover":
        if len(extra_args) < 3:
            error("Usage: build.py cover COMPANY ROLE PROFILE")
        cmd_cover_args = argparse.Namespace(
            company=extra_args[0],
            role=extra_args[1],
            profile=extra_args[2],
        )
        cmd_cover(cmd_cover_args, data, companies)
    elif cmd == "tailor":
        args = argparse.Namespace(
            jd=parsed.jd,
            jd_file=parsed.jd_file,
            profile=parsed.profile,
            company=parsed.company,
            role=parsed.role,
        )
        cmd_tailor(args, data, companies)
    elif cmd in profiles:
        args = argparse.Namespace(profile=cmd)
        cmd_build(args, data, companies)
    else:
        parser.print_help()
        if cmd:
            warn(f"Unknown command or profile: '{cmd}'")

if __name__ == "__main__":
    main()
