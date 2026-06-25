PY    ?= python3
CAD   := cad
BUILD := build

PARTS     := solenoid_block poppet tpu_disc manifold
PART_STLS := $(addprefix $(BUILD)/,$(addsuffix .stl,$(PARTS)))

.PHONY: all parts assembly deps clean help
.DEFAULT_GOAL := all

all: parts assembly ## Build every part + the assembly/section render

parts: $(PART_STLS) ## Build all part STLs

assembly: $(BUILD)/assembly.stl ## Build full + sectioned assembly (STL + PNG)

deps: ## Install Python dependencies
	$(PY) -m pip install build123d trimesh matplotlib manifold3d

# --- parts (prerequisites follow the import chain) ---
$(BUILD)/solenoid_block.stl: $(CAD)/solenoid_block.py $(CAD)/interface.py
	$(PY) $(CAD)/solenoid_block.py

$(BUILD)/poppet.stl: $(CAD)/poppet.py $(CAD)/solenoid_block.py $(CAD)/interface.py
	$(PY) $(CAD)/poppet.py

$(BUILD)/tpu_disc.stl: $(CAD)/tpu_disc.py $(CAD)/poppet.py $(CAD)/solenoid_block.py $(CAD)/interface.py
	$(PY) $(CAD)/tpu_disc.py

$(BUILD)/manifold.stl: $(CAD)/manifold.py $(CAD)/interface.py
	$(PY) $(CAD)/manifold.py

# --- assembly (loads the part STLs; one run emits stl + section stl + png) ---
$(BUILD)/assembly.stl: $(CAD)/assembly.py $(PART_STLS)
	$(PY) $(CAD)/assembly.py
$(BUILD)/assembly_section.stl $(BUILD)/assembly_section.png: $(BUILD)/assembly.stl

clean: ## Remove all build artifacts
	rm -rf $(BUILD) $(CAD)/__pycache__

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'
