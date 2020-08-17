#!/usr/bin/perl

$outputs =`../src/kibot --help-outputs`;
$cmd_help=`../src/kibot --help`;
$preflight=`../src/kibot --help-preflights`;

while (<>)
  {
   $_ =~ s/\@outputs\@/$outputs/;
   $_ =~ s/\@cmd_help\@/$cmd_help/;
   $_ =~ s/\@preflight\@/$preflight/;
   print $_;
  }


