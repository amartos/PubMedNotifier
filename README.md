# PubMedNotifier

## Description

This python script is a python port of the [pubcrawler](http://pubcrawler.gen.tcd.ie/)
perl script. Its purpose is to alert for new PubMed publications for a given query,
without having to go through the PubMed website. This script is powerful when
used as a scheduled task, for eg. as a cron job.

This script is developed for GNU/Linux distributions. PR for adaptations are welcomed.

## Install, upgrade, and reset history

```sh
git clone https://gitea.com/amartos/PubMedNotifier/
cd PubMedNotifier && make install
```

```sh
cd path/to/PubMedNotifier
make upgrade
```

```sh
cd path/to/PubMedNotifier
make reset
```

## Configuration

At first install, you need to configure the DEFAULT section with at least your
e-mail address to avoid being blocked without warning in case of problems (the
NCBI will send you an e-mail beforehand). You can also customize the folder path
where the results files will be written, and other minor searches defaults.

To set-up searches, you need at least a title for the search, and the query. Add
them to the file as follow :

```
[Title]
query = my words to search
```

Query tokens are supported. See the [pubmed
help](https://www.ncbi.nlm.nih.gov/books/NBK3827/) for more details.

You can also narrow searches by adding the following parameters:

* `retstart` indicates the index of the first record to retrieve (default to 0)
* `retmax` defines the max number of records to retrieve (default to 20)
* `mindate` is the oldest date limit for the records' publication (default to
  1900/01/01)
* `maxdate` is the most recent date limit for the records' publication (default
  to script's execution date)

Here is a complete example for a couple of searches:

```
[Alexandre Martos]
query = Alexandre Martos[Author]

[Yeasts]
query = yeasts

[Mitochondria in yeasts]
query = yeasts AND mitochondria
mindate = 2015/07/08
maxdate = 2018/12/31
retstart = 5
retmax = 200
```

## Notes on usage

In order to avoid an overload of the PubMed servers (especially if you have 
plenty of queries), please avoid launching it everyday.

## TODO

[] add other types of notification (mails, etc...)
