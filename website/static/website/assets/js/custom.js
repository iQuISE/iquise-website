jQuery(document).ready(function(){
    jQuery(".admin_edit").each(function(index,value){
        value=jQuery(value);
        var delim = '?'
        if (value.attr("href").indexOf(delim) > -1) {delim = '&';};
        value.attr("href", value.attr("href")+delim+"last="+window.location.pathname);
    });
    jQuery('.close').bind('click', function(e) {
         jQuery(this).parent().slideUp();
    });
    jQuery('.inlinechangelink').text('Details')
});
