import datetime
import re

import requests
import logging
import httplib2
import lxml.html
import pycurl
from feedgen.feed import FeedGenerator
from flask import Flask, request, Response, send_file
from io import BytesIO
from bs4 import BeautifulSoup

import config

log = logging.getLogger('urllib3')
log.setLevel(logging.DEBUG)

# logging from urllib3 to console
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
log.addHandler(ch)

# print statements from `http.client.HTTPConnection` to console/stdout
# HTTPConnection.debuglevel = 1

app = Flask(__name__)


def clean_html(raw_html):
    clean_text = re.sub(re.compile('<.*?>'), '', raw_html)
    return clean_text


@app.route('/')
def index():
    return "It works!"


@app.route('/download_X')
def downloadX():

    board_id = request.args.get('b_id')
    item_id = request.args.get('id')

    if board_id is None or item_id is None:
        return "Parameter Error"

    return Download(b_id=board_id, id=item_id).start()

@app.route('/download')
def download():

    board_id = request.args.get('b_id')
    item_id = request.args.get('id')

    if board_id is None or item_id is None:
        return "Parameter Error"

    params = {"mode": "view", "b_id": board_id, "id": item_id}
    url = "https://www.tfreeca22.com/board.php"

    res = requests.get(url, params=params, headers=config.headers)
    urlKey = ""
    downloadFileName = item_id+".torrent"
    if res.status_code == 200:
        regex = r"href=\"https\:\/\/www\.filetender\.com\/(.*?)\" title=\".*?\" class=\"font11\" target=\"_blank\">(.*?)</a>"
        matches = re.finditer(regex, res.text, re.DOTALL)
        if len(list(matches))>0:
            matches = re.finditer(regex, res.text, re.DOTALL)
            for matchNum, match in enumerate(matches, start=1):
                urlKey = match.group(1)
#                downloadFileName = match.group(2)
        else:
            return Response(response="No data", status=500, mimetype="text/html")
            
    else:
       return Response(response="Tfreeca is down", status=500, mimetype="text/html")


    url = "https://www.filetender.com/"+urlKey
    downloadheaders = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Referer': res.url
    }
    res = requests.get(url, headers= downloadheaders)
    if res.status_code != 200:
        return Response(response="Please Check Referer, User-Agent", status=500, mimetype="text/html")

    soup = BeautifulSoup(res.text, "lxml")
    form = soup.find('form')
    downloadParam = {}
    for input_tag in form.find_all("input"):
        input_name = input_tag.attrs.get("name")
        input_value =input_tag.attrs.get("value", "")
        downloadParam[input_name] = input_value

    downloadheaders = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Referer': url
    }

    downloadUrl = "https://file.filetender.com/Execdownload8.php"

    query_string = '&'.join([f'{key}={value}' for key, value in downloadParam.items()])
    full_url = f'{downloadUrl}?{query_string}'

    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, full_url)
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.USERAGENT, 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
    c.setopt(c.REFERER, url)
    c.setopt(pycurl.VERBOSE, 1)
    c.perform()
    res_http_code = c.getinfo(pycurl.HTTP_CODE)
    c.close()

    if res_http_code != 200:
        return Response(response="Can't download torrent file from Tfreeca", status=500, mimetype="text/html")        


    file_bytes = BytesIO(buffer.getvalue())

    torrentfiledownload = send_file(
            file_bytes,
            as_attachment=True,
            attachment_filename=downloadFileName,
            mimetype='application/x-bittorrent'
        )
    return torrentfiledownload

@app.route('/rss')
def rss():

    board_id = request.args.get('b_id')
    sc = request.args.get('sc')

    if board_id is None:
        return "Parameter Error"

    params = {"mode": "list", "b_id": board_id, "ca": "방영중", "sc": sc}
    url = "https://www.tfreeca22.com/board.php"

    res = requests.get(url, params=params, headers=config.headers)
    date = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=9)))

    fg = FeedGenerator()

    fg.title('Tommy Home OTT RSS')
    fg.author({'name': 'Tommy Jeon', 'email': 'jeon.hyuneum@gmail.com'})
    fg.link(href='TFREECA', rel='alternate')
    fg.subtitle('HOME OTT feed rss')
    fg.language('ko')
    fg.lastBuildDate(date)

    if res.status_code == 200:
        regex = r"href=\"board\.php\?mode=view&b_id=" + board_id + "&id=(.*?)&ca=.*?&page=1&time=.*?\" class=\"stitle[0-9]\">(.*?) </a>"
        matches = re.finditer(regex, res.text, re.DOTALL)
        for matchNum, match in enumerate(matches, start=1):
            item_id = match.group(1)
            item_title = clean_html(match.group(2).strip())

            link = 'https://www.tfreeca22.com/board.php?mode=view&b_id=' + board_id + '&id=' + item_id + '&page=1'
            download_link = request.host_url + 'download?b_id=' + board_id + '&id=' + item_id

            fe = fg.add_entry()
            fe.id(link)
            fe.title(item_title)
            fe.link(href=download_link)
            fe.pubDate(date)
    else:
        print("TFREECA ERROR CODE " + str(res.status_code) + " URL " + res.url)


    rss_feed = fg.rss_str(pretty=True)

    r = Response(response=rss_feed, status=200, mimetype="application/xml")
    r.headers["Content-Type"] = "text/xml; charset=utf-8"

    return r


if __name__ == '__main__':
    app.run(host="0.0.0.0",
            port=8881,
            debug=True
            )
