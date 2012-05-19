#!/usr/bin/python -u
# coding: utf-8

import sys
import time
import urllib2
import re
from optparse import OptionParser

class G1BovespaParser:
    
    def __init__(self):
        self.setContextUrl(None)
    
    def filterUrl(self, url):
        if not "economia" in url:
            return True
        else:
            return False
        
    def clearContext(self):
        self.__keepPage = False
        self.inPlace = False
        
    def setContextUrl(self, url):
        if url and "noticia" in url:
            self.contextUrl = url
        else:
            self.contextUrl = None
            
        self.clearContext()
        
    def parseLine(self, line):
        if not self.__keepPage and self.contextUrl != None:
            if "materia-letra" in line:
                self.inPlace = True
            
            if self.inPlace and ("bovespa" in line or "BOVESPA" in line):
                self.__keepPage = True
            
            if "lista-de-entidades" in line:
                self.inPlace = False
        
    def keepPage(self):
        return self.__keepPage

class SimpleCrawler:
    
    def __init__(self, starting_point, parser):
        self.crawl_queue = []
        self.crawled_urls = []
        self.verbose = False
        self.delay = 0
        self.semanticParser = parser
        self.tldMode = False
        self.pagesKept = []
        
        # regex para identificação de <a>
        self.anchor_re = re.compile(".*<\s*a\s+[^>]*href=['\"]([^'\"]*)['\"].*", re.I)
        
        # regex para urls válidas relativas
        self.relative_url_re = re.compile("/?[^:#\?].*")
        
        # regex para urls absolutas
        self.absolute_url_re = re.compile("https?://.*")
        
        # regex para domínio.
        self.domain_re = re.compile("(https?://([^/:]+)(:\d+)?)(/.*)?")
        
        self.__addUrl(self.__resolveUrl(starting_point,starting_point))
    
    def __printTitle(self, string):
        if self.verbose:
            sub = len(string)
            print "" # Margin top
            print string
            print "=" * sub
    
    def __print(self, string):
        if self.verbose:
            print(string)
    
    def __getTopLevelDomain(self, domain):
        parts = domain.split(".")
        
        if len(parts) > 1:
            top = parts.pop()
            master = parts.pop()
            return "%s.%s" % (master, top)
        else:
            return domain
    
    def __resolveUrl(self, url, context):
        # Arruma urls que não são absolutas preparando
        # as mesmas para o processo de crawling
        # Se uma url for não 'crawleavel' retorna None
        
        resolvedUrl = None
        
        if self.absolute_url_re.match(url):
            if self.tldMode:
                urlDomain = self.__getTopLevelDomain(self.domain_re.match(url).group(2))
                contextDomain = self.__getTopLevelDomain(self.domain_re.match(context).group(2))
            else:
                urlDomain = self.domain_re.match(url).group(2)
                contextDomain = self.domain_re.match(context).group(2)
            
            if urlDomain == contextDomain:
                resolvedUrl = url.rstrip('/')
            else:
                return None
                
        elif self.relative_url_re.match(url) and not "javascript:" in url:
            if url[0] == "/":
                resolvedUrl = "%s/%s" % (self.domain_re.match(context).group(1), url.lstrip('/'))
            else:
                resolvedUrl = "%s/%s" % (context.rstrip('/'), url.lstrip('/'))
                
        if resolvedUrl != None and resolvedUrl.find('#') > 0:
            resolvedUrl = resolvedUrl[0:resolvedUrl.find('#')]
        
        if resolvedUrl != None and self.semanticParser.filterUrl(resolvedUrl):
            return None
        
        return resolvedUrl
    
    def __addUrl(self, url):
        # Adiciona uma URL na fila somente se esta já não estiver lá
        # e já não tiver sido "crawleada"
        if url not in self.crawl_queue and url not in self.crawled_urls:
            self.__print("Adding '%s' to queue" % url)
            self.crawl_queue.append(url)
        else:
            self.__print("Ignoring repeated url '%s'" % url)
    
    def __crawlNext(self):
        if len(self.crawl_queue) > 0:
            # Pega a próxima url da fila
            url = self.crawl_queue.pop(0)
            self.crawled_urls.append(url)
            self.__printTitle("Crawling '%s'" % url)
            self.semanticParser.setContextUrl(url)
            
            # Fazendo um GET simples para a URL
            try:
                url_content = urllib2.urlopen(url)
            except:
                print "Error fetching '%s'" % url
                return
            
            for line in url_content:
                # Procura a cada linha se existe um <a> para uma URL nova
                match = self.anchor_re.match(line)
                if match:
                    resolvedUrl = self.__resolveUrl(match.group(1), url)
                    if resolvedUrl:
                        self.__addUrl(resolvedUrl)
                    else:
                        self.__print("Bad url '%s'" % match.group(1))

                    if self.delay:
                        time.sleep(self.delay)
                
                # Executa a ação semântica para a linha
                self.semanticParser.parseLine(line)
        
            if self.semanticParser.keepPage():
                print "Found page '%s'" % url
                self.pagesKept.append(url)
    
    def setVerbose(self):
        self.verbose = True
    
    def setTLDMode(self):
        self.tldMode = True
    
    def setDelay(self, delay):
        if delay == None:
            self.delay = 0.2
        else:
            self.delay = delay
    
    def start(self):
        print "Crawler started"
        
        while len(self.crawl_queue) > 0:
            self.__crawlNext()
        
        self.__printTitle("Finished crawl process")
        print "URLs visited:", len(self.crawled_urls)
        print "Pages kept:", len(self.pagesKept)
        print self.pagesKept

if __name__ ==  "__main__":
    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="Verbose mode")
    parser.add_option("-t", "--tdl", action="store_true", dest="tld", help="Limit to top level domain.")
    parser.add_option("-d", "--delayed", action="store_true", dest="delayed", help="Delayed execution. Add delay, in seconds, to each matched processed line. Implies verbose.")

    (options, args) = parser.parse_args()

    crawler = SimpleCrawler("http://g1.globo.com/economia/", G1BovespaParser())

    if options.verbose or options.delayed:
        crawler.setVerbose()
        
    if options.tld:
        crawler.setTLDMode()

    if options.delayed:
        crawler.setDelay(0.5)

    crawler.start()