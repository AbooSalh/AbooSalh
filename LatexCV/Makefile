.PHONY: all clean list

all:
	python3 build.py all

# Build a specific profile (e.g. make siemens)
%:
	python3 build.py $@

list:
	python3 build.py list

clean:
	rm -rf output
	rm -f *.log *.aux *.fls *.fdb_latexmk *.out *.synctex.gz

# Generate cover letter
#   make cover COMPANY="Siemens" ROLE="SSP Intern" PROFILE="siemens"
cover:
	python3 build.py cover "$(COMPANY)" "$(ROLE)" "$(PROFILE)"

# AI-tailor CV from job description
#   make tailor JD_FILE=job.txt
tailor:
	python3 build.py tailor --jd-file "$(JD_FILE)" --profile "$(PROFILE)"
