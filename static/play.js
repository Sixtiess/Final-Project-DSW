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
		$.ajax({
			type: "POST",
			url:"/play",
			data: { action : $(this).value}
		});
	
		);
	}
});