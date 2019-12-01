# PubMedNotifier

## Description

## Install & upgrade

To install


## Configuration

At first install, you need to configure the default section with at least your
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

## Usage







