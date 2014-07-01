<xsl:transform version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:output method="xml" indent="yes"/>

    <xsl:template match="@*|node()" name="identity" >
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
        </xsl:copy>
    </xsl:template>
    
    <!-- ********************************************************
                  START QUICK IGNORE/RENAME THESE ELEMENTS
         ******************************************************** -->
    <xsl:template match="net/place|net/transition|net/arc|net/token"/>
    <xsl:template match="place/capacity"/>
    <xsl:template match="transition/orientation|transition/rate|transition/timed|transition/infiniteServer|transition/priority"/>
    <xsl:template match="arc/tagged|arc/arcpath|arc/type"/>
    
    <xsl:template match="value">
        <text>
            <xsl:value-of select="text()" />
        </text>
    </xsl:template>
    
    <!-- REPLACE SPACES IN ID ATTRIBUTES -->
    <xsl:template match="@id">
	   <xsl:attribute name="{name()}">
	      <xsl:value-of select="translate(current(), ' ', '_')" />
	   </xsl:attribute>
	</xsl:template>
    
    <!-- FIX PNML XMLNS -->
    <xsl:template match="pnml">
    	<xsl:copy>
    		<xsl:attribute name="xmlns">http://www.pnml.org/version-2009/grammar/pnml</xsl:attribute>
    		<xsl:apply-templates select="node()" />
    	</xsl:copy>
    </xsl:template>
    
    <!-- FIX NET TYPE -->
    <xsl:template match="net/@type[current() != 'http://www.pnml.org/version-2009/grammar/ptnet']">
    	<xsl:attribute name="type">http://www.pnml.org/version-2009/grammar/ptnet</xsl:attribute>
    </xsl:template>
    
    <!-- FIX INITIAL_MARKING DEFAULT VALUE -->
    <xsl:template match="initialMarking/value[number(text()) != text()]">
    	<text>0</text>
    </xsl:template>
    
    <!-- FIX INSCRIPTION DEFAULT VALUE -->
    <xsl:template match="inscription/value[number(text()) != text()]">
    	<text>1</text>
    </xsl:template>
    
    <!-- FIX ARC GRAPHICS ELEMENT TO INCLUDE AN OFFSET ELEMENT -->
    <xsl:template match="inscription/graphics[not(offset)]">
    	<xsl:copy>
    		<offset x="0.0" y="0.0" />
    		<xsl:apply-templates select="@*|node()" />
    	</xsl:copy>
    </xsl:template>
    <!-- ********************************************************
                   END QUICK IGNORE/RENAME THESE ELEMENTS
         ******************************************************** -->

    <!-- ********************************************************
            START MOVING NODES IN NET TO PAGE (OR CREATE PAGE)
         ******************************************************** -->
    <xsl:template match="net/page[1]">
        <xsl:if test="/pnml/net/token">
            <toolspecific tool="PIPE" version="4.3.0"><xsl:call-template name="line_break" />
                <xsl:copy-of select="/pnml/net/token"/><xsl:call-template name="line_break" />
            </toolspecific><xsl:call-template name="line_break" />
        </xsl:if>
        <xsl:copy>
            <xsl:apply-templates select="@*" />
            <xsl:call-template name="line_break" />
            <xsl:for-each select="/pnml/net/place|/pnml/net/transition|/pnml/net/arc">
                <xsl:copy>
                    <xsl:apply-templates select="@*|node()" />
                </xsl:copy><xsl:call-template name="line_break" />
            </xsl:for-each>
            <xsl:apply-templates select="node()" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="net[not(page)]">
        <xsl:copy>
            <xsl:apply-templates select="@*" />
            <xsl:call-template name="line_break" />
            <xsl:if test="token">
                <toolspecific tool="PIPE" version="4.3.0"><xsl:call-template name="line_break" />
                    <xsl:copy-of select="token"/><xsl:call-template name="line_break" />
                </toolspecific><xsl:call-template name="line_break" />
            </xsl:if>
            <page id="PNLab_top_level" ><xsl:call-template name="line_break" />
                <xsl:for-each select="place|transition|arc">
                    <xsl:copy>
                        <xsl:apply-templates select="@*" />
                        <xsl:call-template name="move_place_properties" />
                        <xsl:call-template name="move_transition_properties" />
                        <xsl:call-template name="move_arc_properties" />
                        <xsl:apply-templates select="node()" />
                    </xsl:copy><xsl:call-template name="line_break" />
                </xsl:for-each>
                <xsl:apply-templates select="node()" />
            </page><xsl:call-template name="line_break" />
        </xsl:copy>
    </xsl:template>
    <!-- ********************************************************
            END MOVING NODES IN NET TO PAGE (OR CREATE PAGE)
         ******************************************************** -->

    <!-- ********************************************************
                START MOVE PLACE PROPS TO TOOLSPECIFIC
         ******************************************************** -->
    <xsl:template match="page/place[not(toolspecific/@tool='PNLab')]">
        <xsl:copy>
            <xsl:apply-templates select="@*" />
            <xsl:call-template name="move_place_properties" />
            <xsl:apply-templates select="node()" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="page/place[capacity]/toolspecific[@tool='PNLab' and not(capacity)]">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
            <capacity><xsl:call-template name="line_break" />
                <text>
                    <xsl:value-of select="../capacity/value/text()" />
                </text><xsl:call-template name="line_break" />
            </capacity><xsl:call-template name="line_break" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="page/place[capacity]/toolspecific[@tool='PNLab']/capacity">
        <capacity><xsl:call-template name="line_break" />
            <text>
                <xsl:value-of select="../../capacity/value/text()" />
            </text><xsl:call-template name="line_break" />
        </capacity><xsl:call-template name="line_break" />
    </xsl:template>
    <!-- ********************************************************
                END MOVE PLACE PROPS TO TOOLSPECIFIC
         ******************************************************** -->
         
    <!-- ********************************************************
               START MOVE TRANSITION PROPS TO TOOLSPECIFIC
         ******************************************************** -->
    <xsl:template match="page/transition">
        <xsl:copy>
            <xsl:apply-templates select="@*" />
            <xsl:if test="not(toolspecific/@tool='PNLab' or toolspecific/@tool='PIPE')" >
            	<xsl:call-template name="move_transition_properties" />
            </xsl:if>
            <xsl:apply-templates select="node()" />
        </xsl:copy>
    </xsl:template>
    
    <!-- ORIENTATION PROPERTY -->
    <xsl:template match="page/transition[orientation]/toolspecific[@tool='PNLab' and not(isHorizontal)]">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
            <isHorizontal><xsl:call-template name="line_break" />
                <text>
                    <xsl:value-of select="../orientation/value/text()" />
                </text><xsl:call-template name="line_break" />
            </isHorizontal><xsl:call-template name="line_break" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="page/transition[orientation]/toolspecific[@tool='PNLab']/isHorizontal">
        <isHorizontal><xsl:call-template name="line_break" />
            <text>
                <xsl:value-of select="../../orientation/value/text()" />
            </text><xsl:call-template name="line_break" />
        </isHorizontal><xsl:call-template name="line_break" />
    </xsl:template>
    
    <!-- RATE PROPERTY -->
    <xsl:template match="page/transition[rate]/toolspecific[@tool='PNLab' and not(rate)]">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
            <rate><xsl:call-template name="line_break" />
                <text>
                    <xsl:value-of select="../rate/value/text()" />
                </text><xsl:call-template name="line_break" />
            </rate><xsl:call-template name="line_break" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="page/transition[rate]/toolspecific[@tool='PNLab']/rate">
        <rate><xsl:call-template name="line_break" />
            <text>
                <xsl:value-of select="../../rate/value/text()" />
            </text><xsl:call-template name="line_break" />
        </rate><xsl:call-template name="line_break" />
    </xsl:template>
    
    <!-- PRIORITY PROPERTY -->
    <xsl:template match="page/transition[priority]/toolspecific[@tool='PNLab' and not(priority)]">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
            <priority><xsl:call-template name="line_break" />
                <text>
                    <xsl:value-of select="../priority/value/text()" />
                </text><xsl:call-template name="line_break" />
            </priority><xsl:call-template name="line_break" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="page/transition[priority]/toolspecific[@tool='PNLab']/priority">
        <priority><xsl:call-template name="line_break" />
            <text>
                <xsl:value-of select="../../priority/value/text()" />
            </text><xsl:call-template name="line_break" />
        </priority><xsl:call-template name="line_break" />
    </xsl:template>
    
    <!-- TIMED/TYPE PROPERTY -->
    <xsl:template match="page/transition[timed]/toolspecific[@tool='PNLab' and not(type)]">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
            <type><xsl:call-template name="line_break" />
                <text>
                	<xsl:choose>
                		<xsl:when test="../timed/value/text() = '1' or ../timed/value/text() = 'true'" >
                			stochastic
                		</xsl:when>
                		<xsl:otherwise>
                			immediate
                		</xsl:otherwise>
                	</xsl:choose>
                </text><xsl:call-template name="line_break" />
            </type><xsl:call-template name="line_break" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="page/transition[timed]/toolspecific[@tool='PNLab']/type">
        <type><xsl:call-template name="line_break" />
            <text>
            	<xsl:choose>
               		<xsl:when test="../../timed/value/text() = '1' or ../../timed/value/text() = 'true'" >
               			stochastic
               		</xsl:when>
               		<xsl:otherwise>
               			immediate
               		</xsl:otherwise>
               	</xsl:choose>
            </text><xsl:call-template name="line_break" />
        </type><xsl:call-template name="line_break" />
    </xsl:template>
    
    <!-- INFINITE_SERVER PROPERTY -->
    <xsl:template match="page/transition[infiniteServer]/toolspecific[@tool='PIPE' and not(infiniteServer)]">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
            <xsl:copy-of select="../infiniteServer" />
            <xsl:call-template name="line_break" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="page/transition[infiniteServer]/toolspecific[@tool='PIPE']/infiniteServer">
    	<xsl:copy-of select="../../infiniteServer" />
    	<xsl:call-template name="line_break" />
    </xsl:template>
    <!-- ********************************************************
               	END MOVE TRANSITION PROPS TO TOOLSPECIFIC
         ******************************************************** -->
    
    <!-- ********************************************************
                START MOVE ARC PROPS TO TOOLSPECIFIC
         ******************************************************** -->
    <xsl:template match="page/arc[not(toolspecific/@tool='PIPE')]">
        <xsl:copy>
            <xsl:apply-templates select="@*" />
            <xsl:call-template name="move_arc_properties" />
            <xsl:apply-templates select="node()" />
        </xsl:copy>
    </xsl:template>

    <!-- TAGGED PROPERTY -->
    <xsl:template match="page/arc[tagged]/toolspecific[@tool='PIPE' and not(tagged)]">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
            <xsl:copy-of select="../tagged" />
            <xsl:call-template name="line_break" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="page/transition[tagged]/toolspecific[@tool='PIPE']/tagged">
    	<xsl:copy-of select="../../tagged" />
    	<xsl:call-template name="line_break" />
    </xsl:template>
    
    <!-- TYPE PROPERTY -->
    <xsl:template match="page/arc[type]/toolspecific[@tool='PIPE' and not(type)]">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
            <xsl:copy-of select="../type" />
            <xsl:call-template name="line_break" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="page/transition[type]/toolspecific[@tool='PIPE']/type">
    	<xsl:copy-of select="../../type" />
    	<xsl:call-template name="line_break" />
    </xsl:template>
    
    <!-- ARCPATH PROPERTY -->
    <xsl:template match="page/arc[arcpath]/toolspecific[@tool='PIPE']">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
            <xsl:copy-of select="../arcpath" />
            <xsl:call-template name="line_break" />
        </xsl:copy>
    </xsl:template>
    <!-- ********************************************************
                END MOVE PLACE PROPS TO TOOLSPECIFIC
         ******************************************************** -->
    
    <!-- ********************************************************
            START FUNCTION TEMPLATES (used with call-template)
         ******************************************************** -->
    <xsl:template mode="function_only" match="page/place[not(toolspecific/@tool='PNLab')]" name="move_place_properties">
        <xsl:if test="capacity">
            <xsl:call-template name="line_break" />
            <toolspecific tool="PNLab" version="0.8"><xsl:call-template name="line_break" />
            	<capacity><xsl:call-template name="line_break" />
            		<text>
            			<xsl:value-of select="capacity/value/text()" />
            		</text><xsl:call-template name="line_break" />
            	</capacity><xsl:call-template name="line_break" />
            </toolspecific><xsl:call-template name="line_break" />
        </xsl:if>
    </xsl:template>
    
    <xsl:template mode="function_only" match="page/arc[not(toolspecific/@tool='PIPE')]" name="move_arc_properties">
        <xsl:if test="tagged|type|arcpath">
            <xsl:call-template name="line_break" />
            <toolspecific tool="PIPE" version="4.3.0"><xsl:call-template name="line_break" />
            	<xsl:if test="tagged">
            		<xsl:copy-of select="tagged" /><xsl:call-template name="line_break" />
            	</xsl:if>
            	<xsl:if test="type">
            		<xsl:copy-of select="type" /><xsl:call-template name="line_break" />
            	</xsl:if>
            	<xsl:for-each select="arcpath">
                    <xsl:copy>
                    	<xsl:apply-templates select="@*|node()" />
                    </xsl:copy><xsl:call-template name="line_break" />
                </xsl:for-each>
            </toolspecific><xsl:call-template name="line_break" />
        </xsl:if>
    </xsl:template>
    
    <xsl:template mode="function_only" match="page/transition[not(toolspecific/@tool='PNLab' or toolspecific/@tool='PIPE')]" name="move_transition_properties">
    	<xsl:if test="infiniteServer">
    		<xsl:call-template name="line_break" />
    		<toolspecific tool="PIPE" version="4.3.0"><xsl:call-template name="line_break" />
    			<xsl:copy-of select="infiniteServer" /><xsl:call-template name="line_break" />
    		</toolspecific>
    	</xsl:if>
        <xsl:if test="orientation|rate|timed|priority">
            <xsl:call-template name="line_break" />
            <toolspecific tool="PNLab" version="0.8"><xsl:call-template name="line_break" />
            	<xsl:if test="orientation">
            		<isHorizontal><xsl:call-template name="line_break" />
            			<text>
            				<xsl:value-of select="orientation/value/text()" />
            			</text><xsl:call-template name="line_break" />
            		</isHorizontal><xsl:call-template name="line_break" />
            	</xsl:if>
                <xsl:if test="rate">
            		<rate><xsl:call-template name="line_break" />
            			<text>
            				<xsl:value-of select="rate/value/text()" />
            			</text><xsl:call-template name="line_break" />
            		</rate><xsl:call-template name="line_break" />
            	</xsl:if>
            	<type><xsl:call-template name="line_break" />
            		<text>
		            	<xsl:choose>
		            		<xsl:when test="not(timed) or timed/value/text() = 'false' or timed/value/text() = '0'">
		            			immediate
		            		</xsl:when>
		            		<xsl:otherwise>
		            			stochastic
		            		</xsl:otherwise>
		            	</xsl:choose>
            		</text><xsl:call-template name="line_break" />
            	</type><xsl:call-template name="line_break" />
            	<xsl:if test="priority">
            		<priority><xsl:call-template name="line_break" />
            			<text>
            				<xsl:value-of select="priority/value/text()" />
            			</text><xsl:call-template name="line_break" />
            		</priority><xsl:call-template name="line_break" />
            	</xsl:if>
            </toolspecific><xsl:call-template name="line_break" />
        </xsl:if>
    </xsl:template>
    
	<xsl:template mode="function_only" name="line_break">
		<xsl:text>
		</xsl:text>
		<!-- <xsl:text>\n</xsl:text> -->
	</xsl:template>
	<!-- ********************************************************
                			END FUNCTION TEMPLATES
         ******************************************************** -->

</xsl:transform>
