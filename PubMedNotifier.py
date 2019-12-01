#!/usr/bin/env python3

import time
import datetime
import errno
import os
import configparser
import metapub
import notify2
import textwrap

class PubMedNotifier:

    def __init__(self):
        self._queries = dict()
        self._results = dict()
        self._counts = dict()
        self._new_papers = dict()
        self._history = list()

        self._user_dir = os.path.expanduser("~/")
        self._cache_dir = self._user_dir+".cache/pubmednotifier"

        self._config_file = self._user_dir+".config/pubmednotifier/config"
        self._config_file_exists()
        self._read_config()
        self._parse_default_config()
        self._parse_queries()

        self._history_file = self._user_dir+".local/share/pubmednotifier/history"
        if self._history_file_exists():
            self._get_history()

        self._fetcher = metapub.PubMedFetcher(email=self._email, cachedir=self._cache_dir)
        self._check_new_results()

    def _config_file_exists(self):
        if not os.path.exists(self._config_file):
            raise FileNotFoundError(
                    errno.ENOENT,
                    os.strerror(errno.ENOENT),
                    self._config_file
                    )

    def _read_config(self):
        self._config = configparser.ConfigParser()
        self._config.read_file(open(self._config_file))

    def _parse_default_config(self):
        self._email = self._config["DEFAULT"]["e-mail"]
        self._new_papers_file = \
            os.path.expanduser(self._config["DEFAULT"]["results path"]) + \
            str(datetime.datetime.now())+".md"
        self._default_retstart = self._config["DEFAULT"]["retstart"]
        self._default_retmax = self._config["DEFAULT"]["retmax"]
        self._default_mindate = self._config["DEFAULT"]["mindate"]
        self._default_maxdate = None

    def _parse_queries(self):
        for item in self._config.sections():
            if not item == "DEFAULT":
                title = item

                try:
                    term = self._config.get(item, "query")
                    if not term:
                        continue
                except configparser.NoOptionError:
                    continue

                try:
                    retstart = self._config.get(item, "retstart")
                except configparser.NoOptionError:
                    retstart = self._default_retstart

                try:
                    retmax = int(self._config.get(item, "retmax"))
                except configparser.NoOptionError:
                    retmax = self._default_retmax

                try:
                    maxdate = int(self._config.get(item, "maxdate"))
                except configparser.NoOptionError:
                    maxdate = self._default_maxdate

                try:
                    mindate = self._config.get(item, "mindate")
                except configparser.NoOptionError:
                    mindate = self._default_mindate

                self._queries[title] = {
                        "query":term,
                        "retstart":retstart,
                        "retmax":retmax,
                        "mindate":mindate,
                        "maxdate":maxdate,
                        }

    def _history_file_exists(self):
        if not os.path.exists(self._history_file):
            open(self._history_file, "w").close()
            return False
        else:
            return True

    def _get_history(self):
        with open(self._history_file,"r") as f :
            self._history = [i.strip("\n") for i in f.readlines()]

    def _check_new_results(self):
        self._fetch_results()
        self._check_history()
        self._parse_results()
        self._set_history()
        self._write_results()
        self._notify()

    def _fetch_results(self):
        for title, values in self._queries.items():
            ids = self._fetcher.pmids_for_query(
                    query=values["query"],
                    since=values["mindate"],
                    until=values["maxdate"],
                    retstart=values["retstart"],
                    retmax=values["retmax"],
                    )
            self._results[title] = ids

    def _check_history(self):
        new_ids = list()
        for title, ids in self._results.items():
            for pmid in ids:
                if not pmid in self._history:
                    new_ids.append(pmid)
            self._results[title] = new_ids
            self._counts[title] = len(new_ids)

    def _parse_results(self):
        for title, ids in self._results.items():
            self._new_papers[title] = dict()
            for pmid in ids:
                article = self._fetcher.article_by_pmid(pmid)
                self._new_papers[title][pmid] = (
                        article.title,
                        article.journal,
                        article.year,
                        ", ".join(article.authors),
                        article.abstract
                        )

    def _set_history(self):
        for title, ids in self._results.items():
            self._history += ids
        self._history = list(set(self._history))
        with open(self._history_file,"w") as f :
            for pmid in self._history:
                f.write(pmid+"\n")

    def _write_results(self):
        empty = True
        text = str()
        for query, ids in self._new_papers.items():
            if ids:
                empty = False
                text += "# "+query+"\n\n"
                for pmid, infos in ids.items():
                    title, journal, year, authors, abstract = infos
                    if not abstract or abstract == "None":
                        abstract = "No abstract."
                    else:
                        abstract = "\n".join(textwrap.wrap(abstract, width=80))
                    text += "## {}\n\n{}, *{}*, {}\n\n[Link to pubmed]({})\n\n{}\n\n".format(
                            title,
                            authors,
                            journal,
                            year,
                            "https://www.ncbi.nlm.nih.gov/pubmed/"+pmid,
                            abstract,
                            )
        if not empty:
            with open(self._new_papers_file, "w") as f:
                f.write(text)

    def _notify(self):
        total = 0
        message = str()
        for title, count in self._counts.items():
            total += count
            message += title+": {} new papers\n".format(str(count))
        if total > 0:
            notify2.init("PubMedNotifier")
            notifier = notify2.Notification(message)
            notifier.show()
            return


if __name__ == "__main__":
    PubMedNotifier()
