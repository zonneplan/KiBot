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
Text Notes 500  750  0    79   ~ 0
This schematic serves as a test-file for the KiBot export script.\nHere we implement the IBoM variants style.
$Comp
L Device:C C1
U 1 1 5F43BEC2
P 1000 1700
F 0 "C1" H 1115 1746 50  0000 L CNN
F 1 "1nF" H 1115 1655 50  0000 L CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 1038 1550 50  0001 C CNN
F 3 "~" H 1000 1700 50  0001 C CNN
F 4 "T2" H 1000 1700 50  0001 C CNN "Config"
	1    1000 1700
	1    0    0    -1  
$EndComp
$Comp
L Device:C C2
U 1 1 5F43CE1C
P 1450 1700
F 0 "C2" H 1565 1746 50  0000 L CNN
F 1 "1000 pF" H 1565 1655 50  0000 L CNN
F 2 "Capacitor_SMD:C_0805_2012Metric" H 1488 1550 50  0001 C CNN
F 3 "~" H 1450 1700 50  0001 C CNN
F 4 "T3" H 1450 1700 50  0001 C CNN "Config"
	1    1450 1700
	1    0    0    -1  
$EndComp
$Comp
L Device:R R1
U 1 1 5F43D144
P 2100 1700
F 0 "R1" H 2170 1746 50  0000 L CNN
F 1 "1k" H 2170 1655 50  0000 L CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 2030 1700 50  0001 C CNN
F 3 "~" H 2100 1700 50  0001 C CNN
F 4 "default" H 2100 1700 50  0001 C CNN "Config"
	1    2100 1700
	1    0    0    -1  
$EndComp
$Comp
L Device:R R2
U 1 1 5F43D4BB
P 2500 1700
F 0 "R2" H 2570 1746 50  0000 L CNN
F 1 "1000" H 2570 1655 50  0000 L CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 2430 1700 50  0001 C CNN
F 3 "~" H 2500 1700 50  0001 C CNN
F 4 "T1" H 2500 1700 50  0001 C CNN "Config"
	1    2500 1700
	1    0    0    -1  
$EndComp
Text Notes 5950 3200 0    118  ~ 0
The test tests the following \nvariants matrix:\n        production   test   default\nC1                     X\nC2          X          X\nR1          X          X       X\nR2          X                  X\n\nproduction: blacklist T2\ntest: blacklist T1\ndefault: whitelist T1,default \n         blacklist T2,T3
$EndSCHEMATC
