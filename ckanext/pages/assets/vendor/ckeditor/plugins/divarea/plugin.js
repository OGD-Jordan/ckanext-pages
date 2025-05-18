/**
 * @license Copyright (c) 2003-2014, CKSource - Frederico Knabben. All rights reserved.
 * For licensing, see LICENSE.md or http://ckeditor.com/license
 */
CKEDITOR.plugins.add("divarea",{afterInit:function(e){e.addMode("wysiwyg",(function(t){var i=CKEDITOR.dom.element.createFromHtml('<div class="cke_wysiwyg_div cke_reset" hidefocus="true"></div>');e.ui.space("contents").append(i),(i=e.editable(i)).detach=CKEDITOR.tools.override(i.detach,(function(e){return function(){e.apply(this,arguments),this.remove()}})),e.setData(e.getData(1),t),e.fire("contentDom")}))}});