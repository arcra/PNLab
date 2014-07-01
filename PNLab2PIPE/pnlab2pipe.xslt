<xsl:transform version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="yes"/>

    <xsl:template match="@*|node()" name="identity" >
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
        </xsl:copy>
    </xsl:template>
    
    <xsl:template match="toolspecific[@tool='PIPE']" />
    
    <xsl:template match="text">
        <value>
            <xsl:value-of select="text()" />
        </value>
    </xsl:template>
    
    <!-- FIX NET TYPE 
    <xsl:template match="net/@type[current() != 'http://www.pnml.org/version-2009/grammar/ptnet']">
    	<xsl:attribute name="type">http://www.pnml.org/version-2009/grammar/ptnet</xsl:attribute>
    </xsl:template>
    -->
    
    <!-- PROCESS NET ELEMENT -->
    <xsl:template match="net[toolspecific/@tool='PIPE']" >
    	<xsl:copy>
    		<xsl:apply-templates select="@*|node()" />
    		<xsl:copy-of select="toolspecific[@tool='PIPE']/node()" />
    	</xsl:copy>
    </xsl:template>

    <!-- PROCESS PAGE ELEMENT -->
    <xsl:template match="page">
    	<xsl:apply-templates select="node()" />
    </xsl:template>

    <!-- PROCESS PLACE ELMENT -->
    <xsl:template match="place[toolspecific/@tool='PNLab']">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
            <xsl:call-template name="line_break" />
            <xsl:if test="toolspecific[@tool='PNLab']/capacity">
            	<capacity><xsl:call-template name="line_break" />
	           		<value>
	           			<xsl:value-of select="toolspecific[@tool='PNLab']/capacity/text/text()" />
	           		</value><xsl:call-template name="line_break" />
           		</capacity><xsl:call-template name="line_break" />
            </xsl:if>
        </xsl:copy>
    </xsl:template>
    
    <!-- PROCESS TRANSITION ELMENT -->
    <xsl:template match="transition[toolspecific/@tool='PNLab']">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
            <xsl:call-template name="line_break" />
            <xsl:if test="toolspecific[@tool='PIPE']">
            	<xsl:copy-of select="toolspecific[@tool='PIPE']/node()" />
            </xsl:if>
            <xsl:if test="toolspecific[@tool='PNLab']/isHorizontal">
            	<orientation><xsl:call-template name="line_break" />
	           		<value>
	           			<xsl:value-of select="toolspecific[@tool='PNLab']/isHorizontal/text/text()" />
	           		</value><xsl:call-template name="line_break" />
           		</orientation><xsl:call-template name="line_break" />
            </xsl:if>
            <xsl:if test="toolspecific[@tool='PNLab']/rate">
            	<rate><xsl:call-template name="line_break" />
	           		<value>
	           			<xsl:value-of select="toolspecific[@tool='PNLab']/rate/text/text()" />
	           		</value><xsl:call-template name="line_break" />
           		</rate><xsl:call-template name="line_break" />
            </xsl:if>
            <xsl:if test="toolspecific[@tool='PNLab']/type">
            	<timed><xsl:call-template name="line_break" />
	           		<value>
	           			<xsl:choose>
	           				<xsl:when test="toolspecific[@tool='PNLab']/type/text/text() = 'immediate'">
	           					0
	           				</xsl:when>
	           				<xsl:otherwise>
	           					1
	           				</xsl:otherwise>
	           			</xsl:choose>
	           		</value><xsl:call-template name="line_break" />
           		</timed><xsl:call-template name="line_break" />
            </xsl:if>
            <xsl:if test="toolspecific[@tool='PNLab']/priority">
            	<priority><xsl:call-template name="line_break" />
	           		<value>
	           			<xsl:value-of select="toolspecific[@tool='PNLab']/priority/text/text()" />
	           		</value><xsl:call-template name="line_break" />
           		</priority><xsl:call-template name="line_break" />
            </xsl:if>
        </xsl:copy>
    </xsl:template>
    
    <!-- PROCESS ARC ELMENT -->
    <xsl:template match="arc[toolspecific/@tool='PIPE']">
    	<xsl:copy>
    		<xsl:apply-templates select="@*|node()" />
    		<xsl:copy-of select="toolspecific[@tool='PIPE']/node()" />
    	</xsl:copy>
    </xsl:template>
    
    <!-- "FUNCTION" for writing a line break -->
	<xsl:template mode="function_only" name="line_break">
		<xsl:text>
		</xsl:text>
		<!-- <xsl:text>\n</xsl:text> -->
	</xsl:template>

</xsl:transform>
