#!/usr/bin/perl

$outputs =`../src/kiplot --help-outputs`;
$cmd_help=`../src/kiplot --help`;

while (<>)
  {
   $_ =~ s/\@outputs\@/$outputs/;
   $_ =~ s/\@cmd_help\@/$cmd_help/;
   print $_;
  }


