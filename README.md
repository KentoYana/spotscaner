# SpotScaner
Recognize &amp; Analyze images of Spot-test in Fungal Genetics

This is the SpotScaner v6.1.0, Coordinated by Kento Yanagisawa.
> Take a photo of spot-test plate with the printed marker,
> and then run this command. You can get a results.csv
usage: spotscaner [-h] [-v] [-e] [-g {marker,cite}] [-a {pipette,replicator}]
                  [-s SINGLE | -m] [-t {1,2,3,4,5,6,7,8,9,10}]

options:
  -h, --help            show this help message and exit
  -v, --version         show version, citation and exit
  -e, --example         show usage example and exit
  -g {marker,cite}, --generate {marker,cite}
                        open the file chosen this option
  -a {pipette,replicator}, --analyze {pipette,replicator}
                        chose analyzing mode (pipette: 4*6 matrix, replicator:
                        8*12 matrix)
  -s SINGLE, --single SINGLE
                        analyze only the inputted image.
  -m, --multi           analyze all images in the current directory
  -t {1,2,3,4,5,6,7,8,9,10}, --threshold {1,2,3,4,5,6,7,8,9,10}
                        threshold for marker recognition(default: 7)
