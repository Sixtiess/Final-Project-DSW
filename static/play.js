$(document).ready(function() {
	// playing = $("#playing").value();
	


	$(".actionButton").click(function(){
		// console.log($(this).value)
		$.ajax({
			type: "POST",
			url:"/action",
			data: { "action" : $(this).val()},
			success: function(data){
				$(".player-hand").load(location.href + " .player-hand"); //reloads player hand div when you click an action button
				$("#actionButtonContainer").load(location.href + " #actionButtonContainer"); //reloads action buttons in case the player click stand
				console.log(data)
				var $response = $(data).filter("#actionButtonContainer").html();
				$("#actionButtonContainer").html($response);
				console.log($response);
			}
		});
		
	});
});

function checkPlaying(data) {

}