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
$Comp
L Device:R R1
U 1 1 5E6A2873
P 2200 2550
F 0 "R1" V 2280 2550 50  0000 C CNN
F 1 "10K" V 2200 2550 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 2130 2550 50  0001 C CNN
F 3 "~" H 2200 2550 50  0001 C CNN
F 4 "5%" V 2200 2550 50  0001 C CNN "Tolerance"
	1    2200 2550
	1    0    0    -1  
$EndComp
$Comp
L Device:R R2
U 1 1 5E6A330D
P 2500 2550
F 0 "R2" V 2580 2550 50  0000 C CNN
F 1 "10K" V 2500 2550 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 2430 2550 50  0001 C CNN
F 3 "~" H 2500 2550 50  0001 C CNN
F 4 "10%" V 2500 2550 50  0001 C CNN "Tolerance"
	1    2500 2550
	1    0    0    -1  
$EndComp
$Comp
L Device:R R3
U 1 1 5E6A35E1
P 2750 2550
F 0 "R3" V 2830 2550 50  0000 C CNN
F 1 "10K" V 2750 2550 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 2680 2550 50  0001 C CNN
F 3 "~" H 2750 2550 50  0001 C CNN
	1    2750 2550
	1    0    0    -1  
$EndComp
$Comp
L Device:R R4
U 1 1 5E6A37B2
P 3000 2550
F 0 "R4" V 3080 2550 50  0000 C CNN
F 1 "10K" V 3000 2550 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 2930 2550 50  0001 C CNN
F 3 "~" H 3000 2550 50  0001 C CNN
	1    3000 2550
	1    0    0    -1  
$EndComp
$Comp
L Device:R R5
U 1 1 5E6A39EB
P 3250 2550
F 0 "R5" V 3330 2550 50  0000 C CNN
F 1 "10K" V 3250 2550 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 3180 2550 50  0001 C CNN
F 3 "~" H 3250 2550 50  0001 C CNN
	1    3250 2550
	1    0    0    -1  
$EndComp
Text Notes 3500 2550 0    50   ~ 0
5 x 10K resistors in 0805 package
$Comp
L Device:R R6
U 1 1 5E6A3CA0
P 2200 3100
F 0 "R6" V 2280 3100 50  0000 C CNN
F 1 "4K7" V 2200 3100 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 2130 3100 50  0001 C CNN
F 3 "~" H 2200 3100 50  0001 C CNN
F 4 "DNF" V 2200 3100 50  0001 C CNN "Config"
	1    2200 3100
	1    0    0    -1  
$EndComp
$Comp
L Device:R R7
U 1 1 5E6A3F38
P 2500 3100
F 0 "R7" V 2580 3100 50  0000 C CNN
F 1 "4700" V 2500 3100 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 2430 3100 50  0001 C CNN
F 3 "~" H 2500 3100 50  0001 C CNN
F 4 "DNC" V 2500 3100 50  0001 C CNN "Config"
	1    2500 3100
	1    0    0    -1  
$EndComp
$Comp
L Device:R R8
U 1 1 5E6A4181
P 2750 3100
F 0 "R8" V 2830 3100 50  0000 C CNN
F 1 "4.7K" V 2750 3100 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 2680 3100 50  0001 C CNN
F 3 "~" H 2750 3100 50  0001 C CNN
	1    2750 3100
	1    0    0    -1  
$EndComp
Text Notes 3500 3150 0    50   ~ 0
3 x 4K7 resistors in 0805 package\nNote: Values are identical even if specified differently
$Comp
L Device:R R9
U 1 1 5E6A448B
P 2200 3650
F 0 "R9" V 2280 3650 50  0000 C CNN
F 1 "4K7" V 2200 3650 50  0000 C CNN
F 2 "Resistor_SMD:R_0603_1608Metric" V 2130 3650 50  0001 C CNN
F 3 "~" H 2200 3650 50  0001 C CNN
	1    2200 3650
	1    0    0    -1  
$EndComp
$Comp
L Device:R R10
U 1 1 5E6A491A
P 2500 3650
F 0 "R10" V 2580 3650 50  0000 C CNN
F 1 "4K7" V 2500 3650 50  0000 C CNN
F 2 "Resistor_SMD:R_0603_1608Metric" V 2430 3650 50  0001 C CNN
F 3 "~" H 2500 3650 50  0001 C CNN
	1    2500 3650
	1    0    0    -1  
