#!/usr/bin/python
from bs4 import BeautifulSoup
import re
import MySQLdb
import mechanize

#Set Variables:

br = mechanize.Browser()
ua = mechanize.UserAgentBase()
ua.addheaders = [("User-agent"),("Mac Safari")]
adviser = []

datab=MySQLdb.connect(user="[user]",passwd="[password]",db="iapd_db")
soup = BeautifulSoup(open("/Library/WebServer/Documents/iapdTemp.txt"))
c = datab.cursor()

for i in range(len(adviser)):
  response = br.open('http://www.adviserinfo.sec.gov/IAPD/crd_iapd_AdvVersionSelector.aspx?ORG_PK='+str(adviser[i])+'&RGLTR_PK=50000')
  content = response.read()
  soup2 = BeautifulSoup(content)
  form = soup2.find('form', attrs={'name':'aspnetForm'})
  action1 = form['action']
  action2 = re.sub('iapd_AdvIdentifyingInfoSection','Sections/iapd_AdvAllPages', action1)
  response2 = br.open('http://www.adviserinfo.sec.gov/iapd/content/viewform/adv/'+action2)
  outfile = open("/Library/WebServer/Documents/iapdTemp.txt", "w")
  outfile.write(response2.read())
  soup = BeautifulSoup(open("/Library/WebServer/Documents/iapdTemp.txt"))

  manName = soup.find('span', attrs={'id':re.compile("ADVHeader_lblPrimaryBusinessName")})
  manNumber = soup.find('span', attrs={'id':re.compile("ADVHeader_lblCrdNumber")})
  domsig = soup.find('tr', attrs={'id':re.compile("ctl00_ctl00_cphMainContent_cphAdvFormContent_ADVExecutionDomesticPHSection")})
  nonres= soup.find('tr', attrs={'id':'ctl00_ctl00_cphMainContent_cphAdvFormContent_ADVExecutionNonResidentPHSection_ctl00_trIAPDHeader'})
  regassets = soup.find('span', attrs={'id':re.compile("AdvFormContent_AssetsUnderMgnmt_ctl00_lbl")})
  owner_table = soup.find('table', attrs={'id':re.compile("ScheduleAPHSection_ctl00_ownersGrid")})
  th = owner_table.find_all('th') #you can print out headers by ' for i in range(len(th)):; print th[i].get_text(strip=True)'
  tr = owner_table.find_all('tr')

  indirect_owner_table = soup.find('table', attrs={'id':re.compile("ScheduleBPHSection_ctl00_ownersGrid")})
  if indirect_owner_table:
    th2 = indirect_owner_table.find_all('th')
    tr2 = indirect_owner_table.find_all('tr')

  c.executemany("""insert ignore into mgr_info (mgr_id, mgr_name) values (%s, %s)""",[(manNumber.get_text(strip=True),manName.get_text(strip=True))])
  datab.commit()
  datab.close

#Form ADV Date here:

  if domsig.parent.find('span', attrs={'class':re.compile("PrintHistRed")}, text=re.compile(r"\d\d/\d\d/\d\d\d\d")):
    date = domsig.parent.find('span', attrs={'class':re.compile("PrintHistRed")}, text=re.compile("\d\d/\d\d/\d\d\d\d"))
  elif nonres.parent.find(attrs={'class':re.compile("PrintHistRed")}, text=re.compile(r"\d\d/\d\d/\d\d\d\d")):
    date = nonres.parent.find('span', attrs={'class':re.compile("PrintHistRed")}, text=re.compile(r"\d\d/\d\d/\d\d\d\d"))
  else:
    date = "NA"


#Manager AUM here
  class_array = []
  def find_class(tag):  #This is to be used to help get regulatory AUM for the Manager
    p = tag.parent
    if p.has_key('class'):
      if p['class']==['flatBorderTable']:
        class_array.append(p)
        return
    find_class(p)

  if regassets:
    find_class(regassets)
    a1 = class_array[0] 
    reds = a1.find_all('span', attrs={'PrintHistRed'}) # The array's 0th element is discretionary AUM, the 4th element (zero-indexed) is total AUM.
  #outfile.write("<tr><td>Manager Total Regulatory AUM: %s</td></tr>\n" % (reds[4].get_text(strip=True).encode('utf-8')))
    rev_aum = re.sub(r"\D","",reds[4].get_text(strip=True).encode('utf-8'))
  else:
    #outfile.write("<tr><td>Manager Total Regulatory AUM: %s</td></tr>\n" % ("NA"))
    rev_aum = 0


# find_class(regassets)
# a1 = class_array[0] 
# reds = a1.find_all('span', attrs={'PrintHistRed'}) # the array's 0th element is discretionary AUM, the 4th element (zero-indexed) is total AUM

  rev_date = re.sub(r"(\d+)/(\d+)/(\d+)","\\3-\\1-\\2", date.get_text(strip=True))

