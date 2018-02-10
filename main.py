
import os, re, codecs, subprocess
import shutil, stat, errno, sys, operator

import urllib.parse, html
from lxml import etree


ref_path = 'e:/tools/wget/cplusplus_reference/www.cplusplus.com/'
full_site = False

web_ref_prefix = 'http://www.cplusplus.com/reference/'
qch_proj_name = 'qch-proj'

ref_dirs = [
  'img',
  'reference',
  'site',
  'v321'
]

QCH_PROJ_TEXT_TMPL = """
<?xml version='1.0' encoding='utf-8'?>
<QtHelpProject version="1.0">
  <namespace>cplusplus_com</namespace>
  <virtualFolder>cpp</virtualFolder>
  <customFilter name="C++ Reference">
    <filterAttribute>cplusplus_ref</filterAttribute>
  </customFilter>
  <filterSection>
    <filterAttribute>cplusplus_ref</filterAttribute>
    <toc>
      {0}
    </toc>
    <keywords>
      {1}
    </keywords>
    <files>
      {2}
    </files>
  </filterSection>
</QtHelpProject>
"""

MAIN_TOC_FULL = """
<section title="cplusplus.com" ref="index.html">
  <section title="Information" ref="info/index.html" />
  <section title="Tutorials" ref="doc/index.html" />
  <section title="Reference" ref="reference/index.html" />
  <section title="Articles" ref="articles/index.html" />
</section>
"""

MAIN_TOC_REF = """
<section title="Standard C++ Library reference" ref="reference/index.html" />
"""


# ---
def print_keywords(keywords):
  for key in keywords:
    print(key + '\n    :: ' + keywords[key] + '\n')


# ---
def clear_html(fp):
  ext = os.path.splitext(fp)[1]
  if ext != '.html' and ext != '.htm':
    return
  
  # relative path from the reference root 
  # and number of folders to go up from the current file directory to the 'reference' root
  rel_fp = fp.replace(ref_path + 'reference/', '')
  updir_count = len(re.findall('/', rel_fp))
  
  parser = etree.HTMLParser()
  html_doc = etree.parse(fp, parser)
  
  html_changed = False
  
  # remove cookie panel
  search_text = 'consent=cookie'
  scripts = html_doc.xpath('//script')
  for script in scripts:
    text = script.text
    if text and search_text in text:
      script.getparent().remove(script)
      html_changed = True
  
  # remove adds
  c_support_header = html_doc.xpath('//div[@class="C_support"]')
  for m in c_support_header:
    m.getparent().remove(m)
    html_changed = True
    
  # remove adds
  ins_elements = html_doc.xpath('//ins')
  for m in ins_elements:
    m.getparent().remove(m)
    html_changed = True
  
  # fix relative links
  links = html_doc.xpath('//a[contains(@href,"' + web_ref_prefix + '")]')
  for link in links:
    href = link.get("href")
    text = link.xpath('string()')
    
    print('Trying to fix external link:\n  {0}\n  {1} :: {2}'.format(fp, href, str(text)))

    href = href.replace(web_ref_prefix, '')
    
    rel_fp_base = os.path.dirname(rel_fp) + '/'
    rel_fp_base_pos = href.find(rel_fp_base)
    if rel_fp_base_pos == 0:
      href = href.replace(rel_fp_base, '')
    else:
      href = '../'*updir_count + href
    
    link.set("href", href)
    html_changed = True
    
  if html_changed:
    html_doc.write(fp, encoding='utf-8', method='html')


# ---
def fix_js():
  main_js = ref_path + 'v321/main.js'
  
  f = codecs.open(main_js, 'r', 'utf-8')
  text = f.read()
  f.close()
  
  # set Qt absolute path instead of the default one (the script adds the 'versions' link after content loaded)
  text = text.replace('"/site/versions/"', '"qthelp://cplusplus_com/cpp/site/versions/index.html"')
  
  f = codecs.open(main_js, 'w', 'utf-8')
  f.write(text)
  f.close()


