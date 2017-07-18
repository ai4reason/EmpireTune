#!/usr/bin/perl -w

=head1 NAME

BliStr.pl (Grow new strategies for E prover by running ParamILS (local search) on suitable problem sets)

=head1 SYNOPSIS

# modify $grootdir and the params above it
# install by running the setupdir.sh script
# if starting with different strategies, describe them in %ginitstrnames
# then:

time ./BliStr.pl 

=head1 DESCRIPTION

BliStr is a system that automatically develops strategies for E prover
on a large set of problems. The main idea is to interleave (i)
iterated low-timelimit local search for new strategies on small sets
of similar easy problems with (ii) higher-timelimit evaluation of the
new strategies on all problems. The accummulated results of the global
higher-timelimit runs are used to evolve the definition of ``easy
similar'' sets of problems, and to control the selection of the next
strategy to be improved.

=head1 COPYRIGHT

Copyright (C) 2012-2013 Josef Urban (firstname dot lastname at gmail dot com)

=head1 LICENCE

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

=cut

use strict;
use File::Copy qw(copy);
use Digest::SHA1  qw(sha1 sha1_hex sha1_base64);
use Cwd qw(realpath getcwd);
use File::Basename;

my $gtesttime  = $ENV{'BST_EVAL_LIMIT'}; # time for testing runs in seconds
my $gmaxiter   = 1000; # max number of the main loop iterations
my $gCores = $ENV{'CORES'}; # number of cores for testing
my $gmaxstrnr = $ENV{'BST_TOPS'}; # The number of top strategies we grow (N)
my $gminstrprobs = $ENV{'BST_VERS'}; # Minimal number of problems where the strategy should be best (versatility)
my $gminproc = $ENV{'BST_MIN_PROC'};
my $gmaxproc = $ENV{'BST_MAX_PROC'};

# the root dir for operations
#my $grootdir = '/home/yan/BliStr-orig';
#my $grootdir = realpath(dirname($0));
my $grootdir = getcwd();
$ENV{ENIGMA_ROOT}="$grootdir/Enigma";

# the diredtory with all problems and generated protocol solutions 
my $gallprobs = "$grootdir/allprobs"; 

# the directory with initial (non-generated) protocol solutions
# the protocols will be copied to $gallprobs using the generated names
# their strategy descriptions have to exist in %ginitstrnames
my $ginitprots = "$grootdir/initprots"; 

# install with rootdir as $1 :
# mkdir $1; cd $1
# mkdir allprobs; mkdir strats; mkdir prots
# wget http://www.cs.ubc.ca/labs/beta/Projects/ParamILS/paramils2.3.5-source.zip
# unzip paramils2.3.5-source.zip
# cd paramils2.3.5-source
# mkdir example_data/e1
my $gepymils = "$grootdir/epymils";

# directory with the e1 subdirectory containing problems
# and .txt and tst files with problems selection
# my $gPIexmpldir = $gPIdir . "/example_data";

# here are scenario files like 
# example_e1/scenario-protocol_my17simple.10.txt
# my $gPIscendir = $gPIdir . "/example_e1";

# the place to put finished strategies in
my $gstratsdir = "$grootdir/strats";

# the place to put E protocol defs in
my $gprotsdir = "$grootdir/prots";

# directory to add to problem names
my $gprobprefix = $ENV{'BST_BENCHMARK'};

# problem name suffix
my $gprobsuffix = '.tptp'; # '.p'; # .p.leancop.cnf

$gmaxstrnr = 20 unless(defined($gmaxstrnr));
$gminstrprobs = 8 unless(defined($gminstrprobs));

my $gprover = $ENV{'BST_PROVER'};
my $gkeyword = "";
my $gprovercmd = "";
my $gtunerbin = "";
my $gparambin = "";
if ($gprover eq "eprover") {
   $gkeyword = "Theorem";
   $gprovercmd = "perf stat -e task-clock:up,page-faults:up,instructions:up eprover -s -p -R --memory-limit=1024 --print-statistics --tstp-format --cpu-limit=$gtesttime";
   $gtunerbin = "eprover_tune.py";
   $gparambin = "eprover_params.py";
}
else {
   $gkeyword = "Tanya";
   $gprovercmd = "perf stat -e task-clock:up,page-faults:up,instructions:up vampire --statistics full -m 2048 -t $gtesttime";
   $gtunerbin = "vampire_tune.py";
   $gparambin = "vampire_params.py";
}
    
# prefix for strategy def files (in the paramils language)
my $gstrdefname = $gprover . '_';

# prefix for E protocol def files (in E language)
my $gprotname = 'protocol_' . $gstrdefname;

