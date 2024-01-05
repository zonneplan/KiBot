# Multi-board projects

## Problem

We have a project we two or more PCBs. It can be as simple as a power source board and the main board.

In KiCad a project can handle a schematic hierarchy and just one PCB.

Here we try to explore possible solutions.


## Solution 1: Using KiKit

Here the idea is that you make one schematic containing all the circuit and one board file containing all the PCBs.
Then you use the `kikit separate` command to separate the PCBs.

Here is a simple example:

![Schematic](KiKit_1/Generated/Schematic.svg)

Note that we avoided the use of global powers, the GND is not explicit.

Our circuit is divided in two boards. Each board contains one filter.
They are connected with a cable between J2 and J3.

The KiCad board file looks like this:

![Board top](KiKit_1/Generated/KiKit_1-assembly_page_01.png)

![Board bottom](KiKit_1/Generated/KiKit_1-assembly_page_02.png)

The `Board A` and `Board B` arrows are used to name each PCB.
After running `kikit separate` we get for board A:

![Board top](KiKit_1/Board_A/Generated/board_a-assembly_page_01.png)

![Board bottom](KiKit_1/Board_A/Generated/board_a-assembly_page_02.png)

And for board B:

![Board top](KiKit_1/Board_B/Generated/board_b-assembly_page_01.png)

![Board bottom](KiKit_1/Board_B/Generated/board_b-assembly_page_02.png)

### Problems

* You have only one stack-up because both circuits comes from the same KiCad PCB file.
* Both circuits gets the same worksheet information (title, revision, etc.)
* You must avoid using global power components. No GND or +5V for global use.
* You need an external tool to separate the PCBs.
* You can't check electrical rules for connections between the boards.





## Solution 2: Using hierarchical sheets A

This looks a little bit more complicated, but solves various problems.

You create individual projects for each PCB board. In our example one project for each filter.

So you have individual pages (or hierarchies) for each part of the circuit, each page belongs to its own project:
Filter A:

![Schematic](Hierarchy_1/Filter_A/Generated/Schematic.svg)

Filter B:
![Schematic](Hierarchy_1/Filter_B/Generated/Schematic.svg)

Note that we added hierarchical labels to all the connectors and we now can
use global powers, but we use different names for each PCB (GND1 and GND2).

With two separated projects we have two separated PCBs.
Filter A:

![Schematic](Hierarchy_1/Filter_A/Generated/Filter_A-assembly_page_01.png)
![Schematic](Hierarchy_1/Filter_A/Generated/Filter_A-assembly_page_02.png)

Filter B:

![Schematic](Hierarchy_1/Filter_B/Generated/Filter_B-assembly_page_01.png)
![Schematic](Hierarchy_1/Filter_B/Generated/Filter_B-assembly_page_02.png)

In order to create a schematic for the whole system you create a third project.
In this project you use hierarchical sheets to join both projects and show
how they are connected.

![Schematic](Hierarchy_1/Top_Level/Generated/Schematic.svg)
![Schematic](Hierarchy_1/Top_Level/Generated/Top_Level-Filter_A.svg)
![Schematic](Hierarchy_1/Top_Level/Generated/Top_Level-Filter_B.svg)

### Problems

* You can't run the ERC for the whole system.
  KiCad will complain about more than one PWR_FLAG for the same node.



## Solution 3: Using hierarchical sheets B

This is just a hack for the second solution.
Here we add a jumper to isolate the powers, we mark it as excluded from the BoM.
Now the top-level looks like this:

![Schematic](Hierarchy_1/Top_Level_B/Generated/Schematic.svg)

And the ERC works.



## Solution 3: Using hierarchical sheets C

This option doesn't allow a full ERC check of the system, you won't detect the
output of one board connected to the output of another. But it allows creating
BoMs that includes things like wires, terminals and crimp housings.

Here the connection between boards is done using components for each element we
need to use:

![Schematic](Hierarchy_1/Top_Level_C/Generated/Schematic.svg)

The ERC works, but is limited.
