# BlocksDS supported build. Override BLOCKSDS/WONDERFUL_TOOLCHAIN if installed elsewhere.
export BLOCKSDS ?= /opt/wonderful/thirdparty/blocksds/core
export WONDERFUL_TOOLCHAIN ?= /opt/wonderful
NAME := mii-ds
GAME_TITLE := Mii Maker DS
GAME_SUBTITLE := Create and edit Mii characters
GAME_ICON := assets/ui/original-icon.gif
GAME_AUTHOR := Independent demake
SOURCEDIRS := source
NITROFSDIR := nitrofiles
# Keep the shipping software renderer until the source skeleton/UVs and
# 3D framebuffer ownership are validated. Nitro Engine links in the
# separately opt-in hardware backend build, not the current ROM.
# BlocksDS default ARM7 core includes Maxmod; soundbank is optional.
LIBS := -lmm9 -lnds9 -lm
LIBDIRS += $(BLOCKSDS)/libs/maxmod
CFLAGS := -Wextra -Werror $(EXTRA_CFLAGS)
ifeq ($(SDK_STAGE),1)
include $(BLOCKSDS)/sys/default_makefiles/rom_arm9/Makefile
NDSTOOL_ARGS += -g MDSD

# Changes to the banner or any embedded asset must repack the ROM.
$(ROM): Makefile $(GAME_ICON) $(shell find nitrofiles -type f)

else
# Local source-derived 3D geometry staging (never part of public ROM/CI).
# Requires a private BOD2 extracted from the user's source assets.
# Nitro Engine includes DSMA and its md5_to_dsma conversion tool.
BOD2_INPUT ?=
DSMA_STAGE ?= /tmp/mii-maker-dsma-private
DSMA_NAME ?= MiiBody
NITRO_ENGINE_MD5_TOOL ?=
.PHONY: dsma-private-model
dsma-private-model:
	@test -n "$(BOD2_INPUT)" || (echo "Set BOD2_INPUT=/path/to/private/BOD2" && exit 2)
	@test -n "$(NITRO_ENGINE_MD5_TOOL)" || (echo "Set NITRO_ENGINE_MD5_TOOL=/path/to/md5_to_dsma.py" && exit 2)
	python3 tools/export_bod2_md5.py --input "$(BOD2_INPUT)" --output "$(DSMA_STAGE)" --name "$(DSMA_NAME)"
	python3 "$(NITRO_ENGINE_MD5_TOOL)" --model "$(DSMA_STAGE)/$(DSMA_NAME).md5mesh" --name "$(DSMA_NAME)" --output "$(DSMA_STAGE)" --texture 8 8 --export-base-pose --bin

# Stage locally converted, privately owned DSMA files for the separate GPU ROM.
# These NitroFS files are gitignored and never included in public CI artifacts.
DSMA_MODEL ?=
DSMA_ANIMATION ?=
.PHONY: stage-dsma-private
stage-dsma-private:
	@test -n "$(DSMA_MODEL)" || (echo "Set DSMA_MODEL=/private/path/MiiBody_dsm.bin" && exit 2)
	@test -n "$(DSMA_ANIMATION)" || (echo "Set DSMA_ANIMATION=/private/path/MiiBody_dsa.bin" && exit 2)
	python3 tools/stage_private_dsma.py --model "$(DSMA_MODEL)" --animation "$(DSMA_ANIMATION)"

# Separate GPU test ROM: never links Nitro Engine into the existing 2D game
# until the original source UVs, bind hierarchy and screen compositor work.
.PHONY: nitro-3d-preview
nitro-3d-preview:
	+$(MAKE) -C hardware3d

.DEFAULT_GOAL := all
.PHONY: all $(NAME).nds clean dump
all: $(NAME).nds
$(NAME).nds:
	python3 tools/build_preflight.py
	python3 tools/check_assets.py $(if $(findstring MDS_IMPORT_TEST_FILES,$(EXTRA_CFLAGS)),--allow-test-import,)
	+$(MAKE) SDK_STAGE=1 $(NAME).nds
	python3 tools/fix_nds_regions.py $@
clean dump:
	+$(MAKE) SDK_STAGE=1 $@
endif