# this was a misunderstaning: numRun is just for bookkeeping
my $gN = 1; # the N parameter for paramils

# init strategies
my $atp_root = $ENV{'ATP_ROOT'};
my $initstrats = $ENV{'BST_INITSTRATS'};
my $initstrats_dir = "$atp_root/inits/$gprover/$initstrats/strats";

my %ginitstrnames;
opendir(DIR, $initstrats_dir) or die $!;
while (my $file = readdir(DIR)) {
   next unless (-f "$initstrats_dir/$file");
   my $key = "protocol_$file";
   $ginitstrnames{$key} = `cat $initstrats_dir/$file`;
}

# initialize with the covering strategies
my %gstrnames = %ginitstrnames;

# record the previous attempts
my %gtested = ();

# for each problem count of prmils runs weighted by the number of problems in each run
my %gprobruncnt = ();

# prefer diversity (explore & exploit)
my $gdiverse = 1;

my $gstarttime = time();

sub LOG {print @_;}



# For each protocol in $%v, print its hash of best-solved problems
# with their performance. Only do this for the problems withe
# performance between min and max.
sub PrintProbStr
{
   my ($v,$min,$max) = @_;
   foreach my $p (sort keys %$v) {
      print "\n$p:\n";
      foreach my $k (sort keys %{$v->{$p}}) {
         print "$k:$v->{$p}{$k}\n" if(($v->{$p}{$k}>=$min) && ($v->{$p}{$k}<=$max));
      }
   }
}



# the info about proiblems, protocols, and perfomance in lines of form:
# MZT001+1.p.protocol_my17simple:# Processed clauses                    : 51
#
# Returns the hash of the best strategies and the counts hash
sub TopStratProbs
{
    my ($maxstr,$minstrprobs,$min,$max) = @_;

    my %g = (); #  the best strategy name for a problem
    my %h = ();   #  best (lowest) score so far for each problem
    my %i = (); #  the second lowest score for each poblem
    my %j = (); #  the second best strategy name for a problem
    my %v = (); #  for each strategy keeps the names of best problems and their scores
    my %c = (); #  for each strategy the (adjusted) count of best solutions
    my %sol = ();

    chdir $gallprobs;
    open(RESULTS,"ls | grep protocol_ | xargs grep -l $gkeyword | xargs grep -H instructions:up |") or die;
    while (<RESULTS>)
    {
       m/^([^.]*)\..*protocol_([^:]*): *([0-9,]+) .*/ or die;
       my $q = $3;
       $q =~ tr/,//d;
       $q = int($q / 1000000);
		 $sol{$2}{$1} = $q;
       if ((! exists($h{$1})) || ($h{$1} > $q))
       {
          $i{$1}=$h{$1};
          $j{$1}=$g{$1};
          $h{$1} = $q;
          $g{$1} = $2;
       }
    }
    close(RESULTS);

    my $allsolved = scalar(keys %h);
    my $runtime = time() - $gstarttime;
    LOG "TOTALSOLVED: $runtime $allsolved\n";

    # zero the $gprobruncnt of newly solved problems
    foreach my $pr (keys %h) { $gprobruncnt{$pr}=0 unless exists($gprobruncnt{$pr}); }

    # count the eligible best problems for each strategy
    # TODO: this means that we disregard the info about easy and very hard problems - could be problematic at some point

    foreach my $k (keys %g) { $c{$g{$k}}++ if( ($h{$k} >= $min) &&  ($h{$k}<=$max)); }

    #print %c,"\n";

    
    # if the eligible count is low, set it to 0 (will boost versatile strats)
    # TODO: after deleting, we could consider again the problems on which the deleted strategies were best

    foreach my $s (keys %c) { $c{$s}=0 if( $c{$s} < $minstrprobs ); }

    #print %c,"\n";

    # also take only best $maxstr strategies, set rest to 0

    my $cnt = 0;
    my @bestorder0 = sort {$c{$b} <=> $c{$a}} keys %c;
    my $bestpr = $bestorder0[0];
    my @bestorder = ();
    foreach my $s (@bestorder0) 
    { 
       $cnt++; 
       $c{$s}=0 if($cnt > $maxstr); 
       push(@bestorder,$s) unless($c{$s}==0);
    }

    #print %c,"\n";

    foreach my $k (sort keys %h)
    {
       $v{$g{$k}}{$k}=$h{$k} if(exists($c{$g{$k}}) && ($c{$g{$k}} > 0));
    }

    return (\@bestorder, \%v, \%h, \%sol );
}


