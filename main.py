import requests
from multiprocessing.dummy import Pool as ThreadPool
from threading import Lock, Thread
from queue import Queue

from bs4 import BeautifulSoup
from time import sleep, time

from os import sys


url = None
baseUrl = "https://ipinfo.io"

done = False
total_ips = 0


queue = Queue()
ips_queue = Queue()

def worker():
    global queue

    while queue.empty():
        sleep(0.1)

    while not queue.empty():
        url = queue.get()       
        req = requests.get(url)

        bsIp = BeautifulSoup(req.text, "html.parser")
        tbody_tag = bsIp.find("tbody", {"class": "t-14"})

        if tbody_tag is not None:
                for td in tbody_tag.findAll("td"):
                        a_tag = td.find("a")
                        if a_tag is not None:
                                ip = a_tag.text.strip()
                                if len(ip) > 0:
                                        ips_queue.put(ip)

def write_to_file(file_name):
        global ips_queue
        global total_ips
        global done

        file = open(file_name,"w")

        if not file:
                print(f"Invalid path {file_name}")
                exit()

        # wait until queue has some data
        while ips_queue.empty():
                sleep(0.1)
        
        while not done:
                while not ips_queue.empty():
                        ip = ips_queue.get()
                        file.write(ip + "\n")
                        total_ips += 1

args = sys.argv

if len(args) != 4:
        print(f"use: python {args[0]} <country> <threads> <output_file>")
        exit()

_, country, total_threads, output_file = args

url = f"https://ipinfo.io/countries/{country}"


req = requests.get(url)
if req.status_code == 404:
        print("Country not found!")
else:
        bs = BeautifulSoup(req.text, "html.parser")

        print(f"[::]Running on {total_threads} threads!")

        threads = []
        for n in range(int(total_threads)):
                th = Thread(target=worker)
                th.start()
                threads.append(th)

        # thread responsible for writing the IPs to a file
        file_thread = Thread(target=write_to_file, args=(output_file, ))
        file_thread.start()
        
        time_start = time()
        
        # get links of all ISPs
        for td in bs.findAll("td"):
                aTag = td.find("a")
                if aTag is not None:
                        hrefLink = baseUrl + aTag["href"]
                        queue.put(hrefLink)

        for th in threads:
                th.join()

        done = True

        file_thread.join()
        total_time = time() - time_start;
        
        print(f"[!!]Done in {total_time:.2f} seconds")
        print(f"[!!]Total IPs range: {total_ips}")