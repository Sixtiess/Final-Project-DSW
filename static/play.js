$(document).ready(function() {
	playing = $("#playing").value();
	if (playing == "false") {
		$.ajax({
			type: "POST",
			url: "/action",
			success
		});
	}
});