# select suitable training problems
sub StrTrainProbs
{
   my ($str,$v,$h,$min,$max) = @_;
   my %res = ();
   foreach my $k (sort keys %{$v->{$str}})
   {
      if(($v->{$str}{$k}>=$min) && ($v->{$str}{$k}<=$max))
      {
         $res{$k} = ();
      }
   }
   return \%res;
}

# return 1 if a strategy was already grown with a hash of problems
sub AlreadyTested
{
    my ($str,$probs) = @_;

    return 0 unless exists $gtested{$str};

    my $probsstr = join(',', sort keys %{$probs});

    return 0 unless exists $gtested{$str}{$probsstr};

    return 1;
}

# Returns the number of problems used for running prmils
sub PrepareStrategy
{

    my ($str,$v,$h,$iter,$subiter,$trainprobs,$sol) = @_;

    my $dir = "$gepymils/epymils-$iter-$subiter";

    `rm -fr $dir`;
    `cp -r $gepymils/skel $dir`;
    
    open(F,">$dir/data/problems.txt");
    my $i = 0;
    foreach my $k (sort keys %{$trainprobs})
    {
       print F ("$gprobprefix/", "$k", $gprobsuffix, "\n");
       $i++;
    }
    close(F);

    open(F,">$dir/data/all.txt");
    foreach my $k (sort keys %{$sol->{$str}})
    {
       print F ("$gprobprefix/", "$k", $gprobsuffix, "\n");
    }
    close(F);

    return $i;
}


# RULES:
# 1. strategy is a string of prmils keys/values, it lives in a content-named file
# 2. protocol is a corresponding string of E options, it inherits name from its strategy
# 3. new strategies are generated in prmils runs (iterations) from old ones
# 4. one prmils run is described by train files and a strategy
# 5. the prmils scenario and log are in scenario-e$iter.txt and $str.iter$iter.mylog

# grow (the current best) strategy on selected training problems by paramils
# Input: strategy, $iter, nr of test runs, $N
# Return: a strategy content name or 'notnew' or 'error'
# Side effects: creates the new strategy def in $gstratsdir/$gstrdefname$strsha1
#               and the new protocol in $gprotsdir/$gprotname$strsha1
sub GrowStratILS
{

    my ($str,$iter,$subiter,$testnr,$N) = @_;
    my $iter1 = $iter+1;
    my $dir = "$gepymils/epymils-$iter-$subiter";
    chdir $dir;

    system("$gtunerbin $gstratsdir/$str | tee epymils.log");
    my $newstrparams = `cat epymils.log | grep 'RESULT:' | tail -n2`;

	 my @strarr = ();
	 my @resultarr = split(/\n/, $newstrparams);
	 foreach my $newstrparams1 (@resultarr) 
	 {
				if ($newstrparams1 =~ m/.*RESULT: /)
				{
					  $newstrparams1 =~ s/.*RESULT: //;
					  my $strsha1 = sha1_hex($newstrparams1);
					  my $newstr = $gstrdefname . $strsha1;
					  my $strfnm = "$gstratsdir/$newstr";
					  if(-e $strfnm)
					  {
							LOG "NEWSTR: not new: $strfnm\n";
                     push @strarr, 'notnew';
					  }
					  else
					  {
							open(F,">$strfnm");
							print F $newstrparams1;
							close(F);
							`$gparambin $strfnm > $gprotsdir/$gprotname$strsha1`;
							print "NEWSTR: $newstr : $strfnm\n";
							push @strarr, $newstr;
					  }
				}
				else
				{
					LOG "NEWSTR: error\n";
               push @strarr, 'error';
				}
	 }
	 return @strarr;
}

# evaluate on all .p problems a strategy $str with gtesttime 
# $ iter is unused now
sub EvalStrat
{
    my ($str,$iter) = @_;
    my $protnm = 'protocol_' . $str;
    my $prot = `cat $gprotsdir/$protnm`;

    `cd $gallprobs; ls *$gprobsuffix | time parallel -j$gCores "$gprovercmd $prot {} > {}.$protnm 2>&1"`;
}

# Initialize the naming of existing strategies and protocols
# Die if an protocol is unknown
sub InitStratsProts
{
   chdir $ginitprots;
   my @all = glob("*.protocol_*");
   my %prot2file = ();

   foreach my $_ (@all)
   {
      m/^(.*)\.(protocol_.*)/ or die;
      my ($name,$prot) = ($1,$2);
      $prot2file{$prot}{$name}= ();
   }

   my $iter = 0;
   foreach my $prot (sort keys %prot2file)
   {
      exists $ginitstrnames{$prot} or die "Initial protocol description needed: $prot"; 
      $iter++;

      my $strparams = $ginitstrnames{$prot};
      my $strsha1 = sha1_hex($strparams);
      my $newstr = $gstrdefname . $strsha1;
      my $strfnm = "$gstratsdir/$newstr";
      my $protnm = $gprotname . $strsha1;
      open(F,">$strfnm");
      print F $strparams;
      close(F);
      `$gparambin $strfnm > $gprotsdir/$protnm`;
      LOG "INITSTR: $strparams : $strfnm\n";
      LOG "$prot ==> $protnm\n";
      foreach my $f (keys %{$prot2file{$prot}})
      {
         copy("$f.$prot", "$gallprobs/$f.$protnm");
      }
   }
   return $iter;
}

