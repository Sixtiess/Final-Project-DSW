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
			data: { "action" : $(this).val()}
		});
	
		player_hand = $(".player-hand");
		player_hand.ajax.reload();
	});
});