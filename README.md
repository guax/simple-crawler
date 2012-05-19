Simple Crawler
==============

Simple crawler designed to fetch all the news urls
from g1.globo.com/economia that contains the word
"bovespa" in its news content.

The crawler uses regex and terms that only apply
to the g1 site state of 2012-05-19 and it has
no intent to keep working past the presentation
date of 2012-05-22.

It will crawl all the pages anyways. That part
of the code is generic enough.

How It Works
============

From a starting poing URL it searches for all
the html <a>nchors elements and add its href
to the crawl queue if it complies with some
restrictions like being part of the same
domain.

The code is simple and straightforward.

