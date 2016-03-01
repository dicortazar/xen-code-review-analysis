Data Analysis
=============

This directory contains two ipython notebooks used for data analysis and manipulation.


Understanding the data
======================

This section is related to the "Analysis-phase.ipynb" Ipython Notebook. This contains first steps on the analysis of the resultant database coming from the data-retrieval phase.
For this, the xen_patches.py command line tool was used to obtain a MySQL database with structured information about the code review process in Xen.

This notebook aims at providing a first approach to manage the new code review database. The usual code review process is done through the mailing lists. This approach migrates that code review into a database schema closer to how Gerrit or another review system works.

The list of metrics for this notebook are the following ones:

Activity General Overview
-------------------------
* Evolution of patch series (1 or more patches)
* Evolution of patch series submitters
* Evolution of comments
* Evolution of people commenting the patch series
* Evolution of people reviewing patches (using the flag reviewed by)

Time analysis
-------------

A patch can be divided into several steps:

1---------2----------3---------4--------5---------A--------C

And each version can be divided into several steps:

1----a)review------b)review------c)review-----------d)review--------------2----------------------------------------------3
    
        

Where 1, 2, 3, .., are the several iterations, A the point where all of the patches were 'Acked-by' and C the commit action into master.
And a, b, c, d comments and reviews.


* Time to merge: time between 1 and C
* Time to commit: time between A and C
* Time to re-work a patch: time between 1_d and the new iteration. Time between the last comment and a new patch.
* Cycle time: time between each pair of iterations: 1&2, 2&3, etc.
* Time to first review: time between 1, 2, 3, etc and its first review.

Backlog analysis
----------------

* Review (of series/patch) completed: all of the patch series merged
* Review (of series/patch) active: patches that were recently reviewed, we'll take the last 7 days as a potential timeframe.
* Review (of series/patch) stalled: patches older than 1 year
* Review (of series/patch) ongoing: patches younger than 1 year. This would include the active reviews.

Patch series complexity analysis
--------------------------------

* Number of versions per patch serie
* From patches merged: check number of 'touched' files plus added and removed lines
* Comments received per patch
* Number of patches per patch serie

Patch series community
----------------------

* Top people sending patches
* Top people reviewing patches
* For all of those, basic analysis with organization info based on email domain

Analysis
--------

This section splits previous information per patch serie into the populations of the several patches per patch serie and by semester.

Results show that at there was an increase in the time to merge, although this seems to be under control during 2015.



Massaging and pushing the data to ElasticSearch
===============================================

This Ipython notebook (ElasticSearch-data-push.ipynb) aims at focusing at the level of several use cases. This query the database, massage the data with Pandas and upload the result into an ElasticSearch instance.

The goal of this notebook is as follows:


This will provide an index full of information for each developer.

The goal is to have a full idea of how developers and organizations (per domain initially) deal with the concept of review, to award top ones if required, to avoid not that useful noise after an ack and to notice those more focused on reviewing activities or in development of new functionalities.

Each row is based on the following fields:
* PatchSerie id
* Patch id
* Comment id
* Subject of the email
* EmailType: 'patch serie', 'patch', 'review' or 'comment'
* Developer: email of the developer
* Domain: domain of the developer
* Time: time when the email was sent
* Balance: this contains a -1 if this is patch and a +1 if this is a review. Any other 'EmailTYpe' contains a 0
* Flag: for 'review' or 'comment' 'EmailType', this contains the specific flag used by the developer if so: eg-'Reviewed-by', etc.
* Merged: this contains a +1 if this was merged. 0 In any other case.
* PostAck: this contains a +1 if the 'EmailType' is 'comment' or 'review', that patch was merged and this comment or review was done after a previous review with the flag 'acked-by' 
* IsAcked: if a patch was acked at some point
           

Python Dependencies
===================

* Pandas
* Numpy
* MySQLdb
* Elasticsearch 
