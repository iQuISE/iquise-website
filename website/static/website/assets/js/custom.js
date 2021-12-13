jQuery(document).ready(function(){
    jQuery(".track_last").each(function(index,html_el){
        const queryString = window.location.search;
        const urlParams = new URLSearchParams(queryString);
        // Next will either carry over or use our current location
        next_url = urlParams.get("next") || window.location.pathname

        html_el=jQuery(html_el);
        var delim = '?'
        if (html_el.attr("href").indexOf(delim) > -1) {delim = '&';};
        html_el.attr("href", html_el.attr("href")+delim+"next="+next_url);
    });
    jQuery('.close').bind('click', function(e) {
         jQuery(this).parent().fadeOut();
    });
    jQuery('.inlinechangelink').text('Details')

    jQuery('.js-copylink').click(jscopy);
});

function jscopy(event) {
      // Select the email link anchor text
      jQuery(this).append('<div id="active-coppy-wrapper"><textarea id="active-copy">'+jQuery(this).attr('data-copy')+'</textarea></div>');
      selection = window.getSelection();    // Save the selection.
      var range = document.createRange();
      range.selectNode(jQuery('#active-copy')[0]);
      selection.removeAllRanges();          // Remove all ranges from the selection.
      selection.addRange(range);            // Add the new range.
      try {
        // Now that we've selected the anchor text, execute the copy command

        var successful = document.execCommand('copy');
        var msg = successful ? 'Copied to clipboard' : 'Failed to copy';
        tempAlert(this,msg,2000);
      } catch(err) {
        tempAlert(this,'Failed to copy',2000);
      }

      // Remove the selections - NOTE: Should use
      // removeRange(range) when it is supported
      window.getSelection().removeAllRanges();
      jQuery('#active-coppy-wrapper').remove()
      return false; // prevent further callback (e.g. close side panel)
}

function tempAlert(target,msg,duration)
{
    var el = jQuery(".popup").removeClass("popup");
    el.text(msg);
    jQuery(target).append(el);
    el.slideDown(200,function(){
        setTimeout(function(){
            el.slideUp(200,function(){el.addClass("popup")});
        }, 1000);
    });
}
