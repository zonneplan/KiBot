EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "KiCost Test Schematic"
Date "2021-04-06"
Rev "A"
Comp "INTI - MyNT"
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
Text Notes 500  600  0    79   ~ 0
This schematic serves as a test-file for the KiBot export script.\n
Text Notes 5950 2600 0    118  ~ 0
The test tests the following \nvariants matrix:\n        production   test   default\nC1                     X\nC2          X          X\nR1          X          X       X\nR2          X                  X\n
$Comp
L Device:C C1
U 1 1 5F43BEC2
P 1000 1700
F 0 "C1" H 1115 1746 50  0000 L CNN
F 1 "1nF" H 1115 1655 50  0000 L CNN
F 2 "" H 1038 1550 50  0001 C CNN
F 3 "~" H 1000 1700 50  0001 C CNN
F 4 "-production,+test" H 1000 1700 50  0001 C CNN "Config"
F 5 "Samsung" H 1000 1700 50  0001 C CNN "manf"
F 6 "CL10B102KC8NNNC" H 1000 1700 50  0001 C CNN "manf#"
F 7 "1276-1131-1-ND" H 1000 1700 50  0001 C CNN "digikey#"
F 8 "20%" H 1000 1700 50  0001 C CNN "tolerance"
F 9 "50 V" H 1000 1700 50  0001 C CNN "voltage"
F 10 "1000pF" H 1000 1700 50  0001 C CNN "capacitance"
	1    1000 1700
	1    0    0    -1  
$EndComp
$Comp
L Device:C C2
U 1 1 5F43CE1C
P 1450 1700
F 0 "C2" H 1565 1746 50  0000 L CNN
F 1 "1000 pF" H 1565 1655 50  0000 L CNN
F 2 "" H 1488 1550 50  0001 C CNN
F 3 "~" H 1450 1700 50  0001 C CNN
F 4 "+production,+test" H 1450 1700 50  0001 C CNN "Config"
F 5 "Samsung" H 1000 1700 50  0001 C CNN "manf"
F 6 "CL10B102KC8NNNC" H 1000 1700 50  0001 C CNN "manf#"
F 7 "1276-1131-1-ND" H 1000 1700 50  0001 C CNN "digikey#"
F 8 "100 V" H 1450 1700 50  0001 C CNN "voltage"
F 9 "1000pF" H 1450 1700 50  0001 C CNN "capacitance"
	1    1450 1700
	1    0    0    -1  
$EndComp
$Comp
L Device:R R1
U 1 1 5F43D144
P 2100 1700
F 0 "R1" H 2170 1746 50  0000 L CNN
F 1 "1k" H 2170 1655 50  0000 L CNN
F 2 "" V 2030 1700 50  0001 C CNN
F 3 "~" H 2100 1700 50  0001 C CNN
F 4 "3k3" H 2100 1700 50  0001 C CNN "test:Value"
F 5 "Bourns" H 1000 1700 50  0001 C CNN "manf"
F 6 "CR0603-JW-102ELF" H 1000 1700 50  0001 C CNN "manf#"
F 7 "CR0603-JW-102ELFCT-ND" H 1000 1700 50  0001 C CNN "digikey#"
F 8 "CR0603-JW-332ELF" H 1000 1700 50  0001 C CNN "test:manf#"
F 9 "CR0603-JW-332ELFCT-ND" H 1000 1700 50  0001 C CNN "test:digikey#"
F 10 "1%" H 2100 1700 50  0001 C CNN "tolerance"
F 11 "1000" H 2100 1700 50  0001 C CNN "Resistance"
	1    2100 1700
	1    0    0    -1  
$EndComp
$Comp
L Device:R R2
U 1 1 5F43D4BB
P 2500 1700
F 0 "R2" H 2570 1746 50  0000 L CNN
F 1 "1000" H 2570 1655 50  0000 L CNN
F 2 "" V 2430 1700 50  0001 C CNN
F 3 "~" H 2500 1700 50  0001 C CNN
F 4 "-test" H 2500 1700 50  0001 C CNN "Config"
F 5 "Bourns" H 1000 1700 50  0001 C CNN "manf"
F 6 "CR0603-JW-102ELF" H 1000 1700 50  0001 C CNN "manf#"
F 7 "CR0603-JW-102ELFCT-ND" H 1000 1700 50  0001 C CNN "digikey#"
F 8 "5%" H 1000 1700 50  0001 C CNN "tolerance"
F 9 "1000" H 2500 1700 50  0001 C CNN "Resistance"
	1    2500 1700
	1    0    0    -1  
$EndComp
$EndSCHEMATC
