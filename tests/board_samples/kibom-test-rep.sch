EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "KiBom Test Schematic"
Date "2020-03-12"
Rev "A"
Comp "https://github.com/SchrodingersGat/KiBom"
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
Text Notes 550  950  0    50   ~ 0
This schematic serves as a test-file for the KiBom export script.\n\nAfter making a change to the schematic, remember to re-export the BOM to generate the intermediate .xml file\n\n(The testing framework cannot perform the netlist-export step!)
$Comp
L 74xx:74LS02 U1
U 1 1 5F32DAD4
P 2500 2000
F 0 "U1" H 2500 2325 50  0000 C CNN
F 1 "74LS02" H 2500 2234 50  0000 C CNN
F 2 "" H 2500 2000 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74ls02" H 2500 2000 50  0001 C CNN
F 4 "" H 2500 2000 50  0001 C CNN "Config"
	1    2500 2000
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS02 U1
U 2 1 5F32F3E6
P 3350 2000
F 0 "U1" H 3350 2325 50  0000 C CNN
F 1 "74LS02" H 3350 2234 50  0000 C CNN
F 2 "" H 3350 2000 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74ls02" H 3350 2000 50  0001 C CNN
F 4 "" H 3350 2000 50  0001 C CNN "Config"
	2    3350 2000
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS02 U1
U 3 1 5F3307F3
P 2500 2650
F 0 "U1" H 2500 2975 50  0000 C CNN
F 1 "74LS02" H 2500 2884 50  0000 C CNN
F 2 "" H 2500 2650 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74ls02" H 2500 2650 50  0001 C CNN
F 4 "" H 2500 2650 50  0001 C CNN "Config"
	3    2500 2650
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS02 U1
U 4 1 5F3307FD
P 3350 2650
F 0 "U1" H 3350 2975 50  0000 C CNN
F 1 "74LS02" H 3350 2884 50  0000 C CNN
F 2 "" H 3350 2650 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74ls02" H 3350 2650 50  0001 C CNN
F 4 "" H 3350 2650 50  0001 C CNN "Config"
	4    3350 2650
	1    0    0    -1  
$EndComp
$Comp
L 74xx:74LS02 U1
U 5 1 5F336BFF
P 2900 3600
F 0 "U1" H 3130 3646 50  0000 L CNN
F 1 "74LS02" H 3130 3555 50  0000 L CNN
F 2 "" H 2900 3600 50  0001 C CNN
F 3 "http://www.ti.com/lit/gpn/sn74ls02" H 2900 3600 50  0001 C CNN
F 4 "" H 2900 3600 50  0001 C CNN "Config"
	5    2900 3600
	1    0    0    -1  
$EndComp
$Comp
L Device:R R1
U 1 1 5F331BEB
P 4200 2000
F 0 "R1" H 4270 2046 50  0000 L CNN
F 1 "DNC" H 4270 1955 50  0000 L CNN
F 2 "" V 4130 2000 50  0001 C CNN
F 3 "~" H 4200 2000 50  0001 C CNN
	1    4200 2000
	1    0    0    -1  
$EndComp
$Comp
L Device:R R2
U 1 1 5F3321E0
P 4200 2350
F 0 "R2" H 4270 2396 50  0000 L CNN
F 1 "100" H 4270 2305 50  0000 L CNN
F 2 "" V 4130 2350 50  0001 C CNN
F 3 "~" H 4200 2350 50  0001 C CNN
F 4 "DNF,DNC" H 4200 2350 50  0001 C CNN "Config"
	1    4200 2350
	1    0    0    -1  
$EndComp
$Comp
L Device:R R3
U 1 1 5F331E0B
P 4200 2750
F 0 "R3" H 4270 2796 50  0000 L CNN
F 1 "DNF" H 4270 2705 50  0000 L CNN
F 2 "" V 4130 2750 50  0001 C CNN
F 3 "~" H 4200 2750 50  0001 C CNN
F 4 "DNF,DNC" H 4200 2750 50  0001 C CNN "Config"
	1    4200 2750
	1    0    0    -1  
$EndComp
$EndSCHEMATC
