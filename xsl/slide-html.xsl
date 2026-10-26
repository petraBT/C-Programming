<?xml version='1.0'?>

<!-- Shared slide tooling: the <slide>, <instructor> and <clr> elements, and
     their exclusion from the search index. Imported by each book's own HTML
     stylesheet (which adds whatever else that book needs). Part of the
     slide-tooling repo; edit it THERE and run scripts/sync-tooling.sh. -->
<!DOCTYPE xsl:stylesheet [
    <!ENTITY % entities SYSTEM "./core/entities.ent">
    %entities;
]>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns:exsl="http://exslt.org/common"
                xmlns:str="http://exslt.org/strings"
                exclude-result-prefixes="exsl str">

<xsl:import href="./core/pretext-html.xsl"/>

<!-- What to do with <slide> blocks in this build:
       'strip'  (default, the reading "web" target) — emit NOTHING. The reading
                book already has the full prose, must not show the condensed
                projector form, and must never leak instructor-only notes or
                solutions inlined in a slide, even in page source.
       'render' (the "web-deck" target the player reads) — emit the hidden
                <div class="deck-slide"> the player extracts.
     Either way a matching template exists, so PreTeXt does not try to assign a
     number to the unknown element (which errors under the stock stylesheet). -->
<xsl:param name="deck.slides" select="'strip'"/>

<!-- What to do with <instructor> blocks in this build:
       'strip'  (default: the reading "web" target, the PDF, and the deck) —
                emit NOTHING, not even in page source. A student who reads the
                HTML source must not find the answer there.
       'render' (the "web-instructor" target) — emit the block, boxed and
                labelled, for the instructor's own copy.
     Use it for anything that hands over work a student or a lab is supposed to
     do: a filled-in driver function, a completed program, an activity's worked
     answer. Reveals that are the class's own teaching — a derivation the room
     does together — are NOT instructor material and should stay in the book. -->
<xsl:param name="book.solutions" select="'strip'"/>

<!-- What to do with INSTRUCTOR-ONLY SLIDES — a <slide instructor="yes">, or a
     deck ref pointing straight at an <instructor> block:
       'strip'  (default, the "web-deck" target the students may be given) —
                emit NOTHING. Until this existed the slide was rendered and the
                player merely filtered it out of the student VIEW, so the answer
                sat in the page source of a deck a student could open.
       'render' (the "web-deck-instructor" target you teach from) — emit it.
     The deck JSON's "instructor": true still drives the player: the badge in
     the instructor view, and dropping the slide from ?student. That flag and
     this one must agree, or the student deck loses a slide it should have kept
     (or keeps one it should not) — scripts/check_deck.py enforces it. -->
<xsl:param name="deck.solutions" select="'strip'"/>

<!-- Instructor-only content, stripped from the student book.
       <instructor xml:id="inst-...">              (xml:id optional)
         <p>...</p> <program>...</program>
         <caption>shown only when a deck slide refs this block</caption>
       </instructor>
     Same contract as <slide>: a matching template always exists, so PreTeXt
     does not try to number the unknown element under the stock stylesheet.

     The @xml:id becomes the div's id so a deck can ref this block DIRECTLY,
     instead of a <slide> repeating the same answer beside it — two copies of
     one solution drift, and the drift is invisible until you project the stale
     one. The deck build that renders such a ref is web-deck-instructor, which
     sets book.solutions=render for exactly this reason. -->
<xsl:template match="instructor">
    <xsl:if test="$book.solutions = 'render'">
        <div class="instructor-only">
            <xsl:if test="@xml:id">
                <xsl:attribute name="id">
                    <xsl:value-of select="@xml:id"/>
                </xsl:attribute>
            </xsl:if>
            <div class="instructor-only-label">Instructor only</div>
            <xsl:apply-templates select="node()[not(self::caption)]"/>
            <!-- Same class the player reads off a <slide>, for parity. In the
                 instructor book it reads as the block's closing line, and the
                 player projects it in the same place — a caption with no figure
                 to sit under closes the body. -->
            <xsl:if test="caption">
                <div class="deck-slide-caption">
                    <xsl:apply-templates select="caption/node()"/>
                </div>
            </xsl:if>
        </div>
    </xsl:if>
