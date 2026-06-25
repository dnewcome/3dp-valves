PY    ?= python3
CAD   := cad
BUILD := build

PARTS     := solenoid_block poppet tpu_disc manifold
PART_STLS := $(addprefix $(BUILD)/,$(addsuffix .stl,$(PARTS)))
REF_STLS  := $(BUILD)/solenoid_coil.stl $(BUILD)/solenoid_plunger.stl

.PHONY: all parts refs assembly deps clean help
.DEFAULT_GOAL := all

all: parts refs assembly ## Build every part + reference solenoid + the renders

parts: $(PART_STLS) ## Build all printable part STLs

refs: $(REF_STLS) ## Build the reference (non-printed) solenoid model

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

# --- reference solenoid (one run emits coil + plunger STLs) ---
$(BUILD)/solenoid_coil.stl: $(CAD)/solenoid_model.py $(CAD)/solenoid_block.py $(CAD)/poppet.py $(CAD)/interface.py
	$(PY) $(CAD)/solenoid_model.py
$(BUILD)/solenoid_plunger.stl: $(BUILD)/solenoid_coil.stl

# --- assembly (loads the part STLs; one run emits stl + section stl + 2 pngs) ---
$(BUILD)/assembly.stl: $(CAD)/assembly.py $(PART_STLS) $(REF_STLS)
	$(PY) $(CAD)/assembly.py
$(BUILD)/assembly_section.stl $(BUILD)/assembly.png $(BUILD)/assembly_section.png: $(BUILD)/assembly.stl

clean: ## Remove all build artifacts
	rm -rf $(BUILD) $(CAD)/__pycache__

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'
