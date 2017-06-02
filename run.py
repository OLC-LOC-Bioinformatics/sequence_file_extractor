from sequence_getter import SequenceGetter
from pyaccessories.TimeLog import Timer
from pyaccessories.SaveLoad import SaveLoad

import sys
import os
import re
import zipfile


class MassExtractor(object):
    def __init__(self, inputs=None, args=None):
        self.missing = list()
        self.script_dir = sys.path[0]
        load = SaveLoad(file_name="config.json", create=True)

        if inputs is not None:
            self.automated = True
            self.inputs = inputs
            self.name = os.path.split(inputs['outputfolder'])[-1]
            nasmnt = load.get('nasmnt', default='/mnt/nas/')
            self.outfolder = inputs['outputfolder']
        elif args is not None:
            self.automated = False
            self.name = os.path.normpath(args.output_folder)

            # If bad arguments
            if not args.fastq and not args.fasta:
                print("Please use -q (fastq) and/or -f (fasta) to choose what filetype you want to retrieve.")
                parser.print_help()
                exit(1)

            # Load NAS directory
            if args.nas is not None:
                nasmnt = args.nas
            else:
                nasmnt = load.get('nasmnt', default='/mnt/nas/')

            if not os.path.normpath(self.name).startswith('/'):
                self.outfolder = os.path.join(self.script_dir, self.name)
            else:
                self.outfolder = self.name
        else:
            raise ValueError('No inputs to constructor!')

        self.retriever = SequenceGetter(outputfolder=self.outfolder,
                                   nasmnt=os.path.normpath(nasmnt), output=False)

        self.t = Timer()
        self.t.set_colour(32)

    def run(self):
        if self.automated:
            fasta = True
            fastq = True
        else:
            fastq = True if args.fasta else False
            fasta = True if args.fasta else False

        if fastq:
            self.t.time_print("Retrieving fastqs...")

            if self.automated:
                ids = self.inputs['fastqs']
            else:
                f = open("fastq_retrieve_list.txt", "r")
                ids = re.findall(r"(2\d{3}-\w{2,10}-\d{3,4})", f.read())
                f.close()

            self.t.time_print("Found %d ids..." % len(ids))
            counter = 1
            total = len(ids)*2

            for seq_id in ids:
                for r in [1, 2]:
                    self.t.time_print("%d of %d:" % (counter+r-1, total))
                    counter += 1
                    msg = self.retriever.retrieve_file(seq_id, filetype="fastq_R%d" % r)
                    self.t.time_print(msg)
                    if 'missing' in msg.lower():
                        self.missing.append(msg + ' (R%d)' % r)

        if fasta:
            self.t.time_print("Retrieving fastas...")
            if self.automated:
                ids = self.inputs['fastas']
            else:
                f = open("fasta_retrieve_list.txt", "r")
                ids = re.findall(r"(2\d{3}-\w{2,10}-\d{3,4})", f.read())
                f.close()

            self.t.time_print("Found %d ids..." % len(ids))
            counter = 1
            total = len(ids)

            for seq_id in ids:
                self.t.time_print("%d of %d:" % (counter, total))
                counter += 1
                msg = self.retriever.retrieve_file(seq_id, filetype="fasta")
                self.t.time_print(msg)
                if 'missing' in msg.lower():
                    self.missing.append(msg)

        if not self.automated:
            if args.zip:
                # Zip all the files
                p = self.outfolder
                results_zip = os.path.join(p, self.name + '.zip')
                self.t.time_print("Creating zip file %s" % results_zip)

                try:
                    os.remove(results_zip)
                except OSError:
                    pass

                zipf = zipfile.ZipFile(results_zip, 'w', zipfile.ZIP_DEFLATED)
                for to_zip in os.listdir(p):
                    zipf.write(os.path.join(p, to_zip), arcname=to_zip)
                    self.t.time_print("Zipped %s" % to_zip)

                zipf.close()
        return self.missing
if __name__ == "__main__":
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

    a = MassExtractor(args=args)
    a.run()