</xsl:template>

<!-- Inline coloured text for slides: <clr c="orange">Channel 1</clr> ->
     <span class="deck-clr-orange">. Colours are styled in the deck player
     (assets/class.html). Meant for slide bullets that mirror a colour in the
     figure beside them (e.g. scope channels); the reading book strips <slide>
     entirely, so this never affects normal prose. -->
<xsl:template match="clr">
    <span class="deck-clr-{@c}"><xsl:apply-templates/></span>
</xsl:template>

<!-- Keep <slide> and <instructor> out of the SEARCH INDEX as well as off the
     page.  PreTeXt builds lunr-pretext-search-index.js in its own modes, which
     walk the source tree rather than the rendered HTML - so the templates above
     are not consulted, and without the four templates below the student book's
     search index carries every presenter note and every worked solution even
     though no page displays them.  A student searching "SevenSeg_write" got the
     finished function back.  Verified by grepping the built index; see the note
     in AUTHORING-book.md under "Instructor-only content". -->
<xsl:template match="slide" mode="search-node-text">
    <!-- Same gate as the page template, and it has to be repeated here rather
         than inherited: PreTeXt builds lunr-pretext-search-index.js in its own
         modes, which walk the SOURCE tree, so a slide stripped from the HTML is
         still indexed unless it is stripped here too. That is how the presenter
         notes leaked the first time. -->
    <xsl:if test="$deck.slides = 'render' and
                  not((@instructor = 'yes' or @instructor = 'private') and $deck.solutions != 'render')">
        <xsl:apply-templates select="node()" mode="search-node-text"/>
    </xsl:if>
</xsl:template>
<!-- A slide's <note> is hers, so it is indexed only where it is rendered: the
     deck she teaches from. Once "web" rendered slides, the gate above let every
     note into the published search index along with the slide. -->
<xsl:template match="slide/note" mode="search-node-text">
    <xsl:if test="$deck.solutions = 'render'">
        <xsl:apply-templates select="node()" mode="search-node-text"/>
    </xsl:if>
</xsl:template>
<xsl:template match="instructor" mode="search-node-text">
    <xsl:if test="$book.solutions = 'render'">
        <xsl:apply-templates select="node()" mode="search-node-text"/>
    </xsl:if>
</xsl:template>
<!-- ... and stop them generating search documents of their own: a <p> with a
     <term> inside a slide would otherwise become its own indexed block. -->
<xsl:template match="slide|instructor" mode="search-block-docs-textbook"/>
<xsl:template match="slide|instructor" mode="search-block-docs-reference"/>

<!-- The condensed in-class slide form of the surrounding content.
       <slide xml:id="sl-..."  ref="fig-...optional">
         <ul> ...condensed bullets... </ul>   (or short <p>s)
         <note> presenter-only reminder, never projected </note>
       </slide>
     @ref names an existing figure / activity / program to show alongside the
     bullets, so its image is never duplicated - the player resolves it. The
     block is hidden in the reading view; only the deck player reveals it. -->
