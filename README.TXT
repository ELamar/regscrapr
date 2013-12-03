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

Fund Table:
  |Fund ID (SEC CRD or IAPD Number)|Fund Name|Manager Number|

Service Provider Table:
  |Service Provider ID (SEC CRD or IAPD Number or Generated Number if none)|Service Provide Name|Service Provider Type (Auditor, Prime Broker, Custodian, Administrator, Other)|

Service Provider Transaction Table
  |Key - Combination Fund No., Service Provider No.  and Form ADV Date|

Manager Fund Bal and Audit Transaction Table:
  |Key - Combination Manager No, Fund No.  and ADV Date|Manager Total AUM|Fund No.|Fund AUM|Unqualified Opinion|
