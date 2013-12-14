#!/usr/bin/python

#This program retrieves the SEC IAPD Search page for a given Investment Adviser number.
#It then retrieves Schedule D for that Adviser

############################################################################################
#Import Statements:

import re
import mechanize
from bs4 import BeautifulSoup
import cgi, cgitb
from django.conf import settings
from django.template import Context, Template
#import MySQLdb

#settings.configure = (DEBUG=True, TEMPLATE_DEBUG=True) #to configure the settings for Django
#you have to configure the settings if you are using only a portion of Django

############################################################################################

#Set Variables:

br = mechanize.Browser()
ua = mechanize.UserAgentBase()
ua.addheaders = [("User-agent"),("Mac Safari")]
formtext = cgi.FieldStorage()

############################################################################################

#Retrieve IAPD number from webform, using 148823 as default if no number is input

if formtext.getvalue('mgrnumber'):
  adviser = formtext.getvalue('mgrnumber')
else:
  adviser = 148823

############################################################################################

#The next set of lines is a 2-step mechanize process of navigating to a page, then submitting
#a form request to get to the 'view all' page of the IAPD search.  The resulting page is
#then downloaded into a 'iapdTemp.txt' file for further processing herein.

response = br.open('http://www.adviserinfo.sec.gov/IAPD/crd_iapd_AdvVersionSelector.aspx?ORG_PK='+str(adviser)+'&RGLTR_PK=50000')
content = response.read()
soup = BeautifulSoup(content)
form = soup.find('form', attrs={'name':'aspnetForm'})
action1 = form['action']
action2 = re.sub('iapd_AdvIdentifyingInfoSection','Sections/iapd_AdvAllPages', action1)
response2 = br.open('http://www.adviserinfo.sec.gov/iapd/content/viewform/adv/'+action2)
outfile = open("/Library/WebServer/Documents/iapdTemp.txt", "w")
outfile.write(response2.read())
soup2 = BeautifulSoup(open("/Library/WebServer/Documents/iapdTemp.txt"))


#Open file for output and write html & body tag

outfile2 = open("/Library/WebServer/Documents/outfile.html","w")
outfile2.write("<html><body>\n")

############################################################################################

# First, find and print Manager name, number, Form ADV Date, and 
#regulatory assets under management (AUM) at top of page.
#This segment will also find the Manager's Owners and Executive Officers

manName = soup2.find('span', attrs={'id':re.compile("ADVHeader_lblPrimaryBusinessName")})
manNumber = soup2.find('span', attrs={'id':re.compile("ADVHeader_lblCrdNumber")})
domsig = soup2.find('tr', attrs={'id':re.compile("ctl00_ctl00_cphMainContent_cphAdvFormContent_ADVExecutionDomesticPHSection")})
nonres= soup2.find('tr', attrs={'id':'ctl00_ctl00_cphMainContent_cphAdvFormContent_ADVExecutionNonResidentPHSection_ctl00_trIAPDHeader'})
regassets = soup2.find('span', attrs={'id':re.compile("AdvFormContent_AssetsUnderMgnmt_ctl00_lbl")})
owner_table = soup2.find('table', attrs={'id':re.compile("ScheduleAPHSection_ctl00_ownersGrid")})
th = owner_table.find_all('th') #you can print out headers by ' for i in range(len(th)):; print th[i].get_text(strip=True)'
tr = owner_table.find_all('tr')
indirect_owner_table = soup2.find('table', attrs={'id':re.compile("ScheduleBPHSection_ctl00_ownersGrid")})
if indirect_owner_table:
  th2 = indirect_owner_table.find_all('th')
  tr2 = indirect_owner_table.find_all('tr')
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

############################################################################################
#Next, find each of the private funds the manager manages and report AUM and Service Provider Information

fundtd=soup2.find_all('td',text=re.compile("PRIVATE FUND")) #Loads all PRIVATE FUND sections into the fundtd array
def find_fund_table(tag):
  p = tag.parent
  if p.parent.has_key('class'):
    if p.parent['class']==['PaperFormTableData']:
      return p.parent
    #else:
    #  find_fund_table(p)
  find_fund_table(p)

fp=[]

#Uses find_fund_table function to create another array [fp] to house the complete PRIVATE FUND tables 
for z in range(len(fundtd)):
  fp.append(find_fund_table(fundtd[z]))

###########################################################################################
#The find_it, print_it and print_button functions are miscellaneous helper functions I will use later
def find_it(var):
  global blank_array
  blank_array = []
  try:
    return blank_array.append(var[0].parent.parent.next_sibling.next_sibling)
  except IndexError:
    return 'None'
   
def print_it():
  #print blank_array[0].find('span', attrs={'class':re.compile("PrintHistRed")}).get_text(strip=True).encode('utf-8')
  #outfile.write(blank_array[0].find('span', attrs={'class':re.compile("PrintHistRed")}).get_text(strip=True).encode('utf-8'))
  try:
    return blank_array[0].find('span', attrs={'class':re.compile("PrintHistRed")}).get_text(strip=True).encode('utf-8')
  except IndexError:
    return 'None'
   
