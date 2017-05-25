from sequence_getter import SequenceGetter
from pyaccessories.TimeLog import Timer
from pyaccessories.SaveLoad import SaveLoad

import sys
import os
import re
import zipfile

import argparse

parser = argparse.ArgumentParser(description="Retrieve fasta and/or fastq files from the NAS")
parser.add_argument('output_folder', type=str, help="Folder to put the results files in")
parser.add_argument("-f", "--fasta", action="store_true",
                    help="Retrieve fasta files in fasta_retrieve_list.txt")
parser.add_argument("-q", "--fastq", action="store_true",
                    help="Retrieve fastq files in fastq_retrieve_list.txt")
parser.add_argument("--zip", action="store_true",
                    help="Zip the final results")
parser.add_argument("-n", "--nas", type=str, help="Use this nas mount"
                                                  " directory instead of the default in the config file.")

args = parser.parse_args()
name = os.path.normpath(args.output_folder)

# If bad arguments
if not args.fastq and not args.fasta:
    print("Please use -q (fastq) and/or -f (fasta) to choose what filetype you want to retrieve.")
    parser.print_help()
    exit(1)


script_dir = sys.path[0]

# Load NAS directory
if args.nas is not None:
    nasmnt = args.nas
else:
    load = SaveLoad(file_name="config.json", create=True)
    nasmnt = load.get('nasmnt', default='/mnt/nas/')

if not os.path.normpath(name).startswith('/'):
    outfolder = os.path.join(script_dir, name)
else:
    outfolder = name

retriever = SequenceGetter(outputfolder=outfolder,
                           nasmnt=os.path.normpath(nasmnt), output=False)

t = Timer()
t.set_colour(32)

if args.fastq:
    t.time_print("Retrieving fastqs...")

    f = open("fastq_retrieve_list.txt", "r")
    ids = re.findall(r"(2\d{3}-\w{2,10}-\d{3,4})", f.read())
    f.close()

    t.time_print("Found %d ids..." % len(ids))
    counter = 1
    total = len(ids)*2

    for seq_id in ids:
        for r in [1, 2]:
            t.time_print("%d of %d:" % (counter+r-1, total))
            counter += 1
            t.time_print(retriever.retrieve_file(seq_id, filetype="fastq_R%d" % r))

if args.fasta:
    t.time_print("Retrieving fastas...")
    f = open("fasta_retrieve_list.txt", "r")
    ids = re.findall(r"(2\d{3}-\w{2,10}-\d{3,4})", f.read())
    f.close()

    t.time_print("Found %d ids..." % len(ids))
    counter = 1
    total = len(ids) * 2

    for seq_id in ids:
        t.time_print("%d of %d:" % (counter, total))
        counter += 1
        t.time_print(retriever.retrieve_file(seq_id, filetype="fasta"))

if args.zip:
    # Zip all the files
    p = outfolder
    results_zip = os.path.join(p, name + '.zip')
    t.time_print("Creating zip file %s" % results_zip)

    try:
        os.remove(results_zip)
    except OSError:
        pass

    zipf = zipfile.ZipFile(results_zip, 'w', zipfile.ZIP_DEFLATED)
    for to_zip in os.listdir(p):
        zipf.write(os.path.join(p, to_zip), arcname=to_zip)
        t.time_print("Zipped %s" % to_zip)

    zipf.close()
