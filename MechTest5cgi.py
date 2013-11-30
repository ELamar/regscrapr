#!/usr/bin/python

#This program retrieves the SEC IAPD Search page for a given Investment Adviser number.
#It then retrieves Schedule D for that Adviser

import re
import mechanize
from bs4 import BeautifulSoup
import cgi, cgitb
from django.conf import settings
from django.template import Context, Template

#settings.configure = (DEBUG=True, TEMPLATE_DEBUG=True) #to configure the settings for Django
#you have to configure the settings if you are using only a portion of Django

br = mechanize.Browser()
ua = mechanize.UserAgentBase()
ua.addheaders = [("User-agent"),("Mac Safari")]

formtext = cgi.FieldStorage()
if formtext.getvalue('mgrnumber'):
  adviser = formtext.getvalue('mgrnumber')
else:
  adviser = 148823

#adviser = 148823
response = br.open('http://www.adviserinfo.sec.gov/IAPD/crd_iapd_AdvVersionSelector.aspx?ORG_PK='+str(adviser)+'&RGLTR_PK=50000')
content = response.read()
soup = BeautifulSoup(content)
form = soup.find('form', attrs={'name':'aspnetForm'})
action1 = form['action']
#action2 = re.sub('iapd_AdvIdentifyingInfoSection','Sections/iapd_AdvScheduleDSection', action1)
action2 = re.sub('iapd_AdvIdentifyingInfoSection','Sections/iapd_AdvAllPages', action1)
response2 = br.open('http://www.adviserinfo.sec.gov/iapd/content/viewform/adv/'+action2)
outfile = open("/Library/WebServer/Documents/iapdTemp.txt", "w")
outfile.write(response2.read())
#print response2.read()

soup2 = BeautifulSoup(open("/Library/WebServer/Documents/iapdTemp.txt"))
fundtd=soup2.find_all('td',text=re.compile("PRIVATE FUND"))

#print fundtd[0]

outfile2 = open("/Library/WebServer/Documents/outfile.html","w")
#outfile2.write("Content-type: text/html\n\n")
outfile2.write("<html><body>\n")

# First, find and print Manager name, number and Form ADV Date at top of page.
manName = soup2.find('span', attrs={'id':re.compile("ADVHeader_lblPrimaryBusinessName")})
manNumber = soup2.find('span', attrs={'id':re.compile("ADVHeader_lblCrdNumber")})
domsig = soup2.find('tr', attrs={'id':re.compile("ctl00_ctl00_cphMainContent_cphAdvFormContent_ADVExecutionDomesticPHSection")})
nonres= soup2.find('tr', attrs={'id':'ctl00_ctl00_cphMainContent_cphAdvFormContent_ADVExecutionNonResidentPHSection_ctl00_trIAPDHeader'})
regassets = soup2.find('span', attrs={'id':re.compile("AdvFormContent_AssetsUnderMgnmt_ctl00_lbl")})
outfile2.write("<table>\n")
outfile2.write("<tr><td>Manager Name: %s;</td><td>Manager Number: %s</tr>\n" % (manName.get_text(strip=True),manNumber.get_text(strip=True)))
outfile2.write("</table>\n")
outfile2.write("<table>")
if domsig.parent.find('span', attrs={'class':re.compile("PrintHistRed")}, text=re.compile(r"\d\d/\d\d/\d\d\d\d")):
  date = domsig.parent.find('span', attrs={'class':re.compile("PrintHistRed")}, text=re.compile("\d\d/\d\d/\d\d\d\d"))
  outfile2.write("<tr><td>Form ADV Date:%s</td></tr>\n" % date.get_text(strip=True))
elif nonres.parent.find(attrs={'class':re.compile("PrintHistRed")}, text=re.compile(r"\d\d/\d\d/\d\d\d\d")):
  date = nonres.parent.find('span', attrs={'class':re.compile("PrintHistRed")}, text=re.compile(r"\d\d/\d\d/\d\d\d\d"))
  outfile2.write("<tr><td>Form ADV Date:%s</td></tr>\n" % date.get_text(strip=True))
else:
  outfile2.write("<tr><td>Form ADV Date:%s</td></tr>\n" % "NA")
#outfile2.write("</table>\n")
class_array = []
def find_class(tag):  #This is to be used to help get regulatory AUM for the Manager
  p = tag.parent
  if p.has_key('class'):
    if p['class']==['flatBorderTable']:
      class_array.append(p)
      return
  find_class(p)

find_class(regassets)
a1 = class_array[0] 
reds = a1.find_all('span', attrs={'PrintHistRed'}) # The array's 0th element is discretionary AUM, the 4th element (zero-indexed) is total AUM.

outfile2.write("<tr><td>Manager Total Regulatory AUM: %s</td></tr>\n" % (reds[4].get_text(strip=True).encode('utf-8')))

outfile2.write("</table>\n")

def find_fund_table(tag):
  p = tag.parent
  if p.parent.has_key('class'):
    if p.parent['class']==['PaperFormTableData']:
      return p.parent
    #else:
    #  find_fund_table(p)
  find_fund_table(p)

fp=[]

for z in range(len(fundtd)):
  fp.append(find_fund_table(fundtd[z]))

for a in range(len(fp)):
  p1 = fp[a]
  fundname = p1.find('span',attrs={'class':'PrintHistRed'})
  pb = p1.find_all(text=re.compile("Name(.*)prime(\W+)broker"))
  aud = p1.find_all(text=re.compile("Name(.*)auditing(\W+)firm"))
  #cust = p1.find_all(text=re.compile("Legal(.*)name(\W+)custodian"))
  unqual = p1.find_all(text=re.compile("Does(.*)report(.*)auditing(.*)firm(.*)unqualified"))
  outfile2.write("<table>\n")
  outfile2.write("<tr><td colspan='2'>%s</td></tr>\n" % fundname.get_text(strip=True))
  outfile2.write("<br />\n")
  for i in range(len(pb)):
    #outfile2.write("<tr><td>%s</td></tr>\n" % pb[i].parent.get_text(strip=True))
    s = pb[i].parent.get_text(strip=True)
    outfile2.write("<tr><td>%s:</td><td>%s</td></tr>\n" % tuple(s.split(':')))
    outfile2.write("<br />\n")
  for i in range(len(aud)):
    sq = aud[i].parent.get_text(strip=True)
    sa1 = aud[i].parent.parent.parent.find('span',attrs={'class':'PrintHistRed'})
    sa2 = sa1.get_text(strip=True)
    outfile2.write("<tr><td>%s:</td><td>%s</td></tr>\n" % (sq,sa2)) #tuple(s.split(':')))
  for i in range(len(unqual)):
    item1 = unqual[i].parent.parent.next_sibling.next_sibling
    yes = item1.find('img', attrs={'alt':re.compile("(\W+)Radio(.*)selected")})
    outfile2.write("<tr><td>Unqualified Opinion:%s</td></tr>\n" % (yes.next_sibling.encode('utf-8')))
  outfile2.write("</table>\n")

outfile2.write("</body></html>\n")
outfile2.close()
print "Content-type: text/html\n\n";
outfile2 = open("/Library/WebServer/Documents/outfile.html","rb")
print outfile2.read();
outfile2.close()