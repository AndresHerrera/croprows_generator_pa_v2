/*
|-------------------------------------------
|	Simple Lightbox Video jQuery
|-------------------------------------------
|
|
|	Author: Pedro Marcelo
|	Author URI: https://github.com/pedromarcelojava
|	Plugin URI: https://github.com/pedromarcelojava/Simple-Lightbox-Video-jQuery
|	Version: 2.0
*/

(function($)
{
	$.extend($.fn, {
		simpleLightboxVideo : function()
		{
			var defaults = {
				delayAnimation: 300,
				keyCodeClose: 27
			};

			$.simpleLightboxVideo.vars = $.extend({}, defaults);

			var video = this;

			video.click(function()
			{
				if (window.innerHeight > 540)
				{
					var margintop = (window.innerHeight - 540) / 2;
				}
				else
				{
					var margintop = 0;
				}

				var ifr = '<iframe src="" width="640" height="480" id="slvj-video-embed" style="border:0;"></iframe>';
				var close = '<div id="slvj-close-icon"></div>';
				var lightbox = '<div class="slvj-lightbox" style="margin-top:' + margintop + 'px">';
				var back = '<div id="slvj-back-lightbox">';
				var bclo = '<div id="slvj-background-close"></div>';
				var win = '<div id="slvj-window">';
				var end = '</div></div></div>';

				$('body').append(win + bclo + back + lightbox + close + ifr + end);
				$('#slvj-window').hide();

				if ($(this).data('videosite') == "youtube") {
					var url = 'http://www.youtube.com/embed/' + $(this).data('videoid') + '?autoplay=1';
				} else if($(this).data('videosite') == "vimeo") {
					var url = 'http://player.vimeo.com/video/' + $(this).data('videoid') + '?autoplay=1';
				}

				$('#slvj-window').fadeIn();
				$('#slvj-video-embed').attr('src', url);

				$('#slvj-close-icon').click(function()
				{
					$('#slvj-window').fadeOut($.simpleLightboxVideo.vars.delayAnimation, function()
					{
						$(this).remove();
					});
				});

				$('#slvj-background-close').click(function()
				{
					$('#slvj-window').fadeOut($.simpleLightboxVideo.vars.delayAnimation, function()
					{
						$(this).remove();
					});
				});

				return false;
			});

			$(document).keyup(function(e)
			{
				if (e.keyCode == 27)
				{
					$('#slvj-window').fadeOut($.simpleLightboxVideo.vars.delayAnimation, function()
					{
						$(this).remove();
					});
				}
			});

			$(window).resize(function()
			{
				if (window.innerHeight > 540)
				{
					var margintop = (window.innerHeight - 540) / 2;
				}
				else
				{
					var margintop = 0;
				}

				$('.slvj-lightbox').css({
					marginTop: margintop + 'px'
				});
			});

			return false;
		}
	});
})(jQuery);

(function($)
{
	$.simpleLightboxVideo = function(options, video)
	{
		return $(video).simpleLightboxVideo();
	}
})(jQuery);