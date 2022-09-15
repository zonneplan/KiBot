#!/usr/bin/perl

$outputs =`../src/kibot --help-outputs`;
$cmd_help=`../src/kibot --help`;
$preflight=`../src/kibot --help-preflights`;
$filters=`../src/kibot --help-filters`;
$variants=`../src/kibot --help-variants`;
$global_options=`../src/kibot --help-global-options`;
$dependencies=`../src/kibot --help-dependencies --markdown`;
$json_dep=`../src/kibot --help-dependencies --json`;
$json_dep=~s/\n/\\\n/g;

while (<>)
  {
   $_ =~ s/\@outputs\@/$outputs/;
   $_ =~ s/\@cmd_help\@/$cmd_help/;
   $_ =~ s/\@preflight\@/$preflight/;
   $_ =~ s/\@filters\@/$filters/;
   $_ =~ s/\@variants\@/$variants/;
   $_ =~ s/\@global_options\@/$global_options/;
   $_ =~ s/\@dependencies\@/$dependencies/;
   $_ =~ s/\@json_dep\@/$json_dep/;
   print $_;
  }


