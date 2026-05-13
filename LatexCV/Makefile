.PHONY: all clean custom cover-letter list

PROFILES = fullstack backend frontend dotnet nodejs
COVER_TEMPLATE = letters/template.tex

all: $(PROFILES)

# Build all profiles
$(PROFILES):
	@mkdir -p output
	latexmk -pdf -cd -output-directory="../output" "profiles/resume-$@.tex"
	@echo "-> output/resume-$@.pdf"

# Build custom profile (copy profiles/resume-custom.tex first)
custom:
	@echo "Edit profiles/resume-custom.tex with your job-specific content, then:"
	@echo "  latexmk -pdf -cd -output-directory=\"../output\" profiles/resume-custom.tex"
	@echo ""
	@echo "Or copy it first: cp profiles/resume-custom.tex profiles/resume-<jobname>.tex"

# Generate cover letter (requires COMPANY, ROLE, PROFILE vars)
#   make cover-letter COMPANY="Stripe" ROLE="Backend Engineer" PROFILE="backend"
cover-letter:
	@if [ -z "$(COMPANY)" ] || [ -z "$(ROLE)" ] || [ -z "$(PROFILE)" ]; then \
	  echo "Usage: make cover-letter COMPANY=\"Stripe\" ROLE=\"Backend Engineer\" PROFILE=\"backend\""; \
	  exit 1; \
	fi
	@./letters/generate-cover.sh "$(COMPANY)" "" "$(ROLE)" "$(PROFILE)"

# Clean generated files
clean:
	rm -rf output
	rm -f *.log *.aux *.fls *.fdb_latexmk *.out *.synctex.gz
	rm -f profiles/*.log profiles/*.aux

# List available profiles
list:
	@echo "Available profiles:"
	@for p in $(PROFILES); do echo "  $$p"; done
	@echo ""
	@echo "Usage: make <profile>"
	@echo "       make all"
	@echo "       make cover-letter COMPANY=\"X\" ROLE=\"Y\" PROFILE=\"Z\""
