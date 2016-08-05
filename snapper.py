from jinja2 import Environment, PackageLoader
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from optparse import OptionParser
from multiprocessing import Process, Queue
import sys, os
try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer
try:
    import SimpleHTTPServer
except ImportError:
    import http.server as SimpleHTTPServer
from os import chdir
from shutil import copyfile
from requests import get
from uuid import uuid4
from selenium.common.exceptions import TimeoutException

env = Environment(autoescape=True, loader=PackageLoader('snapper', 'templates'))

def save_image(uri, file_name, driver):
    try:
        driver.get(uri)
        driver.save_screenshot(file_name)
        return True
    except TimeoutException:
        return False


def host_reachable(host, timeout):
    try:
        get(host, timeout=timeout, verify=False)
        return True
    except:
        return False

def host_worker(hostQueue, fileQueue, timeout, user_agent, verbose):
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = user_agent
    dcap["accept_untrusted_certs"] = True
    driver = webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true'], desired_capabilities=dcap) # or add to your PATH
    driver.set_window_size(1024, 768) # optional
    driver.set_page_load_timeout(timeout)
    while(not hostQueue.empty()):
        host = hostQueue.get()
        if not host.startswith("http://") and not host.startswith("https://"):
            host1 = "http://" + host
            host2 = "https://" + host
            filename1 = os.path.join("output", "images", str(uuid4()) + ".png")
            filename2 = os.path.join("output", "images", str(uuid4()) + ".png")
            if verbose:
                print("Fetching %s" % host1)
            if host_reachable(host1, timeout) and save_image(host1, filename1, driver):
                fileQueue.put({host1: filename1})
            else:
                if verbose:
                    print("%s is unreachable or timed out" % host1)
            if verbose:
                print("Fetching %s" % host2)
            if host_reachable(host2, timeout) and save_image(host2, filename2, driver):
                fileQueue.put({host2: filename2})
            else:
                if verbose:
                    print("%s is unreachable or timed out" % host2)
        else:
            filename = os.path.join("output", "images", str(uuid4()) + ".png")
            if verbose:
                print("Fetching %s" % host)
            if host_reachable(host, timeout) and save_image(host, filename, driver):
                fileQueue.put({host: filename})
            else:
                if verbose:
                    print("%s is unreachable or timed out" % host)

def capture_snaps(hosts, outpath, timeout=10, serve=False, port=8000, 
        verbose=True, numWorkers=1, user_agent="Mozilla/5.0 (Windows NT\
            6.1) AppleWebKit/537.36 (KHTML,like Gecko) Chrome/41.0.2228.\
            0 Safari/537.36"):
    outpath = os.path.join(outpath, "output")
    cssOutputPath = os.path.join(outpath, "css")
    jsOutputPath = os.path.join(outpath, "js")
    imagesOutputPath = os.path.join(outpath, "images")
    if not os.path.exists(outpath):
        os.makedirs(outpath)
    if not os.path.exists(imagesOutputPath):
        os.makedirs(imagesOutputPath)
    if not os.path.exists(cssOutputPath):
        os.makedirs(cssOutputPath)
    if not os.path.exists(jsOutputPath):
        os.makedirs(jsOutputPath)
    cssTemplatePath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates", "css")
    jsTemplatePath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates", "js")
    copyfile(os.path.join(cssTemplatePath, "materialize.min.css"), os.path.join(cssOutputPath, "materialize.min.css"))
    copyfile(os.path.join(jsTemplatePath, "jquery.min.js"), os.path.join(jsOutputPath, "jquery.min.js"))
    copyfile(os.path.join(jsTemplatePath, "materialize.min.js"), os.path.join(jsOutputPath, "materialize.min.js"))
    
    hostQueue = Queue()
    fileQueue = Queue()

    workers = []
    for host in hosts:
        hostQueue.put(host)
    for i in range(numWorkers):
        p = Process(target=host_worker, args=(hostQueue, fileQueue, timeout, user_agent, verbose))
        workers.append(p)
        p.start()
    try:
        for worker in workers:
            worker.join()
    except KeyboardInterrupt:
        for worker in workers:
            worker.terminate()
            worker.join()
        sys.exit()
    setsOfSix = []
    count = 0
    hosts = {}
    while(not fileQueue.empty()):
        if count == 6:
            try:
                setsOfSix.append(hosts.iteritems())
            except AttributeError:
                setsOfSix.append(hosts.items())
            hosts = {}
            count = 0
        temp = fileQueue.get()
        hosts.update(temp)
    try:
        setsOfSix.append(hosts.iteritems())
    except AttributeError:
        setsOfSix.append(hosts.items())
    template = env.get_template('index.html')
    with open(os.path.join(outpath, "index.html"), "w") as outputFile:
        outputFile.write(template.render(setsOfSix=setsOfSix))
    if serve:
        chdir("output")
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        httpd = SocketServer.TCPServer(("127.0.0.1", PORT), Handler)
        print("Serving at port", PORT)
        httpd.serve_forever()
    else:
        return True

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-f", "--file", action="store", dest="filename",
                      help="Souce from input file", metavar="FILE")
    parser.add_option("-l", "--list", action="store", dest="list",
                      help="Source from commandline list")
    parser.add_option("-u", '--user-agent', action='store', 
                      dest="user_agent", type=str, 
                      default="Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML,\
                              like Gecko) Chrome/41.0.2228.0 Safari/537.36", 
                      help='The user agent used for requests')
    parser.add_option("-c", '--concurrency', action='store', 
                      dest="numWorkers", type=int, default=1, 
                      help='Number of cuncurrent processes')
    parser.add_option("-t", '--timeout', action='store', 
                      dest="timeout", type=int, default=10, 
                      help='Number of seconds to try to resolve')
    parser.add_option("-p", '--port', action='store', 
                      dest="port", type=int, default=8000, 
                      help='Port to run server on')
    parser.add_option("-v", action='store_true', dest="verbose",
                      help='Display console output for fetching each host')


    (options, args) = parser.parse_args()
    if options.filename:
        with open(options.filename, 'r') as inputFile:
            hosts = inputFile.readlines()
            hosts = map(lambda s: s.strip(), hosts)
    elif options.list:
        hosts = []
        for item in options.list.split(","):
            hosts.append(item.strip())
    else:
        print("invalid args")
        sys.exit()
    numWorkers = options.numWorkers
    timeout = options.timeout
    verbose = options.verbose
    PORT = options.port
    user_agent = options.user_agent

    capture_snaps(hosts, os.getcwd(), timeout, True, PORT, verbose,
            numWorkers, user_agent)


