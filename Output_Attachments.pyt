import os
import re
import traceback

import PIL.Image
import arcpy
import piexif


"""
Michael Troyer 20190508
"""

def text_to_unicode_points(text):
    """
    Convert text to unicode code points.
    exif dict expects a sequence of code points seperated by nulls (0)
    and ending with two nulls'
    """
    unicode_points = []
    for c in text:
        # add character and a null (0)
        unicode_points.extend([ord(c), 0])
    # Two nulls ends the string
    unicode_points += [0,0]   
    return unicode_points


def update_exif_data(image_path, title=None, subject=None, author=None, keywords=None, comments=None):
    """
    Update photo exif data with title, subject, author, keywords, and comments.
    Keywords and author can accept a string with individual entries seperated by a comma.
    Will leave existing metadata intact. Will overwrite any existing values for provided metadata parameters.
    """
    img = PIL.Image.open(image_path)
    exif_dict = piexif.load(img.info['exif'])

    # All the relevant stuff is in the '0th' exif dict
    zeroth_ifd = {
        piexif.ImageIFD.XPKeywords: keywords,
        piexif.ImageIFD.XPAuthor: author,
        piexif.ImageIFD.XPTitle: title,
        piexif.ImageIFD.XPSubject: subject,
        piexif.ImageIFD.XPComment: comments,
        }

    for k, v in zeroth_ifd.items():
        if v:
            exif_dict['0th'][k] = text_to_unicode_points(v)

    exif_bytes = piexif.dump(exif_dict)
    img.save(image_path, exif=exif_bytes)
    img.close()

class Toolbox(object):
    def __init__(self):
        self.label = "Output_Attachments"
        self.alias = "OutputAttachments"
        self.tools = [OutputAttachments]


class OutputAttachments(object):
    def __init__(self):
        self.label = "Output_Attachments"
        self.description = "Output fGDB feature class attachments and update metadata"
        # THIS HAS TO RUN IN THE FOREGROUND
        # Import PIL will crash the background processor!
        # I don't know why. Stop asking. 
        self.canRunInBackground = False

    def getParameterInfo(self):
                
        inFeas=arcpy.Parameter(
            displayName="Input Feature Class",
            name="InFeas",
            datatype="DETable",
            parameterType="Required",
            direction="Input",
            )
        inRows=arcpy.Parameter(
            displayName="Input Attachments Table",
            name="InRows",
            datatype="DETable",
            parameterType="Required",
            direction="Input",
            )
        idFlds=arcpy.Parameter(
            displayName="Feature Class Attachment ID Fields",
            name="idFlds",
            datatype="String",
            parameterType="Required",
            direction="Input",
            multiValue=True,
            )
        outDir=arcpy.Parameter(
            displayName="Output Workspace",
            name="OutDir",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
            )
        metaTitle=arcpy.Parameter(
            displayName="Metadata Title",
            name="metaTitle",
            datatype="String",
            parameterType="Optional",
            direction="Input",
            category='Update Photo Metadata',
            )
        metaSubject=arcpy.Parameter(
            displayName="Metadata Subject",
            name="metaSubject",
            datatype="String",
            parameterType="Optional",
            direction="Input",
            category='Update Photo Metadata',
            )
        metaAuthor=arcpy.Parameter(
            displayName="Metadata Author (separate multiple authors with a comma)",
            name="metaAuthor",
            datatype="String",
            parameterType="Optional",
            direction="Input",
            category='Update Photo Metadata',
            )
        metaKeywords=arcpy.Parameter(
            displayName="Metadata Keywords (separate multiple keywords with a comma)",
            name="metaKeywords",
            datatype="String",
            parameterType="Optional",
            direction="Input",
            category='Update Photo Metadata',
            )
        metaComments=arcpy.Parameter(
            displayName="Metadata Comments",
            name="metaComments",
            datatype="String",
            parameterType="Optional",
            direction="Input",
            category='Update Photo Metadata',
            )

        return [
            inFeas, inRows, idFlds, outDir,
            metaTitle, metaSubject, metaAuthor, metaKeywords, metaComments
            ]

    def isLicensed(self):
        return True

    def updateParameters(self, params):
        inFC, inTbl, inFields, outDir = params[:4]
        if inFC.value:
            # Get the list of fields to use to name output attachments
            fields = [f.name for f in arcpy.Describe(inFC).fields]
            inFields.filter.type = "ValueList"
            inFields.filter.list = fields
            if not inTbl.value:
                # Default attachment table name
                inTbl.value = inFC.valueAsText + '__ATTACH'
            if not outDir.value:
                # Default output location is enclosing dir of fGDB
                outDir.value = os.path.dirname(os.path.dirname(inFC.valueAsText))
        return

    def updateMessages(self, params):
        return

    def execute(self, params, messages):
        inFC, inTbl, idFlds, outDir, metaTitle, metaSubject, metaAuthor, metaKeywords, metaComments = params

        metaTitle = metaTitle.valueAsText
        metaSubject = metaSubject.valueAsText
        metaAuthor = metaAuthor.valueAsText
        metaKeywords = metaKeywords.valueAsText
        metaComments = metaComments.valueAsText

        # If any metadata updates
        if any([metaTitle, metaSubject, metaAuthor, metaKeywords, metaComments]):
            update_metadata = True
        else:
            update_metadata = False

        # Make feature layer or table view
        if hasattr(arcpy.Describe(inFC.value), 'shapeType'):  # is a feature class
            arcpy.MakeFeatureLayer_management(inFC.value, 'in_memory\\lyr')
        else:
            arcpy.MakeTableView_management(inFC.value, 'in_memory\\lyr')

        fcName = os.path.basename(inFC.valueAsText)
        tblName = os.path.basename(inTbl.valueAsText)
        
        dtFlds = ['ATT_NAME', 'DATA']

        idFlds = ['{}.{}'.format(fcName, fld) for fld in idFlds.values]
        dtFlds = ['{}.{}'.format(tblName, fld) for fld in dtFlds]

        # Assuming relation based on global ID! FK == "REL_GLOBALID"
        arcpy.AddJoin_management('in_memory\\lyr', "GlobalID", inTbl.value, "REL_GLOBALID")

        output_attachments = []

        with arcpy.da.SearchCursor('in_memory\\lyr', idFlds + dtFlds) as cur:
            for row in cur:
                # Strip any non-alphanumeric + _ and . to prevent naming issues
                name = '_'.join([re.sub('[^0-9a-zA-Z-_.]+', '', str(r)) for r in row[:-1]])
                attachment_path = os.path.join(outDir.valueAsText, name)
                data = row[-1]
                if data:
                    try:
                        with open(attachment_path, 'wb') as f:
                            f.write(data)
                            output_attachments.append(attachment_path)
                    except Exception as e:
                        arcpy.AddMessage('[-] Error writing: {}\n{}'.format(attachment_path, e))
        if update_metadata:
            # if a jpg
            for attachment in (att for att in output_attachments if att.endswith('.jpg')):
                try:
                    update_exif_data(
                        attachment,
                        title=metaTitle,
                        subject=metaSubject,
                        author=metaAuthor,
                        keywords=metaKeywords,
                        comments=metaComments,
                        )
                except Exception as e:
                    arcpy.AddMessage(
                        '[-] Error updating metadata: {}\n{}'.format(attachment, traceback.format_exc())
                        )
        return