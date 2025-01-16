$(document).ready(function() {
	// playing = $("#playing").value();
	// if (playing == "false") {
		// $.ajax({
			// type: "POST",
			// url: "/action",
			// success: function () {
				
			// }
		// });
	// }
	$(".actionButton").click(function(){
		// console.log($(this).value)
		$.ajax({
			type: "POST",
			url:"/action",
			data: { "action" : $(this).val()},
			success: function(){
				$(".player-hand").load(location.href + " .player-hand"); //reloads player hand div when you click an action button
				$("#actionButtonContainer").load(location.href + " #actionButtonContainer"); //reloads action buttons in case the player click stand
			  }
		});
		
	});
});