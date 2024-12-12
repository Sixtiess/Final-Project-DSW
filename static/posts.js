$(document).ready(function() {
	$(".post-body").data("is-cutoff", "false");
	
	var maxCutoffCharacters = 237;
	var maxCutoffLines = 3; // Does not check whether there are 3 or more lines of text, only checks return characters ("/n")
	
	
	$(".post-body").each(function() {
		var body = $(this).children("textarea.card-text");
		
		// Auto-resizes the textareas in the posts so that all the text in each post is shown (up to the maxCutoffCharacters character limit)
		body.on("input", function() {
			this.style.height = "auto";
			this.style.height = this.scrollHeight + "px";
		});
		body.trigger("input");
		
		
		var cutoffText = "";
		var fullText = body.text();
		
		if (fullText.length > maxCutoffCharacters) {
			cutoffText = fullText.substring(0, maxCutoffCharacters);
			cutoffText += "..."
			
			body.text(cutoffText);
			$(this).data("is-cutoff", "true");
			$(this).children("button.show-more-button").css("display", "block");
			
			
			// Auto-resizes the textareas in the posts so that all the text in each post is shown (up to the maxCutoffCharacters character limit)
			// Doing this a second time here to update the sizes of the posts that exceeded the character limit before storing their cutoff height
			body.on("input", function() {
				this.style.height = "auto";
				
				this.style.height = (this.scrollHeight) + "px";
			});
			body.trigger("input");
			
			body.data("full-text", fullText);
			body.data("cutoff-text", cutoffText);
			body.data("cutoff-height", body.height());
			
		} else if (countLines(fullText) > maxCutoffLines) {
			var cutoffIndex = indexOfLine(maxCutoffLines, fullText);
			
			cutoffText = fullText.substring(0, cutoffIndex);
			cutoffText += "..."
			
			body.text(cutoffText);
			$(this).data("is-cutoff", "true");
			$(this).children("button.show-more-button").css("display", "block");
			
			
			// Auto-resizes the textareas in the posts so that all the text in each post is shown (up to the maxCutoffCharacters character limit)
			// Doing this a second time here to update the sizes of the posts that exceeded the character limit before storing their cutoff height
			body.on("input", function() {
				this.style.height = "auto";
				
				this.style.height = (this.scrollHeight) + "px";
			});
			body.trigger("input");
			
			body.data("full-text", fullText);
			body.data("cutoff-text", cutoffText);
			body.data("cutoff-height", body.height());
		}
		
		else {
			body.css("height", (body.height() + 4) + "px");
		}
		
		
	});
	
	
	
	
	
	$("button.show-more-button").click(function() {
		var parentDiv = $(this).parent();
		var body = parentDiv.children("textarea.card-text");
		
		var fullText = body.data("full-text");
		var cutoffText = body.data("cutoff-text");
		var cutoffHeight = body.data("cutoff-height");
		
		if (parentDiv.data("is-cutoff") === "true") {
			$(this).text("Show Less");
			parentDiv.data("is-cutoff", "false");
			
			body.text(fullText);
			
			
			body.on("input", function() {
				this.style.height = "auto";
				this.style.height = this.scrollHeight + "px";
			});
			body.trigger("input");
			
			
			parentDiv.css("margin-bottom", "10px");
			
		} else {
			$(this).text("Show More");
			parentDiv.data("is-cutoff", "true");
			
			body.text(cutoffText);
			
			
			body.on("input", function() {
				body.css("height", (cutoffHeight + 4) + "px"); // Adding 4 because JQuery takes 4 pixels off height when using element.height() (idk why)
			});
			body.trigger("input");
			
			
			parentDiv.css("margin-bottom", "0px");
		}
	});
	
	
	$(".card-title").click(function() {
		var postID = $(this).siblings(".post_id").text();
		
		// Redirects the user to the page with only the post that they clicked on, using window.location.href because it allows the user to press the back button
		// to get back to the posts page
		window.location.href = "/post?post-id=" + postID;
	});
});


function countLines(str) {
	var numLines = 0;
	for (let i = 0; i < str.length; i++) {
		if (str[i] == '\n') {
			numLines += 1;
		}
	}
	return numLines;
}

function indexOfLine(numLines, str) {
	var linesFound = 0;
	for (let i = 0; i < str.length; i++) {
		if (str[i] == '\n') {
			linesFound += 1;
			if (linesFound == numLines) {
				return i;
			}
		}
	}
	return -1;
}

