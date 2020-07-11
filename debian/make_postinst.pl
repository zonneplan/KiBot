#!/usr/bin/perl
@l=glob('kiplot/*.py');
print("#!/bin/sh\n");
print("set -e\n");
foreach $v (@l)
   {
    $a = `grep "import macros" $v`;
    if ($?)
      {
       $v = "/usr/lib/python3/dist-packages/$v";
       $cmd = "py3compile -V 3.2- $v";
       print("$cmd\n");
      }
   }
