<?xml version='1.0'?>

<!-- Parts of this file were adapted from the author guide at https://github.com/rbeezer/mathbook and the analagous file at https://github.com/twjudson/aata -->
<!DOCTYPE xsl:stylesheet [
    <!ENTITY % entities SYSTEM "./core/entities.ent">
    %entities;
]>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns:exsl="http://exslt.org/common"
                xmlns:str="http://exslt.org/strings"
>

<!-- Assumes current file is in mathbook/user, so it must be copied there -->
<!-- <xsl:import pretext-href="pretext-html.xsl" /> -->
<xsl:import href="./core/pretext-html.xsl"/>
<!-- <xsl:import href="c-programming-preprocessing.xsl" /> -->

<!-- 
Example:

<figure>
    <caption>Test your knowledge</caption>
    <cmecode startPoint="engs20p_NAGprinting" addOn="&amp;nocheck=true" height="500"></cmecode>
</figure>

<figure>
    <caption>For Loops</caption>
    <codecast href="1513619151761"/>
</figure>

-->

<xsl:template match="codecast">
    <xsl:variable name="the-url">
        <xsl:text>https://codecast.france-ioi.org/v5/player?base=https%3A%2F%2Ffioi-recordings.s3.amazonaws.com%2Fdartmouth%2F</xsl:text>
        <xsl:value-of select="@href"/>
    </xsl:variable>
    <iframe title="A codecast is displayed here" src="{$the-url}" marginwidth="0" scrolling="yes" allowfullscreen="true" style="background: #E5E7E9; padding-center: 10px;" frameborder="0" height="800" width="900"></iframe>
    <p>If you cannot see this codecast, please click <a href="{$the-url}" target="_blank"><font color="blue">here</font></a>.</p>
 </xsl:template>

<xsl:template match="cmecode">
    <xsl:variable name="dummy">
        <xsl:value-of select="@height"/>
    </xsl:variable>
    <xsl:variable name="height">
       <xsl:choose>
          <xsl:when test="$dummy &gt; 200">
             <xsl:value-of select="@height"/>
          </xsl:when>
          <xsl:otherwise>
             <xsl:text>400</xsl:text>
          </xsl:otherwise>
       </xsl:choose>
    </xsl:variable>
    <xsl:variable name="the-url">
        <xsl:text>https://code.thayer.dartmouth.edu/?starting_point=</xsl:text>
        <xsl:value-of select="@startPoint"/>
        <xsl:text>.c</xsl:text>
        <xsl:value-of select="@addOn"/>
    </xsl:variable>
    <xsl:variable name="the-admin-url">
        <xsl:text>https://code.thayer.dartmouth.edu/admin.php?starting_point=</xsl:text>
        <xsl:value-of select="@startPoint"/>
        <xsl:text>.c</xsl:text>
    </xsl:variable>
    <p style="text-align: right;\"><a href="{$the-admin-url}" target="_blank"><font color="#AED6F1">admin</font></a><font color="#FFFFFF">.....</font><a href="{$the-url}" target="_blank"><font color="#1B279F">open in new window</font></a></p>
<!--    <iframe title="Coding Assignment" src="{$the-url}" marginwidth="0" scrolling="yes" allowfullscreen="true" style="background: #FFFFFF; padding-center: 10px; border:1px solid lightgrey;" frameborder="0" width="100%" height="{$height}"></iframe> -->
    <iframe title="Coding Assignment" style="position: absolute; top: -9999em; visibility: hidden;" onload="this.style.position='static'; this.style.visibility='visible';" src="{$the-url}" frameborder="0" width="100%" height="{$height}"></iframe>
</xsl:template>

<xsl:template match="gdoc">
    <xsl:variable name="the-url">
        <xsl:text>https://docs.google.com/document/d/e/</xsl:text>
        <xsl:value-of select="@href"/>
        <xsl:text>/pub?embedded=true</xsl:text>
    </xsl:variable>
    <iframe src="{$the-url}" width="1000" height="700" style="border: 1px solid #0b5942; background: lightgrey;" frameborder="1" marginheight="0" marginwidth="0">Loading...</iframe>
    <p>If you cannot see this document, please click <a href="{$the-url}" target="_blank"><font color="blue">here</font></a>.</p>