<xsl:template match="slide">
    <xsl:if test="$deck.slides = 'render' and
                  not((@instructor = 'yes' or @instructor = 'private') and $deck.solutions != 'render')">
        <div class="deck-slide" hidden="hidden">
            <!-- Marks the block for the player, which badges it in the
                 instructor view. It only ever reaches the HTML in a build that
                 renders instructor slides at all; the student deck does not
                 have this element to badge. -->
            <xsl:if test="@instructor = 'yes' or @instructor = 'private'">
                <xsl:attribute name="data-deck-instructor"><xsl:value-of select="@instructor"/></xsl:attribute>
            </xsl:if>
            <xsl:attribute name="id">
                <xsl:value-of select="@xml:id"/>
            </xsl:attribute>
            <xsl:if test="@ref">
                <xsl:attribute name="data-deck-ref">
                    <xsl:value-of select="@ref"/>
                </xsl:attribute>
            </xsl:if>
            <!-- A slide that is not a figure or a text body but a card the player
                 draws itself: kind="title|section|agenda|recap|notice|prompt".
                 Its words are carried as attributes (title, kicker, subtitle);
                 bullets and body text are the slide's own <ul> and <p>. The
                 player turns these back into the same card it used to draw from
                 the deck JSON. -->
            <xsl:for-each select="@kind|@kicker|@subtitle|@title|@answer">
                <xsl:attribute name="data-deck-{local-name()}">
                    <xsl:value-of select="."/>
                </xsl:attribute>
            </xsl:for-each>
            <!-- Optional layout hint: stack="yes" → bullets full width on top,
                 figure full width (large) below, for wide images. -->
            <xsl:if test="@stack">
                <xsl:attribute name="data-deck-stack">
                    <xsl:value-of select="@stack"/>
                </xsl:attribute>
            </xsl:if>
            <!-- Optional layout hint: mediawide="yes" → narrow the bullet column
                 and give the width to the figure, for a two-column slide whose
                 image carries fine detail (scope screenshots, pinouts).  Petra,
                 2026-09-17, on the Day 3x trigger slide: "Can you make this image
                 bigger and reduce the column width of the left-hand column?  There
                 is plenty of space for this on the left." -->
            <xsl:if test="@mediawide">
                <xsl:attribute name="data-deck-mediawide">
                    <xsl:value-of select="@mediawide"/>
                </xsl:attribute>
            </xsl:if>
            <!-- Optional: room="yes" → leave writing space after each list item,
                 for predict/practice slides students (and the instructor) write on.
                 room="compressed" is the opposite: tighten the gaps (not the type
                 size) so a long activity fits on one slide. -->
            <xsl:if test="@room">
                <xsl:attribute name="data-deck-room">
                    <xsl:value-of select="@room"/>
                </xsl:attribute>
            </xsl:if>
            <!-- Optional: code="small" → this slide's listings at 95% of the
                 code size, for two listings side by side (Day 5's jigsaw). -->
            <xsl:if test="@code">
                <xsl:attribute name="data-deck-code">
                    <xsl:value-of select="@code"/>
                </xsl:attribute>
            </xsl:if>
            <!-- Optional: columns="top" → the slide's <sidebyside> panels start
                 at the top instead of centering vertically. -->
            <xsl:if test="@columns">
                <xsl:attribute name="data-deck-columns">
                    <xsl:value-of select="@columns"/>
                </xsl:attribute>
            </xsl:if>
            <!-- Column widths for a <tabular> in this slide.  PreTeXt honours
                 <col width="..."/> in print but emits NO <colgroup> in HTML, so
                 on a slide the columns size themselves by content: the UART/I2C
                 comparison came out 422px against 755px despite both columns
                 being declared 50%.  Carry the declared widths through so the
                 player can apply them; without this the attribute is simply
                 absent and the table keeps the old content-sized behaviour. -->
            <xsl:if test="descendant::tabular[1]/col/@width">
                <xsl:attribute name="data-deck-colwidths">
                    <xsl:for-each select="descendant::tabular[1]/col">
                        <xsl:value-of select="@width"/>
                        <xsl:if test="position() != last()">,</xsl:if>
                    </xsl:for-each>
                </xsl:attribute>
            </xsl:if>
            <div class="deck-slide-body">
                <xsl:apply-templates select="*[not(self::note) and not(self::caption)]"/>
            </div>
            <!-- A slide's own short, instructive caption. On a slide that refs a
                 figure the player shows it under the image, INSTEAD of the book
                 figure's full caption; on any other slide it closes the body. -->
            <xsl:for-each select="caption">
                <div class="deck-slide-caption">
                    <xsl:apply-templates/>
                </div>
            </xsl:for-each>
            <!-- A <note> is hers: timing, reveal cues, "don't answer yet". Only
                 the deck she teaches from (deck.solutions=render) carries it.
                 It used to be emitted wherever slides were, and once "web"
                 rendered slides (2026-09-25) that put 249 of them in the page
                 source of the published site: hidden by deck.css, readable by
                 anyone who viewed source. -->
            <xsl:if test="$deck.solutions = 'render'">
                <xsl:for-each select="note">
                    <div class="deck-slide-note">
                        <xsl:apply-templates/>
                    </div>
                </xsl:for-each>
            </xsl:if>
        </div>
    </xsl:if>
</xsl:template>
</xsl:stylesheet>
