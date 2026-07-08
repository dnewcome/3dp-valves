PY    ?= python3
CAD   := cad
BUILD := build

PARTS     := solenoid_block poppet tpu_disc manifold
PART_STLS := $(addprefix $(BUILD)/,$(addsuffix .stl,$(PARTS)))
REF_STLS  := $(BUILD)/solenoid_coil.stl $(BUILD)/solenoid_plunger.stl

# --- pump subsystem (twin-cylinder S-valve pump; see PUMP_BRIEF.md) ---
PUMP_PARTS := cylinder_block s_tube wear_ring piston crankshaft
PUMP_STLS  := $(addprefix $(BUILD)/,$(addsuffix .stl,$(PUMP_PARTS)))

# --- vertical submersible variant (rotary distributor; see VPUMP.md) ---
VPUMP_PARTS := v_block v_rotor v_crankshaft
VPUMP_STLS  := $(addprefix $(BUILD)/,$(addsuffix .stl,$(VPUMP_PARTS)))

.PHONY: all valves pump vpump parts refs assembly deps clean help \
        mujoco mujoco-demo mujoco-selftest vmujoco vmujoco-demo vmujoco-selftest
.DEFAULT_GOAL := all

all: valves pump vpump ## Build everything: the valve stack + both pumps

valves: parts refs assembly ## Build every valve part + reference solenoid + the renders

parts: $(PART_STLS) ## Build all printable part STLs

refs: $(REF_STLS) ## Build the reference (non-printed) solenoid model

assembly: $(BUILD)/assembly.stl ## Build full + sectioned assembly (STL + PNG)

deps: ## Install Python dependencies
	$(PY) -m pip install build123d trimesh matplotlib manifold3d mujoco imageio

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

# --- pump parts (every part depends on the shared source of truth pump_params.py) ---
pump: $(BUILD)/pump_assembly.stl ## Build all pump parts + the assembly renders

$(PUMP_STLS): $(BUILD)/%.stl: $(CAD)/%.py $(CAD)/pump_params.py
	$(PY) $(CAD)/$*.py

# --- pump assembly (one run emits stl + section stl + 2 pngs; logs a dated frame too) ---
$(BUILD)/pump_assembly.stl: $(CAD)/pump_assembly.py $(PUMP_STLS) $(CAD)/pump_params.py
	$(PY) $(CAD)/pump_assembly.py
$(BUILD)/pump_assembly_section.stl $(BUILD)/pump_assembly.png $(BUILD)/pump_assembly_section.png: $(BUILD)/pump_assembly.stl

# --- vertical submersible pump (parts share vpump_params.py + the reused piston) ---
vpump: $(BUILD)/v_pump_assembly.stl ## Build the vertical submersible pump + renders

$(VPUMP_STLS): $(BUILD)/%.stl: $(CAD)/%.py $(CAD)/vpump_params.py $(CAD)/piston.py $(CAD)/pump_params.py
	$(PY) $(CAD)/$*.py
$(BUILD)/v_pump_assembly.stl: $(CAD)/v_pump_assembly.py $(VPUMP_STLS) $(CAD)/vpump_params.py
	$(PY) $(CAD)/v_pump_assembly.py
$(BUILD)/v_pump_assembly_section.stl $(BUILD)/v_pump_assembly.png $(BUILD)/v_pump_assembly_section.png: $(BUILD)/v_pump_assembly.stl

# --- pump drive-timing sim (MuJoCo; needs the meshes built) ---
mujoco: $(PUMP_STLS) ## INTERACTIVE MuJoCo viewer — watch the swing track the ports
	$(PY) sim/pump_sim.py
mujoco-demo: $(PUMP_STLS) ## Headless: swing-timing figure + animated gif (sine vs dwell)
	$(PY) sim/pump_sim.py --demo
mujoco-selftest: $(PUMP_STLS) ## Build + pose + assert (no window; CI-safe)
	$(PY) sim/pump_sim.py --selftest

# --- vertical pump rotary-distributor sim (MuJoCo; needs the v-meshes) ---
vmujoco: $(VPUMP_STLS) $(BUILD)/piston.stl ## INTERACTIVE viewer — watch the rotary valve track the ports
	$(PY) sim/vpump_sim.py
vmujoco-demo: $(VPUMP_STLS) $(BUILD)/piston.stl ## Headless: coverage figure + gif (rotary ~89%)
	$(PY) sim/vpump_sim.py --demo
vmujoco-selftest: $(VPUMP_STLS) $(BUILD)/piston.stl ## Build + pose + assert (no window; CI-safe)
	$(PY) sim/vpump_sim.py --selftest

clean: ## Remove all build artifacts
	rm -rf $(BUILD) $(CAD)/__pycache__

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'
