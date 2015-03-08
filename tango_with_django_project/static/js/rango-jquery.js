$(document).ready(function() {
	$('#likes').click(function(){
    var cat_id;
    cat_id = $(this).attr("data-catid");
    $.get('/rango/like_category/', {category_id: cat_id}, function(data){
               $('#like_count').html(data);
               $('#likes').hide();
    
    });
	});
});