def print_button():
  print blank_array[0].find('img', attrs={'alt':re.compile("(\W+)Radio(.*)selected")}).next_sibling.encode('utf-8')
###########################################################################################   

#Printing the table of Direct Owners and Executive Officers
outfile2.write("<p>\n")
outfile2.write("<h3>Direct Owners and Executive Officer Table</h3>\n")
outfile2.write("<table border='1'>\n")
outfile2.write(''.join(map(str,th)))
for i in range(len(tr)):
  td = tr[i].find_all('td')
  array = []
  outfile2.write("<tr>")
  for a in range(len(td)):
    #array.append(td[a]) #array.append(td[a].get_text(strip=True))
    outfile2.write("%s" % td[a])
  outfile2.write("</tr>")
outfile2.write("</table>\n")
outfile2.write("</p>\n")

#Printing table of Indirect Owners

if indirect_owner_table:
  outfile2.write("<p>\n")
  outfile2.write("<h3>Indirect Owner Table</h3>\n")
  outfile2.write("<table border='1'>\n")
  outfile2.write(''.join(map(str,th2)))
  for i in range(len(tr2)):
    td = tr2[i].find_all('td')
    array = []
    outfile2.write("<tr>")
    for a in range(len(td)):
    #array.append(td[a]) #array.append(td[a].get_text(strip=True))
      outfile2.write("%s" % td[a])
    outfile2.write("</tr>")
  outfile2.write("</table>\n")
  outfile2.write("</p>\n")


blank_array = []

for a in range(len(fp)):
  global blank_array
  blank_array = []
  p1 = fp[a]
  fundname = p1.find('span',attrs={'class':'PrintHistRed'})
  fund_no = p1.find('span',attrs={'class':'PrintHistRed'}, text=re.compile(r'805-(\d*)'))
  pb = p1.find_all(text=re.compile("Name(.*)prime(\W+)broker"))
  aud = p1.find_all(text=re.compile("Name(.*)auditing(\W+)firm"))
  #cust = p1.find_all(text=re.compile("Legal(.*)name(\W+)custodian"))
  unqual = p1.find_all(text=re.compile("Does(.*)report(.*)auditing(.*)firm(.*)unqualified"))
  gross_asset_val = p1.find_all(text=re.compile("Current(.*)gross(.*)asset(.*)value(.*)of(.*)the"))
  administrator = p1.find_all(text=re.compile("Name(.*)administrator"))
  custodian = p1.find_all(text=re.compile("Legal(.*)name(.*)custodian"))
  outfile2.write("<table>\n")
  outfile2.write("<tr><td colspan='2'>%s</td></tr>\n" % fundname.get_text(strip=True).encode('utf-8'))
  outfile2.write("<br />\n")
  if fund_no:
    outfile2.write("<tr><td>Fund Number: </td><td>%s</td></tr>\n" % fund_no.get_text(strip=True))
  outfile2.write("<br />\n")
  find_it(gross_asset_val)
  outfile2.write("<tr><td colspan='2'>Fund Current Gross Asset Value:%s</td></tr>\n" % (print_it()))
  for i in range(len(pb)):
    #outfile2.write("<tr><td>%s</td></tr>\n" % pb[i].parent.get_text(strip=True))
    s = pb[i].parent.get_text(strip=True)
    outfile2.write("<tr><td>%s:</td><td>%s</td></tr>\n" % tuple(s.split(':')))
    outfile2.write("<br />\n")
  for i in range(len(aud)):
    sq = aud[i].parent.get_text(strip=True)
    sa1 = aud[i].parent.parent.parent.find('span',attrs={'class':'PrintHistRed'})
    sa2 = sa1.get_text(strip=True)
    outfile2.write("<tr><td>%s</td><td>%s</td></tr>\n" % (sq,sa2)) #tuple(s.split(':')))
  for i in range(len(unqual)):
    item1 = unqual[i].parent.parent.next_sibling.next_sibling
    yes = item1.find('img', attrs={'alt':re.compile("(\W+)Radio(.*)selected")})
    outfile2.write("<tr><td>Unqualified Opinion:%s</td></tr>\n" % (yes.next_sibling.encode('utf-8')))
  find_it(administrator)
  outfile2.write("<tr><td colspan='2'>Fund Administrator: %s</td></tr>\n" % (print_it()))
  for i in range(len(custodian)):
    c = custodian[i].parent.get_text(strip=True)
    outfile2.write("<tr><td>%s:</td><td>%s</td></tr>\n" % tuple(c.split(':'))) #prints the list of custodians for the fund
  outfile2.write("</table>\n")

outfile2.write("</body></html>\n")
outfile2.close()
print "Content-type: text/html\n\n";
outfile2 = open("/Library/WebServer/Documents/outfile.html","rb")
print outfile2.read();
outfile2.close()