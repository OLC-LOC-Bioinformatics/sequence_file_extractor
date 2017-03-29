# Written by Devon Mack
# March 2017
# This will use already existing scripts in the MiSeq_Backup folder and WGSspades to
# extract files easily. It is sped up by the fact that it will create multiple subprocesses
# for every request it makes.
import configparser, os, shutil, subprocess, argparse

#add arguments
parser = argparse.ArgumentParser()
parser.add_argument("-r","--redmine", type=str,help="set a redmine ticket id to put the lists in")
args = parser.parse_args()
redmine = args.redmine

#If the user inputted a redmine ticket number then save this ticket
redmineexists = False
if type(redmine) == str:
    redmineexists = True
    print("Using Redmine ticket " + redmine)

#load config
config = configparser.ConfigParser()
config.read('config.ini')
outputfolder = config['config']['outputfolder']
clear = config['config']['clearfolderifexists']
mnt = config['config']['nasmnt']

#Remove all blank lines and get files to retrieve
f = open("retrieve.txt",'r')
lines = (line.rstrip() for line in f)
lines = list(line for line in lines if line)
f.close()
data = {}
newTag = ""
requests = list()

#Read in data
filetype = "fastq"
for line in lines:
    if line.startswith('#'):
        special = line[1:]
        #If it isnt specifying the file type
        if special.lower() == "fastq" or special.lower() == 'fasta':
            filetype = special.lower()
        else:
            #Add a new tag
            newTag = special
            if not 'fastq' + newTag in data.keys():
                requests.append(newTag)
                data['fastq' + newTag] = list()
                data['fasta' + newTag] = list()
    else:
        #Load in a data request
        data[filetype + newTag].append(line)

#Create the output folder if it doesn't exist
if not os.path.exists(outputfolder):
    os.makedirs(outputfolder)
fastq = []
fasta = []
for requestName in requests:
    if redmineexists:
        red = os.path.join(mnt,'/mnt/nas/bio_requests/') + redmine + '/'
        redpath =  red + requestName + '/'
        if os.path.exists(redpath):
            print("Adding list files to folder " + redpath)
        elif not os.path.exists(red):
            print("Creating folder " + red)
            os.mkdir(red)
            print("Creating folder " + redpath)
            os.mkdir(redpath)
        else:
            print("Creating folder " + redpath)
            os.mkdir(redpath)
    requestFolder = outputfolder + requestName
    if os.path.exists(requestFolder):
        if clear == 'yes':
            print("Clearing already existing folder " + requestFolder)
            shutil.rmtree(requestFolder)
            os.makedirs(requestFolder)
        else:
            print("Not clearing already existing folder " + requestFolder)
    else:
        print("Creating directory " + requestFolder)
        os.makedirs(requestFolder)
    #If there areis any fastq file requests
    if data['fastq' + requestName]:
        print("Creating fastq list at " + requestFolder + "/fastqlist.txt")
        f = open(requestFolder + "/fastqlist.txt",'w')
        for item in data['fastq' + requestName]:
            f.write("%s\n" % item)
        f.close()
        print("Copying " + requestFolder + "/fastqlist.txt" + " to " + redpath)
        shutil.copy(requestFolder + "/fastqlist.txt", redpath + "fastqlist.txt")
        print("[" + requestName + "] " + "Copying fastq files to "+ requestFolder + "/")
        fastq.append(subprocess.Popen(['python',os.path.join(mnt,'MiSeq_Backup/file_extractor_devon.py'), outputfolder +
                                       requestName + "/fastqlist.txt",requestFolder + "/","-n",mnt,"-c",
                                       str(len(data['fastq' + requestName])),"-t",requestName]))
    #If there are any fasta file requests
    if data['fasta' + requestName]:
        print("Creating fasta list at " + requestFolder + '/fastalist.txt')
        f = open(requestFolder + '/fastalist.txt','w')
        for item in data['fasta' + requestName]:
            f.write("%s\n" % item)
        f.close()
        print("Copying " + requestFolder + "/fastalist.txt" + " to " + redpath)
        shutil.copy(requestFolder + "/fastalist.txt", redpath + "fastalist.txt")

        print("[" + requestName + "] " + "Copying fasta files to "+ requestFolder + "/")
        fasta.append(subprocess.Popen(['python', os.path.join(mnt,'WGSspades/file_extractor_devon.py'), requestFolder + "/fastalist.txt", requestFolder + "/","-n", mnt, "-t", requestName]))
#Wait for all processes to finish
for process in fasta:
    process.wait()
#Wait for all processes to finish
for process in fastq:
    process.wait()
print("Finished downloading files to " + outputfolder)