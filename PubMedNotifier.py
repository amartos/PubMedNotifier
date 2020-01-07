#!/usr/bin/env python3

import os, sys, argparse
import re, datetime, textwrap

import metapub
import configparser
from xdg import (XDG_CACHE_HOME, XDG_DATA_HOME, XDG_CONFIG_HOME)

class EmailSyntaxError(ValueError):
    """Error to raise if the provided e-mail is
    not syntactically valid."""
    pass

class EmptyDefaultError(ValueError):
    """Error to raise if a DEFAULT is empty."""
    pass

class QueryInvalidError(ValueError):
    """Error to raise if a query is badly formatted."""
    pass

class PubMedNotifier:

    def __init__(self):
        self._init_vars()
        self._parse_args()

        # These checks are done here as the _config_file var
        # can be changed by the script's arguments
        if os.path.exists(self._config_file):
            self._parse_config()
        else:
            self._error_log("'{}' config file does not exists.".format(self._config_file))
            sys.exit(1)

        if os.path.exists(self._queries_file):
            self._parse_queries()
        else:
            self._error_log("'{}' queries file does not exists.".format(self._queries_file))
            sys.exit(1)

        self._get_pmids_history()

        if self._queries:
            self._check_new_results()
            if self._send_notification:
                self._notify()
        else:
            self._error_log("No defined queries in {}".format(self._config_file))

    def _init_vars(self):
        self._config = None
        self._queries_config = None
        self._defaults = dict()
        self._queries = dict()
        self._results = dict()
        self._counts = dict()
        self._new_papers = dict()
        self._history = list()
        self._send_notification = bool()

        self._cache_dir = str(XDG_CACHE_HOME.absolute())+"/pubmednotifier"
        self._check_if_folder_exists(self._cache_dir)

        self._data_dir = str(XDG_DATA_HOME.absolute())+"/pubmednotifier"
        self._check_if_folder_exists(self._data_dir)
        self._log_file = self._data_dir+"/log_"+str(datetime.datetime.now())
        self._check_if_file_exists(self._log_file)
        self._history_file = self._data_dir+"/history"
        self._check_if_file_exists(self._history_file)
        self._queries_file = self._data_dir+"/queries"
        self._check_if_file_exists(self._queries_file)

        self._config_dir = str(XDG_CONFIG_HOME.absolute())+"/pubmednotifier"
        self._check_if_folder_exists(self._config_dir)
        self._config_file = self._config_dir+"/config"

    def _check_if_folder_exists(self, path):
        if not os.path.exists(path):
            os.mkdir(path)

    def _check_if_file_exists(self, path):
        if not os.path.exists(path):
            open(path, "w").close()

    def _parse_args(self):
        parser = argparse.ArgumentParser(self,
                description="""PubMedNotifier is a script that fetch queries
                results from the Pubmed API and notify if new papers are
                available."""
            )

        parser.add_argument(
                "-c", "--config",
                help="""Specify a path for the config file. Default is in
                $XDG_CONFIG_HOME/pubmednotifier/config"""
            )

        parser.add_argument(
                "-f", "--file",
                help="""Specify a path for the queries file. Default is in
                $XDG_DATA_HOME/pubmednotifier/queries"""
            )

        parser.add_argument(
                "-q", "--quiet",
                help="""Disables notifications.""",
                action="store_true"
            )

        args = parser.parse_args()

        if args.config:
            self._config_file = args.config

        if args.file:
            self._queries_file = args.file

        self._send_notification = not args.quiet

    def _parse_config(self):
        self._config = self._read_config(self._config_file)
        self._parse_default_config()

    def _read_config(self, filepath):
        parser = configparser.ConfigParser()
        parser.read_file(open(filepath))
        return parser

    def _parse_default_config(self):
        self._new_papers_file = os.path.join(
            os.path.expanduser(path),
            str(datetime.datetime.now())+".md"
            )
        self._defaults["e-mail"] = self._get_default_parameters("e-mail")
        self._defaults["retstart"] = self._get_default_parameters("retstart")
        self._defaults["retmax"] = self._get_default_parameters("retmax")
        self._defaults["mindate"] = self._get_default_parameters("mindate")
        self._defaults["maxdate"] = None

    def _get_default_parameters(self, parameter):
        """Get the DEFAULT parameter if valid,
        but raise error and abort if invalid"""
        try:
            value = self._config["DEFAULT"][parameter]
            # check if parameter is empty
            if not value:
                raise EmptyDefaultError
            else:
                # check if e-mail syntax is valid
                if parameter == "e-mail" and \
                        not bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", value)):
                    raise EmailSyntaxError
                else:
                    return value
        except KeyError or EmptyDefaultError as err:
            self._error_log("DEFAULT {} is not defined.".format(parameter))
        except EmailSyntaxError as err:
            self._error_log("{} is not a syntactically valid e-mail.".format(value))

        sys.exit(1)

    def _parse_queries(self):
        self._queries_config = self._read_config(self._queries_file)
        for item in self._queries_config.sections():
            self._read_one_query(item)

    def _read_one_query(self, title):
        try:
            term = self._queries_config.get(title, "query")
            if not term:
                raise QueryInvalidError
        except configparser.NoOptionError or KeyError or QueryInvalidError as err:
            self._error_log("Query {} is not valid.\n".format(title))
            return

        self._queries[title] = {
                "query":term,
                "retstart":"",
                "retmax":"",
                "mindate":"",
                "maxdate":"",
                }

        for item in self._queries[title].keys():
            if item != "query":
                try:
                    self._queries[title][item] = self._queries_config.get(title,item)
                except configparser.NoOptionError:
                    self._queries[title][item] = self._defaults[item]

    def _get_pmids_history(self):
        with open(self._history_file,"r") as f :
            self._history = [i.strip("\n") for i in f.readlines()]

    def _check_new_results(self):
        self._fetch_results()
        self._check_pmids_history()
        self._count_new_items()
        self._retrieve_new_pmid_infos()
        self._save_new_pmids_in_history()
        self._write_results()

    def _fetch_results(self):
        self._fetcher = metapub.PubMedFetcher(email=self._defaults["e-mail"], cachedir=self._cache_dir)
        for title, values in self._queries.items():
            ids = self._fetcher.pmids_for_query(
                    query=values["query"],
                    since=values["mindate"],
                    until=values["maxdate"],
                    retstart=values["retstart"],
                    retmax=values["retmax"],
                    )
            self._results[title] = ids

    def _check_pmids_history(self):
        for title, ids in self._results.items():
            new_items = [i for i in ids if not i in self._history]
            if new_items:
                self._results[title] = new_items

    def _count_new_items(self):
        for title in self._results.keys():
            self._counts[title] = len(self._results[title])

    def _retrieve_new_pmid_infos(self):
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

    def _save_new_pmids_in_history(self):
        with open(self._history_file,"a") as f :
            for title, ids in self._results.items():
                f.write("\n"+"\n".join(ids))

    def _write_results(self):
        text = str()
        for query, ids in self._new_papers.items():
            text += "# "+query+"\n\n"
            for pmid, infos in ids.items():
                title, journal, year, authors, abstract = infos
                if not abstract or abstract == "None":
                    abstract = "No abstract."
                else:
                    abstract = "\n".join(textwrap.wrap(abstract, width=80))
                text += "## {}\n\n{}, *{}*, {}\n\n[PMID: {}]({})\n\n{}\n\n".format(
                        title,
                        authors,
                        journal,
                        year,
                        pmid,
                        "https://www.ncbi.nlm.nih.gov/pubmed/"+pmid,
                        abstract,
                        )
        if text:
            with open(self._new_papers_file, "w") as f:
                f.write(text)

    def _notify(self):
        if os.path.exists(self._new_papers_file):
            self._desktop_notification()

    def _desktop_notification(self):
        import notify2

        message = str()
        for title, count in self._counts.items():
            message += title+": {} new papers\n".format(str(count))
        if message:
            notify2.init("PubMedNotifier")
            notifier = notify2.Notification(message)
            notifier.show()
            return

    def _error_log(self, err_msg):
        with open(self._log_file, "a") as f:
            f.write(str(datetime.datetime.now())+": "+err_msg+"\n")
        print(err_msg)
        self._check_log_size()

    def _check_log_size(self):
        if os.stat(self._log_file).st_size >= 500:
            self._log_file = self._data_dir+"/log_"+str(datetime.datetime.now())
            open(self._log_file, "w").close()

if __name__ == "__main__":
    PubMedNotifier()
