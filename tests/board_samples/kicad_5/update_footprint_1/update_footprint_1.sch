EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "Test for footprint replace"
Date ""
Rev "1"
Comp "KiBot"
Comment1 "We try to replace U1"
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L Device:R R1
U 1 1 6609D7EA
P 1900 2100
F 0 "R1" H 1970 2146 50  0000 L CNN
F 1 "R" H 1970 2055 50  0000 L CNN
F 2 "my_lib:R_0805_2012Metric" V 1830 2100 50  0001 C CNN
F 3 "~" H 1900 2100 50  0001 C CNN
	1    1900 2100
	1    0    0    -1  
$EndComp
$Comp
L Amplifier_Operational:AD797 U1
U 1 1 6609E34C
P 3700 2300
F 0 "U1" H 4044 2346 50  0000 L CNN
F 1 "AD797" H 4044 2255 50  0000 L CNN
F 2 "my_lib:SOIC-8-1EP_3.9x4.9mm_P1.27mm_EP2.29x3mm" H 3750 2350 50  0001 C CNN
F 3 "https://www.analog.com/media/en/technical-documentation/data-sheets/AD797.pdf" H 3750 2450 50  0001 C CNN
	1    3700 2300
	1    0    0    -1  
$EndComp
$Comp
L Device:R R2
U 1 1 6609EDAF
P 2300 2100
F 0 "R2" H 2370 2146 50  0000 L CNN
F 1 "R" H 2370 2055 50  0000 L CNN
F 2 "my_lib:R_0805_2012Metric" V 2230 2100 50  0001 C CNN
F 3 "~" H 2300 2100 50  0001 C CNN
	1    2300 2100
	1    0    0    -1  
$EndComp
$Comp
L Device:R R3
U 1 1 6609EF02
P 2700 2100
F 0 "R3" H 2770 2146 50  0000 L CNN
F 1 "R" H 2770 2055 50  0000 L CNN
F 2 "my_lib:R_0805_2012Metric" V 2630 2100 50  0001 C CNN
F 3 "~" H 2700 2100 50  0001 C CNN
	1    2700 2100
	1    0    0    -1  
$EndComp
$Comp
L Graphic:SYM_Radio_Waves_Small SYM1
U 1 1 6609FE1B
P 2700 1500
F 0 "SYM1" H 2700 1640 50  0001 C CNN
F 1 "SYM_Radio_Waves_Small" H 2700 1375 50  0001 C CNN
F 2 "my_lib:ESD-Logo_13.2x12mm_SilkScreen" H 2700 1325 50  0001 C CNN
F 3 "~" H 2730 1300 50  0001 C CNN
	1    2700 1500
	1    0    0    -1  
$EndComp
$EndSCHEMATC
