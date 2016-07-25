# Snapper
A security tool for grabbing screenshots of many web hosts. This tool is useful after [DNS enumeration](https://github.com/mschwager/fierce) or after enumerating web hosts via nmap or nessus.

## How to install

- Install python dependancies
```bash
pip install -r requirements.txt
```

- Install phantomJS (you need to have [npm installed](https://nodejs.org/en/download/package-manager/))
```bash
npm -g install phantomjs
```

- Clone snapper
```bash
git clone https://github.com/dxa4481/snapper
```

## How to use

For a simple demo try:
```
python snapper.py -l "google.com, gmail.google.com, ads.google.com" -c 3 -v
```
This kicks off 3 processes, each of which fetch screenshots of the http and https versions of the hosts in question. The output is served up via localhost:8000 and can be seen below
![output results](http://i.imgur.com/OlvyIBp.png)

## More options

```bash
python snapper.py --help
```

```
Options:
  -h, --help            show this help message and exit
  -f FILE, --file=FILE  Souce from input file
  -l LIST, --list=LIST  Source from commandline list
  -u USER_AGENT, --user-agent=USER_AGENT
                        The user agent used for requests
  -c NUMWORKERS, --concurrency=NUMWORKERS
                        Number of cuncurrent processes
  -t TIMEOUT, --timeout=TIMEOUT
                        Number of seconds to try to resolve
  -p PORT, --port=PORT  Port to run server on
  -v                    Display console output for fetching each host
```
