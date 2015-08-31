# Destination directory
DEST_DIR = /home/fac_files/code/va/viocs

FILES = *

FULLFILES = $(addprefix $(DEST_DIR)/, $(FILES))

install: $(DEST_DIR) $(FILES)
	cp -r $(FILES) $(DEST_DIR)

$(DEST_DIR):
	mkdir -p $(DEST_DIR)
