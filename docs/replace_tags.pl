#!/usr/bin/perl

$outputs =`../src/kibot --help-outputs`;
$cmd_help=`../src/kibot --help`;
$preflight=`../src/kibot --help-preflights`;
$filters=`../src/kibot --help-filters`;
$global_options=`../src/kibot --help-global-options`;

while (<>)
  {
   $_ =~ s/\@outputs\@/$outputs/;
   $_ =~ s/\@cmd_help\@/$cmd_help/;
   $_ =~ s/\@preflight\@/$preflight/;
   $_ =~ s/\@filters\@/$filters/;
   $_ =~ s/\@global_options\@/$global_options/;
   print $_;
  }


