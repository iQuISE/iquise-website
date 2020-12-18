const iquhack_banner = $("#banner-container");
const iquhack_banner_bg = iquhack_banner.children("img.background");
const iquhack_banner_bg_width = iquhack_banner_bg[0].naturalWidth;
const iquhack_banner_bg_height = iquhack_banner_bg[0].naturalHeight;

function resize_banner(){
    var widthRatio = iquhack_banner_bg_width / iquhack_banner.width();
    var heightRatio = iquhack_banner_bg_height / iquhack_banner.height();
    if (widthRatio > 1 && heightRatio > 1) {
        if (widthRatio > heightRatio) {
            iquhack_banner_bg.css({"height":"100%", "width":"unset"});
        } else {
            iquhack_banner_bg.css({"width":"100%", "height":"unset"});
        }
    }
};

$( document ).ready(resize_banner); // Initial resize
$( window ).resize(resize_banner);
// TODO: This won't update when the left menu is hidden/revealed