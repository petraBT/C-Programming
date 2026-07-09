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

<!-- Set via project.ptx <stringparam key="cmecode.mode" value="static"/> on a build target.
     "live" (default): render the interactive Thayer code window (requires Thayer network access
       and the starting point to already be registered on code.thayer.dartmouth.edu).
     "static": render the code itself, read from the local CMeCodeDir/<startPoint>.c.xml file,
       as a plain read-only, copy-pasteable code block. Useful for previewing/proofreading the
       book before starting points are registered, and for readers without Thayer access. -->
<xsl:param name="cmecode.mode" select="'live'"/>

<!-- Absolute path (with trailing slash) to this project's CMeCodeDir, used only when
     cmecode.mode = 'static'. Must be absolute: PreTeXt stages this stylesheet into a temp
     directory before running the transform, so a path relative to the project root (like
     plain "CMeCodeDir/") resolves relative to that temp directory instead and silently fails
     to find every file. Override per-machine using pretext's stringparam command line
     option for cmecode.root pointed at the absolute path to CMeCodeDir, or set it directly
     in project.ptx's web-static target (see project.ptx for a placeholder). -->
<xsl:param name="cmecode.root" select="'CMeCodeDir/'"/>

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

<!-- Most cmecode instances should follow cmecode.mode (live vs static per build target).
     Some, though, can never work as a live coding window regardless of build target,
     e.g. anything that calls popen("gnuplot", ...) to open a plot, since the embedded
     Thayer terminal has no way to display that plot in any mode. For those, set
     forceStatic="yes" on the individual <cmecode> element to always render it as a
     plain read-only code block, even in a "live" build. -->
<xsl:template match="cmecode">
    <xsl:choose>
        <xsl:when test="$cmecode.mode = 'static' or @forceStatic = 'yes'">
            <xsl:call-template name="cmecode-static"/>
        </xsl:when>
        <xsl:otherwise>
            <xsl:call-template name="cmecode-live"/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template name="cmecode-live">
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

<xsl:template name="cmecode-static">
    <xsl:variable name="filename" select="concat($cmecode.root, @startPoint, '.c.xml')"/>
    <xsl:variable name="cmefile" select="document($filename)"/>
    <xsl:variable name="the-display">
        <program language="c"><code><xsl:value-of select="$cmefile/cme"/></code></program>
    </xsl:variable>
    <div style="border:1px solid #ccc; border-radius:5px; padding:8px 12px; margin-bottom:8px; background-color:#f7f7f7;">
        <p style="margin:0;"><em>Compile and run the code below in your own C environment.</em></p>
    </div>
    <xsl:choose>
        <xsl:when test="not($cmefile)">
            <p><em>Warning: no local starting-point file was found at <xsl:value-of select="$filename"/>.</em></p>
        </xsl:when>
        <xsl:otherwise>
            <xsl:apply-templates select="exsl:node-set($the-display)/*"/>
        </xsl:otherwise>
    </xsl:choose>
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
    <xsl:choose>
        <xsl:when test="$cmecode.mode = 'static'">
            <xsl:call-template name="server-static"/>
        </xsl:when>
        <xsl:otherwise>
            <xsl:call-template name="server-live"/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template name="server-live">
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

<!-- Unlike cmecode (one fixed C program, so its source can be shown as static text), a server
     window is a live interactive Linux terminal session, so there is no fixed "source" to display.
     So the static build just shows a short notice instead, optionally extended per-instance via
     a @staticNote attribute (e.g. explaining what file/folder to create to follow along locally,
     since these exercises often rely on files the Thayer server pre-provisions for the student). -->
<xsl:template name="server-static">
    <div style="border:1px solid #ccc; border-radius:5px; padding:8px 12px; margin-bottom:8px; background-color:#f7f7f7;">
        <p style="margin:0;"><em>Try these commands yourself in a Linux terminal.<xsl:if test="@staticNote"><xsl:text> </xsl:text><xsl:value-of select="@staticNote"/></xsl:if></em></p>
    </div>
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
