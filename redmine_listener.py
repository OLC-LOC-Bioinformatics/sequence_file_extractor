from pyaccessories.TimeLog import Timer
import os
from RedmineAPI.RedmineAPI import RedmineInterface
from pyaccessories.SaveLoad import SaveLoad
from run import MassExtractor
import base64
# TODO documentation


class Run(object):
    def main(self, force):
        if self.first_run == 'yes':
            choice = 'y'
            if force:
                raise ValueError('Need redmine API key!')
        else:
            if force:
                choice = 'n'
            else:
                self.t.time_print("Would you like to set the redmine api key? (y/n)")
                choice = input()
        if choice == 'y':
            self.t.time_print("Enter your redmine api key (will be encrypted to file)")
            self.redmine_api_key = input()
            # Encode and send to json file
            self.loader.redmine_api_key_encrypted = self.encode(self.key, self.redmine_api_key).decode('utf-8')
            self.loader.first_run = 'no'
            self.loader.dump(self.config_json)
        else:
            # Import and decode from file
            self.redmine_api_key = self.decode(self.key, self.redmine_api_key)

        import re
        if not re.match(r'^[a-z0-9]{40}$', self.redmine_api_key):
            self.t.time_print("Invalid Redmine API key!")
            exit(1)

        self.redmine = RedmineInterface('http://redmine.biodiversity.agr.gc.ca/', self.redmine_api_key)

        self.main_loop()

    def get_input(self, input_file, redmine_id):
        mode = 'none'
        regex = r'^(2\d{3}-\w{2,10}-\d{3,4})$'
        inputs = {
            'fastqs': list(),
            'fastas': list(),
            'outputfolder': os.path.join(self.nas_mnt, 'bio_requests', str(redmine_id))
        }
        import re
        for line in input_file:
            # Check for mode changes
            if line.lower().startswith('fasta') and len(line) < len('fasta') + 3:
                mode = 'fasta'
                continue
            elif line.lower().startswith('fastq') and len(line) < len('fastq') + 3:
                mode = 'fastq'
                continue
            elif line.lower() == '':
                # Blank line
                mode = 'none'
                continue

            # Get seq-id
            if mode == 'fasta':
                if re.match(regex, line):
                    inputs['fastas'].append(line)
                else:
                    raise ValueError("Invalid seq-id \"%s\"" % line)
            elif mode == 'fastq':
                if re.match(regex, line):
                    inputs['fastqs'].append(line)
                else:
                    raise ValueError("Invalid seq-id \"%s\"" % line)

        if len(inputs['fastas']) < 1 and len(inputs['fastqs']) < 1:
            raise ValueError("Invalid format for redmine request. Couldn't find any fastas or fastqs to extract")

        return inputs

    def completed_response(self, redmine_id, missing):
        notes = "Completed extracting files. Results stored at %s" % os.path.join("NAS/bio_requests/%s" % redmine_id)
        if len(missing) > 0:
            notes += '\nMissing some files:\n'
            for file in missing:
                notes += file + '\n'

        # Assign it back to the author
        get = self.redmine.get_issue_data(redmine_id)

        self.redmine.update_issue(redmine_id, notes + self.botmsg, status_change=4, assign_to_id=get['issue']['author']['id'])

    def run_request(self, inputs):
        # Parse input
        # noinspection PyBroadException
        try:
            runner = MassExtractor(inputs=inputs)
            missing_files = runner.run()

            # Respond on redmine
            self.completed_response(os.path.split(inputs['outputfolder'])[-1], missing_files)

        except Exception as e:
            import traceback
            self.t.time_print("[Warning] run.py had a problem, continuing redmine api anyways.")
            self.t.time_print("[AutoSNVPhyl Error Dump]\n" + traceback.format_exc())
            # Send response
            msg = traceback.format_exc()

            # Set it to feedback and assign it back to the author
            get = self.redmine.get_issue_data(os.path.split(inputs['outputfolder'])[-1])
            self.redmine.update_issue(
                                      os.path.split(inputs['outputfolder'])[-1],
                                      notes="There was a problem with your request. Please create a new issue on"
                                            " Redmine to re-run it.\n%s" % msg + self.botmsg,
                                      status_change=4,
                                      assign_to_id=get['issue']['author']['id']
                                      )

    def main_loop(self):
        import time
        while True:
            self.make_call()
            self.t.time_print("Waiting for next check.")
            time.sleep(self.seconds_between_redmine_checks)

    def make_call(self):
        self.t.time_print("Checking for extraction requests...")

        data = self.redmine.get_new_issues('cfia')

        found = []

        for issue in data['issues']:
            if issue['id'] not in self.responded_issues and issue['status']['name'] == 'New':
                if issue['subject'].lower() == 'retrieve':
                    found.append(issue)

        self.t.time_print("Found %d issues..." % len(found))

        while len(found) > 0:  # While there are still issues to respond to
            self.respond_to_issue(found.pop(len(found)-1))

    def respond_to_issue(self, issue):
        # Run extraction
        if self.redmine.get_issue_data(issue['id'])['issue']['status']['name'] == 'New':
            self.t.time_print("Found extraction to run. Subject: %s. ID: %s" % (issue['subject'], issue['id']))
            self.t.time_print("Adding to responded to")
            self.responded_issues.add(issue['id'])
            self.issue_loader.responded_issues = list(self.responded_issues)
            self.issue_loader.dump()

            # Turn the description into a list of lines
            input_list = issue['description'].split('\n')
            input_list = map(str.strip, input_list)  # Get rid of \r
            error = False
            try:
                inputs = self.get_input(input_list, issue['id'])
                response = "Retrieving %d fastas and %d fastqs..." % (len(inputs['fastas']), len(inputs['fastqs']))
            except ValueError as e:
                response = "Sorry, there was a problem with your request:\n%s\n" \
                           "Please submit a new request and close this one." % e.args[0]
                error = True

            self.t.time_print('\n' + response)

            if error:  # If something went wrong set the status to feedback and assign the author the issue
                get = self.redmine.get_issue_data(issue['id'])
                self.redmine.update_issue(issue['id'], notes=response + self.botmsg, status_change=4,
                                          assign_to_id=get['issue']['author']['id'])
            else:
                # Set the issue to in progress since the SNVPhyl is running
                self.redmine.update_issue(issue['id'], notes=response + self.botmsg, status_change=2)

            if error:
                return
            else:
                self.run_request(inputs)

    @staticmethod
    def encode(key, string):
        encoded_chars = []
        for i in range(len(string)):
            key_c = key[i % len(key)]
            encoded_c = chr(ord(string[i]) + ord(key_c) % 256)
            encoded_chars.append(encoded_c)
        encoded_string = "".join(encoded_chars)
        encoded_string = bytes(encoded_string, "utf-8")

        return base64.urlsafe_b64encode(encoded_string)

    @staticmethod
    def decode(key, string):
        decoded_chars = []
        string = base64.urlsafe_b64decode(string).decode('utf-8')
        for i in range(len(string)):
            key_c = key[i % len(key)]
            encoded_c = chr(abs(ord(str(string[i]))
                                - ord(key_c) % 256))
            decoded_chars.append(encoded_c)
        decoded_string = "".join(decoded_chars)

        return decoded_string

    def __init__(self, force):
        # import logging
        # logging.basicConfig(level=logging.INFO)
        # Vars
        import sys
        self.script_dir = sys.path[0]
        self.config_json = os.path.join(self.script_dir, "config.json")

        # Set up timer/logger
        import datetime
        if not os.path.exists(os.path.join(self.script_dir, 'runner_logs')):
            os.makedirs(os.path.join(self.script_dir, 'runner_logs'))
        self.t = Timer(log_file=os.path.join(self.script_dir, 'runner_logs',
                                             datetime.datetime.now().strftime("%d-%m-%Y_%S:%M:%H")))
        self.t.set_colour(30)

        # Load issues that the bot has already responded to
        self.issue_loader = SaveLoad(os.path.join(self.script_dir, 'responded_issues.json'), create=True)
        self.responded_issues = set(self.issue_loader.get('responded_issues', default=[], ask=False))

        # Get encrypted api key from config
        # Load the config
        self.loader = SaveLoad(self.config_json, create=True)
        self.redmine_api_key = self.loader.get('redmine_api_key_encrypted', default='none', ask=False)

        # If it's the first run then this will be yes
        self.first_run = self.loader.get('first_run', default='yes', ask=False)

        self.nas_mnt = os.path.normpath(self.loader.get('nasmnt', default="/mnt/nas/", get_type=str))
        self.seconds_between_redmine_checks = self.loader.get('secs_between_redmine_checks', default=600, get_type=int)
        self.key = 'Sixteen byte key'

        self.redmine = None

        self.botmsg = '\n\n_I am a bot. This action was performed automatically._'

        try:
            self.main(force)
        except Exception as e:
            import traceback
            self.t.time_print("[Error] Dumping...\n%s" % traceback.format_exc())
            raise

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--force", action="store_true",
                        help="Don't ask to update redmine api key")

    args = parser.parse_args()
    Run(args.force)
