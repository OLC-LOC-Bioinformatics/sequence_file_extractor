# sequence_file_extractor
Written by Devon Mack, March 31 2017                                             

This program will pull all requested fasta and fastq files into the folder of your choice.
In addition it can create a redmine folder for you with a list of all the files you pulled.

## Prerequisites:
- Python 3
      
## Installation:                                                                                                

`git clone https://github.com/devonpmack/sequence_file_extractor.git`

## Usage:

First enter your information into the retrieve.txt file. The format is like this:

```
#<NAME>
#fastq
<seq id>
<seq id>
<seq id>
...
#fasta
<seq id>
```

You can also use more than one name to request more than one set of files. They will each go in separate folders based on your name.

#### Example:
```
#This_is_a_test
#Fastq
2013-SEQ-0107
2013-SEQ-0108
2014-SEQ-0093
#fasta
2013-SEQ-0135

#Test2
#fastq
2015-SEQ-1855
2015-SEQ-1856
2015-SEQ-1858
2016-SEQ-0732
2016-SEQ-0734
2016-SEQ-0735
2016-SEQ-0736
#fasta
2013-SEQ-0192
#fastq
2013-SEQ-0138

#test3
#Fastq
2016-SEQ-0761
2016-SEQ-0767
2016-SEQ-0768
2016-SEQ-0769
2016-SEQ-0770
```

Next edit the config.ini file to set where you would like to store the extracted files.

Finally run the command:

`python3 retrieve.py`

Optionally, you can set a redmine ticket and it will create a folder in bio_requests for you for each name that includes a text file with the seq ids of all the files you extracted.

`python3 retrieve.py -r 8882`


