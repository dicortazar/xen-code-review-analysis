# What is this?

This project aims at providing a dashboard (ElasticSearch-Kibana-based) that allow developers and managers to understand
how the code review process takes place. This will specifically help to improve the code review process thanks to the
capabilities of Kibana, that allows to drill down till the specific Patch Series or Patches of interest.

Having a better way to identify bottlenecks in the community is expected to help the rest of the overall process.

In addition to this, this dashboard also provides information about developers and organizations involved in the development
of Xen. This helps to understand the general structure and its main actors involved in the project.


# How can you help to improve?

This project is a shared effort between the Xen community and Bitergia. If you have any questions, please look for us at:
* Mailing Lists: [xen-devel mailing list](http://lists.xenproject.org/cgi-bin/mailman/listinfo/xen-devel) or [metrics-grimoire mailing list](https://lists.libresoft.es/listinfo/metrics-grimoire)
* IRC channels: [Xen](irc://irc.freenode.net/xendevel) or [Metrics Grimoire](irc://irc.freenode.net/metrics-grimoire) both in Freenode


# Further steps
* Improve the matching between commits and patches.
 * This is based on the comparison between the commit message and the Patch subject.
* Improve the thread detection.
 * This is heavily based on regular expressions. As this code review process is not that formal if Patchbomb extension is not used, corner cases may appear.


# Other communities of interest
* The Linux kernel uses a similar approach.


# Similar projects
* [Patchwork](https://github.com/stephenfin/patchwork) is a project with a different goal, but uses the same data sources such as the mailing lists as its primary one.
* [Patchbomb](http://wiki.xenproject.org/wiki/Submitting_Xen_Patches_-_mercurial) is a tool used for sending patches to the mailing list for the  Xen community.

# Other links of interest
* [OSCON 2016 talk about this project](http://conferences.oreilly.com/oscon/open-source-us/public/schedule/detail/49031)
