
# Offline Reference from cplusplus.com 

This project allows to generate offline help file with **C++ reference** from the site cplusplus.com.

See the [**releases**](https://github.com/mortalis13/cplusplus.com-reference-offline/releases) section for built packages.

It includes:

- full site in **HTML**
- full site in **QCH**
- reference section in **HTML**
- reference section in **QCH**

The **_site** package includes linked **HTML** pages corresponding to the full site except **Forum** or only **Reference** block of the site. It can be viewed in any browser.

The **QCH** files are in the **Qt Help** format ready to use with the [**Qt Assistant**](http://doc.qt.io/qt-5/assistant-quick-guide.html) tool.

## Build info

The **main.py** script can be used to build **Qt help project** file to then generate **QCH** help file.

**OS:** Windows x64
**Tools**: [wget](http://gnuwin32.sourceforge.net/packages/wget.htm), [Python 3.5](https://www.python.org/downloads/release/python-350/), [Qt 5.3.1](https://download.qt.io/archive/qt/5.3/5.3.1/)

Steps performed to build the available packages:

- Download the pages with **wget**:

      wget -rpk -nc -np -P cplusplus_reference -o cpp_log.txt http://www.cplusplus.com/reference/

  it's enough to download only the reference section to have all reference pages and the majority of links, but it's better to download the whole site (maybe with some restrictions on URLs) and then work only with `reference` folder.
  
  In the latter case all the internal links in the reference will be more stable/offline. I had to launch the wget command multiple times to get all the pages because the downloads are sometimes skipped due to some connection problems.
  
- Fix some page reference problems: first my local pages didn't load images/icons so I downloaded them manually. These were: **v321/bg.png, v321/bgh.png, v321/bgv.png**.

- Adjust variables in the **main.py** script. These are: `ref_path` that points to local root path of the downloaded site (the folder with the **reference** subfolder) and `full_site` (`True` or `False`) to generate a help file with full content or only reference section.

- Run the script

      python main.py

- Wait some time (it was about 1 min in my case) and check the **qch-proj.xml** file in the site root. It has the **Qt Help project** data needed to generate the **.qch** file. It should contain **<keywords>** section which will go the the **Index** panel of the **Qt Assistant** tool with relative links to the pages for each keyword. And **<files>** section with all the files (HTML pages and resources) that will be packed to the help file.

- Generate he **.qch** file with Qt running the command:

      [QT_HOME]\bin\qhelpgenerator "qch-proj.xml" -o "cpp-ref.qch"

  the file should be about 15 MB

- To check the final file open **Qt Assistant** from the **[QT_HOME]\bin\assistant.exe**

- Navigate to the **Edit -> Preferences** menu, **Documentation** tab and **Add** the file to the list.

- After that you should see the **Standard C++ Library reference** entry in the **Content** panel. Click there and navigate the reference. The **Index** panel can be used to search for the most important keywords and the tool also allows to **Search** the content of all the pages.

## Notes

I didn't add **Table of contents** to the **.qch** file because the site itself has already its navigation panel.