# the main clistr loop
# starts from $i = # initial protocolls
sub Iterate
{
   my ($i)=@_;
   while($i < $gmaxiter)
   {
      $i++;
      LOG "ITER: $i\n";
      # in the current directory, find the best covering set
      my ($beststrs,$v,$h,$sol) = TopStratProbs($gmaxstrnr,$gminstrprobs,$gminproc,$gmaxproc);

      # if diversity prefered, sort the strats by lowest avrg previous run nr 
      if($gdiverse == 1)
      {      
         my %tmp = ();
         my %s = ();
         foreach my $str (@$beststrs)
         {
            my $trainprobs = StrTrainProbs($str,$v,$h,$gminproc,$gmaxproc);
            $s{$str} = scalar(keys %{$trainprobs});
            $tmp{$str} = 0;
            foreach my $pr (keys %{$trainprobs})
            {
               $tmp{$str} += $gprobruncnt{$pr};
            }
            if($tmp{$str} > 0)
            {         
               $tmp{$str} = $tmp{$str}/$s{$str};
            }
         }

         # prefer less-run and bigger size of training set
         my @beststrs1 = sort { $tmp{$a} <=> $tmp{$b} || $s{$b} <=> $s{$a}} keys %tmp;
         $beststrs = \@beststrs1;
      }

      LOG "TOPSTRATS:\n";
      PrintProbStr($v,$gminproc,$gmaxproc);

      #  PrintProbStrFiles($v,10,$gminproc,$gmaxproc);

      # try to improve each of the top strategies until a new strategy is found
      my $j = 0;
      LOG "BEST STARTEGIES COUNT: $#{$beststrs}\n";
STR:
      while($j < $#{$beststrs})
      {
         LOG "SUBITER $j\n";
         my $trainprobs = StrTrainProbs($beststrs->[$j],$v,$h,$gminproc,$gmaxproc);
         if(AlreadyTested($beststrs->[$j],$trainprobs) == 1)
         {
            $j++;
            next STR; 
         }
         my $testnr = PrepareStrategy($beststrs->[$j],$v,$h,$i,$j,$trainprobs,$sol);
         my $probsstr = join(',', sort keys %{$trainprobs});
         LOG "Improving $beststrs->[$j] with $testnr problems: $probsstr\n";
         my @improved = GrowStratILS($beststrs->[$j],$i,$j,$testnr,$gN);

         # update the run stats
         $gtested{$beststrs->[$j]}{$probsstr} = ();       
         foreach my $pr (keys %{$trainprobs})
         {
            $gprobruncnt{$pr} += 1/$testnr;
         }

			#YAN# if($improved[0] eq 'error')
			#YAN# {
			#YAN# 	die;
			#YAN# }
			#YAN# elsif($improved[0] eq 'notnew') 
			#YAN# {
			#YAN# 	# produced an old strat, prepare the next best
			#YAN# 	$j++; $i++;
			#YAN# }
			#YAN# else
			#YAN# {
			#YAN# 	# produced a new strat, evaluate and exit this inner loop
			#YAN# 	EvalStrat($improved[0],$i+1);
			#YAN# 	EvalStrat($improved[1],$i+1);
			#YAN# 	$j = 1+$#{$beststrs};
			#YAN# }
         my $somenew = 0;
         foreach my $newstr (@improved)
         {
            if ($newstr eq 'error') { die; }
            if ($newstr ne 'notnew') {
               $somenew = 1;
               EvalStrat($newstr,$i+1);
            }
         }
         if ($somenew) { $j = 1+$#{$beststrs}; } else { $j++; $i++; }
      }
   }
}

sub BliStr1
{
    my $i = InitStratsProts();
    Iterate($i);
}

my $i = InitStratsProts();

Iterate(2);

# my ($beststrs,$v,$h) = TopStratProbs($gmaxstrnr,$gminstrprobs,$gminproc,$gmaxproc);

# PrintProbStr($v,$gminproc,$gmaxproc);

# PrintProbStrFiles($v,$beststrs->[0],10,$gminproc,$gmaxproc);
