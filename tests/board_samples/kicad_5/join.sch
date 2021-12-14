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
L Connector:Conn_01x02_Male J1
U 1 1 5F10E435
P 2850 2300
F 0 "J1" H 2750 2200 50  0000 C CNN
F 1 "Molex KK" H 2850 2100 50  0000 C CNN
F 2 "" H 2850 2300 50  0001 C CNN
F 3 "https://www.molex.com/webdocs/datasheets/pdf/en-us//0022232021_PCB_HEADERS.pdf" H 2850 2300 50  0001 C CNN
F 4 "900-0022232021-ND" H 2850 2300 50  0001 C CNN "digikey#"
F 5 "0022232021" H 2850 2300 50  0001 C CNN "manf#"
F 6 "Molex" H 2850 2300 50  0001 C CNN "manf"
	1    2850 2300
	1    0    0    -1  
$EndComp
$Comp
L Connector:Conn_01x02_Male J2
U 1 1 5F10E81F
P 4500 2300
F 0 "J2" H 4450 2200 50  0000 R CNN
F 1 "Molex KK" H 4700 2100 50  0000 R CNN
F 2 "" H 4500 2300 50  0001 C CNN
F 3 "https://www.molex.com/webdocs/datasheets/pdf/en-us//0022232021_PCB_HEADERS.pdf" H 4500 2300 50  0001 C CNN
F 4 "900-0022232021-ND" H 4500 2300 50  0001 C CNN "digikey#"
F 5 "0022232021" H 4500 2300 50  0001 C CNN "manf#"
F 6 "Molex" H 4500 2300 50  0001 C CNN "manf"
	1    4500 2300
	-1   0    0    -1  
$EndComp
$Comp
L Device:R R1
U 1 1 5F10F746
P 3450 2300
F 0 "R1" V 3350 2300 50  0000 C CNN
F 1 "1k" V 3450 2300 50  0000 C CNN
F 2 "" V 3380 2300 50  0001 C CNN
F 3 "https://www.bourns.com/docs/product-datasheets/CRxxxxx.pdf" H 3450 2300 50  0001 C CNN
F 4 "CR0805-JW-102ELFCT-ND" V 3450 2300 50  0001 C CNN "digikey#"
F 5 "CR0805-JW-102ELF" V 3450 2300 50  0001 C CNN "manf#"
F 6 "5%" V 3450 2300 50  0001 C CNN "Tolerance"
F 7 "Bourns" V 3450 2300 50  0001 C CNN "manf"
	1    3450 2300
	0    1    1    0   
$EndComp
$Comp
L Device:C C1
U 1 1 5F10F92F
P 3750 2500
F 0 "C1" H 3865 2546 50  0000 L CNN
F 1 "1nF" H 3865 2455 50  0000 L CNN
F 2 "" H 3788 2350 50  0001 C CNN
F 3 "https://content.kemet.com/datasheets/KEM_C1002_X7R_SMD.pdf" H 3750 2500 50  0001 C CNN
F 4 "399-1147-1-ND" H 3750 2500 50  0001 C CNN "digikey#"
F 5 "C0805C102K5RACTU" H 3750 2500 50  0001 C CNN "manf#"
F 6 "10%" H 3750 2500 50  0001 C CNN "Tolerance"
F 7 "KEMET" H 3750 2500 50  0001 C CNN "manf"
F 8 "50V" H 3750 2500 50  0001 C CNN "Voltage"
F 9 "Alternative" H 3750 2500 50  0001 C CNN "SMN1"
	1    3750 2500
	1    0    0    -1  
$EndComp
Wire Wire Line
	3050 2300 3300 2300
Wire Wire Line
	3600 2300 3750 2300
Wire Wire Line
	3750 2350 3750 2300
Connection ~ 3750 2300
Wire Wire Line
	3750 2300 4300 2300
Wire Wire Line
	3050 2400 3200 2400
Wire Wire Line
	3200 2400 3200 2750
Wire Wire Line
	3200 2750 3750 2750
Wire Wire Line
	3750 2750 3750 2650
Wire Wire Line
	3750 2750 4150 2750
Wire Wire Line
	4150 2750 4150 2400
Wire Wire Line
	4150 2400 4300 2400
Connection ~ 3750 2750
$EndSCHEMATC
