# sequence_file_extractor
Written by Devon Mack, May 2017                                             

This program will pull all requested fasta and fastq files into the folder of your choice.
In addition, it can zip all your files for you.

## Prerequisites:
- Python 3
      
## Installation
Run the command:
```console
git clone https://github.com/devonpmack/sequence_file_extractor.git --recursive
```
### Configuration of the redmine listener:     
Run the program and it will ask you for all the configuration it needs.
```console
python3 redmine_listener.py
```
It will now ask you for all the configuration options/requirements:
- nasmnt: path to the NAS
- seconds_between_redmine_checks: How many seconds to wait between checks on redmine looking for new SNVPhyls to run

Finally enter your Redmine API Key, you can find your API key on your account page ( /my/account ) when logged in, on the right-hand pane of the default layout.

### Running the Redmine Listener permanently
First install the supervisor package
```console
sudo apt-get install supervisor
```
Create a config file for your daemon at /etc/supervisor/conf.d/file_retriever.conf
```
[program:file_retriever]
directory=/path/to/project/root
environment=ENV_VARIABLE=example,OTHER_ENV_VARIABLE=example2
command=python3 redmine_listener.py -f
autostart=true
autorestart=true
```
Restart supervisor to load your new .conf
```
supervisorctl update
supervisorctl restart file_retriever
```
## Usage Examples:
#### To run the server:
```console
python3 redmine_listener.py
```
#### To retrieve fasta files:

First, edit the file fasta_retrieve_list.txt. Paste in all your seq-ids, separated however you want.

```
2015-SEQ-1245
2016-GTA-1224
2014-SEQ-1145
```

Next, run the command below. I use example as the folder name and -f to tell the program that I want to retrieve fasta files:

`python3 run.py example -f`

This will extract all the files in fasta_retrieve_list.txt and put them into the folder extract/example

#### To retrieve fastq files:
First, edit the file fastq_retrieve_list.txt. Paste in all your seq-ids, separated however you want.

```
2015-BUR-1245,2016-GTA-1224,2014-SEQ-1145
```

Next, run the command below. I use example as the folder name and -q to tell the program that I want to retrieve fastq files. I used --zip to tell the program to zip all the files once it's finished:

`python3 run.py example -q --zip`

This will extract all the files in fastq_retrieve_list.txt and put them into the folder extract/example. It will also create example.zip with all of my files inside of the extract/example folder. 

### Note: To retrieve both fasta and fastq files at the same time, enter your seq-ids into both files, and run the command with both the -q and -f flag. 

