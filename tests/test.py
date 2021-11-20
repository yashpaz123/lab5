#!/usr/bin/python3

import os
import os.path
#import tempfile
import subprocess
import time
import signal
import re
import sys
import xml.etree.ElementTree as ET


file_locations = os.path.expanduser(os.getcwd())
logisim_location = os.path.join(os.getcwd(),"../logisim-evolution-2.15.jar")

def run_test(fname):
  try:
    stdinf = open('/dev/null')
  except Exception as e:
    try:
      stdinf = open('nul')
    except Exception as e:
      print("Could not open nul or /dev/null. Program will most likely error now.")
      sys.exit()
  try:
    proc = subprocess.Popen(["java","-jar",logisim_location,"-tty","table", fname], stdin=stdinf, stdout=subprocess.PIPE)
    lines = proc.stdout.readlines()
  except Exception as e: 
    print(e)
    sys.exit()
  return lines

nandnorxor_colnames = ["X", "Y", "NAND_Result", "NOR_Result", "XOR_Result"]
def parse(line, name2field):
  if type(line) == type(bytes()):
      line = line.decode('utf-8')
  fields = re.split('\t+', line.rstrip())
  if len(fields) != len(name2field):
      print("number of columns in line (%d) does not match known column names (%d)" % (len(fields), len(name2field)))
      return {}
  for i in range(len(fields)):
      if fields[i].find('x') != -1:
        print("circuit is incomplete (i.e. result contains x characters)")
        return {}
      fields[i] = fields[i].replace(' ', '')
  return dict(zip(name2field, fields))
  
def test_nandnorxor(fname):
  lines = run_test(fname)
  #check the result of NAND
  print("Checking NAND...", end='')
  for l in lines:
    cols = parse(l, nandnorxor_colnames)
    if not cols:
        return 1
    x = int(cols["X"])
    y = int(cols["Y"])
    r = int(cols["NAND_Result"])
    r0 = int(not(x and y))
    if r != r0:
      print("X=%d Y=%d Result=%d (expected result=%d)" % (x, y, r, r0))
      return 1
  print("OK")    
  #check the result of NOR
  print("Checking NOR...", end='')
  for l in lines:
    cols = parse(l, nandnorxor_colnames)
    if not cols:
        return 1
    x = int(cols["X"])
    y = int(cols["Y"])
    r = int(cols["NOR_Result"])
    r0 = int(not(x or y))
    if r != r0:
      print("X=%d Y=%d Result=%d (expected result=%d)" % (x, y, r, r0))
      return 1
  print("OK")

  #check the result of XOR
  print("Checking XOR...", end='')
  for l in lines:
    cols = parse(l, nandnorxor_colnames)
    if not cols:
        return 1
    x = int(cols["X"])
    y = int(cols["Y"])
    r = int(cols["XOR_Result"])
    r0 = x ^ y
    if r != r0:
      print("X=%d Y=%d Result=%d (expected result=%d)" % (x, y, r, r0))
      return 1
  print("OK")
  return 0

mux2to1_colnames = ["X", "Y", "S", "Mux2to1_Result"]
def test_mux2to1(fname):
  lines = run_test(fname)
  print("Checking Mux2to1...", end='')
  for l in lines:
    cols = parse(l, mux2to1_colnames)
    if not cols:
        return 1
    x = int(cols["X"])
    y = int(cols["Y"])
    s = int(cols["S"])
    r = int(cols["Mux2to1_Result"])
    if s == 0:
      r0 = x
    else:
      r0 = y
    if r != r0:
      print("X=%d Y=%d S=%d Result=%d (expected result=%d)" % (x, y, s, r, r0))
      return 1
  print("OK")
  return 0

negsign_colnames = ["X", "Negsign_Result"]
def test_negsign(fname):
  lines = run_test(fname)
  print("Checking NegSign...", end='')
  for l in lines:
    cols = parse(l, negsign_colnames)
    if not cols:
        return 1
    x_str = cols["X"]
    r_str = cols["Negsign_Result"]
    if len(x_str) != 8 or len(r_str) !=8:
      print("incorrect field length for X (%d %d)" % (len(x_str), len(r_str)))
      return 1
    if x_str[0] == r_str[0]:
      print("X=%s Result=%s MSB should not be the same" % (x_str, r_str))
      return 1
    for i in range(1, len(x_str)):
      if x_str[i] != r_str[i]:
        print("X=%s Result=%s bit at position %d should not differ" % (len(x_str)-i-1))
        return 1
  print("OK")
  return 0

