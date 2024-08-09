var manual_stop = true;        // to know whether to recall recognition or not
var recognition;        // placeholder for recognition event, will need to stop later
var SpeechRecognition;  // to initiate recognition obj later


// fetches response from the flask api and write it in the paragraph and calls speak
function fetch_response(query){
    // will fetch response from api url and return json
    const url = "/result";
    const data = {
        query_text : query
    };

    fetch(url, {
        method : "POST",
        headers : {
            "Content-Type" : "application/json"
        },
        body : JSON.stringify(data)
    })

    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }

        return response.json();
    })

    .then(data => {
        console.log(data);
        document.getElementById("response_p").innerText = data.response;
        speakText(data.response);
    })

    .catch(error => {
        console.log("problem with fetch :", error)
    });
}

// will be called on file submission
function on_file_upload(event) {
    event.preventDefault();

    const file_input = document.getElementById("query_file");
    const file = file_input.files[0];

    if(file){
        // construct form data to send to url
        const form_data = new FormData();
        form_data.append("file", file);

        fetch("/process_file",{
            method : "POST",
            body : form_data
        })

        .then(response => response.json())
        .then(data => {
            console.log('Success:', data);
            window.alert("File uploaded successfully");
        })

        .catch(error => {
            console.error('Error:', error);
            window.alert("Please upload again.");
        });
    }
    
    else{
        window.alert("Please upload a valid file.");
    }
}

// speaks the text
function speakText(data) {
    // cancel any ongoing speech
    window.speechSynthesis.cancel();

    // break the text into chunks since it cant speak the whole text at once
    const chunks = data.split(/[.!?]+/)

    console.log(chunks)

    const speakChunk = (index) => {
        if (index < chunks.length) {
            const utterance = new SpeechSynthesisUtterance(chunks[index]);
            utterance.rate = 1.2;
            
            // When the last utterance finishes, restart speech recognition if not manually stopped
            if (index === chunks.length - 1) {
                utterance.onend = () => {
                    if (!manual_stop) {
                        speech_recog();
                        document.getElementById("start_stop").className = "button_green";
                    }
                };
            } else {
                // Otherwise, speak the current chunk and call for the next
                utterance.onend = () => speakChunk(index + 1);
            }
            
            window.speechSynthesis.speak(utterance);
        }
    };

    // Start speaking the first chunk
    speakChunk(0);
}

// will create a new speech recognition object and start listening
function speech_recog() {
    recognition = new SpeechRecognition();
        
    // Recognition settings
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.start()

    recognition.onresult = (event) => {
        const temp = event.results[0][0].transcript;
        console.log(temp);
        document.getElementById("query_p").innerText = temp;
        fetch_response(temp);
        document.getElementById("start_stop").className = "button_red";
        recognition.stop();
    };

    recognition.onerror = (event) => {
        console.error('Error occurred in recognition: ', event.error);
        document.getElementById("start_stop").className = "button_red";
    };
}


window.onload = () => {

    // Check for browser compatibility with SpeechRecognition
    SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
     if(!SpeechRecognition) {
        console.log('Speech Recognition API not supported in this browser.');
    }


    // mic button function
    const button = document.getElementById("start_stop")
    button.onclick = () => {
        var button_class = button.className;

        if(button_class == "button_red"){
            button.className = "button_green";
            window.speechSynthesis.cancel();
            speech_recog();
            manual_stop = false;
        }

        else{
            button.className = "button_red";
            recognition.stop();
            manual_stop = true;
        }
    }

    // to process the uploaded file
    document.getElementById("upload_form").addEventListener("submit", on_file_upload);

    // stop speech on mute button
    document.getElementById("stop_speech").onclick = () => {
        window.speechSynthesis.cancel();
        console.log("Speech stopped!")
    };

};