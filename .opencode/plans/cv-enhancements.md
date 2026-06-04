# CV Enhancement Plan

## Step 1: Per-profile experience files

### src/backend/experience.tex
```latex
%-----------WORK EXPERIENCE-----------%
\section{Work Experience}
\resumeSubHeadingListStart

\resumeSubheading
  {Backend Developer}{Jan 2025 -- Present}
  {Paradise Sharm Tours}{\href{https://paradisesharm.com}{\underline{paradisesharm.com}}}
  \resumeItemListStart
    \resumeItem{Architected and deployed a multi-language tour booking platform using Express.js, MongoDB, and Traefik with automated SSL/TLS, serving 115 monthly active users across 6+ countries}
    \resumeItem{Built observability stack with Prometheus, Grafana, and k6 stress testing (up to 220 concurrent VUs, 2-hour soak tests) for production monitoring and capacity planning}
    \resumeItem{Implemented RBAC with JWT refresh tokens, rate limiting, input validation, and automated daily MongoDB backups with 7-day retention to ensure data security and system reliability}
  \resumeItemListEnd

\resumeSubHeadingListEnd
```

### src/frontend/experience.tex
```latex
%-----------WORK EXPERIENCE-----------%
\section{Work Experience}
\resumeSubHeadingListStart

\resumeSubheading
  {Frontend Developer}{Jan 2025 -- Present}
  {Paradise Sharm Tours}{\href{https://paradisesharm.com}{\underline{paradisesharm.com}}}
  \resumeItemListStart
    \resumeItem{Built a multi-language (EN/AR/RU/DE/IT) tour booking interface with Next.js, React Query, TailwindCSS, and Framer Motion, serving 115 monthly active users with SSR/SSG and i18n routing}
    \resumeItem{Optimized frontend to achieve 91 Performance, 100 Accessibility, and 92 Best Practices Lighthouse scores with 0.9s FCP and 0 cumulative layout shift}
    \resumeItem{Integrated Google Analytics, PostHog, and Plerdy for user behavior tracking across 289 users, driving data-informed UI/UX improvements}
  \resumeItemListEnd

\resumeSubHeadingListEnd
```

### src/dotnet/experience.tex
```latex
%-----------WORK EXPERIENCE-----------%
\section{Work Experience}
\resumeSubHeadingListStart

\resumeSubheading
  {Full-Stack Developer}{Jan 2025 -- Present}
  {Paradise Sharm Tours}{\href{https://paradisesharm.com}{\underline{paradisesharm.com}}}
  \resumeItemListStart
    \resumeItem{Architected and deployed a multi-language tour booking platform using Next.js, Express.js, MongoDB, and Traefik with automated SSL/TLS, serving 115 monthly active users across 6+ countries}
    \resumeItem{Built observability stack with Prometheus, Grafana, and k6 stress testing (up to 220 concurrent VUs, 2-hour soak tests) for production monitoring and performance benchmarking}
    \resumeItem{Implemented RBAC with JWT refresh tokens, rate limiting, and automated daily MongoDB backups with 7-day retention; achieved 91 Lighthouse Performance and 100 Accessibility scores}
  \resumeItemListEnd

\resumeSubHeadingListEnd
```

### src/nodejs/experience.tex
```latex
%-----------WORK EXPERIENCE-----------%
\section{Work Experience}
\resumeSubHeadingListStart

\resumeSubheading
  {Node.js Developer}{Jan 2025 -- Present}
  {Paradise Sharm Tours}{\href{https://paradisesharm.com}{\underline{paradisesharm.com}}}
  \resumeItemListStart
    \resumeItem{Architected and deployed a multi-language tour booking platform with Express.js, MongoDB, and Traefik reverse proxy with automated SSL/TLS, serving 115 monthly active users across 6+ countries}
    \resumeItem{Built observability stack with Prometheus, Grafana, and k6 stress testing (up to 220 concurrent VUs, 2-hour soak tests) for production API monitoring and performance tuning}
    \resumeItem{Implemented RBAC with JWT refresh tokens, rate limiting, Helmet security headers, and automated daily MongoDB backups with 7-day retention}
  \resumeItemListEnd

\resumeSubHeadingListEnd
```

## Step 2: Profile .tex file updates

Each profile needs changes:
- `\input{../src/experience}` → `\input{../src/<profile>/experience}`
- `\input{../src/community}` → `\input{../src/<profile>/community}`
- `\input{../src/achievements}` → `\input{../src/<profile>/achievements}`
- Add `\hypersetup{pdftitle=..., pdfsubject=...}` in preamble

## Step 3: ATS hardening

Replace in all content files:
- `\textless ` → `<`
- `\textgreater ` → `>`

## Step 4: Cover letter generator

### letters/template.tex
```latex
\documentclass[11pt]{letter}
\usepackage[empty]{fullpage}
\usepackage[hidelinks]{hyperref}
\usepackage[default]{lato}

\address{Ahmed Saleh \\ +20 115 164 4301 \\ \href{mailto:me@abosaleh.site}{me@abosaleh.site}}
\signature{Ahmed Saleh}

\begin{document}
\begin{letter}{Hiring Manager \\ COMPANY_NAME \\ COMPANY_LOCATION}
\opening{Dear Hiring Manager,}

I am writing to express my interest in the ROLE_NAME position at COMPANY_NAME. 

As a ROLE_KEY_HIGHLIGHT, I have built and deployed production systems...

[Body tailored to the specific role based on the PROFILE]

I would welcome the opportunity to discuss how my experience aligns with COMPANY_NAME's needs.

\closing{Best regards,}
\end{letter}
\end{document}
```

### letters/generate-cover.sh
```bash
#!/bin/bash
# Usage: ./generate-cover.sh "Company" "Location" "Role Title" "profile"
COMPANY=$1
LOCATION=$2
ROLE=$3
PROFILE=$4
mkdir -p output
sed -e "s/COMPANY_NAME/$COMPANY/g" \
    -e "s/COMPANY_LOCATION/$LOCATION/g" \
    -e "s/ROLE_NAME/$ROLE/g" \
    -e "s/PROFILE/$PROFILE/g" \
    template.tex > "output/cover-$ROLE-$COMPANY.tex"
cd output && latexmk -pdf "cover-$ROLE-$COMPANY.tex"
```

## Step 5: Custom profile

### profiles/resume-custom.tex
Copy of an existing profile with comments guiding customization.
Replace `\input` paths and edit section content for the specific job posting.

## Implementation order

1. Write per-profile experience.tex files
2. Copy community.tex and achievements.tex to each profile dir
3. Update all profile .tex files (new paths + PDF metadata)
4. ATS hardening replace \textless and \textgreater
5. Create letters/ directory with template and script
6. Create profiles/resume-custom.tex
7. Rebuild all
