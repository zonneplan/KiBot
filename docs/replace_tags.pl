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
$branch=`git rev-parse --abbrev-ref HEAD`;
chomp($branch);
if ($branch eq "dev")
  {
   $doc_id="# **This is the documentation for the current development KiBot, not yet released.**\n";
  }
else
  {
   open(FI, '../kibot/__init__.py');
   while (<FI>)
     {
      if ($_ =~ /__version__\s+=\s+\'([^\']+)\'/)
        {
         $version = $1;
         last;
        }
     }
   $doc_id="# **This is the documentation for KiBot v$version for the current development read [here](https://github.com/INTI-CMNB/KiBot/tree/dev).**\n";
  }

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
   $_ =~ s/\@doc_id\@/$doc_id/;
   print $_;
  }


