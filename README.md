# EmpireTune
Invention of Targeted Theorem Proving Strategies for E and Vampire

This is a pre-BETA release.  It is usable with some effort.

## Requirements

This distribution contains other software packages:

* GNU Parallel (https://www.gnu.org/software/parallel)
* ParamILS (http://www.cs.ubc.ca/labs/beta/Projects/ParamILS)
* E Prover (http://www.eprover.org) 
   
   You need E "hacked" version 2.0 with 6 new clause evaluation functions.
   A binary for x86 is provided in `atp/bin/eprover`.  Source codes can be
   obtained at:
   
      http://people.ciirc.cvut.cz/~jakubja5/src/E-2.0-PARG.tar.gz

Additionally you need to obtain a Vampire binary (http://www.vprover.org):
   
   Ask Martin Suda (msuda at forsyte.org).
   

To run this software you need to have Python, Perl, and Ruby installed.
You also need the Perl SHA1 package (from CPAN).

## Quickstart

### Prepare experiments

0. Setup environment before running import scripts:
   
   ```
   $ . ./setenv.sh
   ```
   Always run the scripts from the EmpireTune directory.

1. Import benchmark problems:

   ```
   $ ./import-benchmark.sh eprover examples/bechmarks/test test  
   importing examples/bechmarks/test as test ... 10 problems imported
   ```

2. Import initial protocols:

   ```
   $ ./import-inits.sh eprover examples/inits/eprover/tptp tptp
   importing examples/inits/eprover/tptp as tptp ... 10 strategies imported
   ```

### Setup experiments

   ```
   $ vi EmpireTune-RUN.sh
   ```

### Run experiments

   ```
   $ ./EmpireTune-RUN.sh
   ```

### Get results 

   Find the invented strategies in the EmpireTune*/prots directory.

