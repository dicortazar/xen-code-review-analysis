Data retrieval process
======================

The xen_patches.py script needs as input a [CVSANalY] and a [MLStats] database.

CVSANalY database
-----------------

Install CVSAnalY as detailed in the [Installation sectoin](https://github.com/MetricsGrimoire/CVSAnalY#installation).


Clone the repositories used in this analysis. So far there are four of them:

    ~/$ git clone git://xenbits.xenproject.org/xen.git
    ~/$ git clone git://xenbits.xen.org/mini-os.git
    ~/$ git clone git://xenbits.xen.org/people/sstabellini/raisin.git
    ~/$ git clone git://xenbits.xen.org/osstest.git

Then, for each of them, a CVSanaly instance is run. Under each directory, cvsanaly is run and this will retrieve and store in a MySQL database the output. The four repositories are stored in the same database.

    ~/xen/$ cvsanaly2 --db-user="user" --db-password="password" --db-database="xen_cvsanaly" --extensions=CommitsLOC,FileTypes
    ~/mini-os/$ cvsanaly2 --db-user="user" --db-password="password" --db-database="xen_cvsanaly" --extensions=CommitsLOC,FileTypes
    ~/raisin/$ cvsanaly2 --db-user="user" --db-password="password" --db-database="xen_cvsanaly" --extensions=CommitsLOC,FileTypes
    ~/osstest/$ cvsanaly2 --db-user="user" --db-password="password" --db-database="xen_cvsanaly" --extensions=CommitsLOC,FileTypes


MLStats database
----------------

Install Mailing List Stats as detailed in the [Installation section](https://github.com/MetricsGrimoire/MailingListStats#installation).

Launch mlstats command line as follows:

    ~$ mlstats --db-user="user" --db-password="password" --db-database="database" --db-admin-user="admin-user" --db-admin-password="admin-password" "mbox-path"


Other dependencies
------------------

Mailing List Stats and CVSAnalY have their own dependencies. Please, be aware of them in the specific sections.


Running the xen_patches.py analyzer
-----------------------------------

This script uses the CVSAnalY and MLStats databases to build a new database with structured information about each of the code review processes that took place in the xen-devel mailing list.

    ~$ python xen_patches.py -u="user" -p="password" -d="output_database" mlstats_database cvsanaly_database
