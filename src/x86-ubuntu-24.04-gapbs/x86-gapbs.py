# Copyright (c) 2021 The Regents of the University of California.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met: redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer;
# redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution;
# neither the name of the copyright holders nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Script to run the GAP Benchmark Suite with gem5. It is based on the script for running PARSEC benchmarks from gem5/configs/example/gem5_library.

The script expects a benchmark program name and the simulation
size. The system is fixed with 2 CPU cores, MESI Two Level system
cache and 3 GB DDR4 memory. It uses the x86 board.

This script will count the total number of instructions executed
in the ROI. It also tracks how much wallclock and simulated time.

Usage:
------

```
scons build/X86/gem5.opt
./build/X86/gem5.opt \
    /path/to/gem5-resources/src/x86-ubuntu-24.04-gapbs/x86-gapbs.py \
    --benchmark <benchmark_name> \
    --size <simulation_size> \
    --synthetic <t or f>
```
"""
import argparse
import time

import m5
from m5.objects import Root

from gem5.coherence_protocol import CoherenceProtocol
from gem5.components.boards.x86_board import X86Board
from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
    MESITwoLevelCacheHierarchy,
)
from gem5.components.memory import DualChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_switchable_processor import (
    SimpleSwitchableProcessor,
)
from gem5.components.processors.simple_processor import SimpleProcessor

from gem5.isas import ISA
from gem5.resources.resource import (DiskImageResource, obtain_resource )
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires


# We check for the required gem5 build.

requires(
    isa_required=ISA.X86,
    coherence_protocol_required=CoherenceProtocol.MESI_TWO_LEVEL,
    kvm_required=True,
)

size_choices = []

for i in range(1,17):
    size_choices.append(str(i))

size_choices.append("USA-road-d.NY.gr")

benchmark_choices = ["cc", "bc", "tc", "pr", "bfs"]

parser = argparse.ArgumentParser(
    description="An example configuration script to run the npb benchmarks."
)

# The arguments accepted are the benchmark name and the simulation size.

parser.add_argument(
    "--benchmark",
    type=str,
    required=True,
    help="Input the benchmark program to execute.",
    choices=benchmark_choices,
)

parser.add_argument(
    "--size",
    type=str,
    required=True,
    help="Simulation size for the benchmark program.",
    # choices=size_choices,
)

parser.add_argument(
    "--synthetic",
    type=str,
    required=True,
    help="Whether to use a synthetic or real graph.",
    choices=["t", "f"]
)
args = parser.parse_args()

# Setting up all the fixed system parameters here
# Caches: MESI Two Level Cache Hierarchy



cache_hierarchy = MESITwoLevelCacheHierarchy(
    l1d_size="32kB",
    l1d_assoc=8,
    l1i_size="32kB",
    l1i_assoc=8,
    l2_size="256kB",
    l2_assoc=16,
    num_l2_banks=2,
)

# Memory: Dual Channel DDR4 2400 DRAM device.
# The X86 board only supports 3 GB of main memory.

memory = DualChannelDDR4_2400(size="3GB")

# Here we setup the processor. This is a special switchable processor in which
# a starting core type and a switch core type must be specified. Once a
# configuration is instantiated a user may call `processor.switch()` to switch
# from the starting core types to the switch core types. In this simulation
# we start with KVM cores to simulate the OS boot, then switch to the Timing
# cores for the command we wish to run after boot.

# processor = SimpleSwitchableProcessor(
#     starting_core_type=CPUTypes.KVM,
#     switch_core_type=CPUTypes.TIMING,
#     isa=ISA.X86,
#     num_cores=2,
# )

processor = SimpleProcessor(cpu_type=CPUTypes.KVM, num_cores=2, isa=ISA.X86)

# Here we setup the board. The X86Board allows for Full-System X86 simulations

board = X86Board(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)

if (args.synthetic =="f"):
    command= (
        f"cd /home/gem5/gapbs;"
        + f"./{args.benchmark} -sf /home/gem5/{args.size} -n 10"
    )
else:
    command = (
        f"cd /home/gem5/gapbs;"
        + f"./{args.benchmark} -g {args.size} -n 10"
    )


board.set_kernel_disk_workload(
    # The x86 linux kernel will be automatically downloaded to the
    # `~/.cache/gem5` directory if not already present.
    kernel=obtain_resource(
        "x86-linux-kernel-5.4.0-105-generic", resource_version="1.0.0"
    ),
    disk_image=DiskImageResource("/home/bees/gem5-resources/src/x86-ubuntu-24.04-gapbs/disk-image-ubuntu-24-04/x86-ubuntu-24-04"),
    readfile_contents=command,
    kernel_args=[
            "earlyprintk=ttyS0",
            "console=ttyS0",
            "root=/dev/sda2",
            "no_systemd=false" 
        ]
)

# After the system boots, we execute the benchmark program and wait till the
# ROI `workbegin` annotation is reached (m5_work_begin()). We start collecting
# the number of committed instructions till ROI ends (marked by `workend`).
# We then finish executing the rest of the benchmark.

# Also, we sleep the system for some time so that the output is printed
# properly.

# functions to handle different exit events during the simuation
def handle_workbegin():
    print("Done booting Linux")
    print("Resetting stats at the start of ROI!")
    m5.stats.reset()
    processor.switch()
    yield False


def handle_workend():
    print("Dump stats at the end of the ROI!")
    m5.stats.dump()
    yield True


simulator = Simulator(
    board=board,
    # on_exit_event={
    #     ExitEvent.WORKBEGIN: handle_workbegin(),
    #     ExitEvent.WORKEND: handle_workend(),
    # },
)

# We maintain the wall clock time.

globalStart = time.time()

print("Running the simulation")
print("Using KVM cpu")

m5.stats.reset()

# We start the simulation
simulator.run()

print("All simulation events were successful.")

# We print the final simulation statistics.

print("Done with the simulation")
print()
print("Performance statistics:")

print("Simulated time in ROI: " + (str(simulator.get_roi_ticks()[0])))
print(
    "Ran a total of", simulator.get_current_tick() / 1e12, "simulated seconds"
)
print(
    "Total wallclock time: %.2fs, %.2f min"
    % (time.time() - globalStart, (time.time() - globalStart) / 60)
)
