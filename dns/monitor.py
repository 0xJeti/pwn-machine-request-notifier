#!/usr/bin/python3
import time, requests, os, re
from multiprocessing.dummy import Pool

def is_blacklisted(domain):
    blacklist  = open("/data/blacklist.txt")
    return domain in [w.strip() for w in blacklist.readlines()]

def escape_domain(domain):
    return domain.replace('.','[.]')

def watch(fn):
    try:
        fp = open(fn, 'r')
        fp.seek(0,2) # start at the end
        while True:
            new = fp.readline()

            if new:
                match = re.search("Remote (\d+\.\d+\.\d+\.\d+) wants '([A-Za-z0-9-.]+" + domain_regex + ")\|(\w+)'", new)

                if match:
                    yield (match.group(2).lower(), match.group(3), match.group(1))
            else:
                time.sleep(0.5)
    except Exception as e:
        print("Error occurred while monitoring pdns.log:",e)

queries = '/logs/pdns/pdns.log'

if os.environ.get('DOMAIN'):
    domain_regex = os.environ.get('DOMAIN').replace('.','\.')
else:
    print("os.environ.get('DOMAIN') empty")
    exit(1)

# wrap a while loop around this to retry after an error occurred in watch(queries)
while True:
    for domain, type, fromip in watch(queries):
        print(domain, type, fromip)
        if is_blacklisted(domain):
            print("skipping blacklisted domain", domain)
        else:
            message = '[DNS] `' + domain + ' ('+type+')` from '+fromip
            # make an asynchronous request to the webhooks so the responsiveness of the logging isn't impacted
            pool = Pool()
            pool.apply_async(requests.post, ( os.environ.get('DISCORD_WEBHOOK'), ), { 'json': { 'content': message } } )
            pool.apply_async(requests.post, ( os.environ.get('SLACK_WEBHOOK'), ), { 'json': {'text': message} })
