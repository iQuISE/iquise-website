jQuery(document).ready(function(){
    jQuery(".track_last").each(function(index,value){
        value=jQuery(value);
        var delim = '?'
        if (value.attr("href").indexOf(delim) > -1) {delim = '&';};
        value.attr("href", value.attr("href")+delim+"last="+window.location.pathname);
    });
    jQuery('.close').bind('click', function(e) {
         jQuery(this).parent().slideUp();
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
