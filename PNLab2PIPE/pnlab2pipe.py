# -*- coding: utf-8 -*-
"""
@author: Adrián Revuelta Cuauhtli
"""
import os
import io
import lxml.etree as ET

xslt_file = os.path.join(os.path.dirname(__file__), 'pnlab2pipe.xslt')

def convert(et):
    global xslt_file
    
    et = remove_namespace(et)
    xslt_doc=ET.parse(xslt_file)
    transform=ET.XSLT(xslt_doc)
    return transform(et)

def remove_namespace(et):
    # http://wiki.tei-c.org/index.php/Remove-Namespaces.xsl
    xslt='''<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="no"/>
    
    <xsl:template match="/|comment()|processing-instruction()">
        <xsl:copy>
          <xsl:apply-templates/>
        </xsl:copy>
    </xsl:template>
    
    <xsl:template match="*">
        <xsl:element name="{local-name()}">
          <xsl:apply-templates select="@*|node()"/>
        </xsl:element>
    </xsl:template>
    
    <xsl:template match="@*">
        <xsl:attribute name="{local-name()}">
          <xsl:value-of select="."/>
        </xsl:attribute>
    </xsl:template>
    
    <xsl:template match="@xmlns" />
    
    </xsl:stylesheet>
    '''
    xslt_doc=ET.parse(io.BytesIO(xslt))
    transform=ET.XSLT(xslt_doc)
    return transform(et)