// Disable Mouse scrolling on numbers inputs
$(document).on("wheel", "input[type=number]", function (e) {
    $(this).blur();
});

// Add a highligh class when a value of the form is changed
$(".form-group :input").each(function(){
    var input_tag = $(this);
    // apply this only if the value is not empty
    if (input_tag[0].value !== ""){
        input_tag.on('keydown', function () {
            $(this).addClass('highlight');
        });
    }
});

/*
var scenarioName = '';
var timeframeChoice = '';
var evaluatedPeriod = '';

function getScenarioName(value){
	scenarioName = value;
}

function getEvaluatedPeriod(value){
	evaluatedPeriod = value;
}

function getTimeframeChoice(value){
	timeframeChoice = value;
	alert(timeframeChoice);
	if (timeframeChoice == "Year"){
		alert('Yes');
		if (evaluatedPeriod > 1)
			evaluatedPeriod = 1;
	};
	if (timeframeChoice != '' && evaluatedPeriod != ''){
		fill_out_form_scenarioSetup();
	}
}

function fill_out_form_scenarioSetup(){
	var server_data = [
		{"scenarioName": scenarioName},
		{"timeframeChoice": timeframeChoice},
		{"evaluatedPeriod": evaluatedPeriod},
	];
			
	$.ajax({
		type: "POST",
		url: "/en/project/check_time_period/",
		data: JSON.stringify(server_data),
		contentType: "application/json",
		dataType: 'json',
		success: function(response) {
			alert("Got response from server ...");
			alert(response['form_html']);
			$('#act_form_div').html(response['form_html']);
			//scenarioName = '';
			//timeframeChoice = '';
			//evaluatedPeriod = '';
			}
	});
}

$.ajaxSetup({ 
     beforeSend: function(xhr, settings) {
         function getCookie(name) {
             var cookieValue = null;
             if (document.cookie && document.cookie != '') {
                 var cookies = document.cookie.split(';');
                 for (var i = 0; i < cookies.length; i++) {
                     var cookie = jQuery.trim(cookies[i]);
                     // Does this cookie string begin with the name we want?
                     if (cookie.substring(0, name.length + 1) == (name + '=')) {
                         cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                         break;
                     }
                 }
             }
             return cookieValue;
         }
         if (!(/^http:.*/.//test(settings.url) || /^https:.*/.test(settings.url))) {
             // Only send the token to relative URLs i.e. locally.
//             xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
  //       }
    // } 
//});