</xsl:template>

<xsl:template match="server">
    <xsl:variable name="dummy">
        <xsl:value-of select="@height"/>
    </xsl:variable>
    <xsl:variable name="height">
       <xsl:choose>
          <xsl:when test="$dummy &gt; 300">
             <xsl:value-of select="@height"/>
          </xsl:when>
          <xsl:otherwise>
             <xsl:text>300</xsl:text>
          </xsl:otherwise>
       </xsl:choose>
    </xsl:variable>
    <xsl:variable name="the-url">
        <xsl:text>https://code.thayer.dartmouth.edu/linux.php?starting_point=</xsl:text>
        <xsl:value-of select="@startPoint"/>
    </xsl:variable>
<!--    <iframe src="{$the-url}" width="105%" height="{$height}" allowfullscreen="true" style="background: #000000; padding-center: 10px; border:1px solid lightgrey;" frameborder="0" ></iframe> -->
    <iframe title="Linux Practice Window" style="position: absolute; top: -9999em; visibility: hidden;" onload="this.style.position='static'; this.style.visibility='visible';" src="{$the-url}" width="105%" height="{$height}" frameborder="0" ></iframe>
    <p>If the server window does not load, please click <a href="{$the-url}" target="_blank"><font color="blue">here</font></a>.</p>
</xsl:template>

<xsl:template match="cmecodehere">
    <xsl:variable name="mycode" select="text()" />
    <xsl:variable name="percent" select="str:replace($mycode, '%',  '%25')"/>
    <xsl:variable name="lessthan" select="str:replace($percent, '&lt;',  '%3C')"/>
    <xsl:variable name="greaterthan" select="str:replace($lessthan, '&gt;',  '%3E')"/>
    <xsl:variable name="pound" select="str:replace($greaterthan, '#', '%23')"/>
    <xsl:variable name="openparan" select="str:replace($pound, '(', '%28')"/>
    <xsl:variable name="closeparan" select="str:replace($openparan, ')', '%29')"/>
    <xsl:variable name="semicolon" select="str:replace($closeparan, ';', '%3B')"/>
    <xsl:variable name="comma" select="str:replace($semicolon, ';', '%3B')"/>
    <xsl:variable name="exclamation" select="str:replace($comma, '!', '%21')"/>
    <xsl:variable name="equal" select="str:replace($exclamation, '=', '%3D')"/>
    <xsl:variable name="cleancode" select="str:replace($exclamation, '+',  '%2B')"/>
    <iframe title="Coding Assignment" src="https://code.thayer.dartmouth.edu/?starting_point={$cleancode}" marginwidth="0" scrolling="yes" allowfullscreen="true" style="background: #FFFFFF; padding-center: 10px; border:1px solid lightgrey;" frameborder="0" width="100%" height="300"></iframe>
</xsl:template>

<xsl:template match="repl">
    <xsl:variable name="the-url">
        <xsl:text>https://replit.com/team/engs-20-petra-test/</xsl:text>
        <xsl:value-of select="@startPoint"/>
    </xsl:variable>
    <iframe title="A Repl is displayed here" src="{$the-url}" width="900" height="800" style="border: 1px solid #0b5942; background: lightgrey;" frameborder="1" marginheight="0" marginwidth="0">Loading…</iframe>
    <p>If you cannot see Repl.it, please click <a href="{$the-url}" target="_blank"><font color="blue">here</font></a>.</p>
</xsl:template>

<xsl:template match="matlab">
    <xsl:variable name="the-url">
        <xsl:text>https://matlab.mathworks.com/</xsl:text>
    </xsl:variable>
    <iframe src="{$the-url}" width="800" height="700" style="border: 1px solid #0b5942; background: lightgrey;" frameborder="1" marginheight="0" marginwidth="0">Loading...</iframe>
    <p>If you cannot see this MATLAB window, please click <a href="{$the-url}" target="_blank"><font color="blue">here</font></a>.</p>
</xsl:template>

</xsl:stylesheet>
