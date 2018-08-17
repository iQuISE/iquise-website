jQuery(document).ready(function(){
    jQuery(".admin_edit").each(function(index,value){
        value=jQuery(value);
        value.attr("href", value.attr("href")+"?last="+window.location.pathname);
    });
});
