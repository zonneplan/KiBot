# -*- coding: utf-8 -*-
# Copyright (c) 2023 Salvador E. Tropea
# License: AGPL-3.0
# Project: KiBot (formerly KiPlot)
#
# KiCad axial resistor 3D color generator
#
# Works for R_Axial_DIN* KiCad 6.0.10 3D models
# Nice tool: https://www.digikey.com/en/resources/conversion-calculators/conversion-calculator-resistor-color-code
import re
import sys

# Tolerance bar:
# 20%     -     3
# 10%   Silver  4
#  5%    Gold   4
#  2%    Red    5
#  1%   Brown   5
# 0.5%  Green   5
# 0.25%  Blue   5
# 0.1%  Violet  5
# 0.05% Orange  5
# 0.02% Yellow  5
# 0.01%  Grey   5

# Special multipliers
# Multiplier < 1
# 0.1   Gold
# 0.01  Silver

X = 0
Y = 1
Z = 2
WIDTHS_4 = [5, 12, 10.5, 12, 10.5, 12, 21, 12, 5]
WIDTHS_5 = [5, 10, 8.5, 10, 8.5, 10, 8.5, 10, 14.5, 10, 5]
WIDTHS = WIDTHS_5
STARTS = []
COLORS = [(0.149, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.4), # 0 Black
          (0.149, 0.40, 0.26, 0.13, 0.40, 0.26, 0.13, 0.4), # 1 Brown
          (0.149, 0.85, 0.13, 0.13, 0.85, 0.13, 0.13, 0.4), # 2 Red
          (0.149, 0.94, 0.37, 0.14, 0.94, 0.37, 0.14, 0.4), # 3 Naraja
          (0.149, 0.98, 0.99, 0.06, 0.98, 0.99, 0.06, 0.4), # 4 Yellow
          (0.149, 0.20, 0.80, 0.20, 0.20, 0.80, 0.20, 0.4), # 5 Green
          (0.149, 0.03, 0.00, 0.77, 0.03, 0.00, 0.77, 0.4), # 6 Blue
          (0.149, 0.56, 0.00, 1.00, 0.56, 0.00, 1.00, 0.4), # 7 Violet
          (0.149, 0.62, 0.62, 0.62, 0.62, 0.62, 0.62, 0.4), # 8 Grey
          (0.149, 0.99, 0.99, 0.99, 0.99, 0.99, 0.99, 0.4), # 9 White
          (0.379, 0.86, 0.74, 0.50, 0.14, 0.15, 0.18, 0.4), # 5% Gold (10)
          (0.271, 0.82, 0.82, 0.78, 0.33, 0.26, 0.17, 0.7), # 10% Silver (11)
          (0.149, 0.883, 0.711, 0.492, 0.043, 0.121, 0.281, 0.4), # Body color
         ]
TOL_COLORS = {5: 10, 10: 11, 20: 12, 2: 2, 1: 1, 0.5: 5, 0.25: 6, 0.1: 7, 0.05: 3, 0.02: 4, 0.01: 8}


def write_strip(points, file, axis, n, mat, index, only_coord=False):
    if not only_coord:
        file.write("Shape { geometry IndexedFaceSet\n")
        file.write(index)
    start = points[0][axis]
    end = points[2][axis]
    length = start-end
    width = length/15
    n_start = start-STARTS[n]*length
    n_end = n_start-WIDTHS[n]*length
    new_points = []
    for p in points:
        ax = []
        for a, v in enumerate(p):
            if a == axis:
                ax.append("%.3f" % (n_start if v == start else n_end))
            else:
                ax.append("%.3f" % v)
        new_points.append(' '.join(ax))
    file.write("coord Coordinate { point ["+','.join(new_points)+"]\n")
    if only_coord:
        return
    file.write("}}\n")
    file.write("appearance Appearance{material USE "+mat+" }\n")
    file.write("}\n")