$EndComp
Text Notes 3500 3650 0    50   ~ 0
3 x 4K7 resistors in 0603 package
Text Notes 550  950  0    50   ~ 0
This schematic serves as a test-file for the KiBom export script.\n\nAfter making a change to the schematic, remember to re-export the BOM to generate the intermediate .xml file\n\n(The testing framework cannot perform the netlist-export step!)
$Comp
L Device:C C1
U 1 1 5E6A62CC
P 6650 2550
F 0 "C1" H 6675 2650 50  0000 L CNN
F 1 "10nF" H 6675 2450 50  0000 L CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 6688 2400 50  0001 C CNN
F 3 "~" H 6650 2550 50  0001 C CNN
	1    6650 2550
	1    0    0    -1  
$EndComp
$Comp
L Device:C C2
U 1 1 5E6A6854
P 7050 2550
F 0 "C2" H 7075 2650 50  0000 L CNN
F 1 "10n" H 7075 2450 50  0000 L CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 7088 2400 50  0001 C CNN
F 3 "~" H 7050 2550 50  0001 C CNN
	1    7050 2550
	1    0    0    -1  
$EndComp
$Comp
L Device:C C3
U 1 1 5E6A6A34
P 7450 2550
F 0 "C3" H 7475 2650 50  0000 L CNN
F 1 "0.01uF" H 7475 2450 50  0000 L CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 7488 2400 50  0001 C CNN
F 3 "~" H 7450 2550 50  0001 C CNN
	1    7450 2550
	1    0    0    -1  
$EndComp
$Comp
L Device:C C4
U 1 1 5E6A6CB6
P 7900 2550
F 0 "C4" H 7925 2650 50  0000 L CNN
F 1 "0.01uf" H 7925 2450 50  0000 L CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 7938 2400 50  0001 C CNN
F 3 "~" H 7900 2550 50  0001 C CNN
	1    7900 2550
	1    0    0    -1  
$EndComp
$Comp
L Connector:TestPoint P1
U 1 1 5F32EF71
P 2250 4550
F 0 "P1" H 2308 4668 50  0000 L CNN
F 1 "TestPoint" H 2308 4577 50  0000 L CNN
F 2 "" H 2450 4550 50  0001 C CNN
F 3 "~" H 2450 4550 50  0001 C CNN
	1    2250 4550
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:Fiducial FID1
U 1 1 5F32F77F
P 2250 4850
F 0 "FID1" H 2335 4896 50  0000 L CNN
F 1 "Fiducial" H 2335 4805 50  0000 L CNN
F 2 "" H 2250 4850 50  0001 C CNN
F 3 "~" H 2250 4850 50  0001 C CNN
	1    2250 4850
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H1
U 1 1 5F32FC3F
P 2150 5250
F 0 "H1" H 2250 5296 50  0000 L CNN
F 1 "MountingHole" H 2250 5205 50  0000 L CNN
F 2 "" H 2150 5250 50  0001 C CNN
F 3 "~" H 2150 5250 50  0001 C CNN
	1    2150 5250
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole_Pad H3
U 1 1 5F3304C4
P 3100 5300
F 0 "H3" H 3200 5349 50  0000 L CNN
F 1 "MountingHole_Pad" H 3200 5258 50  0000 L CNN
F 2 "" H 3100 5300 50  0001 C CNN
F 3 "~" H 3100 5300 50  0001 C CNN
	1    3100 5300
	1    0    0    -1  
$EndComp
$Comp
L Jumper:SolderJumper_2_Bridged JP2
U 1 1 5F3315CC
P 3350 4450
F 0 "JP2" H 3350 4655 50  0000 C CNN
F 1 "SolderJumper_2_Bridged" H 3350 4564 50  0000 C CNN
F 2 "" H 3350 4450 50  0001 C CNN
F 3 "~" H 3350 4450 50  0001 C CNN
	1    3350 4450
	1    0    0    -1  
$EndComp
$Comp
L Jumper:SolderJumper_2_Open JP3
U 1 1 5F33205B
P 3350 4850
F 0 "JP3" H 3350 5055 50  0000 C CNN
F 1 "SolderJumper_2_Open" H 3350 4964 50  0000 C CNN
F 2 "" H 3350 4850 50  0001 C CNN
F 3 "~" H 3350 4850 50  0001 C CNN
	1    3350 4850
	1    0    0    -1  
$EndComp
$Comp
L Jumper:SolderJumper_3_Bridged12 JP4
U 1 1 5F332E98
P 4400 4450
F 0 "JP4" H 4400 4655 50  0000 C CNN
F 1 "SolderJumper_3_Bridged12" H 4400 4564 50  0000 C CNN
F 2 "" H 4400 4450 50  0001 C CNN
F 3 "~" H 4400 4450 50  0001 C CNN
	1    4400 4450
	1    0    0    -1  
