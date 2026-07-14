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
       book before starting points are registered, and for readers without Thayer access.
     "client": render the new client-side coding window (compiles and runs C entirely in the
       student's browser, no server) - see coding-window/README.md in this repo, and that
       tool's own README.md / DEPLOYMENT.md for how it works. Evaluation/prototype stage as of
       this writing - not yet the default. -->
<xsl:param name="cmecode.mode" select="'live'"/>

<!-- Absolute path (with trailing slash) to this project's CMeCodeDir, used only when
     cmecode.mode = 'static'. Must be absolute: PreTeXt stages this stylesheet into a temp
     directory before running the transform, so a path relative to the project root (like
     plain "CMeCodeDir/") resolves relative to that temp directory instead and silently fails
     to find every file. Override per-machine using pretext's stringparam command line
     option for cmecode.root pointed at the absolute path to CMeCodeDir, or set it directly
     in project.ptx's web-static target (see project.ptx for a placeholder). -->
<xsl:param name="cmecode.root" select="'CMeCodeDir/'"/>

<!-- Used only when cmecode.mode = 'client'. Unlike cmecode.root above, these are ordinary
     relative paths resolved by the BROWSER at view time (not XSLT's document() at build
     time), so they don't need to be absolute - and can't be hardcoded per-machine, since
     they need to work on whatever server this book actually gets deployed to.

     cmecode.client.tool: path to the coding-window tool's index.html, relative to a book
       page. All book pages currently sit flat at the same directory level in the published
       site (chunking doesn't nest them into subfolders), so one relative path works for all
       of them; revisit if that ever changes.
     cmecode.client.root: path the TOOL should fetch each starting-point .c file from,
       relative to the TOOL's own location (not the book page's) - a fetch() inside the
       iframe resolves against the iframe's own document, not its parent. CMeCodeDir is a
       sibling of coding-window/ at the published site root, hence the leading "../".
       deploy.sh copies the plain (non-.c.xml) files from this project's CMeCodeDir into the
       published CMeCodeDir/ this points at. -->
<xsl:param name="cmecode.client.tool" select="'coding-window/index.html'"/>
<xsl:param name="cmecode.client.root" select="'../CMeCodeDir/'"/>

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
     plain read-only code block, even in a "live" build.

     Separately: addOn="...hide_run=true" was the author's old way (Thayer-specific URL
     param) of showing code the student is meant to read and analyze, not run - Thayer
     hides its Run button when it sees that param. That's untouched here: "live" mode
     still passes addOn straight through to Thayer same as always. But the new client
     tool has no such param to hand off to (no Thayer, and this tool doesn't have a way
     to hide its own Run button), so under "client" mode specifically, hide_run=true
     elements render as the same plain read-only display as forceStatic, instead of the
     live tool. -->
<xsl:template match="cmecode">
    <xsl:choose>
        <xsl:when test="$cmecode.mode = 'static' or @forceStatic = 'yes'">
            <xsl:call-template name="cmecode-static"/>
        </xsl:when>
        <xsl:when test="$cmecode.mode = 'client' and contains(@addOn, 'hide_run=true')">
            <xsl:call-template name="cmecode-readonly"/>
        </xsl:when>
        <xsl:when test="$cmecode.mode = 'client'">
            <xsl:call-template name="cmecode-client"/>
        </xsl:when>
        <xsl:otherwise>
            <xsl:call-template name="cmecode-live"/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- New client-side coding window: compiles and runs C entirely in the browser, no server.
     Unlike cmecode-live, there's no "admin" / "open in new window" links row (out of scope
     for this tool by design). -->
