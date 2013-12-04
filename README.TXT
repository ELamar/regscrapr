This project creates an interactive website that will scrape applicable regulatory web pages to return information about related parties to the regulated entity.
In some cases, it produces a network visualization of nodes and relationships.  In other cases, different visualizations are presented.  

The webpage relating to the entity identified by the user is downloaded into a temp file on the server and is then parsed to retrieve a number of key facts relating to the entity.  

This program scrapes the SEC's Investor Adviser's central webpage at www.adviserinfo.sec/IAPD.

After the key facts have been scraped from the parsed webpage, those items are inserted into a MySQL database to be queried in the future.

Tables for the MySQL Database are structured as follows:

There is a Manager Table, A Fund Table, A Service Provider Table and a Transaction Table.
The Transaction Table describes a set of facts and relationships pulled from a particular form ADV at a particular date.
The primary key for the transaction table with be a concatenation of the Manager ID and ADV Date.

The Manager Table:
  |Manager ID (SEC CRD or IAPD Number)|Manager Name|
   VARCHAR(15) - Primary|VARCHAR(75)

Fund Table:
  |Fund ID (SEC Private Fund Identification Number)|Fund Name|Manager Number|
   VARCHAR(20) - Primary|VARCHARD(75)|VARCHAR(75) - Foreign

Service Provider Table:
  |Service Provider ID (SEC CRD or IAPD Number or Generated Number if none)|Service Provide Name|Service Provider Type (Auditor, Prime Broker, Custodian, Administrator, Other)|
  VARCHAR(6) - Primary(Auto Generated--Python Code must cross-check name to prevent duplicates)|VARCHAR(75)|VARCHAR(75)

Service Provider Transaction Table
  |Key - Combination Fund No., Service Provider No.  and Form ADV Date|
  |VARCHAR(20)|VARCHAR(6)|Date(YYYY-MM-DD)

Manager Fund Bal and Audit Transaction Table:
  |Key - Combination Manager No, Fund No.  and ADV Date|Manager Total AUM|Fund No.|Fund AUM|Unqualified Opinion|
  |VARCHAR(15)|VARCHAR(20)|Date(YYYY-MM-DD [First 3 fields are concatenated Primary Key|FLOAT(15,2)|VARCHAR(20)|FLOAT(15,2)|VARCHAR(5)

Owner Table - lists direct and indirect ownership
|Manager Number|Legal Name|DE_FE_I (Domestic Entity, Foreign Entity, Individual)|Status (Founding Partner, CEO, COO, etc.)|Date Status Acquired (Date formatting may be difficult here, SEC presents as M/YYYY, not YYYY-MM-DD MySQL format)|Ownership Code| Control Person|PR|CRD, EIN, SSN, Other ID|
|VARCHAR(15)|VARCHAR(75)|VARCHAR(3)|VARCHAR(75)|DATE|VARCHAR(2)|VARCHAR(3)|VARCHAR(3)|VARCHAR(20)
