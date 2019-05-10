# ArcGIS_GDB_Attachment_Tools
ArcGIS File Geodatabase Attachment Tools

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Output_Attachments.pyt:

Takes a feature class, an associated attachments table, and an output folder location and batch exports all the attachments while allowing you to select fields from the feature class, whose values will be used to name the output attachments:

i.e.  [SITE_ID], [FEA_ID], [DATE] would become:

5FN1234_Feature1_05102019_attachment1.jpg

5FN1234_Feature1_05102019_attachment2.jpg

5FN1234_Feature1_05102019_attachment3.jpg    etc..

It also provides fields to add optional metadata to all the output photos:

Title, Subject, Author, Keywords (tags), and Comments

Multiple Authors and Keywords can be separated by a comma.



++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Pics_to_Feature_Class.pyt

Takes geotagged photographs and creates a database and point feature class and adds the photos as attachments.
ESRI also implmented this, which I didn't realize when I wrote this one.. Ah nuts..
