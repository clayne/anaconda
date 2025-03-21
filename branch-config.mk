# ======================================
# WARNING!
# THIS FILE IS GENERATED FROM A TEMPLATE
# DO NOT EDIT THIS FILE MANUALLY!
# ======================================
# The template is located in: branch-config.mk.j2

# Makefile include for branch specific configuration settings
#
# Copyright (C) 2020  Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Store a branch specific configuration here to avoid dealing with
# conflicts on multiple places.


# Name of the expected current git branch.
# This could be main, fedora-XX, rhel-X ...
GIT_BRANCH ?= main

# Directory for this anaconda branch in anaconda-l10n repository. This could be main, fXX, rhel-8 etc.
L10N_DIR ?= main

# Base container for our containers.
BASE_CONTAINER ?= registry.fedoraproject.org/fedora:rawhide

# COPR repo for use in container builds.
COPR_REPO ?= \@rhinstaller/Anaconda

