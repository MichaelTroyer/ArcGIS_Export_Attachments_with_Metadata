# ArcGIS Export Attachments with Metadata

A Python toolbox that takes a feature class, an associated attachments table, and an output folder location and batch exports all the attachments while allowing you to select fields from the feature class, whose values will be used to name the output attachments:

i.e.  [SITE_ID], [FEA_ID], [DATE] would become:

- 5FN1234_Feature1_05102019_attachment1.jpg

- 5FN1234_Feature1_05102019_attachment2.jpg

- 5FN1234_Feature1_05102019_attachment3.jpg    etc..

The tool also provides fields to add optional photo metadata to all the outputs (jpegs only):

- Title
- Subject
- Author
- Keywords (tags)
- Comments

Multiple Authors and Keywords can be separated by a comma.


Note: requires piexif and pillow
