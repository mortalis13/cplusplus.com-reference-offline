
import os, re, codecs, subprocess
import shutil, stat, errno, sys, operator

import urllib.parse, html
from lxml import etree


# ---
def test1():
  fp = 'e:/tools/wget/cplusplus_reference_v1/www.cplusplus.com/reference/ios/ios/index.html'
  parser = etree.HTMLParser()
  html_doc = etree.parse(fp, parser)
  
  divs = html_doc.xpath('//div[@id="I_nav"]//div')
  for d in divs:
    at_id = d.get('id')
    if at_id and at_id != 'reference_box' and at_id != 'I_subnav':
      links = d.xpath('.//a')
      print(str(len(links)))

# ---
def test():
  ref_path = 'e:/tools/wget/cplusplus_reference/www.cplusplus.com/reference/'
  for root, dirs, files in os.walk(ref_path):
    for f in files:
      ext = os.path.splitext(f)[1]
      if 'htm' in ext:
        parser = etree.HTMLParser()
        fp = root + '/' + f
        # fp = fp.replace('/','\\')
        fp = fp.replace('\\','/')
        html_doc = etree.parse(fp, parser)
        links = html_doc.xpath('//a[contains(@href,"http:")]')
        # print(str(len(links)))
        if len(links):
          print('\n-- ' + fp)
        for link in links:
          href = link.get("href")
          if not web_ref_prefix in href:
            continue
          rel_href = href.replace(web_ref_prefix, '')
          
          rel_fp = fp.replace(ref_path, '')
          updir_count = len(re.findall('/', rel_fp))
          rel_href = '../'*updir_count + rel_href
          
          text = link.xpath("string()")
          print('   {0}\n     {1}\n     {2}'.format(href, rel_href, text))
    
    # return


# -------------------
test()
