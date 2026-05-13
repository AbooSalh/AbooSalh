#!/bin/bash
# Generate a tailored cover letter PDF
# Usage: ./generate-cover.sh <company> <location> <role> <profile>
#   ./generate-cover.sh "Stripe" "San Francisco" "Backend Engineer" "backend"

set -e

if [ $# -lt 4 ]; then
  echo "Usage: $0 <company> <location> <role> <profile>"
  echo "  e.g. $0 \"Stripe\" \"San Francisco\" \"Backend Engineer\" \"backend\""
  echo ""
  echo "Available profiles: $(ls ../src | grep -v '\.tex' | tr '\n' ' ')"
  exit 1
fi

COMPANY="$1"
LOCATION="$2"
ROLE="$3"
PROFILE="$4"
SAFE_NAME=$(echo "$COMPANY-$ROLE" | tr ' ' '-' | tr '[:upper:]' '[:lower:]')

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/../output"
mkdir -p "$OUTPUT_DIR"

TEX_FILE="$OUTPUT_DIR/cover-$SAFE_NAME.tex"

sed -e "s/COMPANY_NAME/$COMPANY/g" \
    -e "s/COMPANY_LOCATION/$LOCATION/g" \
    -e "s/ROLE_NAME/$ROLE/g" \
    -e "s/PROFILE/$PROFILE/g" \
    "$SCRIPT_DIR/template.tex" > "$TEX_FILE"

echo "Generated: $TEX_FILE"
echo "Compiling..."

cd "$OUTPUT_DIR"
latexmk -pdf "cover-$SAFE_NAME.tex" -cd 2>/dev/null || \
  pdflatex -interaction=nonstopmode "cover-$SAFE_NAME.tex" 2>/dev/null

if [ -f "cover-$SAFE_NAME.pdf" ]; then
  echo "-> output/cover-$SAFE_NAME.pdf"
else
  echo "[ERROR] Compilation failed"
fi

cd "$SCRIPT_DIR"
