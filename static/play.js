$(document).ready(function() {
	// playing = $("#playing").value();
	


	$(".hitButtonContainer").click(function(){
		// console.log($(this).value)
		$.ajax({
			type: "POST",
			url:"/action",
			data: { "action" : $(this).children(".hitButton").val()},
			success: function(data){
				// $(".player-hand").load(location.href + " .player-hand"); //reloads player hand div when you click an action button
				$(".cardContainer").load(location.href + " .cardContainer"); //reloads action buttons in case the player click stand
				var standButton = $(data).find(".standButtonContainer").html();
				var hitButton = $(data).find(".hitButtonContainer").html();
				$(".standButtonContainer").html(standButton);
				$(".hitButtonContainer").html(hitButton);
			}
		});
		
	});

	$(".standButtonContainer").click(function(){
		// console.log($(this).value)
		$.ajax({
			type: "POST",
			url:"/action",
			data: { "action" : $(this).children(".standButton").val()},
			success: function(data){
				// $(".player-hand").load(location.href + " .player-hand"); //reloads player hand div when you click an action button
				$(".cardContainer").load(location.href + " .cardContainer"); //reloads action buttons in case the player click stand
				var standButton = $(data).find(".standButtonContainer").html();
				var hitButton = $(data).find(".hitButtonContainer").html();
				$(".standButtonContainer").html(standButton);
				$(".hitButtonContainer").html(hitButton);
			}
		});
		
	});
});