import subprocess

def transcode(input_file, output_file):
    command = ['HandBrakeCLI',
               '-i',
               input_file,
               '-o',
               output_file,
               '--preset=High Profile',
               '--subtitle',
               'scan',
               '-F']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while True:
        # err_line = process.stderr.readline()
        line = ''
        while line[-1:] != '\r' and process.poll() is None:
            line = line + bytes.decode(process.stdout.read(1))
        if process.poll() is not None:
             break
        print(line)
        # print(err_line)
    rc = process.poll()
    print('Returned: {0}'.format(rc))


if __name__ == '__main__':

    transcode('/data/leader/incoming/The Big Bang Theory Season 10/The_Big_Bang_Theory_Season_10_Disc_1_t00.mkv',
              '/data/leader/outgoing/The_Big_Bang_Theory_Season_10_Disc_1_t00.mkv')