mux4to1_colnames = ["A", "B", "C", "D", "S", "Dec2to4_Result", "Mux4to1_Result"]
def test_mux4to1(fname):
  lines = run_test(fname)
  print("Checking Dec2to4...", end='')
  inputs = [-1,-1,-1,-1]
  for l in lines:
    cols = parse(l, mux4to1_colnames)
    if not cols:
        return 1
    s_str = cols["S"]
    if len(s_str) != 2:
        print("incorrect field length for S (%d)", len(s_str))
        return 1
    s = (int(s_str[0])<<1) | int(s_str[1])

    r0 = ""
    for i in range(0,4):
      if i == s:
        r0 = "1" + r0
      else:
        r0  = "0" + r0
    r = cols["Dec2to4_Result"]
    if r != r0:
      print("S=%s Result=%s (expected result=%s)" % (s_str, r, r0))
      return 1
  print("OK")

  print("Checking Mux4to1...", end='')
  inputs = [-1,-1,-1,-1]
  for l in lines:
    cols = parse(l, mux4to1_colnames)
    if not cols:
        return 1
    inputs[0] = cols["A"]
    inputs[1] = cols["B"]
    inputs[2] = cols["C"]
    inputs[3] = cols["D"]
    s_str = cols["S"]
    if len(s_str) != 2:
        print("incorrect field length for S (%d)", len(s_str))
        return 1
    s = (int(s_str[0])<<1) | int(s_str[1])

    r = cols["Mux4to1_Result"]
    r0 = inputs[s]
    if r != r0:
      print("A=%s B=%s C=%s D=%s S=%s Result=%s (expected result=%s)" % (inputs[0], inputs[1], inputs[2], inputs[3], s_str, r, r0))
      return 1
  print("OK")

  return 0

def static_check(fname, forbidden_circs):
  tree = ET.parse(fname) 
  root = tree.getroot()
  for circ in root.findall('circuit'):
    for item in circ:
      if item.tag == "comp":
        if item.attrib['name'] in forbidden_circs:
          print("You cannot use built-in circuit named %s" % (item.attrib['name']))
          sys.exit(1)
  return 

FSM_colnames = ["FSM_Input", "St0", "St1", "Next_St1", "Next_St0"]
reference_out=[
"0	0	0	0	1",
"1	0	0	1	0",
"0	1	0	1	1",
"1	1	0	1	0",
"0	0	1	0	1",
"1	0	1	1	1",
"0	1	1	1	1",
"1	1	1	1	1",
"0	0	0	0	1"]

def test_FSM(fname):
  lines = run_test(fname)
  print("Checking FSM...", end='')
  for i in range(0, len(lines)):
    cols = parse(lines[i], FSM_colnames)
    if not cols:
        return 1
    cols_ref = parse(reference_out[i], FSM_colnames)
    if cols["FSM_Input"] != cols_ref["FSM_Input"] or cols["St0"] != cols_ref["St0"] or cols["St1"] != cols_ref["St1"]:
      print("Mismatched FSM_Input/St0/St1 compared to reference output? Not possible")
      return 1
    if cols["Next_St1"] != cols_ref["Next_St1"]:
      print("FSM_Input=%s St0=%s St1=%s Next_St1=%s (expected Next_St1=%s)" % (cols["FSM_Input"], cols["St0"], cols["St1"], cols["Next_St1"] , cols_ref["Next_St1"]) )
      return 1
    if cols["Next_St0"] != cols_ref["Next_St0"]:
        print("FSM_Input=%s St0=%s St1=%s Next_St0=%s (expected Next_St0=%s)" % (cols["FSM_Input"], cols["St0"], cols["St1"], cols["Next_St0"] , cols_ref["Next_St0"])) 
        return 1
  print("OK")
  return 0

shr_colnames = ["A", "B", "Result"]
def test_shr(fname):
  lines = run_test(fname)
  print("Checking shr...", end='')
  for l in lines:
    cols = parse(l, shr_colnames)
    if not cols:
        return 1
    a = int(cols["A"], 2)
    b = int(cols["B"], 2)
    r0 = a >> b
    r0_str = "{0:b}".format(r0).zfill(8)
    if cols["Result"] != r0_str:
      print("A=%s B=%s Result=%s (expected result %s)" % (cols["A"], cols["B"], cols["Result"], r0_str))
      return 1
  print("OK")
  return 0

if __name__ == '__main__':
  if len(sys.argv) < 2 :
    print("usage: test.py [part1 | FSM | shr | all]")
    sys.exit(1)

  if sys.argv[1] == "part1" or sys.argv[1] == "all":
    static_check("part1.circ", forbidden_circs = ["NAND Gate", "NOR Gate", "Decoder", "Multiplexer"])
    test_nandnorxor("nand_nor_xor_test.circ")
    test_mux2to1("mux2to1_test.circ")
    test_negsign("negsign_test.circ")
    test_mux4to1("mux4to1_test.circ")

  if sys.argv[1] == "FSM" or sys.argv[1] == "all":
    test_FSM("FSM_test.circ")

  if sys.argv[1] == "shr" or sys.argv[1] == "all":
    static_check("shr.circ", forbidden_circs = ["Shifter"])
    test_shr("shr_test.circ")