#if regassets:
  #rev_aum = re.sub(r"\D","",reds[4].get_text(strip=True).encode('utf-8'))
#else:
  #rev_aum = "NA"

  c.executemany("""insert ignore into adv_info (mgr_id, mgr_name, adv_date, mgr_aum) values (%s, %s, %s, %s)""",[(manNumber.get_text(strip=True),manName.get_text(strip=True), rev_date, rev_aum)])
  datab.commit()
  datab.close

############################################################################################

  fundtd=soup.find_all('td',text=re.compile("PRIVATE FUND"))

  def find_fund_table(tag):
    p = tag.parent
    if p.parent.has_key('class'):
      if p.parent['class']==['PaperFormTableData']:
        return p.parent
      else:
        find_fund_table(p)
    find_fund_table(p)

  fp=[]

  for z in range(len(fundtd)):
    fp.append(find_fund_table(fundtd[z]))


  def find_it(var):
    global blank_array
    blank_array = []
    try:
      return blank_array.append(var[0].parent.parent.next_sibling.next_sibling)
    except IndexError:
      return 'None'
   
  def print_it():
    try:
      return blank_array[0].find('span', attrs={'class':re.compile("PrintHistRed")}).get_text(strip=True).encode('utf-8')
    except IndexError:
      return 'None'

   
  def print_button():
    print blank_array[0].find('img', attrs={'alt':re.compile("(\W+)Radio(.*)selected")}).next_sibling.encode('utf-8')

  for i in range(len(tr)):
    td = tr[i].find_all('td')
    array = []
    if i > 0:  #Need to skip tr[0] because those td's are just column headers - don't need those in the database
      t1 = re.sub(r"(\d+)/(\d+)","\\2-\\1-01", td[3].get_text(strip=True)) #this puts the date_status in proper MySQL DATE format
      t2 = re.sub(r"(\d+)/(\d+)/(\d+)","\\3-\\1-\\2", date.get_text(strip=True)) #this puts the date_status in proper MySQL DATE format
      c.executemany("""insert ignore into owner_relation (mgr_id, owner_name, DE_FE_I, entity_owned, status, date_status, ownership_code, control_person, PR, owner_id, adv_date) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",[(manNumber.get_text(strip=True),td[0].get_text(strip=True),td[1].get_text(strip=True),"NA",td[2].get_text(strip=True),t1,td[4].get_text(strip=True),td[5].get_text(strip=True),td[6].get_text(strip=True),td[7].get_text(strip=True),t2)]) #[(manNumber.get_text(strip=True),td[0].get_text(strip=True),td[1].get_text(strip=True),"NA",td[2].get_text(strip=True),t1,td[4].get_text(strip=True),td[5].get_text(strip=True),td[6].get_text(strip=True),td[7].get_text(strip=True),t2)])
      datab.commit()
      datab.close


#Printing table of Indirect Owners


  if indirect_owner_table:
    for i in range(len(tr2)):
      td = tr2[i].find_all('td')
      array = []
      for a in range(len(td)):
        array.append(td[a]) #array.append(td[a].get_text(strip=True))
      if i > 0:  #Need to skip tr[0] because those td's are just column headers - don't need those in the database
        t1 = re.sub(r"(\d+)/(\d+)","\\2-\\1-01", td[4].get_text(strip=True)) #this puts the date_status in proper MySQL DATE format
        t2 = re.sub(r"(\d+)/(\d+)/(\d+)","\\3-\\1-\\2", date.get_text(strip=True)) #this puts the date_status in proper MySQL DATE format
        c.executemany("""insert ignore into owner_relation (mgr_id, owner_name, DE_FE_I, entity_owned, status, date_status, ownership_code, control_person, PR, owner_id, adv_date) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",[(manNumber.get_text(strip=True),td[0].get_text(strip=True),td[1].get_text(strip=True),td[2].get_text(strip=True),td[3].get_text(strip=True),t1,td[5].get_text(strip=True),td[6].get_text(strip=True),td[7].get_text(strip=True),td[8].get_text(strip=True),t2)])
        datab.commit()
        datab.close



  for a in range(len(fp)):
    global db_array #() - indicates what I added to this block to implement the db seeding
    db_array = [manNumber.get_text(strip=True),date.get_text(strip=True)]
    global svc_pvdr_array
    svc_pvdr_array = []
    p1 = fp[a]
    fundname = p1.find('span',attrs={'class':'PrintHistRed'})
    fund_no = p1.find('span',attrs={'class':'PrintHistRed'}, text=re.compile(r'805-(\d*)'))
    pb = p1.find_all(text=re.compile("Name(.*)prime(\W+)broker"))
    aud = p1.find_all(text=re.compile("Name(.*)auditing(\W+)firm"))
    unqual = p1.find_all(text=re.compile("Does(.*)report(.*)auditing(.*)firm(.*)unqualified"))
    gross_asset_val = p1.find_all(text=re.compile("Current(.*)gross(.*)asset(.*)value(.*)of(.*)the"))
    administrator = p1.find_all(text=re.compile("Name(.*)administrator"))
    custodian = p1.find_all(text=re.compile("Legal(.*)name(.*)custodian"))
    if fund_no:
      db_array.append(fund_no.get_text(strip=True)) #() adds fund number as third element to db_array
    find_it(gross_asset_val)
    db_array.append(print_it()) #() adds fund AUM as fourth element in db_array
    for i in range(len(pb)):
      s = pb[i].parent.get_text(strip=True)
      ss = tuple(s.split(":"))
      c.executemany("""insert ignore into fund_svc_provider (fund_id, adv_date, svc_provider_name, svc_provider_type) values (%s, %s, %s, %s)""",[(fund_no.get_text(strip=True),rev_date,ss[1],"Prime Broker")])
      datab.commit()
    for i in range(len(aud)):
      sq = aud[i].parent.get_text(strip=True)
      sa1 = aud[i].parent.parent.parent.find('span',attrs={'class':'PrintHistRed'})
      sa2 = sa1.get_text(strip=True)
      c.executemany("""insert ignore into fund_svc_provider (fund_id, adv_date, svc_provider_name, svc_provider_type) values (%s, %s, %s, %s)""",[(fund_no.get_text(strip=True),rev_date,sa2,"Auditor")])
      datab.commit()
    for i in range(len(unqual)):
      item1 = unqual[i].parent.parent.next_sibling.next_sibling
      yes = item1.find('img', attrs={'alt':re.compile("(\W+)Radio(.*)selected")})
      db_array.append(yes.next_sibling.encode('utf-8'))
    find_it(administrator)
    c.executemany("""insert ignore into fund_svc_provider (fund_id, adv_date, svc_provider_name, svc_provider_type) values (%s, %s, %s, %s)""",[(fund_no.get_text(strip=True),rev_date,print_it(),"Administrator")])
    datab.commit()
    for i in range(len(custodian)):
      cus = custodian[i].parent.get_text(strip=True)
      cuss = tuple(cus.split(":"))
      c.executemany("""insert ignore into fund_svc_provider (fund_id, adv_date, svc_provider_name, svc_provider_type) values (%s, %s, %s, %s)""",[(fund_no.get_text(strip=True),rev_date,cuss[1],"Custiodian")])
      datab.commit()
    db_array[1] = re.sub(r"(\d+)/(\d+)/(\d+)","\\3-\\1-\\2", db_array[1])
    db_array[3] = re.sub(r"\D","",db_array[3])
    p = re.compile(r"(.*)(yes|no)(.*)", re.I)
    db_array[4] = p.match(db_array[4]).group(2)
  #print db_array
    c.executemany("""insert ignore into mgr_fund_bal (mgr_id, adv_date, fund_id, fund_aum, unqual_opinion) values (%s, %s, %s, %s, %s)""",[(db_array[0],db_array[1],db_array[2],db_array[3],db_array[4])])
    c.executemany("""insert ignore into fund_info (fund_id, fund_name, mgr_id) values (%s, %s, %s)""",[(db_array[2],fundname.get_text(strip=True),db_array[0])])
    datab.commit()
    datab.close



# Notes:
# This program (these programs) will result in a single web site providing information
# on managers and funds, detailing amounts and information reported in SEC FORM ADV.
# Structure:
# ADV_Object = attributes: Manager Number, Date; methods = ?
# Manager_Object = attributes: Number, Name, Principal Address, website address, Regulatory AUM, Ttl_No Accts, Private Funds Managed; methods = ?
# Private Funds = Number, Name, Feeders, AUM, Number of beneficial owners, pct-owned related, pct-owned FOF, pct-owned Ex-US, Service Providers
# Service Providers = Type (auditor, prime broker, custodian, administrator, marketer), Location (City, Country)

blank_array = []

# def find_it(var):
#   global blank_array
#   blank_array = []
#   return blank_array.append(var[0].parent.parent.next_sibling.next_sibling)
#    
# def print_it():
#   print blank_array[0].find('span', attrs={'class':re.compile("PrintHistRed")}).get_text(strip=True).encode('utf-8')
#    
# def print_button():
#   print blank_array[0].find('img', attrs={'alt':re.compile("(\W+)Radio(.*)selected")}).next_sibling.encode('utf-8')
#    