def add_colors(file, colors):
    for bar, c in enumerate(colors):
        col = COLORS[c]
        file.write("Shape {\n")
        file.write("\t\tappearance Appearance {material DEF RES-BAR-%02d Material {\n" % (bar+1))
        file.write("\t\tambientIntensity {}\n".format(col[0]))
        file.write("\t\tdiffuseColor {} {} {}\n".format(col[1], col[2], col[3]))
        file.write("\t\tspecularColor {} {} {}\n".format(col[4], col[5], col[6]))
        file.write("\t\temissiveColor 0.0 0.0 0.0\n")
        file.write("\t\ttransparency 0.0\n")
        file.write("\t\tshininess {}\n".format(col[7]))
        file.write("\t\t}\n")
        file.write("\t}\n")
        file.write("}\n")



val = 1200
tol = 20

if val < 0.01:
    print('Minimum value is 10 mOhms')
    exit(3)
val_str = "{0:.0f}".format(val*100)
print(val_str+" mOhms")
if tol < 5:
    # Use 5 bars for 2 % tol or better
    WIDTHS = WIDTHS_5
    nbars = 5
else:
    WIDTHS = WIDTHS_4
    nbars = 4
bars = [0]*nbars
# Bars with digits
dig_bars = nbars-2
# Fill the multiplier
mult = len(val_str)-nbars
if mult < 0:
    val_str = val_str.rjust(dig_bars, '0')
    mult = min(9-mult, 11)
bars[dig_bars] = mult
# Max is all 99 with 9 as multiplier
max_val = pow(10, dig_bars)-1
if val > max_val*1e9:
    print('Maximum value is {} GOhms'.format(max_val))
    exit(3)
# Fill the digits
for bar in range(dig_bars):
    bars[bar] = ord(val_str[bar])-ord('0')
# Make sure we don't have digits that can't be represented
rest = val_str[dig_bars:]
if rest and not all(map(lambda x: x == '0', rest)):
    print("Warning: digits not represented")
# Fill the tolerance color
tol_color = TOL_COLORS.get(tol, None)
if tol_color is None:
    print('Unknown tolerance {}'.format(tol))
    exit(3)
bars[nbars-1] = tol_color
# For 20% remove the last bar
if tol_color == 12:
    bars = bars[:-1]
    WIDTHS[-3] = WIDTHS[-1]+WIDTHS[-2]+WIDTHS[-3]
    WIDTHS = WIDTHS[:-2]
# Show the result
print(bars)

### Process the 3D model
# Fill the starts
ac = 0
for c, w in enumerate(WIDTHS):
    STARTS.append(ac/100)
    WIDTHS[c] = w/100
    ac += w

fn = sys.argv[1]
ou = sys.argv[2]

m = re.search(r"L([\d\.]+)mm", fn)
if not m:
    print("No length in name")
    exit(3)
r_len = float(m.group(1))

coo_re = re.compile(r"coord Coordinate \{ point \[((\S+ \S+ \S+,?)+)\](.*)")
with open(fn, "rt") as f:
    prev_ln = None
    points = None
    axis = None
    with open(ou, "wt") as d:
        colors_defined = False
        for ln in f:
            if not colors_defined and ln.startswith('Shape { geometry IndexedFaceSet'):
                add_colors(d, bars)
                colors_defined = True
            m = coo_re.match(ln)
            if m:
                index = prev_ln
                points = list(map(lambda x: tuple(map(float, x.split(' '))), m.group(1).split(',')))
                x_len = (points[0][X]-points[2][X])*2.54*2
                if abs(x_len-r_len) < 0.01:
                    print(f"Found horizontal: {round(x_len,2)}")
                    write_strip(points, d, X, 0, 'PIN-01', index, only_coord=True)
                    #d.write(ln)
                    axis = X
                else:
                    y_len = (points[0][Z]-points[2][Z])*2.54*2
                    if abs(y_len-r_len) < 0.01:
                        print(f"Found vertical: {round(y_len,2)}")
                        write_strip(points, d, Z, 0, 'PIN-01', index, only_coord=True)
                        axis = Z
                    else:
                        d.write(ln)
                        points = None
            else:
                d.write(ln)
            if ln == "}\n" and points is not None:
                for st in range(1, len(WIDTHS)):
                    bar = (st>>1)+1
                    write_strip(points, d, axis, st, 'RES-BAR-%02d' % bar if st%2 else 'RES-THT-01', index)
                points = None    
            prev_ln = ln