$EndComp
$Comp
L Jumper:SolderJumper_3_Bridged123 JP5
U 1 1 5F333EE0
P 4400 4950
F 0 "JP5" H 4400 5155 50  0000 C CNN
F 1 "SolderJumper_3_Bridged123" H 4400 5064 50  0000 C CNN
F 2 "" H 4400 4950 50  0001 C CNN
F 3 "~" H 4400 4950 50  0001 C CNN
	1    4400 4950
	1    0    0    -1  
$EndComp
$Comp
L Jumper:SolderJumper_3_Open JP6
U 1 1 5F334FB5
P 4400 5450
F 0 "JP6" H 4400 5655 50  0000 C CNN
F 1 "SolderJumper_3_Open" H 4400 5564 50  0000 C CNN
F 2 "" H 4400 5450 50  0001 C CNN
F 3 "~" H 4400 5450 50  0001 C CNN
	1    4400 5450
	1    0    0    -1  
$EndComp
$Comp
L Connector:TestPoint_2Pole P4
U 1 1 5F33653C
P 5500 4450
F 0 "P4" H 5500 4645 50  0000 C CNN
F 1 "TestPoint_2Pole" H 5500 4554 50  0000 C CNN
F 2 "" H 5500 4450 50  0001 C CNN
F 3 "~" H 5500 4450 50  0001 C CNN
	1    5500 4450
	1    0    0    -1  
$EndComp
$Comp
L Connector:TestPoint_Alt P5
U 1 1 5F336FC3
P 5500 4750
F 0 "P5" H 5558 4868 50  0000 L CNN
F 1 "TestPoint_Alt" H 5558 4777 50  0000 L CNN
F 2 "" H 5700 4750 50  0001 C CNN
F 3 "~" H 5700 4750 50  0001 C CNN
	1    5500 4750
	1    0    0    -1  
$EndComp
$Comp
L Connector:TestPoint_Flag P2
U 1 1 5F33770D
P 5450 5000
F 0 "P2" H 5710 5094 50  0000 L CNN
F 1 "TestPoint_Flag" H 5710 5003 50  0000 L CNN
F 2 "" H 5650 5000 50  0001 C CNN
F 3 "~" H 5650 5000 50  0001 C CNN
	1    5450 5000
	1    0    0    -1  
$EndComp
$Comp
L Connector:TestPoint_Small P3
U 1 1 5F337FD0
P 5450 5250
F 0 "P3" H 5498 5296 50  0000 L CNN
F 1 "TestPoint_Small" H 5498 5205 50  0000 L CNN
F 2 "" H 5650 5250 50  0001 C CNN
F 3 "~" H 5650 5250 50  0001 C CNN
	1    5450 5250
	1    0    0    -1  
$EndComp
$Comp
L Connector:TestPoint_Probe P6
U 1 1 5F33872C
P 5500 5600
F 0 "P6" H 5653 5701 50  0000 L CNN
F 1 "TestPoint_Probe" H 5653 5610 50  0000 L CNN
F 2 "" H 5700 5600 50  0001 C CNN
F 3 "~" H 5700 5600 50  0001 C CNN
	1    5500 5600
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:MountingHole H2
U 1 1 5F338F80
P 2200 5800
F 0 "H2" H 2300 5846 50  0000 L CNN
F 1 "2mm" H 2300 5755 50  0000 L CNN
F 2 "" H 2200 5800 50  0001 C CNN
F 3 "~" H 2200 5800 50  0001 C CNN
	1    2200 5800
	1    0    0    -1  
$EndComp
$Comp
L Jumper:SolderJumper_3_Open JP1
U 1 1 5F33938A
P 3050 5800
F 0 "JP1" H 3050 6005 50  0000 C CNN
F 1 "Select" H 3050 5914 50  0000 C CNN
F 2 "" H 3050 5800 50  0001 C CNN
F 3 "~" H 3050 5800 50  0001 C CNN
	1    3050 5800
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:Fiducial X1
U 1 1 5F339B4F
P 3650 5850
F 0 "X1" H 3735 5896 50  0000 L CNN
F 1 "Mark" H 3735 5805 50  0000 L CNN
F 2 "Fiducial:Fiducial_1mm_Mask2mm" H 3650 5850 50  0001 C CNN
F 3 "~" H 3650 5850 50  0001 C CNN
	1    3650 5850
	1    0    0    -1  
$EndComp
$Comp
L Mechanical:Heatsink TP1
U 1 1 5F33AA80
P 4400 5900
F 0 "TP1" H 4542 6021 50  0000 L CNN
F 1 "Heatsink" H 4542 5930 50  0000 L CNN
F 2 "" H 4412 5900 50  0001 C CNN
F 3 "~" H 4412 5900 50  0001 C CNN
	1    4400 5900
	1    0    0    -1  
$EndComp
$EndSCHEMATC
