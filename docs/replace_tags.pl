#!/usr/bin/perl

$outputs =`../src/kiplot --help-outputs`;
$cmd_help=`../src/kiplot --help`;
$preflight=`../src/kiplot --help-preflights`;

while (<>)
  {
   $_ =~ s/\@outputs\@/$outputs/;
   $_ =~ s/\@cmd_help\@/$cmd_help/;
   $_ =~ s/\@preflight\@/$preflight/;
   print $_;
  }


