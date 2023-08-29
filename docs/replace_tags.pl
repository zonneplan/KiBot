#!/usr/bin/perl

$json_dep=`../src/kibot --help-dependencies --json`;
$json_dep=~s/\n/\\\n/g;

while (<>)
  {
   $_ =~ s/\@json_dep\@/$json_dep/;
   print $_;
  }
