# rss list and downloader for flex get


This code includes modules for downloading RSS feeds and torrent files, which are essential for setting up a home OTT service using Flexget, Plex, and Transmission. To download torrent files, a website that provides torrent files is required, and this code utilizes the Tfeeca website for this purpose.

Tfeeca's website is continuously monitored in real-time to collect newly uploaded torrent files, which are then made available as an RSS feed. This feed also includes download URLs. By using these download URLs, you can download torrent files. Two modules are provided to enable the use of these functionalities within Flexget.

### Execute

```
$ git clone https://github.com/tommyjeon/rss_flexget.git
$ cd rss_flexget
$ pip install -r requirments.txt
$ python app.py

```

### RSS FEED
http://127.0.0.1:8881/rss?b_id=tent

### Download
http://127.0.0.1:8881/download?b_id=tent&item_id=710528


### Flexget 
You can install flexget by pip
Please check the manual in order to create the configuration file.


### Plex
You can install Plex on AppStore and GooglePlay

### Transmission
You can install Transmission by downloading it from the official site.

