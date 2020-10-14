EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "KiBot Filters Test Schematic"
Date "2020-08-30"
Rev "r1"
Comp "https://github.com/INTI-CMNB/KiBot"
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
F 1 " " V 2200 2550 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 2130 2550 50  0001 C CNN
F 3 "~" H 2200 2550 50  0001 C CNN
	1    2200 2550
	1    0    0    -1  
$EndComp
$Comp
L Device:R R2
U 1 1 5E6A330D
P 2500 2550
F 0 "R2" V 2580 2550 50  0000 C CNN
F 1 "~" V 2500 2550 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 2430 2550 50  0001 C CNN
F 3 "~" H 2500 2550 50  0001 C CNN
	1    2500 2550
	1    0    0    -1  
$EndComp
Text Notes 2750 2600 0    50   ~ 0
Empty value
$Comp
L Device:R R3
U 1 1 5E6A3CA0
P 2200 3100
F 0 "R3" V 2280 3100 50  0000 C CNN
F 1 "4K7" V 2200 3100 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 2130 3100 50  0001 C CNN
F 3 "~" H 2200 3100 50  0001 C CNN
F 4 "" V 2200 3100 50  0001 C CNN "K K"
	1    2200 3100
	1    0    0    -1  
$EndComp
$Comp
L Device:R R4
U 1 1 5E6A3F38
P 2500 3100
F 0 "R4" V 2580 3100 50  0000 C CNN
F 1 "4700" V 2500 3100 50  0000 C CNN
F 2 "Resistor_SMD:R_0805_2012Metric" V 2430 3100 50  0001 C CNN
F 3 "http://www.google.com/" H 2500 3100 50  0001 C CNN
F 4 "" V 2500 3100 50  0001 C CNN "Q,Q"
	1    2500 3100
	1    0    0    -1  
$EndComp
Text Notes 2750 3150 0    50   ~ 0
With "K K" and "Q,Q" field
$Comp
L Device:R R5
U 1 1 5E6A448B
P 2200 3650
F 0 "R5" V 2280 3650 50  0000 C CNN
F 1 "1k" V 2200 3650 50  0000 C CNN
F 2 "Resistor_SMD:R_0603_1608Metric" V 2130 3650 50  0001 C CNN
F 3 "~" H 2200 3650 50  0001 C CNN
F 4 "K K" V 2200 3650 50  0001 C CNN "BB"
	1    2200 3650
	1    0    0    -1  
$EndComp
$Comp
L Device:R R6
U 1 1 5E6A491A
P 2500 3650
F 0 "R6" V 2580 3650 50  0000 C CNN
F 1 "1000" V 2500 3650 50  0000 C CNN
F 2 "Resistor_SMD:R_0603_1608Metric" V 2430 3650 50  0001 C CNN
F 3 "~" H 2500 3650 50  0001 C CNN
F 4 "Q,Q" V 2500 3650 50  0001 C CNN "BB"
	1    2500 3650
	1    0    0    -1  
$EndComp
Text Notes 2750 3700 0    50   ~ 0
BB field containing "K K" and "Q,Q"
Text Notes 600  1250 0    157  ~ 0
This schematic serves as a test-file for the KiBot export script.\n\nHere we play with filters.
$Comp
L Device:C C1
U 1 1 5E6A62CC
P 6650 2550
F 0 "C1" H 6675 2650 50  0000 L CNN
F 1 "10nF" H 6675 2450 50  0000 L CNN
F 2 "Capacitor_SMD:C_0603_1608Metric" H 6688 2400 50  0001 C CNN
F 3 "This is a long text, wrap check" H 6650 2550 50  0001 C CNN
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
$EndSCHEMATC
