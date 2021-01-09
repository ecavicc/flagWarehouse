#!/usr/bin/env python3
import argparse
import logging
import math
import os
import os.path
import re
import signal
import subprocess
import sys
import time
from datetime import datetime
from multiprocessing import Pool
from threading import Timer

import requests

BANNER = '''
  ___ __               ________                    __                            
.'  _|  |.---.-.-----.|  |  |  |.---.-.----.-----.|  |--.-----.--.--.-----.-----.
|   _|  ||  _  |  _  ||  |  |  ||  _  |   _|  -__||     |  _  |  |  |__ --|  -__|
|__| |__||___._|___  ||________||___._|__| |_____||__|__|_____|_____|_____|_____|
               |_____|                                                           
               
          The perfect solution for running all your exploits in one go!          

'''[1:]

logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S', level=logging.INFO)


def parse_args():
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(description='''Run all the exploits in the specified 
                                            directory against all the teams.''',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-s', '--server-url',
                        type=str,
                        metavar='URL',
                        default='http://localhost:5000',
                        help='The URL of your flagWarehouse server. Please specify the protocol')

    parser.add_argument('-u', '--user',
                        type=str,
                        metavar='USER',
                        required=True,
                        help='Your username')

    parser.add_argument('-t', '--token',
                        type=str,
                        metavar='TOKEN',
                        required=True,
                        help='The authorization token used for the flagWarehouse server API')

    parser.add_argument('-d', '--exploit-directory',
                        type=str,
                        metavar='DIR',
                        required=True,
                        help='The directory that holds all your exploits')

    # parser.add_argument('-i', '--interpreter',
    #                     type=str,
    #                     metavar='COMMAND',
    #                     required=False,
    #                     help='''Since shebangs are not a thing in Windows,
    #                     you can specify which interpreter to use.
    #                     Obviously, all the exploits will have to be
    #                     written in the same language''')

    return parser.parse_args()


def run_exploit(exploit: str, ip: str, round_duration: int, server_url: str, token: str, pattern, user: str):
    def timer_out(process):
        timer.cancel()
        process.kill()

    p = subprocess.Popen([exploit, ip], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    timer = Timer(math.ceil(0.95 * round_duration), timer_out, args=[p])

    timer.start()
    while True:
        output = p.stdout.readline().decode().strip()
        if output == '' and p.poll() is not None:
            break
        if output:
            flags = pattern.findall(output)
            if flags:
                msg = {'username': user, 'flags': []}
                t_stamp = datetime.now().replace(microsecond=0).isoformat(sep=' ')
                for flag in flags:
                    msg['flags'].append({'flag': flag,
                                         'exploit_name': os.path.basename(exploit),
                                         'team_ip': ip,
                                         'time': t_stamp})
                requests.post(server_url + '/api/upload_flags',
                              headers={'X-Auth-Token': token},
                              json=msg)
    p.stdout.close()
    return_code = p.poll()
    timer.cancel()
    if return_code == -9:
        logging.error(f'Exploit {os.path.basename(exploit)} on team {ip} was killed because it took too long to finish')
    elif return_code != 0:
        logging.error(f'Exploit {os.path.basename(exploit)} on team {ip} terminated with error code {return_code}')


def main(args):
    global pool
    print(BANNER)

    server_url = args.server_url
    user = args.user
    token = args.token
    exploit_directory = args.exploit_directory

    logging.info('Connecting to the flagWarehouse server...')
    r = None
    try:
        r = requests.get(server_url + '/api/get_config', headers={'X-Auth-Token': token})
    except requests.exceptions.RequestException as e:
        logging.error('Could not connect to the server: ' + e.__class__.__name__)
        logging.info('Exiting...')
        sys.exit(0)
    config = r.json()
    flag_format = re.compile(config['format'])
    round_duration = config['round']
    teams = config['teams']
    logging.info('Client correctly configured.')

    while True:
        try:
            requests.head(server_url)
            logging.info('Starting new round.')
            s_time = time.time()
            scripts = [os.path.join(exploit_directory, s) for s in os.listdir(exploit_directory) if
                       os.path.isfile(os.path.join(exploit_directory, s))]

            original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
            pool = Pool(len(scripts) * len(teams))
            signal.signal(signal.SIGINT, original_sigint_handler)

            for script in scripts:
                for team in teams:
                    pool.apply_async(run_exploit, (script, team, round_duration, server_url, token, flag_format, user))
            pool.close()
            pool.join()

            duration = time.time() - s_time
            if duration < round_duration:
                logging.debug(f'Sleeping for {round(duration, 1)} seconds')
                time.sleep(round_duration - duration)
        except KeyboardInterrupt:
            logging.info('Caught KeyboardInterrupt. Bye!')
            pool.terminate()
            break
        except requests.exceptions.RequestException:
            logging.error('Could not communicate with the server: retrying in 5 seconds.')
            time.sleep(5)
            continue


if __name__ == '__main__':
    main(parse_args())