# ---
def collect_keywords(fp, keywords, main_ref=False):
  ext = os.path.splitext(fp)[1]
  if ext != '.html' and ext != '.htm' or not 'reference/' in fp:
    return
  
  parser = etree.HTMLParser()
  html_doc = etree.parse(fp, parser)
  
  links = []
  if main_ref:
    # only the Reference block links
    links = html_doc.xpath('//div[@id="I_nav"]//div[@id="reference_box"]//a')
  else:
    # submodules links (below Reference block)
    divs = html_doc.xpath('//div[@id="I_nav"]//div')
    for d in divs:
      at_id = d.get('id')
      if at_id and at_id != 'reference_box' and at_id != 'I_subnav':
        links = d.xpath('.//a')
  
  # get link names and addresses
  for link in links:
    href = link.get("href")
    text = link.xpath("string()")
    
    if href == None or href.find('..') != -1 or href == 'index.html' or href.find('http') == 0:
      continue
    
    href = urllib.parse.unquote(href)
    
    text = html.escape(text)
    text = text.strip()
    
    rel_href = os.path.dirname(fp).replace(ref_path, '') + '/' + href
    rel_href = rel_href.replace('\\', '/')
    
    if text in keywords:
      # add parent folder to distinguish keywords and remove the previous keyword
      prev_href = keywords[text]
      temp_href = prev_href.replace('reference/', '')
      kw_spec = os.path.dirname(os.path.dirname(temp_href))
      text1 = text + ' (' + kw_spec + ')'
      
      temp_href = rel_href.replace('reference/', '')
      kw_spec = os.path.dirname(os.path.dirname(temp_href))
      text2 = text + ' (' + kw_spec + ')'
      
      del keywords[text]
      keywords[text1] = prev_href
      keywords[text2] = rel_href
    else:
      keywords[text] = rel_href
    

# ---
def delete_header_keywords(keywords):
  headers = [
    'C library:',
    'Containers:',
    'Input/Output:',
    'Other:'
  ]
  
  for h in headers:
    del keywords[h]
  

# ---
def run():
  print('Process started')
  print('-- Generating Full site' if full_site else '-- Generating Reference block')
  
  # -- Init
  out_qch_proj = ref_path + qch_proj_name + '.xml'
  
  keywords = {}
  
  toc_ar = []
  keywords_ar = []
  files_ar = []
  
  subsection_indent = '      '
  
  
  # -- Reference block keywords/links
  main_page = ref_path + 'reference/index.html'
  collect_keywords(main_page, keywords, True)
  delete_header_keywords(keywords)
  
  fix_js()
  
  
  print('Processing files')
  
  # -- Process pages (modify content, collect keywords, collect <file>'s for Qt help project)
  for root, dirs, files in os.walk(ref_path):
    root = root.replace('\\', '/')
    
    # filter dirs for not full site (only reference)
    if not full_site and root != ref_path:
      sub_root_match = re.search(ref_path + '(.+?)/', root)
      sub_root_dir = root.replace(ref_path, '')
      if sub_root_match:
        sub_root_dir = sub_root_match.group(1)
      if not sub_root_dir in ref_dirs:
        continue
    
    for f in files:
      fp = root + '/' + f
      rel_fp = fp.replace(ref_path, '')
      if root == ref_path:
        rel_fp = rel_fp[1:]
      
      rel_fp = html.escape(rel_fp)
      felem = subsection_indent + '<file>' + rel_fp + '</file>'
      files_ar.append(felem)
      
      clear_html(fp)
      collect_keywords(fp, keywords)
  
  
  print('Building project tree')
  
  # -- Fill the project file text template
  qtoc = ''
  qkeywords = ''
  qfiles = ''
  
  main_toc = MAIN_TOC_REF
  if full_site:
    main_toc = MAIN_TOC_FULL
  main_toc = main_toc.strip()
  qtoc = main_toc.replace('\n', '\n    ')
  
  for key in keywords:
    kw = subsection_indent + '<keyword name="{0}" id="{0}" ref="{1}"/>'.format(key, keywords[key])
    qkeywords += kw + '\n'
  qkeywords = qkeywords.strip()
  
  for f in files_ar:
    if f.find('.qch') != -1 or f.find(qch_proj_name) != -1:
      continue
    qfiles += f + '\n'
  qfiles = qfiles.strip()
  
  project_text = QCH_PROJ_TEXT_TMPL.format(qtoc, qkeywords, qfiles)
  project_text = project_text.strip()
  
  print('Writing project file')
  
  # -- Write the project file
  f = codecs.open(out_qch_proj, 'w', 'utf-8')
  f.write(project_text)
  f.close()
  
  print('Process finished')


# -------------------
run()