<!-- Extra vertical space this tool's chrome needs beyond what the @height attributes were
     originally tuned for (those numbers came from the old Thayer window's layout). Measured
     directly, not guessed: same starting-point file rendered at height=400 needed 561px
     actual content, and at height=500 needed 545px, once an error/output was showing and the
     "Input" fallback box was visible (which it will be on every exercise once deployed - see
     the interactiveStdin comment on the "Stdin is interactive..." bullet in the coding-window
     tool's own README.md - GitHub Pages can't provide the headers that unlock the live
     terminal, so the fallback box is the deployed reality here, not just a local-preview
     artifact). +180 covers the largest observed gap (161px) with some margin. Iframes still
     scroll internally rather than break if a given exercise's actual output is unusually
     long - this isn't trying to guarantee zero scrolling in every case, just fix the common
     one. Bumped from an initial 180 to 230 after re-measuring with a two-line error message
     (180 left only 3px of margin against a real exercise's actual content height - too close
     for comfort given output length varies). -->
<xsl:param name="cmecode.client.height-buffer" select="230"/>

<xsl:template name="cmecode-client">
    <xsl:variable name="dummy">
        <xsl:value-of select="@height"/>
    </xsl:variable>
    <xsl:variable name="base-height">
       <xsl:choose>
          <xsl:when test="$dummy &gt; 200">
             <xsl:value-of select="@height"/>
          </xsl:when>
          <xsl:otherwise>
             <xsl:text>400</xsl:text>
          </xsl:otherwise>
       </xsl:choose>
    </xsl:variable>
    <xsl:variable name="height" select="$base-height + $cmecode.client.height-buffer"/>
    <!-- Always emit "?src=", even with nothing after it for a startPoint-less element:
         an explicit empty value tells the tool "start blank, don't prepopulate anything"
         (distinct from omitting the param entirely, which the tool takes to mean "not
         embedded by this book, show the default demo starter" - see loadStartingCode()
         in the tool's own src/main.ts). Doesn't currently arise - every <cmecode> in this
         book's source has a startPoint - but this keeps a stray/future startPoint-less one
         from either erroring or confusingly prepopulating unrelated demo content. -->
    <xsl:variable name="the-url">
        <xsl:value-of select="$cmecode.client.tool"/>
        <xsl:text>?src=</xsl:text>
        <xsl:if test="@startPoint != ''">
            <xsl:value-of select="$cmecode.client.root"/>
            <xsl:value-of select="@startPoint"/>
            <xsl:text>.c</xsl:text>
        </xsl:if>
    </xsl:variable>
    <iframe title="Coding Assignment" allow="cross-origin-isolated" style="position: absolute; top: -9999em; visibility: hidden; border: none;" onload="this.style.position='static'; this.style.visibility='visible';" src="{$the-url}" width="100%" height="{$height}"></iframe>
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

<!-- Same file-reading approach as cmecode-static, minus the "compile and run this
     yourself" messaging: this is specifically for hide_run=true content, which was
     never meant to be run at all, only read - that message would be actively wrong
     advice for it. Only reached from "client" mode (see the dispatch template above);
     "live" mode keeps sending hide_run straight through to Thayer as it always has. -->
<xsl:template name="cmecode-readonly">
    <xsl:variable name="filename" select="concat($cmecode.root, @startPoint, '.c.xml')"/>
    <xsl:variable name="cmefile" select="document($filename)"/>
    <xsl:variable name="the-display">
        <program language="c"><code><xsl:value-of select="$cmefile/cme"/></code></program>
    </xsl:variable>
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

<!-- Standard XSLT 1.0 recursive whitespace trim (str:trim, from the same EXSLT strings
     module as str:replace/str:encode-uri below, turned out not to be implemented in this
     particular libexslt build - confirmed by testing before writing this). Used below to
     drop the leading/trailing blank line that PreTeXt's own source indentation puts around
     cmecodehere's inline text content, without touching the code's actual internal
     formatting (only strips the outer whitespace, recursion bottoms out immediately for
     everything in between). -->
<xsl:template name="string-trim">
    <xsl:param name="text"/>
    <xsl:variable name="whitespace" select="'&#9;&#10;&#13;&#32;'"/>
    <xsl:variable name="trimmed-start">
        <xsl:choose>
            <xsl:when test="$text != '' and contains($whitespace, substring($text, 1, 1))">
                <xsl:call-template name="string-trim">
                    <xsl:with-param name="text" select="substring($text, 2)"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="$text"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:variable>
    <xsl:choose>
        <xsl:when test="$trimmed-start != '' and contains($whitespace, substring($trimmed-start, string-length($trimmed-start), 1))">
            <xsl:call-template name="string-trim">
                <xsl:with-param name="text" select="substring($trimmed-start, 1, string-length($trimmed-start) - 1)"/>
            </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
            <xsl:value-of select="$trimmed-start"/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- cmecodehere is like cmecode, but the starting code is written inline as this
     element's own text content instead of referencing a registered CMeCodeDir/Thayer
     starting point - used for small one-off snippets not worth registering separately
     (as of this writing, exactly two: gettingstarted.ptx and loops.ptx). -->
<xsl:template match="cmecodehere">
    <xsl:choose>
        <xsl:when test="$cmecode.mode = 'static'">
            <xsl:call-template name="cmecodehere-static"/>
        </xsl:when>
        <xsl:when test="$cmecode.mode = 'client'">
            <xsl:call-template name="cmecodehere-client"/>
        </xsl:when>
        <xsl:otherwise>
            <xsl:call-template name="cmecodehere-live"/>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<xsl:template name="cmecodehere-live">
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

<!-- Static-mode fallback for cmecodehere. Was previously missing entirely (this element
     had no mode dispatch at all - it always rendered the live Thayer iframe, even under
     the "static" build target, unlike every other cmecode-family element). Fixed here
     alongside adding "client" mode support, for consistency: both gaps had the same root
     cause (no <xsl:choose> on cmecode.mode), so fixing one without the other seemed like
     it'd just be trading one inconsistency for another. -->
<xsl:template name="cmecodehere-static">
    <xsl:variable name="trimmed">
        <xsl:call-template name="string-trim">
            <xsl:with-param name="text" select="."/>
        </xsl:call-template>
    </xsl:variable>
    <div style="border:1px solid #ccc; border-radius:5px; padding:8px 12px; margin-bottom:8px; background-color:#f7f7f7;">
        <p style="margin:0;"><em>Compile and run the code below in your own C environment.</em></p>
    </div>
    <program language="c"><code><xsl:value-of select="$trimmed"/></code></program>
</xsl:template>

<!-- New client-side coding window (see cmecode-client above for the general approach).
     The code lives inline here rather than in a CMeCodeDir file, so there's no file to
     fetch by URL - instead the trimmed text is percent-encoded (str:encode-uri, the real
     thing, unlike cmecodehere-live's hand-rolled partial character replacement above -
     that one's Thayer-specific and intentionally untouched) directly into a data: URL,
     passed as the tool's ?src=. The tool's loading code doesn't need to know or care that
     this "file" was never actually served from anywhere - fetch(), which is what src=
     already triggers, resolves data: URLs natively.

     Encoded TWICE, not once - confirmed by testing this actually breaks with a single
     encoding pass, silently truncating the code at its first "#" (e.g. right before
     "#include", corrupting every real C file this way): the tool reads ?src= via
     URLSearchParams.get(), which auto-decodes one percent-encoding layer before the
     value ever reaches fetch(). A single-encoded payload comes out of that decode with
     its "#"/"&"/etc. already bare, which a URL parser then reads as a fragment separator
     (or similar), silently dropping everything after it. Encoding twice means the string
     surviving that first auto-decode is still exactly one layer of valid percent-encoding
     - safe for fetch()'s own URL parsing to decode correctly, same as a real (non-inline)
     ?src= file reference always was. -->
<xsl:template name="cmecodehere-client">
    <xsl:variable name="trimmed">
        <xsl:call-template name="string-trim">
            <xsl:with-param name="text" select="."/>
        </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="encoded" select="str:encode-uri(str:encode-uri($trimmed, true()), true())"/>
    <xsl:variable name="the-url">
        <xsl:value-of select="$cmecode.client.tool"/>
        <xsl:text>?src=data:text/plain,</xsl:text>
        <xsl:value-of select="$encoded"/>
    </xsl:variable>
    <xsl:variable name="height" select="400 + $cmecode.client.height-buffer"/>
    <iframe title="Coding Assignment" allow="cross-origin-isolated" style="position: absolute; top: -9999em; visibility: hidden; border: none;" onload="this.style.position='static'; this.style.visibility='visible';" src="{$the-url}" width="100%" height="{$height}"></iframe>
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

<!-- Override core's runestone-link/mathjax-link (see pretext-html.xsl): those
     reference runestone.academy/mathjax.org directly, and neither sends a
     Cross-Origin-Resource-Policy header, so both logos get silently blocked
     by the browser on any page that's cross-origin isolated (COOP/COEP,
     needed for the coding-window tool's interactive stdin - see
     cmecode-client below and this project's _headers file). Self-hosting
     local copies (downloaded once into assets/images/) sidesteps this
     entirely, since a same-origin image was never subject to COEP in the
     first place. Same visual result either way - these are just two footer
     attribution logos. -->
<xsl:template name="runestone-link">
    <a class="runestone-link" href="https://runestone.academy" title="Runestone Academy">
        <img class="logo" src="external/images/RAIcon_cropped.png" alt="Runstone Academy logo"/>
    </a>
</xsl:template>

<xsl:template name="mathjax-link">
    <a class="mathjax-link" href="https://www.mathjax.org" title="MathJax">
        <img class="logo" src="external/images/mathjax-badge-square-2.png" alt="MathJax logo"/>
    </a>
</xsl:template>

</xsl:stylesheet>
