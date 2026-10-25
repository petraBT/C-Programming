<?xml version='1.0'?>

<!-- Shared slide tooling, print side: <slide> and <instructor> never reach the
     PDF. ANY new strip-by-default element needs a template here, in
     slide-html.xsl, and the four search-index templates there. Part of the
     slide-tooling repo. -->
<!DOCTYPE xsl:stylesheet [
    <!ENTITY % entities SYSTEM "./core/entities.ent">
    %entities;
]>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">


<xsl:import href="./core/pretext-latex.xsl"/>

<!-- Omit projector slides from the printed book entirely. -->
<xsl:template match="slide"/>

<!-- Omit worked solutions from the printed book entirely.
     This template is the whole strip: without it there is no match, PreTeXt's
     stock fallback recurses into the children, and every <instructor> block is
     typeset into the PDF — and WITHOUT the "Instructor only" label, which is
     produced by the HTML template, so it reads as ordinary book prose. That was
     the state until 2026-08-11, while AUTHORING-book.md said the PDF stripped
     it; the leak was invisible because the print build died on an SVG in
     Chapter 2 and never reached Chapter 9, where the blocks are (fixed
     2026-09-27, see the image-inclusion template below).

     There is deliberately no print equivalent of web-instructor: the strip is
     unconditional here rather than keyed to book.solutions. If a printable
     answer key is ever wanted, that is a new target AND a rendering for it.

     ANY new strip-by-default element needs a template in BOTH stylesheets —
     this one and engs28-html.xsl — plus the four search-index templates the
     HTML one documents. Three places, and only one of them is obvious. -->
<xsl:template match="instructor"/>

</xsl:stylesheet>
