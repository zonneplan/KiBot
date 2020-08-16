import yaml
document = []
document.append("""
v1: 1
v2: 5.3
v3: -3.0e6
""")  # 0
document.append("""
v1: true
v2: false
""")  # 1
document.append("""
v1: True
v2: False
""")  # 2
document.append("""
v1: Hi!
v2: '3'
v3: \"true\"
v4: \"  I have spaces  \"
""")  # 3
document.append("""
- abc
- '3'
- \"true\"
- \"  I have spaces  \"
""")  # 4
document.append("""
people:
  - John
  - Cindy
  - Luca
  - Laura
""")  # 5
document.append("""
John:
  age: 25
  gender: male
""")  # 6
document.append("""
people:
  - John:
      age: 25
      gender: male
  - Cindy
  - Luca
  - Laura
""")  # 7
document.append("""
list_of_lists:
  - - a
    - b
    - c
  - - 1
    - 2
    - 3
    - 4
""")  # 8
document.append("""
list_of_lists:
  - [ a, b, c ]
  - [ 1, 2, 3, 4 ]
""")  # 9
document.append("""
people:
  - John: { age: 25, gender: male }
  - Cindy
  - Luca
  - Laura
""")  # 10
document.append("""
people: [['a','b'],['c','d']]
""")  # 11


print(yaml.load(document[-1]))
