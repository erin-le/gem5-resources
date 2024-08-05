#!/bin/bash

# Copyright (c) 2024 The Regents of the University of California.
# SPDX-License-Identifier: BSD 3-Clause

PACKER_VERSION="1.10.0"

if [ ! -f ./packer ]; then
    wget https://releases.hashicorp.com/packer/${PACKER_VERSION}/packer_${PACKER_VERSION}_linux_amd64.zip;
    unzip packer_${PACKER_VERSION}_linux_amd64.zip;
    rm packer_${PACKER_VERSION}_linux_amd64.zip;
fi

# Check if the configuration file variable is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <configuration_file>"
    exit 1
fi

# Store the configuration file name from the command line argument
config_file="$1"

# Check if the specified configuration file exists
if [ -f "$config_file" ]; then
    # Install the needed plugins
    ./packer init "$config_file"
    # Build the image
    ./packer build "$config_file"
else
    echo "Error: Configuration file '$config_file' not found."
    exit 1
fi
