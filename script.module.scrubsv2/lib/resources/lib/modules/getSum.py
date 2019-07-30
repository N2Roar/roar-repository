# -*- coding: utf-8 -*-
# --[getSum v1.2]--|--[From JewBMX]--
# Lazy Module to make life a little easier.

import re, time, traceback
from resources.lib.modules import log_utils
import HTMLParser

headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3555.0 Safari/537.36"}


def replaceHTMLCodes(text):
    try:
        text = re.sub("(&#[0-9]+)([^;^0-9]+)", "\\1;\\2", text)
        text = HTMLParser.HTMLParser().unescape(text)
        text = text.replace("&quot;", "\"")
        text = text.replace("&amp;", "&")
        text = text.replace("%2B", "+")
        text = text.replace("\/", "/")
        text = text.replace("\\", "")
        text = text.strip()
        return text
    except Exception:
        error = traceback.format_exc()
        log_utils.log('getSum - replaceHTMLCodes ERROR:  ' + str(error))
        return


# Normal = getSum.get(url)
# CFscrape = getSum.get(url, Type='cfscrape')
def get(url, Type=None):
    try:
        if not url:
            return
        if Type == 'client' or Type == None:
            from resources.lib.modules import client
            content = client.request(url, headers=headers)
        if Type == 'cfscrape':
            from resources.lib.modules import cfscrape
            cfscraper = cfscrape.create_scraper()
            content = cfscraper.get(url, headers=headers).content
        if Type == 'redirect':
            import requests
            content = requests.get(url, headers=headers).url
        elif content is None:
            log_utils.log('getSum - Get ERROR:  No Content Got.')
            raise Exception()
        return content
    except Exception:
        error = traceback.format_exc()
        log_utils.log('getSum - Get ERROR:  ' + str(error))
        return


# results = getSum.findEm(text, '(?:iframe|source).+?(?:src)=(?:\"|\')(.+?)(?:\"|\')')
# for result in results:
def findEm(text, regex):
    try:
        results = re.findall(regex, text, flags=re.DOTALL | re.IGNORECASE)
        if results:
            return results
    except Exception:
        error = traceback.format_exc()
        log_utils.log('getSum - findEm ERROR:  ' + str(error))
        return []


# results = getSum.findThat(text, 'hhhhh')
# for result in results:
def findThat(text, regex):
    try:
        p_reg = re.compile(regex, flags=re.DOTALL | re.IGNORECASE)
        results = p_reg.findall(text)
        if results:
            return results
    except Exception:
        error = traceback.format_exc()
        log_utils.log('getSum - findAll ERROR:  ' + str(error))
        return []


class GetSum(object):
    _frame_regex = r'(?:iframe|source).+?(?:src)=(?:\"|\')(.+?)(?:\"|\')'
    _datavideo_regex = r'(?:data-video|data-src|data-href)=(?:\"|\')(.+?)(?:\"|\')'
    _filesource_regex = r'(?:file|source)(?:\:)\s*(?:\"|\')(.+?)(?:\"|\')'
    _magnet_regex = r'''(magnet:\?[^"']+)'''
    _timeout = 10
    def findSum(self, text, type=None):
        try:
            self.links = set()
            if not text:
                return
            if re.search(self._frame_regex, text, re.IGNORECASE) or type == 'iframe':
                links = self._findSum_iframe(text)
                if links:
                    for link in links:
                        link =  "https:" + link if not link.startswith('http') else link
                        if link in self.links:
                            continue
                        self.links.add(link)
            if re.search(self._datavideo_regex, text, re.IGNORECASE) or type == 'datavideo':
                links = self._findSum_datavideo(text)
                if links:
                    for link in links:
                        link =  "https:" + link if not link.startswith('http') else link
                        if link in self.links:
                            continue
                        self.links.add(link)
            if re.search(self._filesource_regex, text, re.IGNORECASE) or type =='filesource':
                links = self._findSum_filesource(text)
                if links:
                    for link in links:
                        link =  "https:" + link if not link.startswith('http') else link
                        if link in self.links:
                            continue
                        self.links.add(link)
            if re.search(self._magnet_regex, text, re.IGNORECASE) or type == 'magnet':
                links = self._findSum_magnet(text)
                if links:
                    for link in links:
                        link = str(replaceHTMLCodes(link).encode('utf-8').split('&tr')[0])
                        link =  "magnet:" + link if not link.startswith('magnet') else link
                        if link in self.links:
                            continue
                        self.links.add(link)
            return self.links
        except Exception:
            error = traceback.format_exc()
            log_utils.log('getSum - findSum ERROR:  ' + str(error))
            return []


    def _findSum_iframe(self, text):
        try:
            results = re.compile('(?:iframe|source).+?(?:src)=(?:\"|\')(.+?)(?:\"|\')').findall(text)
            if results:
                return results
        except Exception:
            error = traceback.format_exc()
            log_utils.log('getSum - _findSum_iframe ERROR:  ' + str(error))
            return []


    def _findSum_datavideo(self, text):
        try:
            results = re.compile('(?:data-video)=(?:\"|\')(.+?)(?:\"|\')').findall(text)
            if results:
                return results
        except Exception:
            error = traceback.format_exc()
            log_utils.log('getSum - _findSum_datavideo ERROR:  ' + str(error))
            return []


    def _findSum_filesource(self, text):
        try:
            results = re.compile('(?:file|source)(?:\:)\s*(?:\"|\')(.+?)(?:\"|\')').findall(text)
            if results:
                return results
        except Exception:
            error = traceback.format_exc()
            log_utils.log('getSum - _findSum_filesource ERROR:  ' + str(error))
            return []


    def _findSum_magnet(self, text):
        try:
            results = re.compile('''(magnet:\?[^"']+)''').findall(text)
            if results:
                return results
        except Exception:
            error = traceback.format_exc()
            log_utils.log('getSum - _findSum_magnet ERROR:  ' + str(error))
            return []


# results = getSum.findSum(text)
# for result in results:
def findSum(text, type=None, timeout=10):
    try:
        if not text:
            return
        getSum = GetSum()
        results = getSum.findSum(text, type=type)
        if results:
            return results
    except Exception:
        error = traceback.format_exc()
        log_utils.log('getSum - findSum ERROR:  ' + str(error))
        return []


# moreresults = getSum.findSumMo(text)
# for result in moreresults:
def findSumMo(url, type=None, timeout=10):
    try:
        if not url:
            return
        _embedders = ['vidcloud.icu', 'nextwebsite.gov']
        for i in _embedders:
            if i.lower() in url.lower():
                text = get(url, Type='cfscrape')
                getSum = GetSum()
                results = getSum.findSum(text, type=type)
                if results:
                    return results
    except Exception:
        error = traceback.format_exc()
        log_utils.log('getSum - findSumMo ERROR:  ' + str(error))
        return []


