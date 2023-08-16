<?xml version='1.0'?>

<!DOCTYPE xsl:stylesheet [
    <!ENTITY % entities SYSTEM "./core/entities.ent">
    %entities;
]>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns:exsl="http://exslt.org/common"
                xmlns:str="http://exslt.org/strings"
                extension-element-prefixes="exsl"
>

<!-- Assumes current file is in mathbook/user, so it must be copied there -->
<!-- <xsl:import pretext-href="pretext-html.xsl" /> -->
<xsl:import href="./core/pretext-latex.xsl"/>

<!-- 
Example: Assumes c-source code is in source subdirectory /CMeCodeDir

<figure>
    <caption>For Loops</caption>
    <codecast href="1513619151761"/>
</figure>
<figure>
    <caption>Test your knowledge</caption>
    <cmecode startPoint="engs20p_NWhile2" addOn="&amp;nocheck=true"></cmecode>
</figure>

-->

<!-- Assumes QR code png files are in LaTeX subdirectory /QRDir -->
<!-- Assumes screenshot png files are in LaTeX subdirectory /CodecastDir -->

<!-- This uses the c-file rather than the image -->


<xsl:template match="codecast">
   <xsl:variable name="screenshot" select="concat('CodecastDir/', @href, '.png')"/>
   <xsl:variable name="qr-file" select="concat('QRDir/', @href, '.png')"/>
   <xsl:variable name="filename" select="concat('CodecastDir/', @href, '.c.xml')"/>  
   <xsl:variable name="cmefile" select="document($filename, /pretext)"/> 
   <xsl:variable name="the-display">
        <p>The code below is from a Codecast video.
        Access the video by scanning the QR code.</p>
      <sidebyside widths="80% 20%" margins="auto" valign="middle">
          <program language="c">
              <input>
                 <xsl:value-of select="$cmefile/cme"/>    
              </input>
          </program>
          <image source="{$qr-file}" />
       </sidebyside>
   </xsl:variable>
   <xsl:apply-templates select="exsl:node-set($the-display)/*" />
</xsl:template>

<!--
   <xsl:template match="codecast">
   <xsl:variable name="screenshot" select="concat('CodecastDir/', @href, '.png')"/>
   <xsl:variable name="qr-file" select="concat('QRDir/', @href, '.png')"/>
   <xsl:variable name="filename" select="concat('CodecastDir/', @href, '.c.xml')"/>  
   <xsl:variable name="cmefile" select="document($filename, /pretext)"/>
   <xsl:variable name="the-display">
      <sidebyside widths="80% 20%" margins="auto" valign="middle">
        <p><p>The code below is from a Codecast video.</p>
          <p>Access the video by scanning the QR code. <m>\Longrightarrow</m></p>
           <p>This is the code discussed in the video. <m>\Downarrow</m></p>
        </p>
        <image source="{$qr-file}" />
      </sidebyside>

      <sidebyside margins="auto" valign="middle">
          <program language="c">
              <input>
                 <xsl:value-of select="$cmefile/cme"/>    
              </input>
          </program>
       </sidebyside>
   </xsl:variable>
   <xsl:apply-templates select="exsl:node-set($the-display)/*" />
</xsl:template>
-->


<!-- This one is side-by-side which makes the screenshot too small -->
<!--
<xsl:template match="codecast">
   <xsl:variable name="qr-file" select="concat('QRDir/', @href, '.png')"/>
   <xsl:variable name="screenshot" select="concat('CodecastDir/', @href, '.png')"/>
   <xsl:variable name="the-display">
       <sidebyside widths="80% 20%" margins="auto" valign="middle">
           <image source="{$screenshot}"/>
           <image source="{$qr-file}" />
       </sidebyside>
  </xsl:variable>
  <xsl:apply-templates select="exsl:node-set($the-display)/*" />
</xsl:template>
-->

<!-- This one is vertical - not pretty but better to read. 
<xsl:template match="codecast">
   <xsl:variable name="qr-file" select="concat('QRDir/', @href, '.png')"/>
   <xsl:variable name="screenshot" select="concat('CodecastDir/', @href, '.png')"/>
   <xsl:variable name="the-display">
   <image source="{$screenshot}" width="100%"/>
   <image source="{$qr-file}" width="20%"/>
  </xsl:variable>
  <xsl:apply-templates select="exsl:node-set($the-display)/*" />
</xsl:template>
-->

<xsl:template match="cmecode">
   <xsl:variable name="qr-file" select="concat('QRDir/', @startPoint, '.png')"/>
   <xsl:variable name="filename" select="concat('CMeCodeDir/', @startPoint, '.c.xml')"/>
   <xsl:variable name="cmefile" select="document($filename, /pretext)"/> 
   <xsl:variable name="the-display">
       <sidebyside widths="80% 20%" margins="auto" valign="middle">
          <program language="c">
              <input>
                  <xsl:value-of select="$cmefile/cme"/>    
              </input>
          </program>
          <image source="{$qr-file}" />
       </sidebyside>
   </xsl:variable>
   <xsl:apply-templates select="exsl:node-set($the-display)/*" />
</xsl:template>

<!--
<xsl:template match="cmecode">
   <xsl:variable name="qr-file" select="concat('QRDir/', @startPoint, '.png')"/>
   <xsl:variable name="the-display">
       <sidebyside widths="80% 20%" margins="auto" valign="middle">
          <program language="c">
              <input>
                   <xsl:call-template name="sanitize-text">
                       <xsl:with-param name="text" select="text()" />
                   </xsl:call-template>
              </input>
          </program>
          <image source="{$qr-file}" />
       </sidebyside>
   </xsl:variable>
   <xsl:apply-templates select="exsl:node-set($the-display)/*" />
</xsl:template>
-->

<xsl:template match="cmecodehere">
    <xsl:variable name="the-display">
       <sidebyside>
          <program language="c">
              <input>
                   <xsl:call-template name="sanitize-text">
                       <xsl:with-param name="text" select="text()" />
                   </xsl:call-template>
              </input>
          </program>
       </sidebyside>
    </xsl:variable>
    <xsl:apply-templates select="exsl:node-set($the-display)/*" />
</xsl:template>


</xsl:stylesheet>
